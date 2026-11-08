#!/usr/bin/env python3

"""Leitura e escrita de arquivos CSV e JSON."""

import csv
import json

from pathlib import Path

from .pipeline_estoque import CAMPOS_DERIVADOS


def ler_csv(caminho: Path) -> tuple[list[str], list[dict[str, str]]]:

    with caminho.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as arquivo:

        leitor = csv.DictReader(arquivo)

        if not leitor.fieldnames:
            raise ValueError("O CSV não possui cabeçalho.")

        campos = list(leitor.fieldnames)
        registros = list(leitor)

    return campos, registros


def salvar_csv(
    caminho: Path,
    campos: list[str],
    registros: list[dict],
    incluir_campos_derivados: bool = True,
) -> None:

    caminho.parent.mkdir(parents=True, exist_ok=True)

    campos_saida = list(campos)
    if incluir_campos_derivados:
        campos_saida += [
            campo
            for campo in CAMPOS_DERIVADOS
            if campo not in campos_saida
        ]

    with caminho.open(
        "w",
        encoding="utf-8-sig",
        newline=""
    ) as arquivo:

        escritor = csv.DictWriter(
            arquivo,
            fieldnames=campos_saida,
            extrasaction="ignore"
        )

        escritor.writeheader()
        escritor.writerows(registros)


def salvar_json(caminho: Path, dados: dict) -> None:

    caminho.parent.mkdir(parents=True, exist_ok=True)

    caminho.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )