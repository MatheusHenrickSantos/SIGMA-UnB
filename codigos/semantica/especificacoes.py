"""Regras que extraem e comparam especificações técnicas de descrições.

Extraídas sem alteração de codigos/validacao_e_cobertura_precos.py (teste
de viabilidade), para serem usadas também pela busca semântica sem trazer
junto pandas e requests. Ver docs/testes/teste-de-viabilidade.md.

A comparação é conservadora: aponta conflitos explícitos (resistência,
capacitância, potência, massa, volume, tensão, dimensões, cor...) e
especificações ausentes. Ausência de conflito não confirma equivalência.
"""

from __future__ import annotations

import html
import json
import math
import re
import unicodedata
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from typing import Any


def maiuscula_ascii(valor: Any) -> str:
    if valor is None or (isinstance(valor, float) and math.isnan(valor)):
        return ""
    texto = html.unescape(str(valor)).upper()
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(ch for ch in texto if not unicodedata.combining(ch))


def texto_decimal(cru: str) -> str:
    return cru.replace(",", ".")


def normalizar_decimal(cru: str) -> str:
    try:
        d = Decimal(texto_decimal(cru)).normalize()
        return format(d, "f")
    except (InvalidOperation, ValueError):
        return texto_decimal(cru)


def extrair_dimensao(s: str) -> set[str]:
    encontrado: set[str] = set()
    padrao = re.compile(
        r"(?<![A-Z0-9])\d+(?:[.,]\d+)?(?:\s*[X×]\s*\d+(?:[.,]\d+)?){1,3}\s*(?:MM|CM|M)?\b"
    )
    for m in padrao.finditer(s):
        valor = m.group(0).replace("×", "X")
        busca_unidade = re.search(r"(MM|CM|M)\s*$", valor)
        unidade = busca_unidade.group(1) if busca_unidade else ""
        numeros = re.findall(r"\d+(?:[.,]\d+)?", valor)
        encontrado.add("X".join(normalizar_decimal(n) for n in numeros) + unidade)
    return encontrado


def extrair_resistencia(s: str) -> set[str]:
    valores: set[str] = set()
    for m in re.finditer(r"(?<![A-Z0-9])(\d+)\s*K\s*(\d)(?![A-Z0-9])", s):
        val = Decimal(f"{m.group(1)}.{m.group(2)}") * Decimal(1000)
        valores.add(format(val.normalize(), "f"))
    for m in re.finditer(r"(?<![A-Z0-9])(\d+(?:[.,]\d+)?)\s*(KOHMS?|OHMS?|OHM|K|R)\b", s):
        num = Decimal(texto_decimal(m.group(1)))
        unidade = m.group(2)
        if unidade.startswith("K"):
            num *= Decimal(1000)
        valores.add(format(num.normalize(), "f"))
    return valores


