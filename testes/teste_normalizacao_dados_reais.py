"""Normalização sobre descrições REAIS do estoque da UnB.

Usa seeds/materiais_normalizados.csv (coluna descricao_original), gerado a
partir da camada bronze por codigos/normalizar/main.py. Pulado se o arquivo
não existir.
"""

from __future__ import annotations

import csv
import html
import re
import unicodedata
from collections import Counter
from pathlib import Path

import pytest

from semantica.normalizacao import normalizar_descricao, normalizar_texto

SEMENTE = Path(__file__).resolve().parents[1] / "seeds" / "materiais_normalizados.csv"


@pytest.fixture(scope="module")
def descricoes() -> list[str]:
    if not SEMENTE.exists():
        pytest.skip(f"{SEMENTE.name} não existe")
    with SEMENTE.open(encoding="utf-8-sig", newline="") as arquivo:
        return [linha["descricao_original"] for linha in csv.DictReader(arquivo)]


def teste_todas_as_descricoes_reais_sao_validas(descricoes):
    recusadas = [d for d in descricoes if not normalizar_descricao(d).valida]
    assert len(descricoes) > 1000
    assert recusadas == []


def teste_normalizacao_e_idempotente_nas_descricoes_reais(descricoes):
    nao_idempotentes = [
        d for d in descricoes if normalizar_texto(normalizar_texto(d)) != normalizar_texto(d)
    ]
    assert nao_idempotentes == []


def teste_nenhum_numero_some_nas_descricoes_reais(descricoes):
    """As sequências de dígitos do original (depois de NFKC: ½ -> 1/2) continuam no texto."""
    divergentes = []
    for original in descricoes:
        esperado = Counter(re.findall(r"\d+", unicodedata.normalize("NFKC", html.unescape(original))))
        obtido = Counter(re.findall(r"\d+", normalizar_texto(original)))
        if esperado != obtido:
            divergentes.append(original)
    assert divergentes == []


def teste_entidades_html_em_maiusculas():
    assert normalizar_texto("CONECTOR, P2, EST&EACUTE;REO") == "conector, p2, estereo"
    assert normalizar_texto("CONECTOR, XLR, F&ECIRC;MEA") == "conector, xlr, femea"
