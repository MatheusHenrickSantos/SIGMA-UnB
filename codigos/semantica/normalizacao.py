"""Validação e identificação de descrições para o pipeline semântico.

As regras textuais são compartilhadas com codigos.normalizar.limpeza; este
módulo mantém apenas metadados, hashes e critérios de validade da semântica.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from functools import partial

try:  # execução no repositório
    from codigos.normalizar.limpeza import VERSAO_NORMALIZACAO, normalizar_texto as _normalizar
except ModuleNotFoundError:  # imagem enxuta do serviço semantica
    from normalizar.limpeza import VERSAO_NORMALIZACAO, normalizar_texto as _normalizar

normalizar_texto = partial(_normalizar, maiusculo=False)

TAMANHO_MINIMO = 3
SITUACAO_VALIDA = "valida"
SITUACAO_VAZIA = "vazia"
SITUACAO_INVALIDA = "invalida"


@dataclass(frozen=True)
class DescricaoNormalizada:
    """Resultado da normalização de uma descrição de origem."""

    original: str | None
    texto: str | None
    situacao: str
    motivo: str | None
    hash_original: str | None
    hash_normalizado: str | None

    @property
    def valida(self) -> bool:
        return self.situacao == SITUACAO_VALIDA


def _sha256(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def hash_normalizado(texto_normalizado: str) -> str:
    """Hash do texto normalizado, amarrado à versão das regras."""
    return _sha256(f"{VERSAO_NORMALIZACAO}\n{texto_normalizado}")


def normalizar_descricao(valor: object) -> DescricaoNormalizada:
    """Normaliza uma descrição de origem e diz se ela serve para embedding."""
    if valor is None:
        return DescricaoNormalizada(None, None, SITUACAO_VAZIA, "descrição ausente (nula)", None, None)

    original = str(valor)
    hash_original = _sha256(original)

    def recusada(situacao: str, motivo: str) -> DescricaoNormalizada:
        return DescricaoNormalizada(original, None, situacao, motivo, hash_original, None)

    if not original.strip():
        return recusada(SITUACAO_VAZIA, "descrição em branco")

    texto = normalizar_texto(original)
    if not texto:
        return recusada(SITUACAO_INVALIDA, "sem conteúdo depois da normalização")
    if not any(c.isalpha() for c in texto):
        return recusada(SITUACAO_INVALIDA, "sem letras (só números ou símbolos)")
    if len(texto) < TAMANHO_MINIMO:
        return recusada(SITUACAO_INVALIDA, f"curta demais (menos de {TAMANHO_MINIMO} caracteres)")

    return DescricaoNormalizada(
        original, texto, SITUACAO_VALIDA, None, hash_original, hash_normalizado(texto)
    )
