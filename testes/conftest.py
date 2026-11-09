"""Fixtures compartilhadas pelos testes.

Testes marcados com a fixture `banco` precisam de um PostgreSQL 16 com a
extensão pgvector. Eles só rodam quando a variável SIGMA_TESTES_BANCO aponta
para um banco de manutenção onde o usuário pode criar e apagar bancos, por
exemplo:

    SIGMA_TESTES_BANCO="host=localhost user=sigma password=sigma dbname=postgres" pytest

Com o Docker Compose do projeto no ar (porta 5432 exposta), o mesmo valor
funciona. Sem a variável, esses testes são pulados.
"""

from __future__ import annotations

import os
import re
import uuid
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
PASTA_MIGRACOES = RAIZ / "db" / "migrations"


def _versao(caminho: Path) -> int:
    return int(re.match(r"V(\d+)__", caminho.name).group(1))


def migracoes() -> list[Path]:
    """Arquivos V<n>__*.sql na ordem em que o Flyway os aplicaria."""
    return sorted(PASTA_MIGRACOES.glob("V*__*.sql"), key=_versao)


@pytest.fixture(scope="session")
def dsn_manutencao() -> str:
    dsn = os.environ.get("SIGMA_TESTES_BANCO")
    if not dsn:
        pytest.skip("defina SIGMA_TESTES_BANCO para rodar os testes com banco")
    return dsn


def _dsn_para(dsn_manutencao: str, banco: str) -> str:
    import psycopg.conninfo

    partes = psycopg.conninfo.conninfo_to_dict(dsn_manutencao)
    partes["dbname"] = banco
    return psycopg.conninfo.make_conninfo(**partes)


@pytest.fixture(scope="session")
def banco_modelo(dsn_manutencao: str):
    """Banco com todas as migrações aplicadas, usado como TEMPLATE."""
    import psycopg

    nome = f"sigma_teste_modelo_{uuid.uuid4().hex[:8]}"
    with psycopg.connect(dsn_manutencao, autocommit=True) as conn:
        conn.execute(f'CREATE DATABASE "{nome}"')
    try:
        with psycopg.connect(_dsn_para(dsn_manutencao, nome), autocommit=True) as conn:
            for caminho in migracoes():
                conn.execute(caminho.read_text(encoding="utf-8"))
        yield nome
    finally:
        with psycopg.connect(dsn_manutencao, autocommit=True) as conn:
            conn.execute(f'DROP DATABASE IF EXISTS "{nome}" WITH (FORCE)')


@pytest.fixture
def banco(dsn_manutencao: str, banco_modelo: str) -> str:
    """DSN de um banco novo, já migrado, exclusivo do teste."""
    import psycopg

    nome = f"sigma_teste_{uuid.uuid4().hex[:12]}"
    with psycopg.connect(dsn_manutencao, autocommit=True) as conn:
        conn.execute(f'CREATE DATABASE "{nome}" TEMPLATE "{banco_modelo}"')
    try:
        yield _dsn_para(dsn_manutencao, nome)
    finally:
        with psycopg.connect(dsn_manutencao, autocommit=True) as conn:
            conn.execute(f'DROP DATABASE IF EXISTS "{nome}" WITH (FORCE)')
