"""Testes da importação de decisões em lote (semantica/decisoes.py) e da V5."""

from __future__ import annotations

import psycopg
import pytest

from codificador_teste import CodificadorDeTeste
from semantica import correspondencia, decisoes, processamento
from semantica.correspondencia import ParametrosBusca

ESTOQUE = [
    ("ma0001", "PILHA ALCALINA AAA 1,5V"),
    ("ma0002", "CANETA ESFEROGRAFICA AZUL"),
    ("ma0003", "ARTEFATO SEM EQUIVALENTE"),
]
CATMAT = [
    ("990011", "PILHA, TIPO: ALCALINA, TAMANHO: AAA, TENSÃO NOMINAL: 1,5 V"),
    ("990012", "PILHA ALCALINA AAA 1,5 V CARTELA"),
    ("990020", "CANETA ESFEROGRÁFICA, COR: AZUL"),
]


def conectar(dsn: str) -> psycopg.Connection:
    return psycopg.connect(dsn, autocommit=True)


def preparar(conn) -> None:
    processamento.sincronizar_origem(conn, "estoque", ESTOQUE)
    processamento.sincronizar_origem(conn, "catmat", CATMAT)


def linha(material, codigos="", sem="nao", confianca="alta", justificativa="", revisor=None):
    registro = {"material": material, "codigos_equivalentes": codigos, "sem_correspondente": sem,
                "confianca": confianca, "justificativa": justificativa}
    if revisor:
        registro["revisor"] = revisor
    return registro


def pares(conn) -> set[tuple]:
    return set(conn.execute(
        "SELECT texto_material, codigo_item, decisao, tipo_revisor, revisor "
        "FROM semantica.revisao_correspondencia"
    ).fetchall())


@pytest.mark.parametrize("registro, trecho", [
    (linha(""), "material vazio"),
    (linha("X", "1", sem="talvez"), "sem_correspondente"),
    (linha("X", "1", confianca="total"), "confianca"),
    (linha("X", "1|abc"), "não numérico"),
    (linha("X", "1", sem="sim"), "com códigos"),
    (linha("X", ""), "sem códigos"),
])
def teste_linhas_invalidas_sao_recusadas(registro, trecho):
    decisao, erro = decisoes.interpretar(registro)
    assert decisao is None and trecho in erro


def teste_interpretar_ordena_codigos_e_aceita_acentos():
    decisao, erro = decisoes.interpretar(linha("X", "30|4| 200", sem="não", confianca="média"))
    assert erro is None
    assert decisao.codigos == ("4", "30", "200")
    assert decisao.sem_correspondente is False and decisao.confianca == "media"


def teste_importa_pares_e_decisao_por_material(banco):
    with conectar(banco) as conn:
        preparar(conn)
        resumo = decisoes.importar(conn, [
            linha("PILHA ALCALINA AAA 1,5V", "990012|990011", confianca="media", justificativa="mesma pilha"),
            linha("ARTEFATO SEM EQUIVALENTE", sem="sim", confianca="baixa"),
        ], "agente:teste", "agente")
        gravados = pares(conn)
        por_material = {texto: resto for texto, *resto in conn.execute(
            "SELECT texto_material, sem_correspondente, confianca, tipo_revisor "
            "FROM semantica.revisao_material"
        ).fetchall()}
        aprovados = conn.execute(
            "SELECT identificador_material, codigo_item FROM semantica.v_item_aprovado ORDER BY 2"
        ).fetchall()
        observacao = conn.execute(
            "SELECT observacao FROM semantica.revisao_correspondencia LIMIT 1"
        ).fetchone()[0]

    assert (resumo.materiais, resumo.sem_correspondente, resumo.pares_equivalentes) == (2, 1, 2)
    assert gravados == {
        ("PILHA ALCALINA AAA 1,5V", "990011", "equivalente", "agente", "agente:teste"),
        ("PILHA ALCALINA AAA 1,5V", "990012", "equivalente", "agente", "agente:teste"),
    }
    assert por_material["ARTEFATO SEM EQUIVALENTE"] == [True, "baixa", "agente"]
    assert aprovados == [("ma0001", "990011"), ("ma0001", "990012")]
    assert observacao == "confiança media; mesma pilha"


