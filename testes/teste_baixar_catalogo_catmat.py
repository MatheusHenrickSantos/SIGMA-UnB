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


def teste_ajuda_usa_pasta_dados_catmat(modulo):
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
    assert "dados/catmat" in saida
    assert "dados/teste" not in saida


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


def teste_salva_catalogo_em_um_unico_json(tmp_path, monkeypatch):
    diretorio_cache = tmp_path / "cache_catmat_json"
    diretorio_cache.mkdir()
    (diretorio_cache / "pagina_000001.json").write_text(
        json.dumps(
            {
                "totalPaginas": 1,
                "resultado": [
                    {"codigoItem": 123, "descricao": "Descrição antiga"},
                    {"codigoItem": 123, "descricao": "Descrição atual"},
                    {"codigoItem": 456, "descricao": "Outro item"},
                ],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "sys.argv",
        ["baixar_catalogo_catmat.py", "--saida", str(tmp_path)],
    )

    spec = importlib.util.spec_from_file_location(
        "baixar_catalogo_catmat_exec", MODULE_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module.executar() == 0

    caminho_catalogo = tmp_path / "catalogo_catmat.json"
    catalogo = json.loads(caminho_catalogo.read_text(encoding="utf-8"))

    assert catalogo == [
        {"codigoItem": 123, "descricao": "Descrição atual"},
        {"codigoItem": 456, "descricao": "Outro item"},
    ]
    assert not (tmp_path / "catalogo_catmat.csv").exists()
    assert not (tmp_path / "catalogo_catmat_baixado.csv").exists()
