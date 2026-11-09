"""Testes da geração de embeddings: codificador, sincronização e incremental."""

from __future__ import annotations

import psycopg
import pytest

from codificador_teste import CodificadorDeTeste
from semantica import processamento, repositorio
from semantica.embeddings import (
    CodificadorSentenceTransformers,
    ErroEmbedding,
    prefixos_do_modelo,
    validar_vetores,
)

ESTOQUE = [
    ("ma0001", "PAPEL A4, 75G/M2, BRANCO"),
    ("ma0002", "CANETA ESFEROGRAFICA AZUL"),
    ("ma0003", "caneta esferografica  azul"),  # mesmo texto normalizado de ma0002
    ("ma0004", "1234"),                         # inválida: sem letras
    ("ma0005", None),                           # vazia
]


def conectar(dsn: str) -> psycopg.Connection:
    return psycopg.connect(dsn, autocommit=True)


def contar(conn, tabela: str) -> int:
    return conn.execute(f"SELECT count(*) FROM {tabela}").fetchone()[0]


# ---------------------------------------------------------------------------
# Codificador (sem banco)
# ---------------------------------------------------------------------------

class ModeloFalso:
    """Imita a interface de SentenceTransformer usada pelo codificador."""

    max_seq_length = 4

    def __init__(self) -> None:
        self.recebidos: list[list[str]] = []
        self.opcoes: dict = {}

    def get_embedding_dimension(self) -> int:
        return 3

    def encode(self, textos, **opcoes):
        self.recebidos.append(list(textos))
        self.opcoes = opcoes
        return [[1.0, 0.0, 0.0] for _ in textos]

    def tokenizer(self, textos, truncation):
        return {"input_ids": [texto.split() for texto in textos]}


@pytest.mark.parametrize("nome, consulta", [
    ("intfloat/multilingual-e5-small", "query: "),
    ("intfloat/multilingual-e5-base", "query: "),
    ("intfloat/e5-base-v2", "query: "),
    ("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", ""),
    ("BAAI/bge-m3", ""),
])
def teste_prefixos_por_familia_de_modelo(nome, consulta):
    assert prefixos_do_modelo(nome)["consulta"] == consulta


def teste_codificador_aplica_prefixo_por_papel_e_normaliza():
    modelo = ModeloFalso()
    codificador = CodificadorSentenceTransformers("intfloat/multilingual-e5-small", modelo=modelo)
    codificador.codificar(["papel a4"], "consulta")
    codificador.codificar(["papel a4"], "documento")
    assert modelo.recebidos == [["query: papel a4"], ["passage: papel a4"]]
    assert modelo.opcoes["normalize_embeddings"] is True
    assert modelo.opcoes["prompt"] == ""
    assert codificador.dimensao == 3
    assert codificador.revisao == "desconhecida"
    assert codificador.metadados["limite_tokens"] == 4


def teste_codificador_recusa_papel_desconhecido():
    codificador = CodificadorSentenceTransformers("x/e5", modelo=ModeloFalso())
    with pytest.raises(ValueError):
        codificador.codificar(["a"], "outro")


def teste_codificador_conta_textos_acima_do_limite_de_tokens():
    codificador = CodificadorSentenceTransformers("intfloat/multilingual-e5-small", modelo=ModeloFalso())
    # 'query:' + 3 palavras = 4 tokens (no limite); + 4 palavras = 5 (passa)
    assert codificador.contar_truncados(["a b c", "a b c d"], "consulta") == 1


@pytest.mark.parametrize("vetores, mensagem", [
    ([[0.1, 0.2]], "2 dimensões"),
    ([[0.1, 0.2, float("nan")]], "NaN"),
    ([], "0 vetores"),
])
def teste_validar_vetores(vetores, mensagem):
    with pytest.raises(ErroEmbedding, match=mensagem):
        validar_vetores(vetores, 1, 3)


def teste_chave_repetida_vale_a_ultima_e_sem_chave_e_descartada():
    descricoes, sem_chave, repetidas = processamento.normalizar_registros(
        [("1", "PAPEL A4"), ("1", "PAPEL A3"), (None, "CANETA"), ("  ", "LAPIS")]
    )
    assert [(chave, d.texto) for chave, d in descricoes] == [("1", "papel a3")]
    assert (sem_chave, repetidas) == (2, 1)