def extrair_especificacoes(texto: Any) -> dict[str, set[str]]:
    s = maiuscula_ascii(texto)
    especificacoes: dict[str, set[str]] = defaultdict(set)

    resistencias = extrair_resistencia(s)
    if resistencias:
        especificacoes["resistencia_ohm"].update(resistencias)

    pares_capacitores = set()
    for m in re.finditer(r"(?<![A-Z0-9])(\d+(?:[.,]\d+)?)\s*\+\s*(\d+(?:[.,]\d+)?)\s*(MF|UF|NF)\b", s):
        pares_capacitores.add(f"{normalizar_decimal(m.group(1))}+{normalizar_decimal(m.group(2))}{m.group(3)}")
    if pares_capacitores:
        especificacoes["capacitancia_par"].update(pares_capacitores)
    else:
        for m in re.finditer(r"(?<![A-Z0-9])(\d+(?:[.,]\d+)?)\s*(MF|UF|NF)\b", s):
            especificacoes["capacitancia"].add(f"{normalizar_decimal(m.group(1))}{m.group(2)}")

    for m in re.finditer(r"(?<![A-Z0-9])(\d+)\s*/\s*(\d+)\s*W\b", s):
        try:
            val = Decimal(m.group(1)) / Decimal(m.group(2))
            especificacoes["potencia_w"].add(format(val.normalize(), "f"))
        except (InvalidOperation, ZeroDivisionError):
            pass

    s_sem_w_fracional = re.sub(r"(?<![A-Z0-9])\d+\s*/\s*\d+\s*W\b", " ", s)
    for m in re.finditer(r"(?<![A-Z0-9])(\d+(?:[.,]\d+)?)\s*W\b", s_sem_w_fracional):
        especificacoes["potencia_w"].add(normalizar_decimal(m.group(1)))

    for m in re.finditer(r"(?<![A-Z0-9])(\d+(?:[.,]\d+)?)\s*(?:%|PER(?:CENT)?\b)", s):
        especificacoes["percentual"].add(normalizar_decimal(m.group(1)))

    for m in re.finditer(r"(?<![A-Z0-9])(\d+(?:[.,]\d+)?)\s*(KG|MG|GR|G|LITROS?|LT|ML|L)\b", s):
        numero = Decimal(texto_decimal(m.group(1)))
        unidade = m.group(2)
        if unidade == "KG":
            numero *= Decimal(1000)
            especificacoes["massa_g"].add(format(numero.normalize(), "f"))
        elif unidade in {"G", "GR"}:
            especificacoes["massa_g"].add(format(numero.normalize(), "f"))
        elif unidade == "MG":
            numero /= Decimal(1000)
            especificacoes["massa_g"].add(format(numero.normalize(), "f"))
        elif unidade in {"L", "LT", "LITRO", "LITROS"}:
            numero *= Decimal(1000)
            especificacoes["volume_ml"].add(format(numero.normalize(), "f"))
        elif unidade == "ML":
            especificacoes["volume_ml"].add(format(numero.normalize(), "f"))

    for m in re.finditer(r"(?<![A-Z0-9])(\d+(?:[.,]\d+)?)\s*V\b", s):
        especificacoes["tensao_v"].add(normalizar_decimal(m.group(1)))
    for m in re.finditer(r"(?<![A-Z0-9])(\d+(?:[.,]\d+)?)\s*(MIN|MINUTO|MINUTOS|HORA|HORAS|H)\b", s):
        val = Decimal(texto_decimal(m.group(1)))
        unidade = m.group(2)
        if unidade in {"HORA", "HORAS", "H"}:
            val *= Decimal(60)
        especificacoes["duracao_min"].add(format(val.normalize(), "f"))

    dimensoes = extrair_dimensao(s)
    if dimensoes:
        especificacoes["dimensoes"].update(dimensoes)

    cores = {
        "AMARELO", "AMARELA", "AZUL", "VERDE", "VERMELHO", "VERMELHA",
        "PRETO", "PRETA", "BRANCO", "BRANCA", "CIANO", "MAGENTA", "INCOLOR",
        "TRANSPARENTE", "ROSA", "LARANJA", "MARROM", "CINZA", "VIOLETA",
    }
    tokens = set(re.findall(r"[A-Z]+", s))
    acertos_cores = tokens & cores
    if acertos_cores:
        if "AMARELO" in acertos_cores or "AMARELA" in acertos_cores:
            acertos_cores -= {"AMARELO", "AMARELA"}
            acertos_cores.add("AMARELO")
        if "VERMELHO" in acertos_cores or "VERMELHA" in acertos_cores:
            acertos_cores -= {"VERMELHO", "VERMELHA"}
            acertos_cores.add("VERMELHO")
        if "PRETO" in acertos_cores or "PRETA" in acertos_cores:
            acertos_cores -= {"PRETO", "PRETA"}
            acertos_cores.add("PRETO")
        if "BRANCO" in acertos_cores or "BRANCA" in acertos_cores:
            acertos_cores -= {"BRANCO", "BRANCA"}
            acertos_cores.add("BRANCO")
        especificacoes["cor"].update(acertos_cores)

    formas = {"GEL", "LIQUIDO", "LIQUIDA", "SOLIDO", "SOLIDA", "PO", "PASTA", "AEROSOL", "GRANULADO"}
    acertos_formas = tokens & formas
    if acertos_formas:
        if "LIQUIDO" in acertos_formas or "LIQUIDA" in acertos_formas:
            acertos_formas -= {"LIQUIDO", "LIQUIDA"}
            acertos_formas.add("LIQUIDO")
        if "SOLIDO" in acertos_formas or "SOLIDA" in acertos_formas:
            acertos_formas -= {"SOLIDO", "SOLIDA"}
            acertos_formas.add("SOLIDO")
        especificacoes["apresentacao"].update(acertos_formas)

    if "PILHA" in tokens or "BATERIA" in tokens:
        formatos_bateria = tokens & {"AA", "AAA", "C", "D"}
        if formatos_bateria:
            especificacoes["formato_pilha"].update(formatos_bateria)

    identificadores: set[str] = set()
    for m in re.finditer(r"\b[A-Z]{1,8}[-/]?\d{2,}[A-Z0-9]*\b", s):
        identificadores.add(re.sub(r"[^A-Z0-9]", "", m.group(0)))

    for m in re.finditer(r"\b[A-Z]{1,3}\d\b", s):
        identificadores.add(m.group(0))

    if identificadores:
        especificacoes["identificadores"].update(identificadores)

    if re.search(r"\bSEM\s+VALVULA\b", s):
        especificacoes["valvula"].add("SEM_VALVULA")
    elif re.search(r"\bCOM\s+VALVULA\b", s):
        especificacoes["valvula"].add("COM_VALVULA")

    return dict(especificacoes)


