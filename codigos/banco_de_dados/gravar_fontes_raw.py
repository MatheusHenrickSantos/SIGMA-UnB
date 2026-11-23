"""Persistência direta das respostas das APIs nas tabelas da camada raw."""

from __future__ import annotations

import json
import re
from datetime import date
from typing import Any

from psycopg.types.json import Jsonb

from .conectar_com_banco_de_dados import conectar
from codigos.utilidades import calcular_hash

_ARQUIVO_ESTOQUE = re.compile(r"estoque-do-almoxarifado-(\d{2})-(\d{4})\.json\Z")


def serializar_json(dado: Any, *, indent: int | None = None) -> str:
    """Usa a mesma representação estável que os antigos arquivos JSON."""
    return json.dumps(dado, ensure_ascii=False, indent=indent)


def salvar_estoque(nome_recurso: str, conteudo: str, dado: list[dict]) -> bool:
    """Grava uma resposta mensal do estoque; devolve False se já existia."""
    correspondencia = _ARQUIVO_ESTOQUE.fullmatch(nome_recurso)
    if correspondencia is None:
        raise ValueError(f"Nome de recurso de estoque inválido: {nome_recurso}")
    mes, ano = map(int, correspondencia.groups())
    if not 1 <= mes <= 12:
        raise ValueError(f"Mês inválido no recurso de estoque: {nome_recurso}")

    with conectar() as conn:
        cursor = conn.execute(
            """
            INSERT INTO raw.estoque
                (dado_bruto, hash_do_arquivo, mes_de_referencia, ano_de_referencia)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (hash_do_arquivo) DO NOTHING
            RETURNING 1
            """,
            (Jsonb(dado), calcular_hash(conteudo), mes, ano),
        )
        return cursor.fetchone() is not None


def salvar_catmat(dado: list[dict], conteudo: str) -> bool:
    """Grava o catálogo CATMAT completo; devolve False se já existia."""
    with conectar() as conn:
        cursor = conn.execute(
            """
            INSERT INTO raw.catmat (dado_bruto, hash_do_arquivo)
            VALUES (%s, %s)
            ON CONFLICT (hash_do_arquivo) DO NOTHING
            RETURNING 1
            """,
            (Jsonb(dado), calcular_hash(conteudo)),
        )
        return cursor.fetchone() is not None


def compras_coletadas(inicio: date, fim: date) -> set[int]:
    """Códigos já processados por completo nesta janela, inclusive sem compras."""
    with conectar() as conn:
        linhas = conn.execute(
            """
            SELECT codigo_item_catalogo
            FROM raw.compras_coleta
            WHERE data_inicio = %s AND data_fim = %s
            """,
            (inicio, fim),
        ).fetchall()
    return {linha[0] for linha in linhas}


def salvar_compras(
    codigo: int,
    inicio: date,
    fim: date,
    registros: list[dict],
    conteudo: str,
) -> bool:
    """Grava o resultado e o checkpoint do código na mesma transação."""
    with conectar() as conn:
        with conn.transaction():
            inserido = False
            if registros:
                cursor = conn.execute(
                    """
                    INSERT INTO raw.compras (dado_bruto, hash_do_arquivo)
                    VALUES (%s, %s)
                    ON CONFLICT (hash_do_arquivo) DO NOTHING
                    RETURNING 1
                    """,
                    (Jsonb(registros), calcular_hash(conteudo)),
                )
                inserido = cursor.fetchone() is not None
            conn.execute(
                """
                INSERT INTO raw.compras_coleta
                    (codigo_item_catalogo, data_inicio, data_fim, total_registros)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (codigo_item_catalogo, data_inicio, data_fim)
                DO NOTHING
                """,
                (codigo, inicio, fim, len(registros)),
            )
    return inserido
