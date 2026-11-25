import importlib.util
import pathlib
import threading
import time

import pytest

CAMINHO = pathlib.Path(__file__).resolve().parents[1] / "codigos" / "inserir" / "baixar_compras.py"


@pytest.fixture
def modulo():
    spec = importlib.util.spec_from_file_location("baixar_compras", CAMINHO)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _preparar(modulo, monkeypatch, falham=()):
    gravados, threads = {}, set()

    def baixar_falso(sessao, codigo, inicio, fim, pausa, max_paginas):
        threads.add(threading.get_ident())
        time.sleep(0.003)
        if codigo in falham:
            raise RuntimeError("API devolveu 400")
        return [{"codigoItemCatalogo": codigo, "n": i} for i in range(codigo % 3)], 1, False

    monkeypatch.setattr(modulo, "baixar_codigo", baixar_falso)
    monkeypatch.setattr(modulo, "criar_sessao", lambda: object())
    monkeypatch.setattr(modulo, "compras_coletadas", lambda inicio, fim: set())
    monkeypatch.setattr(modulo, "salvar_compras",
                        lambda codigo, inicio, fim, regs, conteudo: gravados.__setitem__(codigo, len(regs)))
    return gravados, threads


def teste_paralelo_grava_o_mesmo_que_o_modo_em_sequencia(modulo, monkeypatch):
    codigos = ",".join(str(c) for c in range(100, 160))
    resultados = {}
    for trabalhadores in (1, 4):
        gravados, threads = _preparar(modulo, monkeypatch)
        monkeypatch.setattr("sys.argv", ["baixar_compras.py", "--codigos", codigos,
                                         "--pausa", "0", "--paralelismo", str(trabalhadores)])
        assert modulo.executar() == 0
        resultados[trabalhadores] = gravados
    assert resultados[4] == resultados[1] and len(resultados[1]) == 60
    assert len(threads) > 1  # o último run (4 trabalhadores) usou mais de uma thread


def teste_erro_de_um_codigo_nao_derruba_os_outros(modulo, monkeypatch):
    gravados, _ = _preparar(modulo, monkeypatch, falham={103})
    monkeypatch.setattr("sys.argv", ["baixar_compras.py", "--codigos", "101,102,103,104",
                                     "--pausa", "0", "--paralelismo", "4"])
    assert modulo.executar() == 0            # sem --estrito, só avisa
    assert set(gravados) == {101, 102, 104}  # 103 não é gravado como concluído
    monkeypatch.setattr("sys.argv", ["baixar_compras.py", "--codigos", "101,103",
                                     "--pausa", "0", "--paralelismo", "2", "--estrito"])
    assert modulo.executar() == 1


def teste_paralelismo_invalido(modulo, monkeypatch):
    monkeypatch.setattr(modulo, "compras_coletadas", lambda inicio, fim: set())
    monkeypatch.setattr("sys.argv", ["baixar_compras.py", "--codigos", "1", "--paralelismo", "0"])
    with pytest.raises(SystemExit):
        modulo.executar()
