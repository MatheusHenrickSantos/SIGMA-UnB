"""Testes das migrações de busca e correspondência num PostgreSQL real."""

from __future__ import annotations

import math

import psycopg
import pytest

from semantica.correspondencia import SQL_INDICE_HNSW

DIMENSAO = 384


def vetor(*inicio: float) -> str:
    """Literal pgvector de 384 posições: os valores dados e zeros no resto."""
    valores = list(inicio) + [0.0] * (DIMENSAO - len(inicio))
    return "[" + ",".join(repr(float(v)) for v in valores) + "]"


def _modelo(cur) -> int:
    cur.execute(
        "INSERT INTO busca.modelo_embedding (nome, revisao, dimensao) "
        "VALUES ('teste', 'r1', 384) RETURNING id_modelo"
    )
    return cur.fetchone()[0]


def _descricao(cur, origem: str, chave: str, texto: str = "texto") -> int:
    cur.execute(
        """
        INSERT INTO busca.descricao (origem, chave_origem, texto_original, hash_original,
                                         texto_normalizado, hash_normalizado,
                                         versao_normalizacao, situacao)
        VALUES (%s, %s, %s, repeat('a', 64), %s, repeat('b', 64), '1', 'valida')
        RETURNING id_descricao
        """,
        (origem, chave, texto, texto),
    )
    return cur.fetchone()[0]


def _embedding(cur, id_descricao: int, origem: str, id_modelo: int, literal: str) -> None:
    cur.execute(
        "INSERT INTO busca.embedding (id_descricao, origem, id_modelo, hash_normalizado, vetor) "
        "VALUES (%s, %s, %s, repeat('b', 64), %s::vector)",
        (id_descricao, origem, id_modelo, literal),
    )


def teste_objetos_criados(banco):
    with psycopg.connect(banco) as conn:
        versao = conn.execute(
            "SELECT extversion FROM pg_extension WHERE extname = 'vector'"
        ).fetchone()[0]
        tabelas_busca = {
            linha[0] for linha in conn.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'busca'"
            )
        }
        tabelas_prata = {
            linha[0] for linha in conn.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'prata'"
            )
        }
        indices_hnsw = conn.execute(
            "SELECT count(*) FROM pg_indexes WHERE schemaname = 'busca' AND indexdef ILIKE '%%hnsw%%'"
        ).fetchone()[0]
        dimensao = conn.execute(
            "SELECT atttypmod FROM pg_attribute "
            "WHERE attrelid = 'busca.embedding'::regclass AND attname = 'vetor'"
        ).fetchone()[0]
        schema_antigo = conn.execute("SELECT to_regnamespace('semantica')").fetchone()[0]

    assert tuple(int(p) for p in versao.split(".")[:2]) >= (0, 8)
    assert {"modelo_embedding", "descricao", "embedding", "execucao_correspondencia"} <= tabelas_busca
    assert {
        "candidato_catmat", "revisao_correspondencia", "revisao_material",
        "v_candidato_catmat", "v_fila_revisao", "v_item_aprovado",
    } <= tabelas_prata
    assert schema_antigo is None
    # criado na V2 e removido na V3 (ADR 0005): a busca é exata
    assert indices_hnsw == 0
    assert dimensao == DIMENSAO


def teste_tabelas_da_v1_continuam_existindo(banco):
    with psycopg.connect(banco) as conn:
        for tabela in ("public.material", "public.estoque_saldo", "public.carga_execucao"):
            assert conn.execute("SELECT to_regclass(%s)", (tabela,)).fetchone()[0] is not None


