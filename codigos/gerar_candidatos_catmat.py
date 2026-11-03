#!/usr/bin/env python3
"""Gera candidatos CATMAT para uma amostra de materiais.

Uso:
  python gerar_candidatos_catmat.py amostra.csv catalogo_catmat.csv --saida dados/teste

O script sugere candidatos e não aprova códigos CATMAT automaticamente.
"""
from __future__ import annotations

import argparse
import re
import unicodedata
from pathlib import Path
from typing import Any

import pandas as pd
from rapidfuzz import fuzz, process

GENERIC_LABELS = {
    "A", "AS", "AO", "AOS", "DA", "DAS", "DE", "DO", "DOS", "E", "EM", "NA", "NAS", "NO", "NOS",
    "PARA", "POR", "COM", "SEM", "UM", "UMA", "UNS", "UMAS",
    "MATERIAL", "TIPO", "APLICACAO", "USO", "NOME", "ASPECTO", "FISICO",
    "CARACTERISTICA", "CARACTERISTICAS", "ADICIONAL", "ADICIONAIS", "DESCRICAO",
    "COMPOSICAO", "BASICA", "FORMA", "APRESENTACAO", "REFERENCIA", "FABRICANTE",
    "COR", "DIMENSAO", "DIMENSOES", "MEDIDA", "MEDIDAS", "CAPACIDADE", "NOMINAL",
    "MINIMA", "MINIMO", "MAXIMA", "MAXIMO", "APROXIMADAMENTE", "CERCA",
}


