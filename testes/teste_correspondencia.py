"""Testes da correspondência top-K por cosseno e da revisão humana."""

from __future__ import annotations

import math
import random

import psycopg
import pytest

from codificador_teste import CodificadorDeTeste
from semantica import correspondencia, processamento, repositorio
from semantica.correspondencia import ErroCorrespondencia, ParametrosBusca

DIMENSAO = 384


def conectar(dsn: str) -> psycopg.Connection:
    return psycopg.connect(dsn, autocommit=True)


def angulo(graus: float) -> list[float]:
    """Vetor unitário no plano das duas primeiras dimensões."""
    radianos = math.radians(graus)
    return [math.cos(radianos), math.sin(radianos)] + [0.0] * (DIMENSAO - 2)


def preparar(conn, estoque: dict[str, list[float] | None], catmat: dict[str, list[float]]) -> int:
    """Sincroniza as descrições e grava vetores escolhidos à mão. Devolve id_modelo."""
    processamento.sincronizar_origem(conn, "estoque", [(c, f"MATERIAL {c}") for c in estoque])
    processamento.sincronizar_origem(conn, "catmat", [(c, f"ITEM CATMAT {c}") for c in catmat])
    id_modelo = processamento.preparar_modelo(conn, CodificadorDeTeste())
    for origem, vetores in (("estoque", estoque), ("catmat", catmat)):
        ids = dict(conn.execute(
            "SELECT chave_origem, id_descricao FROM semantica.descricao WHERE origem = %s", (origem,)
        ).fetchall())
        repositorio.gravar_vetores(
            conn, id_modelo, origem,
            [(ids[chave], "x" * 64, vetor) for chave, vetor in vetores.items() if vetor is not None],
        )
    return id_modelo


def candidatos(conn, id_execucao: int) -> list[tuple]:
    return conn.execute(
        "SELECT identificador_material, posicao, codigo_item, similaridade, vantagem_sobre_proximo "
        "FROM semantica.v_candidato_catmat WHERE id_execucao = %s "
        "ORDER BY identificador_material, posicao",
        (id_execucao,),
    ).fetchall()


CATMAT = {"c10": angulo(10), "c30": angulo(30), "c60": angulo(60), "c90": angulo(90)}


def teste_top_k_em_ordem_de_similaridade(banco):
    with conectar(banco) as conn:
        id_modelo = preparar(conn, {"m1": angulo(0)}, CATMAT)
        resumo = correspondencia.executar_correspondencia(conn, id_modelo, ParametrosBusca(top_k=3, metodo="cosseno"))
        linhas = candidatos(conn, resumo.id_execucao)

    assert [codigo for _, _, codigo, _, _ in linhas] == ["c10", "c30", "c60"]
    assert [posicao for _, posicao, _, _, _ in linhas] == [1, 2, 3]
    for (_, _, _, similaridade, _), graus in zip(linhas, (10, 30, 60)):
        assert similaridade == pytest.approx(math.cos(math.radians(graus)), abs=1e-6)
    assert linhas[0][4] == pytest.approx(math.cos(math.radians(10)) - math.cos(math.radians(30)), abs=1e-6)
    assert linhas[2][4] is None
    assert (resumo.materiais, resumo.candidatos, resumo.materiais_sem_candidato) == (1, 3, 0)


def teste_limiar_filtra_depois_do_top_k(banco):
    with conectar(banco) as conn:
        id_modelo = preparar(conn, {"m1": angulo(0)}, CATMAT)
        parcial = correspondencia.executar_correspondencia(
            conn, id_modelo, ParametrosBusca(top_k=4, limiar_similaridade=0.8)
        )
        nenhum = correspondencia.executar_correspondencia(
            conn, id_modelo, ParametrosBusca(top_k=4, limiar_similaridade=0.99)
        )
        assert [linha[2] for linha in candidatos(conn, parcial.id_execucao)] == ["c10", "c30"]
    assert (nenhum.candidatos, nenhum.materiais_sem_candidato) == (0, 1)


def teste_reexecucao_reproduz_os_mesmos_candidatos(banco):
    with conectar(banco) as conn:
        id_modelo = preparar(conn, {"m1": angulo(0), "m2": angulo(85)}, CATMAT)
        primeira = correspondencia.executar_correspondencia(conn, id_modelo)
        segunda = correspondencia.executar_correspondencia(conn, id_modelo)
        a = [linha[:4] for linha in candidatos(conn, primeira.id_execucao)]
        b = [linha[:4] for linha in candidatos(conn, segunda.id_execucao)]
    assert a == b and len(a) == 8


