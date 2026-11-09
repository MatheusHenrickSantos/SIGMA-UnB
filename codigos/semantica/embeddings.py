"""Geração de embeddings: transforma texto normalizado em vetor.

Este módulo não fala com o banco nem normaliza texto: recebe textos já
normalizados e devolve vetores. Assim dá para testar o resto do pipeline
com um codificador falso, sem baixar o modelo.

Modelo padrão: intfloat/multilingual-e5-small (384 dimensões). Os modelos
da família e5 foram treinados com prefixos: 'query: ' no texto que procura
e 'passage: ' no texto onde se procura. Aqui, o material do estoque é a
consulta e o item CATMAT é o documento. Os prefixos ficam registrados junto
com o modelo no banco (semantica.modelo_embedding).
"""

from __future__ import annotations

import math
import re
from importlib import metadata
from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence

MODELO_PADRAO = "intfloat/multilingual-e5-small"

PAPEL_CONSULTA = "consulta"    # texto que procura (material do estoque)
PAPEL_DOCUMENTO = "documento"  # texto onde se procura (item CATMAT)
PAPEIS = (PAPEL_CONSULTA, PAPEL_DOCUMENTO)

_PREFIXOS_E5 = {PAPEL_CONSULTA: "query: ", PAPEL_DOCUMENTO: "passage: "}
_SEM_PREFIXO = {PAPEL_CONSULTA: "", PAPEL_DOCUMENTO: ""}
_FAMILIA_E5 = re.compile(r"(^|[/_-])e5([_-]|$)", re.IGNORECASE)


class ErroEmbedding(RuntimeError):
    """Vetor inválido ou modelo incompatível com o banco."""


class Codificador(Protocol):
    """O que o pipeline espera de um modelo de embedding."""

    nome: str
    revisao: str
    dimensao: int
    prefixos: Mapping[str, str]
    metadados: Mapping[str, Any]

    def codificar(self, textos: Sequence[str], papel: str) -> list[list[float]]:
        """Um vetor por texto, na mesma ordem."""
        ...


def prefixos_do_modelo(nome: str) -> dict[str, str]:
    """Prefixos de consulta/documento exigidos pelo modelo (vazio se nenhum)."""
    nome_curto = nome.rstrip("/").split("/")[-1]
    return dict(_PREFIXOS_E5 if _FAMILIA_E5.search(nome_curto) else _SEM_PREFIXO)


def validar_vetores(vetores: Sequence[Sequence[float]], quantidade: int, dimensao: int) -> None:
    """Falha cedo, com mensagem clara, em vez de gravar lixo no banco."""
    if len(vetores) != quantidade:
        raise ErroEmbedding(f"o modelo devolveu {len(vetores)} vetores para {quantidade} textos")
    for posicao, vetor in enumerate(vetores):
        if len(vetor) != dimensao:
            raise ErroEmbedding(
                f"vetor {posicao} tem {len(vetor)} dimensões; esperado {dimensao}"
            )
        if not all(math.isfinite(valor) for valor in vetor):
            raise ErroEmbedding(f"vetor {posicao} tem NaN ou infinito")


def _versao(pacote: str) -> str | None:
    try:
        return metadata.version(pacote)
    except metadata.PackageNotFoundError:
        return None


def _revisao_em_cache(nome: str, revisao: str | None) -> str | None:
    """Commit do modelo baixado (pasta snapshots/<commit> do cache do Hugging Face)."""
    if Path(nome).is_dir():
        return None  # modelo numa pasta local: não há commit do Hugging Face
    try:
        from huggingface_hub import try_to_load_from_cache

        caminho = try_to_load_from_cache(nome, "config.json", revision=revisao)
    except Exception:  # noqa: BLE001 - só metadado; a falha vira 'desconhecida'
        return None
    if isinstance(caminho, str):
        return Path(caminho).parent.name
    return None


class CodificadorSentenceTransformers:
    """Modelo carregado com a biblioteca sentence-transformers (CPU por padrão).

    `modelo` permite injetar um objeto compatível nos testes; em uso normal
    o modelo é baixado do Hugging Face (ou lido do cache em HF_HOME).
    """

    def __init__(
        self,
        nome: str = MODELO_PADRAO,
        revisao: str | None = None,
        dispositivo: str = "cpu",
        tamanho_lote: int = 32,
        modelo: Any = None,
    ) -> None:
        if modelo is None:
            from sentence_transformers import SentenceTransformer

            modelo = SentenceTransformer(nome, revision=revisao, device=dispositivo)
            revisao = _revisao_em_cache(nome, revisao) or revisao
        self._modelo = modelo
        self._tamanho_lote = tamanho_lote
        self.nome = nome
        self.revisao = revisao or "desconhecida"
        # get_embedding_dimension a partir da sentence-transformers 6.x
        obter_dimensao = getattr(modelo, "get_embedding_dimension", None) or getattr(
            modelo, "get_sentence_embedding_dimension"
        )
        self.dimensao = int(obter_dimensao())
        self.prefixos = prefixos_do_modelo(nome)
        self.limite_tokens = getattr(modelo, "max_seq_length", None)
        self.metadados = {
            "biblioteca": "sentence-transformers",
            "sentence_transformers": _versao("sentence-transformers"),
            "transformers": _versao("transformers"),
            "torch": _versao("torch"),
            "dispositivo": dispositivo,
            "limite_tokens": self.limite_tokens,
            "normalizado_l2": True,
        }

    def contar_truncados(self, textos: Sequence[str], papel: str) -> int:
        """Quantos textos passam do limite de tokens do modelo (o fim seria ignorado)."""
        tokenizador = getattr(self._modelo, "tokenizer", None)
        if tokenizador is None or not self.limite_tokens:
            return 0
        prefixo = self.prefixos[papel]
        ids = tokenizador([prefixo + t for t in textos], truncation=False)["input_ids"]
        return sum(1 for sequencia in ids if len(sequencia) > self.limite_tokens)

    def codificar(self, textos: Sequence[str], papel: str) -> list[list[float]]:
        if papel not in PAPEIS:
            raise ValueError(f"papel inválido: {papel!r}")
        prefixo = self.prefixos[papel]
        vetores = self._modelo.encode(
            [prefixo + texto for texto in textos],
            # prompt="" impede que um prompt padrão da configuração do modelo
            # seja somado ao prefixo explícito acima
            prompt="",
            batch_size=self._tamanho_lote,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return [[float(valor) for valor in vetor] for vetor in vetores]
