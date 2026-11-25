"""Persistência direta das respostas das APIs nas tabelas da camada raw."""

from __future__ import annotations

import json
import os
import re
from datetime import date
from typing import Any

from psycopg.types.json import Jsonb

from .conectar_com_banco_de_dados import conectar
from codigos.utilidades import calcular_hash

_ARQUIVO_ESTOQUE = re.compile(r"estoque-do-almoxarifado-(\d{2})-(\d{4})\.json\Z")

# Identificação do fornecedor: a análise de preço não usa (LGPD, ADR 0012). A API devolve
# CNPJ ou CPF e o nome; o CPF é de pessoa física.
CAMPOS_FORNECEDOR = ("niFornecedor", "nomeFornecedor")


def remover_fornecedor_ativo() -> bool:
    """Minimização na gravação; desligue com REMOVER_IDENTIFICACAO_FORNECEDOR=false."""
    return os.environ.get("REMOVER_IDENTIFICACAO_FORNECEDOR", "true").strip().lower() not in (
        "0", "false", "nao", "não", "no",
    )


def sem_identificacao_do_fornecedor(registros: list[dict]) -> list[dict]:
    """Cópia dos registros sem os campos do fornecedor (o original não é alterado)."""
    return [{k: v for k, v in r.items() if k not in CAMPOS_FORNECEDOR} for r in registros]


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


def catmat_em_cache() -> bool:
    """Indica se o banco já contém um snapshot completo do CATMAT."""
    with conectar() as conn:
        linha = conn.execute(
            "SELECT completa FROM raw.catmat_coleta WHERE id_coleta = 1"
        ).fetchone()
    return bool(linha and linha[0])


def catmat_cache_vencido(validade_dias: int) -> bool:
    """True se o snapshot do CATMAT em raw tem mais de `validade_dias` dias (0 = nunca vence)."""
    if validade_dias <= 0:
        return False
    with conectar() as conn:
        linha = conn.execute(
            "SELECT atualizada_em < now() - make_interval(days => %s) "
            "FROM raw.catmat_coleta WHERE id_coleta = 1",
            (validade_dias,),
        ).fetchone()
    return bool(linha and linha[0])


def salvar_catmat(
    dado: list[dict],
    conteudo: str,
    *,
    completa: bool,
    total_paginas: int,
) -> bool:
    """Substitui o snapshot na raw e atualiza o cache persistido no banco."""
    hash_conteudo = calcular_hash(conteudo)
    with conectar() as conn:
        with conn.transaction():
            # CATMAT é um snapshot do catálogo vigente; manter versões
            # anteriores juntas duplicaria itens na Bronze.
            conn.execute("DELETE FROM raw.catmat")
            cursor = conn.execute(
                """
                INSERT INTO raw.catmat (dado_bruto, hash_do_arquivo)
                VALUES (%s, %s)
                RETURNING 1
                """,
                (Jsonb(dado), hash_conteudo),
            )
            conn.execute(
                """
                INSERT INTO raw.catmat_coleta
                    (id_coleta, completa, total_paginas, total_itens,
                     hash_do_arquivo, atualizada_em)
                VALUES (1, %s, %s, %s, %s, now())
                ON CONFLICT (id_coleta) DO UPDATE SET
                    completa = EXCLUDED.completa,
                    total_paginas = EXCLUDED.total_paginas,
                    total_itens = EXCLUDED.total_itens,
                    hash_do_arquivo = EXCLUDED.hash_do_arquivo,
                    atualizada_em = EXCLUDED.atualizada_em
                """,
                (completa, total_paginas, len(dado), hash_conteudo),
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

            UNION

            SELECT DISTINCT
                NULLIF(elemento ->> 'codigoItemCatalogo', '')::INTEGER
            FROM raw.compras AS compras
            CROSS JOIN LATERAL jsonb_array_elements(compras.dado_bruto) AS item(elemento)
            WHERE NULLIF(elemento ->> 'codigoItemCatalogo', '') IS NOT NULL
              AND NULLIF(elemento ->> 'dataCompra', '')::DATE BETWEEN %s AND %s
            """,
            (inicio, fim, inicio, fim),
        ).fetchall()
    return {linha[0] for linha in linhas}


def salvar_compras(
    codigo: int,
    inicio: date,
    fim: date,
    registros: list[dict],
    conteudo: str,
) -> bool:
    """Grava o resultado e o checkpoint do código na mesma transação.

    O hash é o do conteúdo ORIGINAL (deduplicação idempotente, ADR 0009); o que vai para a
    raw já sai sem o fornecedor, então o dado pessoal nunca chega ao banco.
    """
    gravar = sem_identificacao_do_fornecedor(registros) if remover_fornecedor_ativo() else registros
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
                    (Jsonb(gravar), calcular_hash(conteudo)),
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
