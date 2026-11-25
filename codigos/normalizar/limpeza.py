"""Regras compartilhadas para normalizar descrições de materiais.

A semântica usa a mesma transformação em minúsculas; o pipeline de estoque
pode pedir a forma em maiúsculas para manter o formato publicado no seed.
"""

from __future__ import annotations

import html
import re
import unicodedata

from .correcoes import DICIONARIO_CORRECAO

VERSAO_NORMALIZACAO = "3"

_MARCA_MOJIBAKE = re.compile(
    "[ÂÃ][\\u0080-¿ŒœŠšŸŽžƒˆ˜–—‘-„†-•…‰‹›€™]"
)
_TIPOGRAFICOS = str.maketrans({
    "‘": "'", "’": "'", "‚": "'", "‛": "'",
    "“": '"', "”": '"', "„": '"', "«": '"', "»": '"',
    "‐": "-", "‑": "-", "‒": "-", "–": "-", "—": "-",
    "―": "-", "−": "-", "⁄": "/",
})
_SIMBOLOS_SEM_SIGNIFICADO = re.compile(r"[*_|`~^]+")
_BARRA_ABREVIADA = re.compile(r"(?<![\w/])([csp])/(?=\s|\w)", re.IGNORECASE)
_EXPANSAO_BARRA = {"c": "com ", "s": "sem ", "p": "para "}
_ABREVIACOES = {
    "cx": "caixa", "pct": "pacote", "pcte": "pacote",
    "un": "unidade", "und": "unidade", "unid": "unidade",
    "tam": "tamanho", "aprox": "aproximadamente",
    "qtd": "quantidade", "qtde": "quantidade",
}
_PALAVRA_ABREVIADA = re.compile(
    r"(?<![\w-])(" + "|".join(sorted(_ABREVIACOES, key=len, reverse=True)) + r")\.?(?![\w-])",
    re.IGNORECASE,
)
_X_ENTRE_NUMEROS = re.compile(r"(?<=\d)\s*[x×]\s*(?=\d)", re.IGNORECASE)
_UNIDADES = (
    "mm", "cm", "m", "km", "m2", "m3", "cm2", "cm3", "mm2",
    "mg", "g", "kg", "ml", "l", "lt", "gl", "w", "kw", "v", "kv",
    "mah", "hz", "khz", "mhz", "uf", "nf", "pf", "ohm", "ohms",
    "kohm", "kohms", "gb", "mb", "tb", "pol",
)
_NUMERO_COLADO_EM_UNIDADE = re.compile(
    r"(?<![a-z0-9.,])(\d+(?:[.,]\d+)?)("
    + "|".join(sorted(_UNIDADES, key=len, reverse=True))
    + r")\b", re.IGNORECASE,
)
_ESPACO_ANTES_DE_PONTUACAO = re.compile(r"\s+([,.;:])")
_PONTUACAO_REPETIDA = re.compile(r"([,.;:!?\-])\1+")
_VIRGULA_SEM_ESPACO = re.compile(r"([,;])(?=[a-z])", re.IGNORECASE)
_PONTAS = re.compile(r"^[\s,.;:\-]+|[\s,;:\-]+$")
_ESPACOS = re.compile(r"\s+")
_ENTIDADE_HTML = re.compile(r"&([A-Za-z][A-Za-z0-9]*);")


def _entidade_sem_caixa(achado: re.Match) -> str:
    nome = achado.group(1)
    for candidato in (nome, nome.lower(), nome.capitalize()):
        decodificado = html.unescape(f"&{candidato};")
        if decodificado != f"&{candidato};":
            return decodificado
    return achado.group(0)


def _desfazer_html(texto: str) -> str:
    for _ in range(3):
        novo = _ENTIDADE_HTML.sub(_entidade_sem_caixa, html.unescape(texto))
        if novo == texto:
            break
        texto = novo
    return texto


def _corrigir_mojibake(texto: str) -> str:
    if not _MARCA_MOJIBAKE.search(texto):
        return texto
    bytes_originais = bytearray()
    for caractere in texto:
        try:
            bytes_originais += caractere.encode("cp1252")
        except UnicodeEncodeError:
            if ord(caractere) > 0xFF:
                return texto
            bytes_originais.append(ord(caractere))
    try:
        return bytes(bytes_originais).decode("utf-8")
    except UnicodeDecodeError:
        return texto


def _corrigir_digitacao(texto: str) -> str:
    for erro, correcao in DICIONARIO_CORRECAO.items():
        texto = re.sub(
            rf"(?<![A-ZÀ-Ÿ]){re.escape(erro)}(?![A-ZÀ-Ÿ])",
            correcao.lower(),
            texto,
            flags=re.IGNORECASE,
        )
    return texto


def _remover_acentos(texto: str) -> str:
    decomposto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in decomposto if unicodedata.category(c) != "Mn")


def normalizar_texto(texto: str | None, *, maiusculo: bool = True) -> str:
    """Normaliza texto sem descartar números, unidades ou códigos de modelo."""
    texto = "" if texto is None else str(texto)
    texto = _desfazer_html(texto)
    texto = _corrigir_mojibake(texto)
    texto = unicodedata.normalize("NFKC", texto)
    texto = "".join(
        " " if unicodedata.category(c) in ("Cc", "Cf", "Zl", "Zp") else c
        for c in texto
    )
    texto = texto.translate(_TIPOGRAFICOS)
    texto = _remover_acentos(texto.lower())
    texto = _corrigir_digitacao(texto)
    texto = _SIMBOLOS_SEM_SIGNIFICADO.sub(" ", texto)
    texto = _BARRA_ABREVIADA.sub(lambda m: _EXPANSAO_BARRA[m.group(1).lower()], texto)
    texto = _PALAVRA_ABREVIADA.sub(lambda m: _ABREVIACOES[m.group(1).lower()], texto)
    texto = _X_ENTRE_NUMEROS.sub(" x ", texto)
    texto = _NUMERO_COLADO_EM_UNIDADE.sub(lambda m: f"{m.group(1)} {m.group(2).lower()}", texto)
    texto = _ESPACOS.sub(" ", texto)
    texto = _ESPACO_ANTES_DE_PONTUACAO.sub(r"\1", texto)
    texto = _PONTUACAO_REPETIDA.sub(r"\1", texto)
    texto = _VIRGULA_SEM_ESPACO.sub(r"\1 ", texto)
    texto = _PONTAS.sub("", texto)
    texto = _ESPACOS.sub(" ", texto).strip()
    return texto.upper() if maiusculo else texto


def criar_chave_material(texto_normalizado: str) -> str:
    """Cria uma chave auxiliar para detectar descrições textualmente iguais."""
    texto = unicodedata.normalize("NFKD", texto_normalizado.casefold())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"(?<=\d)[,.](?=\d)", " DECIMAL ", texto)
    texto = re.sub(r"[^a-z0-9]+", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def transformar_material(material: str | None) -> tuple[str, str]:
    """Retorna a descrição normalizada e sua chave auxiliar."""
    normalizado = normalizar_texto(material)
    return normalizado, criar_chave_material(normalizado)
