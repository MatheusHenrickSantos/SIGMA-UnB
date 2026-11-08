"""Leitura e gravação do schema semantica no PostgreSQL.

Só SQL: este módulo não normaliza texto nem chama o modelo. As funções que
gravam abrem a própria transação, por isso esperam uma conexão com
autocommit=True (a mesma convenção de codigos/carregar.py).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import psycopg
from psycopg.types.json import Jsonb

from .normalizacao import VERSAO_NORMALIZACAO, DescricaoNormalizada

ORIGENS = ("estoque", "catmat")


class ErroOrigem(RuntimeError):
    """A origem lida não pode ser sincronizada (vazia, por exemplo)."""


@dataclass(frozen=True)
class ResumoSincronizacao:
    origem: str
    lidas: int
    novas: int
    alteradas: int
    desativadas: int
    validas: int
    recusadas: int
    vetores_descartados: int


def exigir_autocommit(conn: psycopg.Connection) -> None:
    if not conn.autocommit:
        raise ValueError(
            "use uma conexão com autocommit=True: cada etapa abre a própria transação"
        )


def literal_vetor(vetor: Sequence[float]) -> str:
    """Formato de texto do pgvector. 9 dígitos preservam um float32."""
    return "[" + ",".join(f"{valor:.9g}" for valor in vetor) + "]"


# ---------------------------------------------------------------------------
# Modelo
# ---------------------------------------------------------------------------

def dimensao_da_coluna(conn: psycopg.Connection) -> int:
    """Dimensão declarada em semantica.embedding.vetor (vector(N))."""
    linha = conn.execute(
        "SELECT atttypmod FROM pg_attribute "
        "WHERE attrelid = 'semantica.embedding'::regclass AND attname = 'vetor'"
    ).fetchone()
    return int(linha[0])


def registrar_modelo(
    conn: psycopg.Connection,
    nome: str,
    revisao: str,
    dimensao: int,
    prefixos: Mapping[str, str],
    metadados: Mapping[str, Any],
) -> int:
    """Devolve o id do modelo, registrando-o na primeira vez.

    O registro é imutável: os metadados gravados são os da primeira execução.
    """
    exigir_autocommit(conn)
    with conn.transaction():
        id_modelo, dimensao_gravada = conn.execute(
            """
            INSERT INTO semantica.modelo_embedding
                (nome, revisao, dimensao, prefixo_consulta, prefixo_documento, metadados)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT ON CONSTRAINT uq_modelo DO UPDATE SET nome = EXCLUDED.nome
            RETURNING id_modelo, dimensao
            """,
            (nome, revisao, dimensao, prefixos["consulta"], prefixos["documento"],
             Jsonb(dict(metadados))),
        ).fetchone()
    if dimensao_gravada != dimensao:
        raise ValueError(
            f"modelo {nome}@{revisao} já registrado com {dimensao_gravada} dimensões, "
            f"agora gera {dimensao}"
        )
    return id_modelo


# ---------------------------------------------------------------------------
# Descrições
# ---------------------------------------------------------------------------

_CONTEUDO_MUDOU = """
    (d.hash_original, d.hash_normalizado, d.versao_normalizacao, d.situacao, d.motivo, d.ativa)
    IS DISTINCT FROM
    ({0}.hash_original, {0}.hash_normalizado, %(versao)s, {0}.situacao, {0}.motivo, true)
