#!/usr/bin/env python3
"""Gera uma amostra diversificada de materiais do último mês de registro por almoxarifado.

Uso:
  python gerar_amostra_almoxarifado.py --saida dados/teste
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd


def extrair_mes_do_nome_arquivo(nome_arquivo: str) -> tuple[int, int] | None:
    padrao = r"Estoque_do_Almoxarifado_(\d{2})-(\d{4})_csv\.csv$|Estoque_do_Almoxarifado_(\d{2})-(\d{4})\.csv$"
    correspondencia = re.search(padrao, nome_arquivo)
    if not correspondencia:
        return None
    mes = int(correspondencia.group(1) or correspondencia.group(3))
    ano = int(correspondencia.group(2) or correspondencia.group(4))
    return ano, mes


def encontrar_ultimo_arquivo_por_almoxarifado(diretorio_base: Path) -> dict[str, Path]:
    arquivos_com_data: list[tuple[tuple[int, int], Path]] = []
    
    for caminho_arquivo in diretorio_base.glob("*.csv"):
        chave_mes = extrair_mes_do_nome_arquivo(caminho_arquivo.name)
        if chave_mes is not None:
            arquivos_com_data.append((chave_mes, caminho_arquivo))
            
    arquivos_com_data.sort(key=lambda x: x[0], reverse=True)

    ultimo_por_almoxarifado: dict[str, Path] = {}
    
    for chave_mes, caminho_arquivo in arquivos_com_data:
        try:
            df = pd.read_csv(caminho_arquivo, dtype=str, encoding="utf-8-sig", low_memory=False)
        except Exception:
            continue
            
        if "almoxarifado" not in df.columns or "material" not in df.columns:
            continue

        almoxarifados_no_arquivo = df["almoxarifado"].dropna().astype(str).str.strip().unique()
        for almoxarifado in almoxarifados_no_arquivo:
            almoxarifado = almoxarifado.strip()
            if not almoxarifado:
                continue
            if almoxarifado not in ultimo_por_almoxarifado:
                ultimo_por_almoxarifado[almoxarifado] = caminho_arquivo
                
    return ultimo_por_almoxarifado


def obter_familia_material(material: str) -> str:
    """Extrai a categoria/família principal do material (ex: o texto antes da primeira vírgula)."""
    if not material:
        return ""
    # Pega tudo antes da primeira vírgula e remove espaços extras
    partes = material.split(",")
    return partes[0].strip().upper()


def construir_amostra(diretorio_base: Path, min_por_almoxarifado: int, max_por_almoxarifado: int | None) -> pd.DataFrame:
    linhas: list[dict[str, str]] = []
    ultimo_por_almoxarifado = encontrar_ultimo_arquivo_por_almoxarifado(diretorio_base)
    
    if not ultimo_por_almoxarifado:
        raise FileNotFoundError(f"Nenhum arquivo de estoque foi encontrado em: {diretorio_base}")

    for almoxarifado, caminho_arquivo in sorted(ultimo_por_almoxarifado.items()):
        df = pd.read_csv(caminho_arquivo, dtype=str, encoding="utf-8-sig", low_memory=False)
        
        subconjunto = df.loc[
            df["almoxarifado"].astype(str).str.strip().eq(almoxarifado) & df["material"].astype(str).str.strip().ne(""),
            ["material", "almoxarifado", "saldo"],
        ].copy()
        
        subconjunto["material"] = subconjunto["material"].astype(str).str.strip()

        if "saldo" in subconjunto.columns:
            subconjunto["saldo_num"] = (
                subconjunto["saldo"]
                .astype(str)
                .str.replace("R$", "", regex=False)
                .str.replace(".", "", regex=False)
                .str.replace(",", ".", regex=False)
                .str.replace(" ", "", regex=False)
                .apply(lambda x: float(x) if x else float("nan"))
            )
            subconjunto = subconjunto[subconjunto["saldo_num"].notna() & (subconjunto["saldo_num"] > 0)].copy()
        else:
            subconjunto["saldo_num"] = 0.0

        subconjunto = (
            subconjunto.drop_duplicates(subset=["material"], keep="first")
            .sort_values(["saldo_num", "material"], ascending=[False, True])
            .reset_index(drop=True)
        )

        # Determina o tamanho alvo da amostra
        if max_por_almoxarifado is None:
            tamanho_alvo = min(min_por_almoxarifado, len(subconjunto))
        else:
            if max_por_almoxarifado < min_por_almoxarifado:
                raise ValueError("--max-por-almoxarifado deve ser >= --min-por-almoxarifado.")
            tamanho_alvo = min(max_por_almoxarifado, len(subconjunto))

        # Seleção diversificada: limita a repetição de itens da mesma família (ex: máximo 2 por família)
        selecionados = []
        contador_familias: dict[str, int] = {}
        limite_por_familia = 2  # Evita que mais de 2 itens da mesma categoria ocupem a amostra

        # 1ª Passagem: Tenta pegar itens de famílias diferentes
        for _, item in subconjunto.iterrows():
            if len(selecionados) >= tamanho_alvo:
                break
            familia = obter_familia_material(item["material"])
            if contador_familias.get(familia, 0) < limite_por_familia:
                contador_familias[familia] = contador_familias.get(familia, 0) + 1
                selecionados.append(item)

        # Se ainda faltarem itens (caso o estoque tenha poucas famílias distintas), completa com os próximos disponíveis
        if len(selecionados) < tamanho_alvo:
            for _, item in subconjunto.iterrows():
                if len(selecionados) >= tamanho_alvo:
                    break
                if not any(s["material"] == item["material"] for s in selecionados):
                    selecionados.append(item)

        if len(subconjunto) < min_por_almoxarifado:
            print(
                f"Aviso: {almoxarifado} tem apenas {len(subconjunto)} materiais com saldo positivo no mês mais recente; "
                f"foram usados todos os disponíveis.",
            )

        linhas.extend({"almoxarifado": almoxarifado, "material": item["material"]} for item in selecionados)

    amostra = pd.DataFrame(linhas, columns=["almoxarifado", "material"])
    if amostra.empty:
        raise ValueError("Nenhum material foi encontrado para formar a amostra.")
        
    return amostra.drop_duplicates(subset=["almoxarifado", "material"], keep="first").reset_index(drop=True)


def principal() -> int:
    raiz_repo = Path(__file__).resolve().parents[1]
    entrada_padrao = raiz_repo / "dados" / "almoxarifado"
    saida_padrao = raiz_repo / "dados" / "teste"

    analisador = argparse.ArgumentParser(description=__doc__)
    analisador.add_argument("--entrada", default=str(entrada_padrao), help="Diretório com os CSVs de estoque do almoxarifado")
    analisador.add_argument("--saida", default=str(saida_padrao), help="Diretório para salvar a amostra")
    analisador.add_argument("--min-por-almoxarifado", type=int, default=10, help="Mínimo de materiais por almoxarifado")
    analisador.add_argument("--max-por-almoxarifado", type=int, default=None, help="Opcional: limita o número máximo por almoxarifado")
    args = analisador.parse_args()

    if args.min_por_almoxarifado < 1:
        analisador.error("--min-por-almoxarifado deve ser >= 1.")
    if args.max_por_almoxarifado is not None and args.max_por_almoxarifado < args.min_por_almoxarifado:
        analisador.error("--max-por-almoxarifado deve ser >= --min-por-almoxarifado.")

    diretorio_entrada = Path(args.entrada)
    diretorio_saida = Path(args.saida)
    diretorio_saida.mkdir(parents=True, exist_ok=True)

    amostra = construir_amostra(diretorio_entrada, args.min_por_almoxarifado, args.max_por_almoxarifado)
    caminho_saida = diretorio_saida / "amostra_10_por_almoxarifado_ultimo_mes.csv"
    amostra.to_csv(caminho_saida, index=False, encoding="utf-8-sig")

    print(f"Amostra diversificada salva em: {caminho_saida}")
    print(amostra.groupby("almoxarifado").size().to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())