# ---------------------------------------------------------------------------
# Sincronização e vetores (com banco)
# ---------------------------------------------------------------------------

def teste_sincronizacao_guarda_original_normalizado_e_motivo(banco):
    with conectar(banco) as conn:
        resumo, sem_chave, repetidas = processamento.sincronizar_origem(conn, "estoque", ESTOQUE)
        linhas = {
            linha[0]: linha[1:]
            for linha in conn.execute(
                "SELECT chave_origem, texto_original, texto_normalizado, situacao, motivo "
                "FROM semantica.descricao"
            )
        }

    assert (resumo.lidas, resumo.novas, resumo.validas, resumo.recusadas) == (5, 5, 3, 2)
    assert (sem_chave, repetidas) == (0, 0)
    assert linhas["ma0003"] == ("caneta esferografica  azul", "caneta esferografica azul", "valida", None)
    assert linhas["ma0004"][2:] == ("invalida", "sem letras (só números ou símbolos)")
    assert linhas["ma0005"] == (None, None, "vazia", "descrição ausente (nula)")


def teste_sincronizar_de_novo_nao_altera_nada(banco):
    with conectar(banco) as conn:
        processamento.sincronizar_origem(conn, "estoque", ESTOQUE)
        antes = conn.execute("SELECT max(atualizada_em) FROM semantica.descricao").fetchone()[0]
        resumo, _, _ = processamento.sincronizar_origem(conn, "estoque", ESTOQUE)
        depois = conn.execute("SELECT max(atualizada_em) FROM semantica.descricao").fetchone()[0]
    assert (resumo.novas, resumo.alteradas, resumo.desativadas) == (0, 0, 0)
    assert antes == depois


def teste_origem_vazia_e_recusada_sem_alterar_nada(banco):
    with conectar(banco) as conn:
        processamento.sincronizar_origem(conn, "estoque", ESTOQUE)
        with pytest.raises(repositorio.ErroOrigem):
            processamento.sincronizar_origem(conn, "estoque", [])
        assert conn.execute(
            "SELECT count(*) FROM semantica.descricao WHERE ativa"
        ).fetchone()[0] == 5


def teste_embeddings_so_das_validas_sem_recalcular_texto_repetido(banco):
    codificador = CodificadorDeTeste()
    with conectar(banco) as conn:
        processamento.sincronizar_origem(conn, "estoque", ESTOQUE)
        id_modelo = processamento.preparar_modelo(conn, codificador)
        resumo = processamento.atualizar_embeddings(conn, codificador, id_modelo, "estoque", "consulta")
        total = contar(conn, "semantica.embedding")

    assert (resumo.pendentes, resumo.gravados) == (3, 3)
    # ma0002 e ma0003 têm o mesmo texto normalizado: o modelo vê 2 textos
    assert sorted(codificador.textos_enviados) == ["caneta esferografica azul", "papel a4, 75 g/m2, branco"]
    assert total == 3


def teste_reexecucao_nao_duplica_nem_recalcula(banco):
    codificador = CodificadorDeTeste()
    with conectar(banco) as conn:
        processamento.sincronizar_origem(conn, "estoque", ESTOQUE)
        id_modelo = processamento.preparar_modelo(conn, codificador)
        processamento.atualizar_embeddings(conn, codificador, id_modelo, "estoque", "consulta")
        chamadas = len(codificador.chamadas)
        resumo = processamento.atualizar_embeddings(conn, codificador, id_modelo, "estoque", "consulta")
        assert processamento.preparar_modelo(conn, codificador) == id_modelo
        total = contar(conn, "semantica.embedding")
        modelos = contar(conn, "semantica.modelo_embedding")

    assert (resumo.pendentes, resumo.textos_enviados_ao_modelo) == (0, 0)
    assert len(codificador.chamadas) == chamadas
    assert (total, modelos) == (3, 1)


