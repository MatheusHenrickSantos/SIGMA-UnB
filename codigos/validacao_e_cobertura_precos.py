#!/usr/bin/env python3
"""Etapa 2 do teste CATMAT: validação de especificações e cobertura de preços.

Usa candidatos já gerados pelo ranking CATMAT. A validação é conservadora:
identifica conflitos explícitos e informações ausentes, mas não declara um código
CATMAT correto apenas por similaridade textual.

Por padrão, consulta a API oficial de preços para o melhor candidato sem conflito
explícito de cada material e filtra a data da compra localmente.
"""

from __future__ import annotations

import argparse
import html
import json
import math
import re
import sys
import time
import unicodedata
from collections import defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

URL_API = "https://dadosabertos.compras.gov.br/modulo-pesquisa-preco/1_consultarMaterial"


def maiuscula_ascii(valor: Any) -> str:
    if valor is None or (isinstance(valor, float) and math.isnan(valor)):
        return ""
    texto = html.unescape(str(valor)).upper()
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(ch for ch in texto if not unicodedata.combining(ch))


def chave_cabecalho(valor: Any) -> str:
    texto = maiuscula_ascii(valor).replace("*", "")
    return re.sub(r"[^A-Z0-9]", "", texto)


def encontrar_coluna(df: pd.DataFrame, apelidos: list[str], obrigatorio: bool = True) -> str | None:
    mapeamento = {chave_cabecalho(col): col for col in df.columns}
    for apelido in apelidos:
        chave = chave_cabecalho(apelido)
        if chave in mapeamento:
            return mapeamento[chave]
    if obrigatorio:
        raise ValueError(
            f"Não encontrei nenhuma coluna equivalente a {apelidos}. "
            f"Colunas disponíveis: {list(df.columns)}"
        )
    return None


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


def converter_bool(valor: Any) -> bool | None:
    if valor is None or (isinstance(valor, float) and math.isnan(valor)):
        return None
    s = maiuscula_ascii(valor).strip()
    if s in {"TRUE", "1", "SIM", "S", "ATIVO", "YES"}:
        return True
    if s in {"FALSE", "0", "NAO", "NÃO", "N", "INATIVO", "NO"}:
        return False
    return None