def teste_ordem_por_distancia_de_cosseno_e_indice_recriavel(banco):
    with psycopg.connect(banco) as conn, conn.cursor() as cur:
        id_modelo = _modelo(cur)
        # ângulos crescentes em relação à consulta (1, 0)
        for chave, x, y in (("perto", 1.0, 0.1), ("medio", 1.0, 1.0), ("longe", 0.1, 1.0)):
            _embedding(cur, _descricao(cur, "catmat", chave), "catmat", id_modelo, vetor(x, y))
        consulta = vetor(1.0, 0.0)
        sql = """
            SELECT d.chave_origem, e.vetor <=> %s::vector AS distancia
            FROM busca.embedding e
            JOIN busca.descricao d USING (id_descricao)
            WHERE e.origem = 'catmat'
            ORDER BY e.vetor <=> %s::vector
            LIMIT 3
        """
        linhas = cur.execute(sql, (consulta, consulta)).fetchall()

        # o índice removido na V3 pode ser recriado e é usado pela mesma consulta
        cur.execute(SQL_INDICE_HNSW.format(nome="ix_embedding_catmat_hnsw"))
        cur.execute("SET enable_seqscan = off")
        plano = "\n".join(
            linha[0]
            for linha in cur.execute(
                "EXPLAIN SELECT id_descricao FROM busca.embedding WHERE origem = 'catmat' "
                "ORDER BY vetor <=> %s::vector LIMIT 3",
                (consulta,),
            )
        )

    assert [chave for chave, _ in linhas] == ["perto", "medio", "longe"]
    # distância de cosseno = 1 - cos(ângulo)
    assert linhas[1][1] == pytest.approx(1 - 1 / math.sqrt(2), abs=1e-6)
    assert "ix_embedding_catmat_hnsw" in plano


def teste_dimensao_errada_e_recusada(banco):
    with psycopg.connect(banco) as conn, conn.cursor() as cur:
        id_modelo = _modelo(cur)
        id_descricao = _descricao(cur, "catmat", "x")
        with pytest.raises(psycopg.errors.DataException, match="384"):
            _embedding(cur, id_descricao, "catmat", id_modelo, "[1,2,3]")


def teste_nan_e_recusado(banco):
    with psycopg.connect(banco) as conn, conn.cursor() as cur:
        id_modelo = _modelo(cur)
        id_descricao = _descricao(cur, "catmat", "x")
        literal = "[NaN" + ",0" * (DIMENSAO - 1) + "]"
        with pytest.raises(psycopg.errors.DataException):
            _embedding(cur, id_descricao, "catmat", id_modelo, literal)


def teste_origem_do_embedding_tem_que_bater_com_a_descricao(banco):
    with psycopg.connect(banco) as conn, conn.cursor() as cur:
        id_modelo = _modelo(cur)
        id_descricao = _descricao(cur, "estoque", "ma0001")
        with pytest.raises(psycopg.errors.ForeignKeyViolation):
            _embedding(cur, id_descricao, "catmat", id_modelo, vetor(1.0))


def teste_descricao_valida_exige_texto_normalizado(banco):
    with psycopg.connect(banco) as conn, conn.cursor() as cur:
        with pytest.raises(psycopg.errors.CheckViolation):
            cur.execute(
                "INSERT INTO busca.descricao (origem, chave_origem, texto_original, hash_original, "
                "versao_normalizacao, situacao) VALUES ('estoque', 'ma1', 'x', repeat('a', 64), '1', 'valida')"
            )


def teste_descricao_invalida_exige_motivo(banco):
    with psycopg.connect(banco) as conn, conn.cursor() as cur:
        with pytest.raises(psycopg.errors.CheckViolation):
            cur.execute(
                "INSERT INTO busca.descricao (origem, chave_origem, texto_original, hash_original, "
                "versao_normalizacao, situacao) VALUES ('estoque', 'ma1', '', repeat('a', 64), '1', 'vazia')"
            )


def teste_apagar_descricao_apaga_seus_vetores(banco):
    with psycopg.connect(banco) as conn, conn.cursor() as cur:
        id_modelo = _modelo(cur)
        id_descricao = _descricao(cur, "catmat", "x")
        _embedding(cur, id_descricao, "catmat", id_modelo, vetor(1.0))
        cur.execute("DELETE FROM busca.descricao WHERE id_descricao = %s", (id_descricao,))
        assert cur.execute("SELECT count(*) FROM busca.embedding").fetchone()[0] == 0
