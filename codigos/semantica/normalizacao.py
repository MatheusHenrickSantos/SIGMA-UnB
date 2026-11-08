"""Normalização de descrições de materiais antes de gerar embeddings.

A mesma função é aplicada às descrições do estoque e do CATMAT, para que
os dois lados da comparação passem pelas mesmas regras. O texto original
nunca é alterado: ele é guardado ao lado do normalizado.

Regras, na ordem em que são aplicadas (versão VERSAO_NORMALIZACAO):

 1. entidades HTML desfeitas (&amp;, &Aacute;...);
 2. mojibake (UTF-8 lido como cp1252/latin-1, ex.: 'SABÃƒO') corrigido,
    só quando a conversão de volta é exata;
 3. Unicode NFKC (², ½, espaços especiais, ligaduras viram a forma comum);
 4. caracteres de controle e invisíveis viram espaço;
 5. aspas e travessões tipográficos viram ASCII;
 6. minúsculas e sem acentos (ç -> c);
 7. símbolos sem significado (* _ | ` ~ ^) viram espaço;
 8. abreviações de cadastro de almoxarifado são expandidas
    (c/ -> com, cx -> caixa, pct -> pacote...);
 9. 'x' entre números ganha espaços (210x297 -> 210 x 297) e número colado
    em unidade conhecida é separado (500ml -> 500 ml);
10. espaço antes de pontuação removido, pontuação repetida reduzida,
    espaços colapsados, pontas aparadas.

O que NÃO é feito, de propósito: remover números, unidades, medidas,
percentuais, códigos de modelo (cf283a) ou trocar separador decimal
(1,5 fica 1,5). Esses detalhes distinguem materiais parecidos.

Mudou alguma regra? Incremente VERSAO_NORMALIZACAO: o hash do texto
normalizado muda e os vetores afetados são recalculados na próxima execução.
"""

from __future__ import annotations

import hashlib
import html
import re
import unicodedata
from dataclasses import dataclass

VERSAO_NORMALIZACAO = "1"

TAMANHO_MINIMO = 3

SITUACAO_VALIDA = "valida"
SITUACAO_VAZIA = "vazia"
SITUACAO_INVALIDA = "invalida"


@dataclass(frozen=True)
class DescricaoNormalizada:
    """Resultado da normalização de uma descrição de origem."""

    original: str | None
    texto: str | None
    situacao: str
    motivo: str | None
    hash_original: str | None
    hash_normalizado: str | None

    @property
    def valida(self) -> bool:
        return self.situacao == SITUACAO_VALIDA


# ---------------------------------------------------------------------------
# Regras
# ---------------------------------------------------------------------------

# 'Ã' ou 'Â' seguidos de um caractere que só aparece nessa posição quando
# bytes UTF-8 foram decodificados como cp1252/latin-1.
_MARCA_MOJIBAKE = re.compile(
    "[ÂÃ][\u0080-¿ŒœŠšŸŽž"
    "ƒˆ˜–—‘-„†-•…‰"
    "‹›€™]"
)

_TIPOGRAFICOS = str.maketrans({
    "‘": "'", "’": "'", "‚": "'", "‛": "'",
    "“": '"', "”": '"', "„": '"', "«": '"', "»": '"',
    "‐": "-", "‑": "-", "‒": "-", "–": "-", "—": "-",
    "―": "-", "−": "-", "⁄": "/",
})

_SIMBOLOS_SEM_SIGNIFICADO = re.compile(r"[*_|`~^]+")

# c/ s/ p/ isolados (não pegam 1/2, g/m2, 26/6, km/h)
_BARRA_ABREVIADA = re.compile(r"(?<![\w/])([csp])/(?=\s|\w)")
_EXPANSAO_BARRA = {"c": "com ", "s": "sem ", "p": "para "}

_ABREVIACOES = {
    "cx": "caixa",
    "pct": "pacote",
    "pcte": "pacote",
    "un": "unidade",
    "und": "unidade",
    "unid": "unidade",
    "tam": "tamanho",
    "aprox": "aproximadamente",
    "qtd": "quantidade",
    "qtde": "quantidade",
}
_PALAVRA_ABREVIADA = re.compile(
    r"(?<![\w-])(" + "|".join(sorted(_ABREVIACOES, key=len, reverse=True)) + r")\.?(?![\w-])"
)

_X_ENTRE_NUMEROS = re.compile(r"(?<=\d)\s*[x×]\s*(?=\d)")

# Unidades que aparecem coladas ao número nos cadastros. 'a' (ampère) fica de
# fora por ser ambíguo com ordinal ('2a via').
_UNIDADES = (
    "mm", "cm", "m", "km", "m2", "m3", "cm2", "cm3", "mm2",
    "mg", "g", "kg", "ml", "l", "lt", "gl",
    "w", "kw", "v", "kv", "mah", "hz", "khz", "mhz",
    "uf", "nf", "pf", "ohm", "ohms", "kohm", "kohms",
    "gb", "mb", "tb", "pol",
)
# número no começo de um token (não pega '283a' de 'cf283a')
_NUMERO_COLADO_EM_UNIDADE = re.compile(
    r"(?<![a-z0-9.,])(\d+(?:[.,]\d+)?)("
    + "|".join(sorted(_UNIDADES, key=len, reverse=True))
    + r")\b"
)