def ler_csv_robusto(caminho: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(caminho, dtype=str, encoding="utf-8-sig", keep_default_na=False)
    except UnicodeDecodeError:
        return pd.read_csv(caminho, dtype=str, encoding="latin1", keep_default_na=False)


def carregar_candidatos(caminho: Path) -> tuple[pd.DataFrame, dict[str, str | None]]:
    df = ler_csv_robusto(caminho)
    colunas = {
        "linha": encontrar_coluna(df, ["linha_amostra", "linha", "id_material", "id"], obrigatorio=False),
        "almoxarifado": encontrar_coluna(df, ["almoxarifado"], obrigatorio=False),
        "estoque": encontrar_coluna(df, ["material_estoque", "material", "descricao_estoque"], obrigatorio=True),
        "estoque_norm": encontrar_coluna(df, ["material_estoque_normalizado", "material_normalizado", "material_normalizado_usado"], obrigatorio=False),
        "codigo": encontrar_coluna(df, ["codigoItem", "codigo_catmat", "codigoItemCatalogo", "melhor_codigoItem"], obrigatorio=True),
        "descricao": encontrar_coluna(df, ["descricaoItem_CATMAT", "descricaoItem", "descricaoCATMAT", "melhor_descricao_CATMAT", "descricao_catmat"], obrigatorio=True),
        "pontuacao": encontrar_coluna(df, ["score_combinado", "score_maximo", "melhor_score_combinado", "score_WRatio_diagnostico", "score_WRatio", "score"], obrigatorio=False),
        "ativo": encontrar_coluna(df, ["statusItem", "status_item"], obrigatorio=False),
    }
    if colunas["linha"] is None:
        df["__linha_amostra"] = [str(i + 1) for i in range(len(df))]
        colunas["linha"] = "__linha_amostra"
    if colunas["pontuacao"] is None:
        df["__score"] = "0"
        colunas["pontuacao"] = "__score"
    if colunas["ativo"] is None:
        df["__statusItem"] = ""
        colunas["ativo"] = "__statusItem"

    df["__pontuacao_num"] = pd.to_numeric(df[colunas["pontuacao"]].astype(str).str.replace(",", ".", regex=False), errors="coerce").fillna(0.0)
    df["__codigo_num"] = df[colunas["codigo"]].astype(str).str.strip()
    df = df[df["__codigo_num"].ne("") & df["__codigo_num"].ne("nan")].copy()
    df["__status_ativo"] = df[colunas["ativo"]].map(converter_bool)
    return df, colunas


def validar_candidatos(df: pd.DataFrame, colunas: dict[str, str | None]) -> pd.DataFrame:
    linhas_saida = []
    colunas_ordenacao = [colunas["linha"], "__pontuacao_num"]
    trabalho = df.sort_values(colunas_ordenacao, ascending=[True, False], kind="stable")
    for _, linha in trabalho.iterrows():
        texto_fonte = linha[colunas["estoque"]]
        texto_candidato = linha[colunas["descricao"]]
        resultado = comparar_especificacoes(texto_fonte, texto_candidato)
        saida = {
            "linha_amostra": str(linha[colunas["linha"]]),
            "almoxarifado": linha[colunas["almoxarifado"]] if colunas["almoxarifado"] else "",
            "material_estoque": texto_fonte,
            "codigo_catmat": str(linha[colunas["codigo"]]).strip(),
            "descricao_catmat": texto_candidato,
            "score_combinado": float(linha["__pontuacao_num"]),
            "status_item_catmat": linha[colunas["ativo"]] if colunas["ativo"] else "",
            "status_item_ativo_bool": linha["__status_ativo"],
            **resultado,
        }
        linhas_saida.append(saida)
    df_resultado = pd.DataFrame(linhas_saida)
    df_resultado["rank_score"] = df_resultado.groupby("linha_amostra")["score_combinado"].rank(method="first", ascending=False).astype(int)
    df_resultado["__linha_ordem"] = pd.to_numeric(df_resultado["linha_amostra"], errors="coerce")
    df_resultado = df_resultado.sort_values(["__linha_ordem", "linha_amostra", "rank_score"], kind="stable", na_position="last")
    return df_resultado.drop(columns=["__linha_ordem"])


def criar_sessao() -> requests.Session:
    sessao = requests.Session()
    tentativa = Retry(
        total=4,
        connect=4,
        read=4,
        backoff_factor=0.7,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        respect_retry_after_header=True,
    )
    adaptador = HTTPAdapter(max_retries=tentativa)
    sessao.mount("https://", adaptador)
    sessao.headers.update({"Accept": "application/json", "User-Agent": "unb-almoxarifado-elt/0.1 (academic data quality test)"})
    return sessao


def ler_cache_ou_buscar(sessao: requests.Session, codigo: str, pagina: int, pasta_cache: Path, atualizar: bool, atraso: float) -> dict[str, Any]:
    caminho = pasta_cache / str(codigo) / f"pagina_{pagina:05d}.json"
    if caminho.exists() and not atualizar:
        with caminho.open("r", encoding="utf-8") as f:
            return json.load(f)
    parametros = {
        "tipo": "codigoItemCatalogo",
        "codigo": int(codigo),
        "pagina": pagina,
        "tamanhoPagina": 500
    }
    resposta = sessao.get(URL_API, params=parametros, timeout=(15, 90))
    resposta.raise_for_status()
    try:
        payload = resposta.json()
    except ValueError as exc:
        raise RuntimeError(f"Resposta não é JSON para código {codigo}, página {pagina}") from exc
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    if atraso > 0:
        time.sleep(atraso)
    return payload


def analisar_inteiro(valor: Any, padrao: int = 0) -> int:
    try:
        return int(valor)
    except (TypeError, ValueError):
        return padrao


def analisar_preco(valor: Any) -> float | None:
    if valor is None or valor == "":
        return None
    if isinstance(valor, (int, float)):
        val = float(valor)
        return val if math.isfinite(val) else None
    s = str(valor).strip().replace("R$", "").replace(" ", "")
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        val = float(s)
        return val if math.isfinite(val) else None
    except ValueError:
        return None


def analisar_data_api(valor: Any) -> date | None:
    if valor is None or valor == "":
        return None
    cru = str(valor).strip()
    try:
        return date.fromisoformat(cru[:10])
    except ValueError:
        return None


def buscar_precos_codigo(
    sessao: requests.Session,
    codigo: str,
    pasta_cache: Path,
    inicio: date,
    fim: date,
    max_paginas: int,
    atualizar: bool,
    atraso: float,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    metadados: dict[str, Any] = {
        "codigo_catmat": codigo,
        "status_consulta": "ok",
        "paginas_planejadas": 0,
        "paginas_lidas": 0,
        "total_registros_reportado_api": 0,
        "total_registros_lidos": 0,
        "registros_no_periodo": 0,
        "precos_positivos_no_periodo": 0,
        "erro": "",
    }
    todas_linhas: list[dict[str, Any]] = []
    paginas_concluidas: set[int] = set()
    try:
        primeira = ler_cache_ou_buscar(sessao, codigo, 1, pasta_cache, atualizar, atraso)
        paginas_concluidas.add(1)
        resultado = primeira.get("resultado", []) or []
        total_paginas = analisar_inteiro(primeira.get("totalPaginas"), 1)
        total_relatado = analisar_inteiro(primeira.get("totalRegistros"), len(resultado))
        if total_paginas < 1:
            total_paginas = 1
        paginas_para_ler = total_paginas
        if max_paginas > 0:
            paginas_para_ler = min(total_paginas, max_paginas)
        metadados["paginas_planejadas"] = total_paginas
        metadados["total_registros_reportado_api"] = total_relatado

        for pagina in range(1, paginas_para_ler + 1):
            if pagina == 1:
                payload = primeira
            else:
                payload = ler_cache_ou_buscar(sessao, codigo, pagina, pasta_cache, atualizar, atraso)
                paginas_concluidas.add(pagina)
            linhas = payload.get("resultado", []) or []
            for registro in linhas:
                if not isinstance(registro, dict):
                    continue
                item = dict(registro)
                item["_codigo_catmat_consultado"] = codigo
                item["_pagina_api"] = pagina
                item["_data_compra_parseada"] = str(analisar_data_api(item.get("dataCompra")) or "")
                item["_preco_numerico"] = analisar_preco(item.get("precoUnitario"))
                todas_linhas.append(item)

        metadados["paginas_lidas"] = len(paginas_concluidas)
        metadados["total_registros_lidos"] = len(todas_linhas)
        if paginas_para_ler < total_paginas:
            metadados["status_consulta"] = "parcial_limite_paginas"
        elif len(todas_linhas) < total_relatado:
            metadados["status_consulta"] = "possivelmente_incompleta"

        linhas_periodo = []
        validos_positivos = 0
        for item in todas_linhas:
            d = analisar_data_api(item.get("dataCompra"))
            if d and inicio <= d <= fim:
                linhas_periodo.append(item)
                preco = analisar_preco(item.get("precoUnitario"))
                if preco is not None and preco > 0:
                    validos_positivos += 1
        metadados["registros_no_periodo"] = len(linhas_periodo)
        metadados["precos_positivos_no_periodo"] = validos_positivos
        return linhas_periodo, metadados
    except Exception as exc:
        metadados["status_consulta"] = "erro_api"
        metadados["erro"] = f"{type(exc).__name__}: {exc}"
        metadados["paginas_lidas"] = len(paginas_concluidas)
        metadados["total_registros_lidos"] = len(todas_linhas)
        return [], metadados


def escrever_json(caminho: Path, valor: Any) -> None:
    with caminho.open("w", encoding="utf-8") as f:
        json.dump(valor, f, ensure_ascii=False, indent=2, default=str)


def principal() -> int:
    analisador = argparse.ArgumentParser(description="Valida candidatos CATMAT e testa cobertura de preços públicos.")
    analisador.add_argument("candidatos", help="CSV candidatos_catmat.csv gerado pela etapa anterior")
    analisador.add_argument("--inicio", default="2025-07-01", help="Data inicial inclusiva (AAAA-MM-DD); padrão: 2025-07-01")
    analisador.add_argument("--fim", default="2025-12-31", help="Data final inclusiva (AAAA-MM-DD); padrão: 2025-12-31")
    analisador.add_argument("--top-n-precos", type=int, default=1, help="Candidatos sem conflito explícito consultados por material; padrão: 1")
    analisador.add_argument("--max-pages-per-code", type=int, default=0, help="Limite opcional de páginas por código; 0 = todas as páginas")
    analisador.add_argument("--delay", type=float, default=0.15, help="Pausa entre requisições (segundos); padrão: 0.15")
    analisador.add_argument("--saida", default="resultado_etapa2", help="Pasta de saída")
    analisador.add_argument("--cache", default="cache_precos_catmat", help="Pasta de cache das respostas JSON")
    analisador.add_argument("--refresh-cache", action="store_true", help="Ignora e substitui respostas já salvas no cache")
    analisador.add_argument("--somente-validacao", action="store_true", help="Executa validação, mas não consulta a API de preços")
    args = analisador.parse_args()

    try:
        inicio = date.fromisoformat(args.inicio)
        fim = date.fromisoformat(args.fim)
        if inicio > fim:
            raise ValueError("A data inicial é posterior à data final.")
        if args.top_n_precos < 1:
            raise ValueError("--top-n-precos deve ser maior ou igual a 1.")
        caminho_entrada = Path(args.candidatos)
        pasta_saida = Path(args.saida)
        pasta_cache = Path(args.cache)
        pasta_saida.mkdir(parents=True, exist_ok=True)

        candidatos, colunas = carregar_candidatos(caminho_entrada)
        if candidatos.empty:
            raise ValueError("O CSV não contém candidatos com código CATMAT.")
        validacao = validar_candidatos(candidatos, colunas)
        caminho_validacao = pasta_saida / "validacao_especificacoes_catmat.csv"
        validacao.to_csv(caminho_validacao, index=False, encoding="utf-8-sig")

        elegiveis = validacao[validacao["elegivel_teste_preco"] == True].copy()  # noqa: E712
        elegiveis = elegiveis.sort_values(["linha_amostra", "score_combinado"], ascending=[True, False], kind="stable")
        elegiveis = elegiveis.drop_duplicates(subset=["linha_amostra", "codigo_catmat"], keep="first")
        elegiveis["rank_elegivel"] = elegiveis.groupby("linha_amostra").cumcount() + 1
        selecionados = elegiveis[elegiveis["rank_elegivel"] <= args.top_n_precos].copy()
        caminho_selecionados = pasta_saida / "candidatos_selecionados_para_teste_precos.csv"
        selecionados.to_csv(caminho_selecionados, index=False, encoding="utf-8-sig")

        resumos_itens = []
        for id_linha, grupo in validacao.groupby("linha_amostra", sort=False):
            grupo = grupo.sort_values("score_combinado", ascending=False, kind="stable")
            melhor = grupo.iloc[0]
            grupo_elegivel = grupo[grupo["elegivel_teste_preco"] == True]  # noqa: E712
            melhor_elegivel = grupo_elegivel.iloc[0] if not grupo_elegivel.empty else None
            resumos_itens.append({
                "linha_amostra": id_linha,
                "almoxarifado": melhor["almoxarifado"],
                "material_estoque": melhor["material_estoque"],
                "candidatos_avaliados": int(len(grupo)),
                "melhor_codigo_score": melhor["codigo_catmat"],
                "melhor_descricao_score": melhor["descricao_catmat"],
                "melhor_score": melhor["score_combinado"],
                "status_validacao_melhor_score": melhor["status_validacao"],
                "melhor_codigo_sem_conflito": melhor_elegivel["codigo_catmat"] if melhor_elegivel is not None else "",
                "descricao_melhor_sem_conflito": melhor_elegivel["descricao_catmat"] if melhor_elegivel is not None else "",
                "score_melhor_sem_conflito": melhor_elegivel["score_combinado"] if melhor_elegivel is not None else "",
                "status_melhor_sem_conflito": melhor_elegivel["status_validacao"] if melhor_elegivel is not None else "nenhum_candidato_sem_conflito",
                "candidatos_sem_conflito": int(len(grupo_elegivel)),
            })
        resumo_validacao = pd.DataFrame(resumos_itens)
        caminho_resumo_validacao = pasta_saida / "resumo_validacao_por_material.csv"
        resumo_validacao.to_csv(caminho_resumo_validacao, index=False, encoding="utf-8-sig")

        if args.somente_validacao:
            print("Validação concluída. Consulta de preços desativada (--somente-validacao).")
            print(f"Candidatos validados: {len(validacao):,}")
            print(f"Conflitos técnicos: {(validacao['status_validacao'] == 'conflito_tecnico').sum():,}")
            print(f"Sem conflito explícito: {(validacao['elegivel_teste_preco'] == True).sum():,}")  # noqa: E712
            print(f"Saídas: {pasta_saida.resolve()}")
            return 0

        if selecionados.empty:
            pd.DataFrame(columns=["codigo_catmat", "status_consulta", "registros_no_periodo"]).to_csv(
                pasta_saida / "cobertura_precos_por_codigo.csv", index=False, encoding="utf-8-sig"
            )
            pd.DataFrame(columns=["_codigo_catmat_consultado", "dataCompra", "precoUnitario"]).to_csv(
                pasta_saida / "precos_publicos_periodo.csv", index=False, encoding="utf-8-sig"
            )
            linhas_material = []
            for _, r in resumo_validacao.iterrows():
                linhas_material.append({
                    "linha_amostra": r["linha_amostra"],
                    "almoxarifado": r["almoxarifado"],
                    "material_estoque": r["material_estoque"],
                    "codigos_candidatos_consultados": "",
                    "quantidade_codigos_consultados": 0,
                    "codigos_com_preco_positivo_no_periodo": "",
                    "quantidade_codigos_com_preco": 0,
                    "possui_preco_em_algum_candidato": False,
                    "codigos_consulta_completa_sem_preco": "",
                    "codigos_com_erro_api": "",
                    "ha_consulta_parcial_ou_com_erro": False,
                    "interpretacao": "Nenhum candidato sem conflito explícito foi selecionado para consulta de preço.",
                })
            pd.DataFrame(linhas_material).to_csv(pasta_saida / "cobertura_precos_por_material.csv", index=False, encoding="utf-8-sig")
            escrever_json(pasta_saida / "metadados_execucao.json", {
                "arquivo_candidatos": str(caminho_entrada.resolve()),
                "data_inicio_inclusiva": str(inicio),
                "data_fim_inclusiva": str(fim),
                "top_n_precos_por_material": args.top_n_precos,
                "url_api": URL_API,
                "codigos_unicos_consultados": 0,
                "nota": "Nenhum candidato sem conflito explícito foi selecionado; nenhuma consulta à API foi realizada.",
            })
            print("Validação concluída, mas nenhum candidato sem conflito explícito foi selecionado para consultar preços.")
            print(f"Saídas: {pasta_saida.resolve()}")
            return 0

        codigo_para_materiais: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for _, linha in selecionados.iterrows():
            codigo = str(linha["codigo_catmat"]).strip()
            codigo_para_materiais[codigo].append({
                "linha_amostra": linha["linha_amostra"],
                "almoxarifado": linha["almoxarifado"],
                "material_estoque": linha["material_estoque"],
                "rank_elegivel": int(linha["rank_elegivel"]),
                "score_combinado": float(linha["score_combinado"]),
                "status_validacao": linha["status_validacao"],
            })

        sessao = criar_sessao()
        todas_linhas_periodo: list[dict[str, Any]] = []
        linhas_cobertura: list[dict[str, Any]] = []
        total_codigos = len(codigo_para_materiais)
        for indice, (codigo, materiais) in enumerate(codigo_para_materiais.items(), start=1):
            print(f"[{indice}/{total_codigos}] Consultando CATMAT {codigo} ...", flush=True)
            linhas, metadados = buscar_precos_codigo(
                sessao=sessao,
                codigo=codigo,
                pasta_cache=pasta_cache,
                inicio=inicio,
                fim=fim,
                max_paginas=args.max_pages_per_code,
                atualizar=args.refresh_cache,
                atraso=args.delay,
            )
            metadados["materiais_amostra_associados"] = len({m["linha_amostra"] for m in materiais})
            metadados["linhas_amostra"] = " | ".join(sorted({str(m["linha_amostra"]) for m in materiais}))
            metadados["materiais_amostra"] = " || ".join(sorted({str(m["material_estoque"]) for m in materiais}))
            precos = [analisar_preco(r.get("precoUnitario")) for r in linhas]
            precos = [p for p in precos if p is not None and p > 0]
            metadados["mediana_preco_positivo_periodo"] = float(pd.Series(precos).median()) if precos else None
            metadados["min_preco_positivo_periodo"] = min(precos) if precos else None
            metadados["max_preco_positivo_periodo"] = max(precos) if precos else None
            metadados["tem_preco_no_periodo"] = bool(precos)
            linhas_cobertura.append(metadados)
            todas_linhas_periodo.extend(linhas)

        cobertura = pd.DataFrame(linhas_cobertura)
        cobertura.to_csv(pasta_saida / "cobertura_precos_por_codigo.csv", index=False, encoding="utf-8-sig")

        df_precos = pd.DataFrame(todas_linhas_periodo)
        if not df_precos.empty:
            if "idItemCompra" in df_precos.columns:
                subconjunto = ["_codigo_catmat_consultado", "idCompra", "idItemCompra"]
                df_precos = df_precos.drop_duplicates(subset=subconjunto, keep="first")
            df_precos.to_csv(pasta_saida / "precos_publicos_periodo.csv", index=False, encoding="utf-8-sig")
        else:
            pd.DataFrame(columns=["_codigo_catmat_consultado", "dataCompra", "precoUnitario"]).to_csv(
                pasta_saida / "precos_publicos_periodo.csv", index=False, encoding="utf-8-sig"
            )

        cobertura_por_codigo = cobertura.set_index("codigo_catmat").to_dict(orient="index")
        for _codigo, _registro in cobertura_por_codigo.items():
            _registro["codigo_catmat"] = str(_codigo)
        resumos_precos_material = []
        for id_linha, grupo in resumo_validacao.groupby("linha_amostra", sort=False):
            grupo_selecionado = selecionados[selecionados["linha_amostra"].astype(str) == str(id_linha)]
            codigos_escolhidos = list(dict.fromkeys(grupo_selecionado["codigo_catmat"].astype(str).tolist()))
            relatorios = [cobertura_por_codigo[c] for c in codigos_escolhidos if c in cobertura_por_codigo]
            codigos_com_precos = [r["codigo_catmat"] for r in relatorios if r.get("precos_positivos_no_periodo", 0) > 0]
            codigos_com_zero = [r["codigo_catmat"] for r in relatorios if r.get("status_consulta") == "ok" and r.get("precos_positivos_no_periodo", 0) == 0]
            codigos_erro = [r["codigo_catmat"] for r in relatorios if str(r.get("status_consulta", "")).startswith("erro")]
            algum_parcial = any(r.get("status_consulta") not in {"ok"} for r in relatorios)
            primeiro = resumo_validacao[resumo_validacao["linha_amostra"].astype(str) == str(id_linha)].iloc[0]
            resumos_precos_material.append({
                "linha_amostra": id_linha,
                "almoxarifado": primeiro["almoxarifado"],
                "material_estoque": primeiro["material_estoque"],
                "codigos_candidatos_consultados": " | ".join(codigos_escolhidos),
                "quantidade_codigos_consultados": len(codigos_escolhidos),
                "codigos_com_preco_positivo_no_periodo": " | ".join(codigos_com_precos),
                "quantidade_codigos_com_preco": len(codigos_com_precos),
                "possui_preco_em_algum_candidato": bool(codigos_com_precos),
                "codigos_consulta_completa_sem_preco": " | ".join(codigos_com_zero),
                "codigos_com_erro_api": " | ".join(codigos_erro),
                "ha_consulta_parcial_ou_com_erro": algum_parcial,
                "interpretacao": "Cobertura de candidatos; não confirma por si só o código correto do material.",
            })
        pd.DataFrame(resumos_precos_material).to_csv(pasta_saida / "cobertura_precos_por_material.csv", index=False, encoding="utf-8-sig")

        info_execucao = {
            "arquivo_candidatos": str(caminho_entrada.resolve()),
            "data_inicio_inclusiva": str(inicio),
            "data_fim_inclusiva": str(fim),
            "top_n_precos_por_material": args.top_n_precos,
            "limite_paginas_por_codigo": args.max_pages_per_code,
            "url_api": URL_API,
            "nota": "A API não documenta filtro por intervalo de data para este endpoint; dataCompra é filtrada após a extração.",
            "codigos_unicos_consultados": len(codigo_para_materiais),
            "total_registros_no_periodo_exportados_antes_de_deduplicacao": len(todas_linhas_periodo),
            "cache_dir": str(pasta_cache.resolve()),
        }
        escrever_json(pasta_saida / "metadados_execucao.json", info_execucao)

        print("\nEtapa 2 concluída.")
        print(f"Candidatos avaliados: {len(validacao):,}")
        print(f"Conflitos técnicos explícitos: {(validacao['status_validacao'] == 'conflito_tecnico').sum():,}")
        print(f"Códigos CATMAT consultados: {len(codigo_para_materiais):,}")
        print(f"Códigos com preço positivo no período: {(cobertura['precos_positivos_no_periodo'] > 0).sum():,}")
        print(f"Códigos com erro ou consulta parcial: {(cobertura['status_consulta'] != 'ok').sum():,}")
        print(f"Arquivos gerados em: {pasta_saida.resolve()}")
        return 0

    except Exception as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(principal())