def teste_busca_exata_e_indice_concordam(banco):
    sorteio = random.Random(2026)

    def aleatorio() -> list[float]:
        vetor = [sorteio.gauss(0, 1) for _ in range(DIMENSAO)]
        norma = math.sqrt(sum(v * v for v in vetor))
        return [v / norma for v in vetor]

    catmat = {f"c{i:03d}": aleatorio() for i in range(300)}
    estoque = {f"m{i}": aleatorio() for i in range(5)}
    with conectar(banco) as conn:
        id_modelo = preparar(conn, estoque, catmat)
        exata = correspondencia.executar_correspondencia(
            conn, id_modelo, ParametrosBusca(top_k=5, busca_exata=True)
        )
        # sem índice desde a V3: recria-o e, como com 300 linhas o planejador
        # prefere varrer a tabela, força o uso dele
        conn.execute(correspondencia.SQL_INDICE_HNSW.format(nome="ix_embedding_catmat_hnsw"))
        conn.execute("SET enable_seqscan = off")
        plano = "\n".join(linha[0] for linha in conn.execute(
            "EXPLAIN " + correspondencia._BUSCA,
            {"modelo": id_modelo, "top_k": 5, "limiar": None, "chaves": None},
        ))
        indice = correspondencia.executar_correspondencia(
            conn, id_modelo, ParametrosBusca(top_k=5, ef_search=100)
        )
        a = [linha[:3] for linha in candidatos(conn, exata.id_execucao)]
        b = [linha[:3] for linha in candidatos(conn, indice.id_execucao)]
    assert "ix_embedding_catmat_hnsw" in plano
    assert a == b and len(a) == 25


def teste_sem_indice_a_busca_padrao_e_exata(banco):
    parametros = {"modelo": 1, "top_k": 5, "limiar": None, "chaves": None}
    with conectar(banco) as conn:
        plano = "\n".join(r[0] for r in conn.execute("EXPLAIN " + correspondencia._BUSCA, parametros))
    assert "hnsw" not in plano.lower()
    # a ordem por distância sai de uma ordenação completa (exata), não de índice
    assert "Sort Key: ((c.vetor <=> em.vetor))" in plano


def teste_com_indice_recriado_so_a_busca_aproximada_o_usa(banco):
    parametros = {"modelo": 1, "top_k": 5, "limiar": None, "chaves": None}
    with conectar(banco) as conn, conn.transaction():
        conn.execute(correspondencia.SQL_INDICE_HNSW.format(nome="ix_embedding_catmat_hnsw"))
        conn.execute("SET LOCAL enable_seqscan = off")
        aproximada = "\n".join(r[0] for r in conn.execute("EXPLAIN " + correspondencia._BUSCA, parametros))
        conn.execute("SET LOCAL enable_seqscan = on")
        conn.execute("SET LOCAL enable_indexscan = off")
        exata = "\n".join(r[0] for r in conn.execute("EXPLAIN " + correspondencia._BUSCA, parametros))
    assert "ix_embedding_catmat_hnsw" in aproximada
    assert "ix_embedding_catmat_hnsw" not in exata


def teste_sem_vetores_catmat_falha_com_mensagem(banco):
    with conectar(banco) as conn:
        processamento.sincronizar_origem(conn, "estoque", [("m1", "PAPEL A4")])
        id_modelo = processamento.preparar_modelo(conn, CodificadorDeTeste())
        with pytest.raises(ErroCorrespondencia, match="embeddings"):
            correspondencia.executar_correspondencia(conn, id_modelo)
        assert conn.execute("SELECT count(*) FROM semantica.execucao_correspondencia").fetchone()[0] == 0


def teste_material_sem_vetor_e_contado(banco):
    with conectar(banco) as conn:
        id_modelo = preparar(conn, {"m1": angulo(0), "m2": None}, CATMAT)
        resumo = correspondencia.executar_correspondencia(conn, id_modelo, ParametrosBusca(top_k=2))
    assert (resumo.materiais, resumo.materiais_sem_vetor, resumo.materiais_sem_candidato) == (2, 1, 1)


