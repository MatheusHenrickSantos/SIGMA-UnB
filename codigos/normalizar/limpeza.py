#!/usr/bin/env python3

"""Funções de normalização de descrições de materiais."""

import html
import re
import unicodedata

from .correcoes import corrigir_erros_de_digitoacao


# Unidades comuns no arquivo. A regra apenas insere um espaço entre valor e unidade;
# não converte grandezas nem altera o valor numérico.
UNIDADES = r"(?:MM|CM|KM|ML|L|GR|KG|MG|G|W|KW|MW|V|KV|GB|TB|MB|HZ|MHZ|GHZ)"
VALOR_UNIDADE_RE = re.compile(rf"(?<![A-Z0-9.,])(\d+(?:[,.]\d+)?)(\s*)({UNIDADES})\b", re.IGNORECASE)



def _decodificar_entidades_html(texto: str) -> str:
    """Normaliza entidades HTML nomeadas em qualquer caixa antes de decodificar."""

    texto = str(texto or "")
    for _ in range(2):
        texto = re.sub(
            r"&([A-Za-z0-9]+);",
            lambda m: "&" + m.group(1).lower() + ";",
            texto,
        )
        texto = html.unescape(texto)

    return texto


def normalizar_texto(texto: str | None) -> str:
    """Aplica transformações textuais previsíveis e conservadoras."""

    texto = corrigir_erros_de_digitoacao(_decodificar_entidades_html(texto))
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(
        ch for ch in texto
        if not unicodedata.combining(ch)
    )

    # Remove caracteres de controle invisíveis.
    texto = "".join(
        ch for ch in texto
        if unicodedata.category(ch) not in {"Cc", "Cf"}
        or ch in "\t\n\r"
    )

    texto = texto.upper()
    texto = re.sub(r"\s+", " ", texto).strip()

    # Preserva vírgulas decimais.
    marcador_decimal = "\ue000"

    texto = re.sub(
        r"(?<=\d),(?=\d)",
        marcador_decimal,
        texto
    )

    texto = re.sub(r"\s*,\s*", ", ", texto)
    texto = texto.replace(marcador_decimal, ",")

    texto = re.sub(r"\s*/\s*", "/", texto)
    texto = re.sub(r"\s+([;:])", r"\1", texto)

    # Padroniza a separação entre número e unidade.
    texto = VALOR_UNIDADE_RE.sub(
        lambda m: f"{m.group(1)} {m.group(3).upper()}",
        texto
    )

    # Tratamento conservador de ampere.
    texto = re.sub(
        r"(\d+[,.]\d+)A\b",
        r"\1 A",
        texto
    )

    texto = re.sub(
        r"(\d+)A(?=/)",
        r"\1 A",
        texto
    )

    texto = re.sub(r"\.+$", "", texto).strip()

    return texto


def criar_chave_material(texto_normalizado: str) -> str:
    """Cria uma representação auxiliar para comparação textual."""

    texto = unicodedata.normalize(
        "NFKD",
        texto_normalizado.casefold()
    )

    texto = "".join(
        ch for ch in texto
        if not unicodedata.combining(ch)
    )

    texto = re.sub(
        r"(?<=\d)[,.](?=\d)",
        " DECIMAL ",
        texto
    )

    texto = re.sub(r"[^a-z0-9]+", " ", texto)

    return re.sub(r"\s+", " ", texto).strip()


def transformar_material(material: str | None) -> tuple[str, str]:
    """Retorna a descrição normalizada e sua chave auxiliar."""

    normalizado = normalizar_texto(material)
    chave = criar_chave_material(normalizado)

    return normalizado, chave