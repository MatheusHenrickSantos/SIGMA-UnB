import contextlib
import importlib.util
import io
import json
import pathlib

import pytest


MODULE_PATH = (
    pathlib.Path(__file__).resolve().parents[1]
    / "codigos"
    / "inserir"
    / "baixar_catalogo_catmat.py"
)


@pytest.fixture
def modulo():
    spec = importlib.util.spec_from_file_location(
        "baixar_catalogo_catmat", MODULE_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def teste_ajuda_indica_tabela_raw(modulo):
    with pytest.raises(SystemExit):
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            import sys

            original_argv = sys.argv[:]
            try:
                sys.argv = ["baixar_catalogo_catmat.py", "--help"]
                modulo.executar()
            finally:
                sys.argv = original_argv

    saida = stdout.getvalue()
    assert "raw.catmat" in saida


def teste_max_paginas_deve_ser_positivo(modulo):
    with pytest.raises(SystemExit):
        with contextlib.redirect_stderr(io.StringIO()) as stderr:
            import sys

            original_argv = sys.argv[:]
            try:
                sys.argv = ["baixar_catalogo_catmat.py", "--max-paginas", "0"]
                modulo.executar()
            finally:
                sys.argv = original_argv

    saida = stderr.getvalue()
    assert "maior que zero" in saida


def teste_salva_catalogo_diretamente_na_raw(modulo, monkeypatch):
    class Resposta:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "totalPaginas": 1,
                "resultado": [
                    {"codigoItem": 123, "descricao": "Descrição antiga"},
                    {"codigoItem": 123, "descricao": "Descrição atual"},
                    {"codigoItem": 456, "descricao": "Outro item"},
                ],
            }

    class Sessao:
        headers = {}

        def get(self, *args, **kwargs):
            return Resposta()

        def close(self):
            pass

    gravados = []
    monkeypatch.setattr(modulo.requests, "Session", Sessao)
    monkeypatch.setattr(modulo, "salvar_catmat", lambda dado, conteudo: gravados.append((dado, conteudo)) or True)
    monkeypatch.setattr(
        "sys.argv", ["baixar_catalogo_catmat.py", "--max-paginas", "1"]
    )

    assert modulo.executar() == 0
    assert gravados[0][0] == [
        {"codigoItem": 123, "descricao": "Descrição atual"},
        {"codigoItem": 456, "descricao": "Outro item"},
    ]
    assert json.loads(gravados[0][1]) == gravados[0][0]