@pytest.mark.parametrize("parametros", [
    ParametrosBusca(top_k=0),
    ParametrosBusca(top_k=101),
    ParametrosBusca(top_k=10, ef_search=5),
    ParametrosBusca(limiar_similaridade=1.5),
])
def teste_parametros_invalidos(parametros):
    with pytest.raises(ValueError):
        parametros.validar()


def teste_execucao_e_atomica(banco, monkeypatch):
    with conectar(banco) as conn:
        id_modelo = preparar(conn, {"m1": angulo(0)}, CATMAT)
        chamadas = []

        def quebra(*args):
            chamadas.append(args)
            if len(chamadas) == 2:
                raise RuntimeError("falha simulada")
            return "sem_especificacoes_verificaveis", {}

        monkeypatch.setattr(correspondencia, "avaliar_especificacoes", quebra)
        with pytest.raises(RuntimeError):
            correspondencia.executar_correspondencia(conn, id_modelo)
        assert conn.execute("SELECT count(*) FROM semantica.execucao_correspondencia").fetchone()[0] == 0
        assert conn.execute("SELECT count(*) FROM semantica.candidato_catmat").fetchone()[0] == 0


# ---------------------------------------------------------------------------
# Especificações com o codificador de teste (palavras em comum)
# ---------------------------------------------------------------------------

def teste_conflito_de_especificacao_e_marcado(banco):
    codificador = CodificadorDeTeste()
    with conectar(banco) as conn:
        processamento.sincronizar_origem(conn, "estoque", [("ma0001", "PILHA ALCALINA AAA 1,5V")])
        processamento.sincronizar_origem(conn, "catmat", [
            ("990010", "PILHA, TIPO: ALCALINA, TAMANHO: AA, TENSÃO NOMINAL: 1,5 V"),
            ("990011", "PILHA, TIPO: ALCALINA, TAMANHO: AAA, TENSÃO NOMINAL: 1,5 V"),
            ("990013", "SACO PLÁSTICO LIXO, CAPACIDADE: 100 L, COR: PRETA"),
        ])
        id_modelo = processamento.preparar_modelo(conn, codificador)
        processamento.atualizar_embeddings(conn, codificador, id_modelo, "estoque", "consulta")
        processamento.atualizar_embeddings(conn, codificador, id_modelo, "catmat", "documento")
        resumo = correspondencia.executar_correspondencia(conn, id_modelo, ParametrosBusca(top_k=2, metodo="cosseno"))
        linhas = dict(conn.execute(
            "SELECT codigo_item, situacao_especificacao FROM semantica.v_candidato_catmat "
            "WHERE id_execucao = %s", (resumo.id_execucao,)
        ).fetchall())
        detalhes = conn.execute(
            "SELECT especificacoes FROM semantica.v_candidato_catmat "
            "WHERE id_execucao = %s AND codigo_item = '990010'", (resumo.id_execucao,)
        ).fetchone()[0]

    assert set(linhas) == {"990010", "990011"}
    assert linhas["990010"] == "conflito_tecnico"
    assert linhas["990011"] != "conflito_tecnico"
    assert "formato_pilha" in detalhes["conflitos"]
    assert resumo.candidatos_com_conflito == 1


# ---------------------------------------------------------------------------
# Revisão humana
# ---------------------------------------------------------------------------

def teste_revisao_sobrevive_a_nova_execucao_e_sai_da_fila(banco):
    with conectar(banco) as conn:
        id_modelo = preparar(conn, {"m1": angulo(0), "m2": angulo(85)}, CATMAT)
        correspondencia.executar_correspondencia(conn, id_modelo, ParametrosBusca(top_k=2))
        correspondencia.registrar_revisao(conn, "m1", "c10", "equivalente", "Revisora", "conferido")
        nova = correspondencia.executar_correspondencia(conn, id_modelo, ParametrosBusca(top_k=2))

        decisao = conn.execute(
            "SELECT decisao, revisor FROM semantica.v_candidato_catmat "
            "WHERE id_execucao = %s AND identificador_material = 'm1' AND codigo_item = 'c10'",
            (nova.id_execucao,),
        ).fetchone()
        na_fila = {linha[0] for linha in conn.execute(
            "SELECT DISTINCT identificador_material FROM semantica.v_fila_revisao"
        )}
        execucoes_na_fila = {linha[0] for linha in conn.execute(
            "SELECT DISTINCT id_execucao FROM semantica.v_fila_revisao"
        )}

    assert decisao == ("equivalente", "Revisora")
    assert na_fila == {"m2"}
    assert execucoes_na_fila == {nova.id_execucao}


