#!/usr/bin/env python3

"""Ponto de entrada da normalização de materiais do estoque."""

import argparse
import csv
import json

from pathlib import Path

from .fonte_banco import FonteEstoqueBanco
from .fonte_csv import salvar_csv
from .limpeza import transformar_material


def carregar_materials_do_bronze() -> list[str]:
    """Consulta os materiais distintos da camada bronze, tabela estoque."""

    return FonteEstoqueBanco().carregar()


def exportar_materials_normalizados(saida: Path | None = None) -> list[dict[str, str]]:
    """Normaliza os materiais do bronze e salva uma tabela CSV em seeds."""

    raiz_projeto = Path(__file__).resolve().parents[2]
    destino = saida or raiz_projeto / "seeds" / "materiais_normalizados.csv"
    destino.parent.mkdir(parents=True, exist_ok=True)

    registros = []
    for material in carregar_materials_do_bronze():
        descricao_normalizada, _ = transformar_material(material)
        registros.append(
            {
                "descricao_original": material,
                "descricao_normalizada": descricao_normalizada,
            }
        )

    salvar_csv(
        destino,
        ["descricao_original", "descricao_normalizada"],
        registros,
        incluir_campos_derivados=False,
    )

    return registros


def main() -> None:
    """Exporta a tabela final de materiais normalizados para a pasta seeds."""

    parser = argparse.ArgumentParser(
        description="Normaliza materiais da camada bronze e salva em seeds."
    )
    parser.add_argument(
        "--saida",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "seeds" / "materiais_normalizados.csv",
        help="Caminho do CSV de saída. Padrão: seeds/materiais_normalizados.csv",
    )
    argumentos = parser.parse_args()

    registros = exportar_materials_normalizados(argumentos.saida)
    print(
        json.dumps(
            {
                "registros_salvos": len(registros),
                "arquivo_saida": str(argumentos.saida),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()