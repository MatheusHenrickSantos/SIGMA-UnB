"""
Resume a camada bruta: para cada arquivo em dados/bruto/<dataset>/, conta os
registros, lista as colunas e guarda alguns exemplos.

Gera dados/bruto/inspecao.json. É usado para conferir se o portal mudou o
formato de algum arquivo e para caracterizar o volume (ADR 0001).

Uso:
    python inspecionar_bruto.py
"""

import json
from collections import Counter
from pathlib import Path

from carregar import PASTA_BRUTO, ler_registros, mes_do_arquivo

EXEMPLOS_POR_ARQUIVO = 3


def main():
    resumo = {}

    for pasta in sorted(p for p in PASTA_BRUTO.iterdir() if p.is_dir()):
        arquivos = sorted(p for p in pasta.iterdir() if p.suffix in (".json", ".csv"))
        colunas_por_versao = Counter()
        itens = []

        for caminho in arquivos:
            try:
                registros = ler_registros(caminho)
            except Exception as erro:
                itens.append({"arquivo": caminho.name, "erro": str(erro)})
                continue

            colunas = sorted({c for r in registros for c in r})
            colunas_por_versao[tuple(colunas)] += 1
            mes = mes_do_arquivo(caminho)

            itens.append(
                {
                    "arquivo": caminho.name,
                    "mes": mes.isoformat() if mes else None,
                    "bytes": caminho.stat().st_size,
                    "registros": len(registros),
                    "colunas": colunas,
                    "exemplos": registros[:EXEMPLOS_POR_ARQUIVO],
                }
            )

        resumo[pasta.name] = {
            "arquivos": len(arquivos),
            "registros": sum(i.get("registros", 0) for i in itens),
            "bytes": sum(i.get("bytes", 0) for i in itens),
            "versoes_de_colunas": [
                {"colunas": list(c), "arquivos": n} for c, n in colunas_por_versao.items()
            ],
            "por_arquivo": itens,
        }

        print(f"{pasta.name:<12} {len(arquivos):>4} arquivos {resumo[pasta.name]['registros']:>9} registros "
              f"{len(colunas_por_versao)} formato(s) de colunas")

    saida = PASTA_BRUTO / "inspecao.json"
    saida.write_text(json.dumps(resumo, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"\nResumo gravado em {saida}")


if __name__ == "__main__":
    main()