def teste_revisao_vale_para_o_texto_revisado(banco):
    with conectar(banco) as conn:
        id_modelo = preparar(conn, {"m1": angulo(0)}, CATMAT)
        correspondencia.registrar_revisao(conn, "m1", "c10", "nao_equivalente", "Revisora")
        # o texto do material muda na origem: a decisão antiga não se aplica mais
        processamento.sincronizar_origem(conn, "estoque", [("m1", "MATERIAL m1 DESCRIÇÃO NOVA")])
        repositorio.gravar_vetores(conn, id_modelo, "estoque", [(
            conn.execute("SELECT id_descricao FROM semantica.descricao WHERE chave_origem = 'm1'").fetchone()[0],
            "y" * 64, angulo(0),
        )])
        resumo = correspondencia.executar_correspondencia(conn, id_modelo, ParametrosBusca(top_k=1))
        decisao = conn.execute(
            "SELECT decisao FROM semantica.v_candidato_catmat WHERE id_execucao = %s", (resumo.id_execucao,)
        ).fetchone()[0]
        guardada = conn.execute("SELECT count(*) FROM semantica.revisao_correspondencia").fetchone()[0]
    assert decisao is None
    assert guardada == 1


@pytest.mark.parametrize("material, codigo, decisao, revisor, erro", [
    ("m1", "c10", "talvez", "Revisora", ValueError),
    ("m1", "c10", "equivalente", " ", ValueError),
    ("m9", "c10", "equivalente", "Revisora", ErroCorrespondencia),
    ("m1", "c99", "equivalente", "Revisora", ErroCorrespondencia),
])
def teste_revisao_recusa_dados_invalidos(banco, material, codigo, decisao, revisor, erro):
    with conectar(banco) as conn:
        preparar(conn, {"m1": angulo(0)}, CATMAT)
        with pytest.raises(erro):
            correspondencia.registrar_revisao(conn, material, codigo, decisao, revisor)


# ---------------------------------------------------------------------------
# Busca híbrida (cosseno + trigramas, reordenada)
# ---------------------------------------------------------------------------

def preparar_com_textos(conn, estoque: dict[str, tuple[str, list[float]]],
                        catmat: dict[str, tuple[str, list[float]]]) -> int:
    """Como preparar(), mas com o texto de cada descrição escolhido pelo teste."""
    processamento.sincronizar_origem(conn, "estoque", [(c, t) for c, (t, _) in estoque.items()])
    processamento.sincronizar_origem(conn, "catmat", [(c, t) for c, (t, _) in catmat.items()])
    id_modelo = processamento.preparar_modelo(conn, CodificadorDeTeste())
    for origem, dados in (("estoque", estoque), ("catmat", catmat)):
        ids = dict(conn.execute(
            "SELECT chave_origem, id_descricao FROM semantica.descricao WHERE origem = %s", (origem,)
        ).fetchall())
        repositorio.gravar_vetores(
            conn, id_modelo, origem, [(ids[c], "x" * 64, v) for c, (_, v) in dados.items()]
        )
    return id_modelo


def hibridos(conn, id_execucao: int) -> list[tuple]:
    return conn.execute(
        "SELECT posicao, codigo_item, pontuacao, recuperado_por, situacao_especificacao, medidas "
        "FROM semantica.v_candidato_catmat WHERE id_execucao = %s ORDER BY posicao",
        (id_execucao,),
    ).fetchall()


def teste_hibrido_poe_na_frente_o_texto_parecido(banco):
    with conectar(banco) as conn:
        id_modelo = preparar_com_textos(
            conn,
            {"m1": ("RESISTOR 1,2 KOHM 1/4 W", angulo(0))},
            {"c_errado": ("CAPACITOR CERAMICO 1,2 NF 50 V", angulo(25)),
             "c_certo": ("RESISTOR, RESISTENCIA: 1,2 KOHM, POTENCIA: 1/4 W", angulo(30)),
             "c_longe": ("SACO PLASTICO PARA LIXO 100 L", angulo(80))},
        )
        resumo = correspondencia.executar_correspondencia(conn, id_modelo, ParametrosBusca(top_k=3))
        linhas = hibridos(conn, resumo.id_execucao)
        execucao = conn.execute(
            "SELECT metodo, k_vetor, k_trigrama, versao_reordenacao, pesos "
            "FROM semantica.execucao_correspondencia WHERE id_execucao = %s",
            (resumo.id_execucao,),
        ).fetchone()

    assert [codigo for _, codigo, *_ in linhas] == ["c_certo", "c_errado", "c_longe"]
    pontuacoes = [p for _, _, p, *_ in linhas]
    assert pontuacoes == sorted(pontuacoes, reverse=True)
    assert set(linhas[0][5]) == {"cosseno", "token_set", "token_sort", "cobertura"}
    assert execucao[:4] == ("hibrido", 50, 20, "1")
    assert execucao[4]["cosseno"] == pytest.approx(0.40)