def teste_texto_alterado_recalcula_so_ele(banco):
    codificador = CodificadorDeTeste()
    with conectar(banco) as conn:
        processamento.sincronizar_origem(conn, "estoque", ESTOQUE)
        id_modelo = processamento.preparar_modelo(conn, codificador)
        processamento.atualizar_embeddings(conn, codificador, id_modelo, "estoque", "consulta")

        alterado = [("ma0001", "PAPEL A4, 90G/M2, BRANCO")] + ESTOQUE[1:]
        sinc, _, _ = processamento.sincronizar_origem(conn, "estoque", alterado)
        resumo = processamento.atualizar_embeddings(conn, codificador, id_modelo, "estoque", "consulta")

    assert (sinc.alteradas, sinc.vetores_descartados) == (1, 1)
    assert (resumo.pendentes, resumo.textos_enviados_ao_modelo) == (1, 1)
    assert codificador.chamadas[-1] == ["papel a4, 90 g/m2, branco"]


def teste_chave_que_some_e_volta(banco):
    codificador = CodificadorDeTeste()
    with conectar(banco) as conn:
        processamento.sincronizar_origem(conn, "estoque", ESTOQUE)
        id_modelo = processamento.preparar_modelo(conn, codificador)
        processamento.atualizar_embeddings(conn, codificador, id_modelo, "estoque", "consulta")

        sem_ma0003 = [r for r in ESTOQUE if r[0] != "ma0003"]
        saiu, _, _ = processamento.sincronizar_origem(conn, "estoque", sem_ma0003)
        assert contar(conn, "semantica.embedding") == 2

        voltou, _, _ = processamento.sincronizar_origem(conn, "estoque", ESTOQUE)
        enviados_antes = len(codificador.textos_enviados)
        resumo = processamento.atualizar_embeddings(conn, codificador, id_modelo, "estoque", "consulta")

    assert (saiu.desativadas, saiu.vetores_descartados) == (1, 1)
    assert voltou.alteradas == 1
    # o texto de ma0003 é igual ao de ma0002: o vetor é copiado, sem chamar o modelo
    assert resumo.reaproveitados == 1
    assert len(codificador.textos_enviados) == enviados_antes


def teste_dimensao_incompativel_falha_antes_de_gravar(banco):
    with conectar(banco) as conn:
        with pytest.raises(ErroEmbedding, match=r"vector\(384\)"):
            processamento.preparar_modelo(conn, CodificadorDeTeste(dimensao=10))
        assert contar(conn, "semantica.modelo_embedding") == 0


def teste_falha_no_meio_mantem_lotes_anteriores_e_retoma(banco):
    with conectar(banco) as conn:
        processamento.sincronizar_origem(conn, "estoque", ESTOQUE)
        quebrado = CodificadorDeTeste(falhar_na_chamada=2)
        id_modelo = processamento.preparar_modelo(conn, quebrado)
        with pytest.raises(ErroEmbedding, match="lote 2"):
            processamento.atualizar_embeddings(conn, quebrado, id_modelo, "estoque", "consulta", tamanho_lote=1)
        assert contar(conn, "semantica.embedding") == 1

        resumo = processamento.atualizar_embeddings(
            conn, CodificadorDeTeste(), id_modelo, "estoque", "consulta", tamanho_lote=1
        )
        assert resumo.reaproveitados + resumo.gravados == 2
        assert contar(conn, "semantica.embedding") == 3


def teste_vetor_com_nan_nao_e_gravado(banco):
    with conectar(banco) as conn:
        processamento.sincronizar_origem(conn, "estoque", ESTOQUE)
        codificador = CodificadorDeTeste(devolver_nan=True)
        id_modelo = processamento.preparar_modelo(conn, codificador)
        with pytest.raises(ErroEmbedding):
            processamento.atualizar_embeddings(conn, codificador, id_modelo, "estoque", "consulta")
        assert contar(conn, "semantica.embedding") == 0


def teste_modelo_registrado_com_metadados(banco):
    with conectar(banco) as conn:
        processamento.preparar_modelo(conn, CodificadorDeTeste())
        nome, dimensao, metadados = conn.execute(
            "SELECT nome, dimensao, metadados FROM semantica.modelo_embedding"
        ).fetchone()
    assert (nome, dimensao, metadados) == ("teste/hash-de-palavras", 384, {"tipo": "codificador de teste"})


def teste_exige_conexao_em_autocommit(banco):
    with psycopg.connect(banco) as conn:
        with pytest.raises(ValueError, match="autocommit"):
            processamento.sincronizar_origem(conn, "estoque", ESTOQUE)