def comparar_especificacoes(fonte: Any, candidato: Any) -> dict[str, Any]:
    especificacoes_fonte = extrair_especificacoes(fonte)
    especificacoes_candidato = extrair_especificacoes(candidato)
    compativeis, ausentes, conflitos = [], [], []
    detalhes_conflitos: list[str] = []

    for categoria, valores_fonte in especificacoes_fonte.items():
        valores_candidato = especificacoes_candidato.get(categoria, set())
        if not valores_candidato:
            ausentes.append(categoria)
            continue

        if categoria == "identificadores":
            candidato_compacto = re.sub(r"[^A-Z0-9]", "", maiuscula_ascii(candidato))
            ids_compativeis = {x for x in valores_fonte if x in candidato_compacto}
            if ids_compativeis:
                compativeis.append(categoria)
            else:
                ausentes.append(categoria)
            continue

        sobreposicao = valores_fonte & valores_candidato
        if sobreposicao:
            compativeis.append(categoria)
            continue

        if categoria in {
            "resistencia_ohm", "capacitancia_par", "capacitancia", "potencia_w",
            "percentual", "massa_g", "volume_ml", "tensao_v", "duracao_min",
            "dimensoes", "cor", "apresentacao", "valvula", "formato_pilha",
        }:
            conflitos.append(categoria)
            detalhes_conflitos.append(f"{categoria}: estoque={sorted(valores_fonte)}; CATMAT={sorted(valores_candidato)}")
        else:
            ausentes.append(categoria)

    if conflitos:
        status = "conflito_tecnico"
    elif not especificacoes_fonte:
        status = "sem_especificacoes_verificaveis"
    elif ausentes:
        status = "sem_conflito_mas_incompleto"
    else:
        status = "sem_conflito_detectado"

    return {
        "status_validacao": status,
        "quantidade_categorias_estoque": len(especificacoes_fonte),
        "quantidade_categorias_compativeis": len(set(compativeis)),
        "especificacoes_estoque": json.dumps({k: sorted(v) for k, v in especificacoes_fonte.items()}, ensure_ascii=False),
        "especificacoes_catmat": json.dumps({k: sorted(v) for k, v in especificacoes_candidato.items()}, ensure_ascii=False),
        "categorias_compativeis": " | ".join(sorted(set(compativeis))),
        "categorias_ausentes_no_catmat": " | ".join(sorted(set(ausentes))),
        "categorias_com_conflito": " | ".join(sorted(set(conflitos))),
        "detalhes_conflitos": " ; ".join(detalhes_conflitos),
        "elegivel_teste_preco": not bool(conflitos),
    }