def teste_reimportar_substitui_e_nao_duplica(banco):
    with conectar(banco) as conn:
        preparar(conn)
        decisoes.importar(conn, [linha("PILHA ALCALINA AAA 1,5V", "990011|990012")], "agente:a", "agente")
        decisoes.importar(conn, [linha("PILHA ALCALINA AAA 1,5V", "990012")], "agente:a", "agente")
        gravados = pares(conn)
        materiais = conn.execute("SELECT count(*) FROM semantica.revisao_material").fetchone()[0]

    assert {codigo for _, codigo, *_ in gravados} == {"990012"}
    assert materiais == 1


def teste_agente_nao_sobrescreve_pessoa_e_pessoa_sobrescreve_agente(banco):
    with conectar(banco) as conn:
        preparar(conn)
        decisoes.importar(conn, [linha("CANETA ESFEROGRAFICA AZUL", "990020")], "agente:a", "agente")
        correspondencia.registrar_revisao(conn, "ma0002", "990020", "nao_equivalente", "Ana")
        decisoes.importar(conn, [linha("CANETA ESFEROGRAFICA AZUL", sem="sim", revisor="Bia")],
                          "x", "pessoa")
        resumo = decisoes.importar(conn, [linha("CANETA ESFEROGRAFICA AZUL", "990020")], "agente:a", "agente")
        gravados = pares(conn)
        material = conn.execute(
            "SELECT sem_correspondente, revisor, tipo_revisor FROM semantica.revisao_material"
        ).fetchone()

    assert gravados == {("CANETA ESFEROGRAFICA AZUL", "990020", "nao_equivalente", "pessoa", "Ana")}
    assert material == (True, "Bia", "pessoa")
    assert resumo.preservadas_de_pessoa == 1


def teste_material_ou_codigo_desconhecido_e_recusado_sem_parar_o_resto(banco):
    with conectar(banco) as conn:
        preparar(conn)
        resumo = decisoes.importar(conn, [
            linha("MATERIAL QUE NAO EXISTE", "990011"),
            linha("PILHA ALCALINA AAA 1,5V", "990011|123"),
            linha("CANETA ESFEROGRAFICA AZUL", "990020"),
        ], "agente:a", "agente")

    assert resumo.materiais == 1
    assert len(resumo.recusadas) == 2
    assert any("não encontrado" in r for r in resumo.recusadas)
    assert any("['123']" in r for r in resumo.recusadas)


def teste_fila_mantem_decisao_de_agente_e_tira_decisao_de_pessoa(banco):
    codificador = CodificadorDeTeste()
    with conectar(banco) as conn:
        preparar(conn)
        id_modelo = processamento.preparar_modelo(conn, codificador)
        processamento.atualizar_embeddings(conn, codificador, id_modelo, "estoque", "consulta")
        processamento.atualizar_embeddings(conn, codificador, id_modelo, "catmat", "documento")
        correspondencia.executar_correspondencia(conn, id_modelo, ParametrosBusca(top_k=3))
        decisoes.importar(conn, [
            linha("PILHA ALCALINA AAA 1,5V", "990011", confianca="baixa"),
            linha("ARTEFATO SEM EQUIVALENTE", sem="sim"),
        ], "agente:a", "agente")
        antes = conn.execute(
            "SELECT DISTINCT identificador_material, confianca_sugestao, sugestao_sem_correspondente "
            "FROM semantica.v_fila_revisao ORDER BY 1"
        ).fetchall()
        correspondencia.registrar_revisao(conn, "ma0001", "990011", "equivalente", "Ana")
        decisoes.importar(conn, [linha("ARTEFATO SEM EQUIVALENTE", sem="sim")], "Bia", "pessoa")
        depois = {m for (m,) in conn.execute("SELECT DISTINCT identificador_material FROM semantica.v_fila_revisao")}

    assert antes == [("ma0001", "baixa", False), ("ma0002", None, None), ("ma0003", "alta", True)]
    assert depois == {"ma0002"}


def teste_parametros_invalidos(banco):
    with conectar(banco) as conn:
        with pytest.raises(ValueError):
            decisoes.importar(conn, [], "a", "robo")
        with pytest.raises(ValueError):
            decisoes.importar(conn, [], " ", "agente")
