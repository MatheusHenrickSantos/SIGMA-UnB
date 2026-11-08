#!/usr/bin/env python3

"""Dicionário de correções ortográficas para descrições de materiais."""

import re

DICIONARIO_CORRECAO: dict[str, str] = {
    "FEVERDOR": "FERVEDOR",
    "FERVEDOR": "FERVEDOR",
    "TRASISTOR": "TRANSISTOR",
    "POTENCIONETRO": "POTENCIOMETRO",
    "CONTATORA": "CONTACTORA",
    "CONTATOR": "CONTACTOR",
    "POTENCIOMETR": "POTENCIOMETRO",
}


def corrigir_erros_de_digitoacao(texto: str | None) -> str:
    """Aplica correções de grafia observadas no estoque."""

    valor = str(texto or "")
    for erro, correcao in DICIONARIO_CORRECAO.items():
        valor = re.sub(
            rf"(?<![A-ZÀ-Ÿ]){re.escape(erro)}(?![A-ZÀ-Ÿ])",
            correcao,
            valor,
            flags=re.IGNORECASE,
        )
    return valor