def teste_hibrido_recupera_por_trigrama_o_que_o_vetor_deixou_de_fora(banco):
    with conectar(banco) as conn:
        id_modelo = preparar_com_textos(
            conn,
            {"m1": ("LUVA LATEX PROCEDIMENTO TAMANHO M", angulo(0))},
            {"c_vetor": ("CAIXA ORGANIZADORA PLASTICA", angulo(5)),
             "c_texto": ("LUVA PROCEDIMENTO, MATERIAL: LATEX, TAMANHO: M", angulo(70))},
        )
        resumo = correspondencia.executar_correspondencia(
            conn, id_modelo, ParametrosBusca(top_k=2, k_vetor=2, k_trigrama=1)
        )
        so_vetor = correspondencia.executar_correspondencia(
            conn, id_modelo, ParametrosBusca(top_k=1, k_vetor=1, k_trigrama=0)
        )
        linhas = hibridos(conn, resumo.id_execucao)
        linhas_so_vetor = hibridos(conn, so_vetor.id_execucao)

    por_codigo = {codigo: recuperado for _, codigo, _, recuperado, *_ in linhas}
    assert por_codigo["c_texto"] == ["vetor", "trigrama"]
    assert por_codigo["c_vetor"] == ["vetor"]
    assert linhas[0][1] == "c_texto"
    # sem trigramas e com um vizinho só, o item certo nem aparece
    assert [codigo for _, codigo, *_ in linhas_so_vetor] == ["c_vetor"]


def teste_hibrido_poe_conflito_de_especificacao_por_ultimo(banco):
    with conectar(banco) as conn:
        id_modelo = preparar_com_textos(
            conn,
            {"m1": ("PILHA ALCALINA AAA 1,5V", angulo(0))},
            {"990010": ("PILHA ALCALINA AA 1,5V", angulo(5)),
             "990011": ("PILHA, TIPO: ALCALINA, TAMANHO: AAA, TENSÃO NOMINAL: 1,5 V", angulo(20))},
        )
        resumo = correspondencia.executar_correspondencia(conn, id_modelo, ParametrosBusca(top_k=2))
        linhas = hibridos(conn, resumo.id_execucao)

    assert [(codigo, situacao) for _, codigo, _, _, situacao, _ in linhas][0][0] == "990011"
    assert linhas[1][1] == "990010"
    assert linhas[1][4] == "conflito_tecnico"
    # a pontuação do item em conflito é maior: a ordem vem do conflito, não dela
    assert linhas[1][2] > linhas[0][2]
    assert resumo.candidatos_com_conflito == 1


def teste_cosseno_nao_grava_pontuacao(banco):
    with conectar(banco) as conn:
        id_modelo = preparar(conn, {"m1": angulo(0)}, CATMAT)
        resumo = correspondencia.executar_correspondencia(
            conn, id_modelo, ParametrosBusca(top_k=2, metodo="cosseno")
        )
        linhas = hibridos(conn, resumo.id_execucao)
        metodo = conn.execute(
            "SELECT metodo, k_vetor, pesos FROM semantica.execucao_correspondencia "
            "WHERE id_execucao = %s", (resumo.id_execucao,)
        ).fetchone()

    assert all(pontuacao is None for _, _, pontuacao, *_ in linhas)
    assert metodo == ("cosseno", None, None)


@pytest.mark.parametrize("parametros", [
    ParametrosBusca(metodo="outro"),
    ParametrosBusca(top_k=10, k_vetor=5),
    ParametrosBusca(k_trigrama=-1),
    ParametrosBusca(k_vetor=50, ef_search=40),
])
def teste_parametros_hibridos_invalidos(parametros):
    with pytest.raises(ValueError):
        parametros.validar()