_ESPACO_ANTES_DE_PONTUACAO = re.compile(r"\s+([,.;:])")
_PONTUACAO_REPETIDA = re.compile(r"([,.;:!?\-])\1+")
_VIRGULA_SEM_ESPACO = re.compile(r"([,;])(?=[a-z])")
_PONTAS = re.compile(r"^[\s,.;:\-]+|[\s,;:\-]+$")
_ESPACOS = re.compile(r"\s+")
_LETRA = re.compile(r"[a-z]")


def corrigir_mojibake(texto: str) -> str:
    """Desfaz 'SABÃƒO' -> 'SABÃO'. Se a conversão não for exata, devolve o texto."""
    if not _MARCA_MOJIBAKE.search(texto):
        return texto
    bytes_originais = bytearray()
    for caractere in texto:
        try:
            bytes_originais += caractere.encode("cp1252")
        except UnicodeEncodeError:
            if ord(caractere) > 0xFF:
                return texto
            # posições indefinidas no cp1252 (0x81, 0x8d...) vêm de latin-1
            bytes_originais.append(ord(caractere))
    try:
        return bytes(bytes_originais).decode("utf-8")
    except UnicodeDecodeError:
        return texto


def _desfazer_html(texto: str) -> str:
    # até 3 voltas cobre '&amp;Aacute;' (escapado duas vezes)
    for _ in range(3):
        novo = html.unescape(texto)
        if novo == texto:
            break
        texto = novo
    return texto


def _remover_controles(texto: str) -> str:
    return "".join(
        " " if unicodedata.category(c) in ("Cc", "Cf", "Zl", "Zp") else c for c in texto
    )


def _remover_acentos(texto: str) -> str:
    decomposto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in decomposto if unicodedata.category(c) != "Mn")


def normalizar_texto(texto: str) -> str:
    """Aplica as regras do módulo. Determinística e idempotente."""
    texto = _desfazer_html(texto)
    texto = corrigir_mojibake(texto)
    texto = unicodedata.normalize("NFKC", texto)
    texto = _remover_controles(texto)
    texto = texto.translate(_TIPOGRAFICOS)
    texto = _remover_acentos(texto.lower())
    texto = _SIMBOLOS_SEM_SIGNIFICADO.sub(" ", texto)

    texto = _BARRA_ABREVIADA.sub(lambda m: _EXPANSAO_BARRA[m.group(1)], texto)
    texto = _PALAVRA_ABREVIADA.sub(lambda m: _ABREVIACOES[m.group(1)], texto)

    texto = _X_ENTRE_NUMEROS.sub(" x ", texto)
    texto = _NUMERO_COLADO_EM_UNIDADE.sub(r"\1 \2", texto)

    texto = _ESPACOS.sub(" ", texto)
    texto = _ESPACO_ANTES_DE_PONTUACAO.sub(r"\1", texto)
    texto = _PONTUACAO_REPETIDA.sub(r"\1", texto)
    texto = _VIRGULA_SEM_ESPACO.sub(r"\1 ", texto)
    texto = _PONTAS.sub("", texto)
    return _ESPACOS.sub(" ", texto).strip()


def _sha256(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def hash_normalizado(texto_normalizado: str) -> str:
    """Hash do texto normalizado, amarrado à versão das regras."""
    return _sha256(f"{VERSAO_NORMALIZACAO}\n{texto_normalizado}")


def normalizar_descricao(valor: object) -> DescricaoNormalizada:
    """Normaliza uma descrição de origem e diz se ela serve para embedding."""
    if valor is None:
        return DescricaoNormalizada(None, None, SITUACAO_VAZIA, "descrição ausente (nula)", None, None)

    original = str(valor)
    hash_original = _sha256(original)

    def recusada(situacao: str, motivo: str) -> DescricaoNormalizada:
        return DescricaoNormalizada(original, None, situacao, motivo, hash_original, None)

    if not original.strip():
        return recusada(SITUACAO_VAZIA, "descrição em branco")

    texto = normalizar_texto(original)
    if not texto:
        return recusada(SITUACAO_INVALIDA, "sem conteúdo depois da normalização")
    if not _LETRA.search(texto):
        return recusada(SITUACAO_INVALIDA, "sem letras (só números ou símbolos)")
    if len(texto) < TAMANHO_MINIMO:
        return recusada(SITUACAO_INVALIDA, f"curta demais (menos de {TAMANHO_MINIMO} caracteres)")

    return DescricaoNormalizada(
        original, texto, SITUACAO_VALIDA, None, hash_original, hash_normalizado(texto)
    )
