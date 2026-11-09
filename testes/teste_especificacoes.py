"""Testes das regras de especificação (codigos/semantica/especificacoes.py).

Documentam o comportamento atual das regras herdadas do teste de
viabilidade; não pretendem cobrir todas as categorias.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from semantica.especificacoes import comparar_especificacoes, extrair_especificacoes


@pytest.mark.parametrize("estoque, catmat, situacao, conflito", [
    ("PILHA ALCALINA AAA 1,5V", "PILHA, TIPO: ALCALINA, TAMANHO: AA, TENSÃO NOMINAL: 1,5 V",
     "conflito_tecnico", "formato_pilha"),
    ("RESISTOR 10K OHMS 1/4W", "RESISTOR, RESISTÊNCIA: 1 KOHM, POTÊNCIA: 1/4 W",
     "conflito_tecnico", "resistencia_ohm"),
    ("DETERGENTE LÍQUIDO NEUTRO 500ML", "DETERGENTE, ASPECTO FÍSICO: LÍQUIDO, CAPACIDADE: 5 L",
     "conflito_tecnico", "volume_ml"),
])
def teste_conflitos_explicitos(estoque, catmat, situacao, conflito):
    resultado = comparar_especificacoes(estoque, catmat)
    assert resultado["status_validacao"] == situacao
    assert conflito in resultado["categorias_com_conflito"]
    assert resultado["elegivel_teste_preco"] is False


def teste_unidades_diferentes_mesma_quantidade_sao_compativeis():
    resultado = comparar_especificacoes("ÁLCOOL ETÍLICO 70% 1 LITRO", "ÁLCOOL ETÍLICO, 70%, CAPACIDADE: 1000 ML")
    assert resultado["status_validacao"] == "sem_conflito_detectado"


def teste_sem_especificacoes_verificaveis():
    assert comparar_especificacoes("CANETA", "CANETA ESFEROGRÁFICA")["status_validacao"] == (
        "sem_especificacoes_verificaveis"
    )


def teste_extracao_normaliza_valores():
    especificacoes = extrair_especificacoes("CAPACITOR 100UF 25V, 1 KG, 210 X 297 MM")
    assert especificacoes["capacitancia"] == {"100UF"}
    assert especificacoes["tensao_v"] == {"25"}
    assert especificacoes["massa_g"] == {"1000"}
    assert especificacoes["dimensoes"] == {"210X297MM"}


def teste_script_de_validacao_usa_as_mesmas_regras():
    pytest.importorskip("pandas")
    pytest.importorskip("requests")
    caminho = Path(__file__).resolve().parents[1] / "codigos" / "validacao_e_cobertura_precos.py"
    spec = importlib.util.spec_from_file_location("validacao_e_cobertura_precos", caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    assert modulo.comparar_especificacoes is comparar_especificacoes
