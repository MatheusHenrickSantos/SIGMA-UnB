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
    monkeypatch.setattr(modulo, "catmat_em_cache", lambda: False)
    monkeypatch.setattr(
        modulo,
        "salvar_catmat",
        lambda dado, conteudo, **metadados: gravados.append(
            (dado, conteudo, metadados)
        ) or True,
    )
    monkeypatch.setattr(
        "sys.argv", ["baixar_catalogo_catmat.py", "--max-paginas", "1"]
    )

    assert modulo.executar() == 0
    assert gravados[0][0] == [
        {"codigoItem": 123, "descricao": "Descrição atual"},
        {"codigoItem": 456, "descricao": "Outro item"},
    ]
    assert json.loads(gravados[0][1]) == gravados[0][0]
    assert gravados[0][2] == {"completa": True, "total_paginas": 1}


def teste_paginas_em_paralelo_mantem_a_ordem(modulo, monkeypatch):
    """Com vários trabalhadores o catálogo sai na mesma ordem do modo em sequência."""
    import time

    def pagina_falsa(sessao, pagina, tamanho, pausa):
        time.sleep(0.002 * (7 - pagina % 7))  # páginas terminam fora de ordem
        return {"totalPaginas": 20, "resultado": [{"codigoItem": pagina * 10 + i} for i in range(3)]}

    monkeypatch.setattr(modulo, "solicitar_pagina", pagina_falsa)
    monkeypatch.setattr(modulo, "criar_sessao", lambda: object())
    sequencial, total_a, baixadas_a = modulo.baixar_catalogo(500, 0, None, trabalhadores=1)
    paralelo, total_b, baixadas_b = modulo.baixar_catalogo(500, 0, None, trabalhadores=4)
    assert paralelo == sequencial
    assert (total_b, baixadas_b) == (20, 20) == (total_a, baixadas_a)
    assert len(paralelo) == 60


def teste_cache_do_catmat_respeita_a_validade(modulo, monkeypatch):
    """Cache completo e dentro da validade: não baixa; vencido ou --atualizar: baixa."""
    chamadas = []
    monkeypatch.setattr(modulo, "catmat_em_cache", lambda: True)
    monkeypatch.setattr(modulo, "baixar_catalogo", lambda *a, **k: chamadas.append(a) or ([{"codigoItem": 1}], 1, 1))
    monkeypatch.setattr(modulo, "salvar_catmat", lambda *a, **k: True)

    monkeypatch.setattr(modulo, "catmat_cache_vencido", lambda dias: False)
    monkeypatch.setattr("sys.argv", ["baixar_catalogo_catmat.py"])
    assert modulo.executar() == 0 and chamadas == []

    monkeypatch.setattr(modulo, "catmat_cache_vencido", lambda dias: True)
    assert modulo.executar() == 0 and len(chamadas) == 1

    chamadas.clear()
    monkeypatch.setattr(modulo, "catmat_cache_vencido", lambda dias: False)
    monkeypatch.setattr("sys.argv", ["baixar_catalogo_catmat.py", "--atualizar"])
    assert modulo.executar() == 0 and len(chamadas) == 1
