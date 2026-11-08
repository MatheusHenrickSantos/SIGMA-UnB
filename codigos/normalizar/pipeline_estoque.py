#!/usr/bin/env python3

"""Pipeline de limpeza e identificação de duplicatas do estoque."""

from collections import Counter, defaultdict
from typing import Iterable, Mapping

from .limpeza import transformar_material


CAMPOS_DERIVADOS = [
    "material_normalizado",
    "material_chave",
    "duplicata_textual_no_almoxarifado",
]


def validar_campos(campos: Iterable[str]) -> None:
    """Verifica se os campos necessários estão disponíveis."""

    obrigatorios = {"material", "almoxarifado"}
    ausentes = obrigatorios - set(campos)

    if ausentes:
        raise ValueError(
            f"Campos obrigatórios ausentes: {', '.join(sorted(ausentes))}"
        )


def processar_registros(
    registros: Iterable[Mapping[str, object]]
) -> tuple[list[dict[str, object]], dict]:
    """
    Normaliza as descrições e identifica duplicatas textuais
    dentro de cada almoxarifado.

    Não remove nem consolida registros.
    """

    linhas_saida = [dict(registro) for registro in registros]

    chaves_por_almox = defaultdict(list)
    alteracoes = 0

    # Primeira passagem: normalização.
    for indice, linha in enumerate(linhas_saida, start=1):

        original = str(linha.get("material") or "")

        normalizado, chave = transformar_material(original)

        almox = str(
            linha.get("almoxarifado") or ""
        ).strip().casefold()

        if normalizado != original:
            alteracoes += 1

        linha["material_normalizado"] = normalizado
        linha["material_chave"] = chave

        linha["duplicata_textual_no_almoxarifado"] = "NAO"

        # Não agrupa materiais sem identificação ou almoxarifado.
        if chave and almox:
            chaves_por_almox[(almox, chave)].append(indice)

    # Segunda passagem: identificação das duplicatas.
    duplicatas = []

    for (almox, chave), indices in chaves_por_almox.items():

        if len(indices) <= 1:
            continue

        duplicatas.append({
            "almoxarifado": almox,
            "material_chave": chave,
            "posicoes_no_lote": indices,
        })

        for indice in indices:
            linhas_saida[indice - 1][
                "duplicata_textual_no_almoxarifado"
            ] = "SIM"

    resumo = {
        "registros": len(linhas_saida),

        "almoxarifados": dict(
            Counter(
                str(r.get("almoxarifado") or "").strip()
                for r in linhas_saida
            )
        ),

        "descricoes_alteradas_pela_limpeza_segura": alteracoes,

        "grupos_de_duplicatas_textuais_no_mesmo_almoxarifado": (
            len(duplicatas)
        ),

        "grupos_duplicados": duplicatas,

        "observacao": (
            "Nenhum registro foi removido ou consolidado. "
            "As duplicatas identificadas possuem chaves textuais iguais."
        ),
    }

    return linhas_saida, resumo