"""


def gravar_descricoes(
    conn: psycopg.Connection,
    origem: str,
    descricoes: Sequence[tuple[str, DescricaoNormalizada]],
) -> ResumoSincronizacao:
    """Aplica uma fotografia completa da origem, numa transação só.

    - chave nova: inserida; chave com texto ou regra mudada: atualizada;
    - chave que sumiu da origem: marcada ativa = false (a linha fica, porque
      candidatos antigos apontam para ela);
    - vetores de descrições inativas, inválidas ou com texto mudado são
      apagados: na tabela embedding só fica vetor atual.
    """
    exigir_autocommit(conn)
    if origem not in ORIGENS:
        raise ValueError(f"origem desconhecida: {origem!r}")
    if not descricoes:
        raise ErroOrigem(
            f"a origem {origem!r} veio vazia; nada foi alterado "
            "(confira se a Prata foi gerada pelo dbt)"
        )

    parametros = {"origem": origem, "versao": VERSAO_NORMALIZACAO}
    with conn.transaction(), conn.cursor() as cur:
        cur.execute(
            """
            CREATE TEMP TABLE tmp_descricao (
                chave_origem      TEXT PRIMARY KEY,
                texto_original    TEXT,
                hash_original     CHAR(64),
                texto_normalizado TEXT,
                hash_normalizado  CHAR(64),
                situacao          TEXT NOT NULL,
                motivo            TEXT
            ) ON COMMIT DROP
            """
        )
        with cur.copy(
            "COPY tmp_descricao (chave_origem, texto_original, hash_original, "
            "texto_normalizado, hash_normalizado, situacao, motivo) FROM STDIN"
        ) as copia:
            for chave, d in descricoes:
                copia.write_row(
                    (chave, d.original, d.hash_original, d.texto, d.hash_normalizado,
                     d.situacao, d.motivo)
                )

        novas, alteradas = cur.execute(
            f"""
            SELECT count(*) FILTER (WHERE d.id_descricao IS NULL),
                   count(*) FILTER (WHERE d.id_descricao IS NOT NULL AND {_CONTEUDO_MUDOU.format('t')})
            FROM tmp_descricao AS t
            LEFT JOIN semantica.descricao AS d
                   ON d.origem = %(origem)s AND d.chave_origem = t.chave_origem
            """,
            parametros,
        ).fetchone()

        cur.execute(
            f"""
            INSERT INTO semantica.descricao AS d
                (origem, chave_origem, texto_original, hash_original, texto_normalizado,
                 hash_normalizado, versao_normalizacao, situacao, motivo)
            SELECT %(origem)s, chave_origem, texto_original, hash_original, texto_normalizado,
                   hash_normalizado, %(versao)s, situacao, motivo
            FROM tmp_descricao
            ON CONFLICT (origem, chave_origem) DO UPDATE SET
                texto_original      = EXCLUDED.texto_original,
                hash_original       = EXCLUDED.hash_original,
                texto_normalizado   = EXCLUDED.texto_normalizado,
                hash_normalizado    = EXCLUDED.hash_normalizado,
                versao_normalizacao = EXCLUDED.versao_normalizacao,
                situacao            = EXCLUDED.situacao,
                motivo              = EXCLUDED.motivo,
                ativa               = true,
                sincronizada_em     = now(),
                atualizada_em       = CASE
                    WHEN (d.hash_original, d.hash_normalizado, d.situacao)
                         IS DISTINCT FROM
                         (EXCLUDED.hash_original, EXCLUDED.hash_normalizado, EXCLUDED.situacao)
                    THEN now() ELSE d.atualizada_em END
            WHERE {_CONTEUDO_MUDOU.format('EXCLUDED')}
            """,
            parametros,
        )

        cur.execute(
            """
            UPDATE semantica.descricao AS d
            SET ativa = false, sincronizada_em = now()
            WHERE d.origem = %(origem)s AND d.ativa
              AND NOT EXISTS (SELECT 1 FROM tmp_descricao t WHERE t.chave_origem = d.chave_origem)
            """,
            parametros,
        )
        desativadas = cur.rowcount

        cur.execute(
            """
            DELETE FROM semantica.embedding AS e
            USING semantica.descricao AS d
            WHERE e.id_descricao = d.id_descricao
              AND d.origem = %(origem)s
              AND (NOT d.ativa OR d.situacao <> 'valida'
                   OR e.hash_normalizado IS DISTINCT FROM d.hash_normalizado)
            """,
            parametros,
        )
        vetores_descartados = cur.rowcount

    validas = sum(1 for _, d in descricoes if d.valida)
    return ResumoSincronizacao(
        origem=origem,
        lidas=len(descricoes),
        novas=novas,
        alteradas=alteradas,
        desativadas=desativadas,
        validas=validas,
        recusadas=len(descricoes) - validas,
        vetores_descartados=vetores_descartados,
    )


# ---------------------------------------------------------------------------
# Vetores
# ---------------------------------------------------------------------------

def reaproveitar_vetores(conn: psycopg.Connection, id_modelo: int, origem: str) -> int:
    """Copia o vetor de uma descrição com o mesmo texto normalizado (e origem)."""
    exigir_autocommit(conn)
    with conn.transaction():
        cursor = conn.execute(
            """
            INSERT INTO semantica.embedding (id_descricao, origem, id_modelo, hash_normalizado, vetor)
            SELECT DISTINCT ON (d.id_descricao)
                   d.id_descricao, d.origem, %(modelo)s, d.hash_normalizado, e.vetor
            FROM semantica.descricao AS d
            JOIN semantica.embedding AS e
              ON e.origem = d.origem
             AND e.id_modelo = %(modelo)s
             AND e.hash_normalizado = d.hash_normalizado
            WHERE d.origem = %(origem)s AND d.ativa AND d.situacao = 'valida'
              AND NOT EXISTS (
                  SELECT 1 FROM semantica.embedding x
                  WHERE x.id_descricao = d.id_descricao AND x.id_modelo = %(modelo)s
              )
            ORDER BY d.id_descricao, e.id_descricao
            """,
            {"modelo": id_modelo, "origem": origem},
        )
        return cursor.rowcount


def descricoes_pendentes(
    conn: psycopg.Connection, id_modelo: int, origem: str
) -> list[tuple[int, str, str]]:
    """(id_descricao, texto_normalizado, hash) das válidas sem vetor atual."""
    return conn.execute(
        """
        SELECT d.id_descricao, d.texto_normalizado, d.hash_normalizado
        FROM semantica.descricao AS d
        WHERE d.origem = %(origem)s AND d.ativa AND d.situacao = 'valida'
          AND NOT EXISTS (
              SELECT 1 FROM semantica.embedding e
              WHERE e.id_descricao = d.id_descricao
                AND e.id_modelo = %(modelo)s
                AND e.hash_normalizado = d.hash_normalizado
          )
        ORDER BY d.id_descricao
        """,
        {"modelo": id_modelo, "origem": origem},
    ).fetchall()


def gravar_vetores(
    conn: psycopg.Connection,
    id_modelo: int,
    origem: str,
    linhas: Sequence[tuple[int, str, Sequence[float]]],
) -> None:
    """Grava (id_descricao, hash, vetor) numa transação; regrava se já existir."""
    exigir_autocommit(conn)
    with conn.transaction(), conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO semantica.embedding (id_descricao, origem, id_modelo, hash_normalizado, vetor)
            VALUES (%s, %s, %s, %s, %s::vector)
            ON CONFLICT (id_descricao, id_modelo) DO UPDATE SET
                hash_normalizado = EXCLUDED.hash_normalizado,
                vetor            = EXCLUDED.vetor,
                gerado_em        = now()
            """,
            [(id_descricao, origem, id_modelo, hash_, literal_vetor(vetor))
             for id_descricao, hash_, vetor in linhas],
        )