def normalizar(valor: Any) -> str:
    """Normalização textual conservadora e correção de pequenos erros comuns."""
    if valor is None or pd.isna(valor):
        return ""
    
    texto = unicodedata.normalize("NFKD", str(valor))
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch)).upper()
    
    # Correções de digitação frequentes em almoxarifados
    texto = texto.replace("ENCARDENADORA", "ENCARDENACAO")
    
    texto = re.sub(r"\bME\s*/\s*EPP\b", " ", texto)
    texto = re.sub(r"\bMICROEMPRESA\s+EMPRESA\s+DE\s+PEQUENO\s+PORTE\b", " ", texto)
    texto = re.sub(r"(?<=\d),(?=\d)", ".", texto)
    texto = re.sub(r"[-/]+", " ", texto)
    texto = re.sub(r"[^A-Z0-9%+. ]+", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def tokens_relevantes(texto: str) -> set[str]:
    tokens = set(re.findall(r"[A-Z0-9]+(?:\.[A-Z0-9]+)*", texto))
    return {tok for tok in tokens if tok not in GENERIC_LABELS}


def ler_csv_robusto(caminho: str) -> pd.DataFrame:
    """Tenta ler o CSV em UTF-8 com BOM e recorre a latin1 se houver erro de codec."""
    try:
        return pd.read_csv(caminho, dtype=str, low_memory=False, encoding="utf-8-sig")
    except UnicodeDecodeError:
        return pd.read_csv(caminho, dtype=str, low_memory=False, encoding="latin1")


def gerar_candidatos(caminho_amostra: str, caminho_catalogo: str, diretorio_saida: Path, top_n: int, por_metodo: int) -> None:
    amostra = ler_csv_robusto(caminho_amostra)
    catalogo = ler_csv_robusto(caminho_catalogo)

    if "material" in amostra.columns:
        coluna_material = "material"
    elif "material_normalizado" in amostra.columns:
        coluna_material = "material_normalizado"
    else:
        raise ValueError("A amostra precisa ter uma coluna 'material' ou 'material_normalizado'.")
        
    if "codigoItem" not in catalogo.columns or "descricaoItem" not in catalogo.columns:
        raise ValueError(
            "O CSV do catálogo precisa conter as colunas 'codigoItem' e 'descricaoItem'. "
            f"Colunas encontradas: {catalogo.columns.tolist()}"
        )

    catalogo = catalogo.dropna(subset=["codigoItem", "descricaoItem"]).copy()
    catalogo["codigoItem"] = catalogo["codigoItem"].astype(str).str.strip()
    catalogo["descricaoCATMAT_normalizada"] = catalogo["descricaoItem"].map(normalizar)
    catalogo = catalogo[catalogo["descricaoCATMAT_normalizada"].ne("")].drop_duplicates("codigoItem").reset_index(drop=True)
    escolhas = catalogo["descricaoCATMAT_normalizada"].tolist()
    print(f"Amostra: {len(amostra)} linhas | Catálogo utilizável: {len(catalogo)} códigos")

    linhas_candidatos: list[dict[str, Any]] = []
    linhas_resumo: list[dict[str, Any]] = []
    avaliadores = [
        ("token_set_ratio", fuzz.token_set_ratio),
        ("token_sort_ratio", fuzz.token_sort_ratio),
        ("ratio", fuzz.ratio),
    ]

    for indice_amostra, linha in amostra.iterrows():
        original = str(linha.get(coluna_material, "") or "")
        consulta = normalizar(original)
        tokens_consulta = tokens_relevantes(consulta)
        
        if not consulta:
            linhas_resumo.append({"linha_amostra": indice_amostra + 1, "material": original, "resultado": "descricao_vazia"})
            continue

        indices_encontrados: set[int] = set()
        for _nome, avaliador in avaliadores:
            correspondencias = process.extract(consulta, escolhas, scorer=avaliador, limit=por_metodo, processor=None)
            indices_encontrados.update(int(match[2]) for match in correspondencias)

        classificados: list[dict[str, Any]] = []
        for idx in indices_encontrados:
            cat = catalogo.iloc[idx]
            descricao = str(cat["descricaoCATMAT_normalizada"])
            tokens_cat = tokens_relevantes(descricao)
            sobreposicao = sorted(tokens_consulta & tokens_cat)
            faltantes = sorted(tokens_consulta - tokens_cat)
            cobertura = (len(sobreposicao) / len(tokens_consulta) * 100.0) if tokens_consulta else 0.0

            pont_set = float(fuzz.token_set_ratio(consulta, descricao))
            pont_sort = float(fuzz.token_sort_ratio(consulta, descricao))
            pont_ratio = float(fuzz.ratio(consulta, descricao))
            pont_wratio = float(fuzz.WRatio(consulta, descricao))
            
            pontuacao_combinada = (
                0.35 * pont_set
                + 0.25 * pont_sort
                + 0.15 * pont_ratio
                + 0.25 * cobertura
            )

            saida: dict[str, Any] = {
                "linha_amostra": indice_amostra + 1,
                "almoxarifado": linha.get("almoxarifado", ""),
                "material_estoque": original,
                "material_estoque_normalizado": consulta,
                "codigoItem": cat.get("codigoItem", ""),
                "descricaoItem_CATMAT": cat.get("descricaoItem", ""),
                "descricaoCATMAT_normalizada": descricao,
                "score_combinado": round(pontuacao_combinada, 2),
                "score_token_set": round(pont_set, 2),
                "score_token_sort": round(pont_sort, 2),
                "score_ratio": round(pont_ratio, 2),
                "score_WRatio_diagnostico": round(pont_wratio, 2),
                "cobertura_tokens_pct": round(cobertura, 2),
                "tokens_em_comum": " | ".join(sobreposicao),
                "tokens_estoque_ausentes_no_catmat": " | ".join(faltantes),
                "codigoGrupo": cat.get("codigoGrupo", ""),
                "nomeGrupo": cat.get("nomeGrupo", ""),
                "codigoClasse": cat.get("codigoClasse", ""),
                "nomeClasse": cat.get("nomeClasse", ""),
                "codigoPdm": cat.get("codigoPdm", ""),
                "nomePdm": cat.get("nomePdm", ""),
                "statusItem": cat.get("statusItem", ""),
                "status_correspondencia": "candidato_para_validacao",
            }
            classificados.append(saida)

        classificados.sort(
            key=lambda x: (
                x["score_combinado"],
                x["cobertura_tokens_pct"],
                x["score_token_set"],
            ),
            reverse=True,
        )
        
        melhor = classificados[0] if classificados else {}
        segundo = classificados[1] if len(classificados) > 1 else {}
        margem = (melhor.get("score_combinado", 0) - segundo.get("score_combinado", 0)) if segundo else None
        
        linhas_candidatos.extend(classificados[:top_n])
        linhas_resumo.append({
            "linha_amostra": indice_amostra + 1,
            "almoxarifado": linha.get("almoxarifado", ""),
            "material": original,
            "material_normalizado_usado": consulta,
            "candidatos_avaliados": len(classificados),
            "melhor_codigoItem": melhor.get("codigoItem"),
            "melhor_descricao_CATMAT": melhor.get("descricaoItem_CATMAT"),
            "melhor_score_combinado": melhor.get("score_combinado"),
            "segundo_score_combinado": segundo.get("score_combinado"),
            "margem_melhor_segundo": round(margem, 2) if margem is not None else None,
            "melhor_cobertura_tokens_pct": melhor.get("cobertura_tokens_pct"),
            "melhor_tokens_ausentes": melhor.get("tokens_estoque_ausentes_no_catmat"),
            "resultado": "candidatos para validação" if classificados else "sem candidato",
            "observacao": "Pontuações exploratórias; não aprovam a correspondência automaticamente.",
        })
        print(f"[{indice_amostra + 1}/{len(amostra)}] {original[:55]} -> {len(classificados)} candidatos; melhor score={melhor.get('score_combinado', 'N/A')}")

    diretorio_saida.mkdir(parents=True, exist_ok=True)
    caminho_candidatos = diretorio_saida / "candidatos_catmat.csv"
    caminho_resumo = diretorio_saida / "resumo_catmat.csv"

    pd.DataFrame(linhas_candidatos).to_csv(caminho_candidatos, index=False, encoding="utf-8-sig")
    pd.DataFrame(linhas_resumo).to_csv(caminho_resumo, index=False, encoding="utf-8-sig")

    print(f"\nArquivos gerados com sucesso em: {diretorio_saida.resolve()}")
    print(f"- {caminho_candidatos.name}")
    print(f"- {caminho_resumo.name}")
    print("Nenhuma correspondência foi aprovada automaticamente.")


def main() -> int:
    raiz_repo = Path(__file__).resolve().parents[1]
    saida_padrao = raiz_repo / "dados" / "teste"

    analisador = argparse.ArgumentParser(description=__doc__)
    analisador.add_argument("amostra", help="CSV da amostra de materiais")
    analisador.add_argument("catalogo", help="CSV completo do catálogo CATMAT já baixado")
    analisador.add_argument("--saida", default=str(saida_padrao), help="Diretório de saída (padrão: dados/teste)")
    analisador.add_argument("--top", type=int, default=20, help="Candidatos exportados por material")
    analisador.add_argument("--candidatos-por-metodo", type=int, default=100, help="Candidatos recuperados por métrica")
    args = analisador.parse_args()
    
    if args.top < 1 or args.candidatos_por_metodo < args.top:
        analisador.error("Use --top >= 1 e --candidatos-por-metodo >= --top.")
        
    gerar_candidatos(args.amostra, args.catalogo, Path(args.saida), args.top, args.candidatos_por_metodo)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())