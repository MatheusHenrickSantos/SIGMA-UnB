"""A raw não recebe o fornecedor: a minimização acontece na gravação, antes do banco."""
import contextlib
import json
import pathlib

import pytest

from codigos.banco_de_dados import gravar_fontes_raw as gravar
from codigos.utilidades import calcular_hash

REGISTROS = [
    {"idCompra": 1, "precoUnitario": 10.5, "niFornecedor": "12345678901", "nomeFornecedor": "FULANO"},
    {"idCompra": 2, "precoUnitario": 11.0, "niFornecedor": "12345678000199", "nomeFornecedor": "EMPRESA LTDA"},
]


class ConexaoFalsa:
    def __init__(self):
        self.consultas = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def transaction(self):
        return contextlib.nullcontext()

    def execute(self, sql, params=None):
        self.consultas.append((sql, params))

        class Cursor:
            def fetchone(self_inner):
                return (1,)

        return Cursor()


@pytest.fixture
def conexao(monkeypatch):
    falsa = ConexaoFalsa()
    monkeypatch.setattr(gravar, "conectar", lambda: falsa)
    return falsa


def _gravado(conexao):
    sql, params = next(c for c in conexao.consultas if "INSERT INTO raw.compras " in c[0])
    return params[0].obj, params[1]


def teste_grava_sem_fornecedor_e_preserva_o_hash_original(conexao, monkeypatch):
    monkeypatch.delenv("REMOVER_IDENTIFICACAO_FORNECEDOR", raising=False)
    conteudo = json.dumps(REGISTROS, ensure_ascii=False)
    gravar.salvar_compras(7, __import__("datetime").date(2025, 7, 1), __import__("datetime").date(2025, 12, 31), REGISTROS, conteudo)
    dado, hash_ = _gravado(conexao)
    assert all("niFornecedor" not in r and "nomeFornecedor" not in r for r in dado)
    assert [r["precoUnitario"] for r in dado] == [10.5, 11.0]      # o resto do registro fica
    assert hash_ == calcular_hash(conteudo)                          # deduplicação idempotente
    assert "niFornecedor" in REGISTROS[0]                            # a lista original não foi alterada


def teste_pode_ser_desligada(conexao, monkeypatch):
    monkeypatch.setenv("REMOVER_IDENTIFICACAO_FORNECEDOR", "false")
    gravar.salvar_compras(7, __import__("datetime").date(2025, 7, 1), __import__("datetime").date(2025, 12, 31), REGISTROS, json.dumps(REGISTROS))
    dado, _ = _gravado(conexao)
    assert dado[0]["niFornecedor"] == "12345678901"


@pytest.mark.parametrize("valor,ativo", [("", True), ("true", True), ("1", True), ("false", False), ("0", False), ("Não", False)])
def teste_interruptor(monkeypatch, valor, ativo):
    monkeypatch.setenv("REMOVER_IDENTIFICACAO_FORNECEDOR", valor)
    assert gravar.remover_fornecedor_ativo() is ativo


def teste_no_banco_real_o_fornecedor_nao_chega_a_raw(banco, monkeypatch):
    """Grava num PostgreSQL de verdade (já migrado) e confere o que ficou em raw.compras."""
    import datetime

    import psycopg

    monkeypatch.delenv("REMOVER_IDENTIFICACAO_FORNECEDOR", raising=False)
    monkeypatch.setattr(gravar, "conectar", lambda: psycopg.connect(banco))
    # as tabelas raw vêm do ddl.sql (inicializar_esquema, rodado pelo serviço ingest), não das migrações
    ddl = pathlib.Path(__file__).resolve().parents[1] / "db" / "migrations" / "ddl.sql"
    with psycopg.connect(banco, autocommit=True) as conn:
        conn.execute(ddl.read_text(encoding="utf-8"))
    conteudo = json.dumps(REGISTROS, ensure_ascii=False)
    ini, fim = datetime.date(2025, 7, 1), datetime.date(2025, 12, 31)

    assert gravar.salvar_compras(7, ini, fim, REGISTROS, conteudo) is True
    assert gravar.salvar_compras(7, ini, fim, REGISTROS, conteudo) is False  # mesmo hash: não duplica

    with psycopg.connect(banco) as conn:
        texto, linhas, hash_ = conn.execute(
            "SELECT dado_bruto::text, count(*) OVER (), hash_do_arquivo FROM raw.compras"
        ).fetchone()
        coleta = conn.execute("SELECT total_registros FROM raw.compras_coleta WHERE codigo_item_catalogo = 7").fetchone()
    assert "Fornecedor" not in texto and "12345678901" not in texto and "EMPRESA" not in texto
    assert linhas == 1 and hash_ == calcular_hash(conteudo)
    assert coleta == (2,)
