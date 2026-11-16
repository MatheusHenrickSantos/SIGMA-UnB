"""Reordenação híbrida dos candidatos: cosseno + rapidfuzz.

A busca por cosseno sozinha recupera bem, mas ordena mal: no conjunto de
referência de 150 materiais reais (ver docs/dados-e-pipeline/semantica.md,
seção "Busca híbrida"), o item correto estava entre os 50 vizinhos mais
próximos em 93% dos casos, mas era o primeiro colocado em só ~50%. Somando
medidas lexicais do rapidfuzz e a cobertura de termos, o primeiro colocado
passa a acertar ~59%.

    pontuacao = 0,40 * cosseno*100 + 0,20 * token_set + 0,15 * token_sort
                + 0,25 * cobertura

- token_set / token_sort: rapidfuzz.fuzz sobre os textos em maiúsculas, sem
  acentos e sem pontuação (normalizar_lexico);
- cobertura: % dos termos relevantes do material (sem palavras genéricas
  como MATERIAL, TIPO, COR) que aparecem no item CATMAT.

Todas as medidas ficam em 0-100. Os pesos foram escolhidos no conjunto de
referência; trocar pesos ou regras exige incrementar VERSAO_REORDENACAO.

Este módulo é puro (sem banco nem modelo), para ser testado isoladamente.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Iterable

from rapidfuzz import fuzz

VERSAO_REORDENACAO = "1"

PESOS_PADRAO = {"cosseno": 0.40, "token_set": 0.20, "token_sort": 0.15, "cobertura": 0.25}

# Palavras que aparecem em quase toda descrição e não distinguem materiais.
PALAVRAS_GENERICAS = frozenset({
    "A", "AS", "AO", "AOS", "DA", "DAS", "DE", "DO", "DOS", "E", "EM", "NA", "NAS", "NO", "NOS",
    "PARA", "POR", "COM", "SEM", "UM", "UMA", "UNS", "UMAS",
    "MATERIAL", "TIPO", "APLICACAO", "USO", "NOME", "ASPECTO", "FISICO",
    "CARACTERISTICA", "CARACTERISTICAS", "ADICIONAL", "ADICIONAIS", "DESCRICAO",
    "COMPOSICAO", "BASICA", "FORMA", "APRESENTACAO", "REFERENCIA", "FABRICANTE",
    "COR", "DIMENSAO", "DIMENSOES", "MEDIDA", "MEDIDAS", "CAPACIDADE", "NOMINAL",
    "MINIMA", "MINIMO", "MAXIMA", "MAXIMO", "APROXIMADAMENTE", "CERCA",
})

_ME_EPP = re.compile(r"\bME\s*/\s*EPP\b")
_MICROEMPRESA = re.compile(r"\bMICROEMPRESA\s+EMPRESA\s+DE\s+PEQUENO\s+PORTE\b")
_VIRGULA_DECIMAL = re.compile(r"(?<=\d),(?=\d)")
_HIFEN_BARRA = re.compile(r"[-/]+")
_OUTROS = re.compile(r"[^A-Z0-9%+. ]+")
_ESPACOS = re.compile(r"\s+")
_TERMO = re.compile(r"[A-Z0-9]+(?:\.[A-Z0-9]+)*")


def normalizar_lexico(texto: str | None) -> str:
    """Forma usada só para as medidas lexicais: maiúsculas, sem acento nem pontuação.

    Recebe o texto já normalizado (normalizacao.normalizar_texto) ou o
    original; o resultado é o mesmo nos dois casos para fins de comparação.
    1,5 vira 1.5 para que o número continue sendo um termo só.
    """
    if not texto:
        return ""
    texto = unicodedata.normalize("NFKD", str(texto))
    texto = "".join(c for c in texto if not unicodedata.combining(c)).upper()
    texto = _ME_EPP.sub(" ", texto)
    texto = _MICROEMPRESA.sub(" ", texto)
    texto = _VIRGULA_DECIMAL.sub(".", texto)
    texto = _HIFEN_BARRA.sub(" ", texto)
    texto = _OUTROS.sub(" ", texto)
    return _ESPACOS.sub(" ", texto).strip()


def termos_relevantes(texto_lexico: str) -> set[str]:
    """Termos de um texto já passado por normalizar_lexico, sem as palavras genéricas."""
    return {t for t in _TERMO.findall(texto_lexico) if t not in PALAVRAS_GENERICAS}


@dataclass(frozen=True)
class Medidas:
    cosseno: float
    token_set: float
    token_sort: float
    cobertura: float
    pontuacao: float

    def como_dict(self) -> dict[str, float]:
        return {
            "cosseno": round(self.cosseno, 6),
            "token_set": round(self.token_set, 2),
            "token_sort": round(self.token_sort, 2),
            "cobertura": round(self.cobertura, 2),
        }


@dataclass
class Consulta:
    """Texto do material preparado uma vez e reaproveitado para todos os candidatos."""

    lexico: str
    termos: set[str] = field(default_factory=set)

    @classmethod
    def de(cls, texto: str | None) -> "Consulta":
        lexico = normalizar_lexico(texto)
        return cls(lexico, termos_relevantes(lexico))


def pontuar(
    consulta: Consulta,
    texto_catmat: str | None,
    cosseno: float,
    pesos: dict[str, float] = PESOS_PADRAO,
) -> Medidas:
    """Medidas de um par material x item CATMAT e a pontuação combinada (0-100)."""
    lexico = normalizar_lexico(texto_catmat)
    token_set = float(fuzz.token_set_ratio(consulta.lexico, lexico))
    token_sort = float(fuzz.token_sort_ratio(consulta.lexico, lexico))
    if consulta.termos:
        cobertura = 100.0 * len(consulta.termos & termos_relevantes(lexico)) / len(consulta.termos)
    else:
        cobertura = 0.0
    cos100 = max(0.0, min(1.0, cosseno)) * 100.0
    pontuacao = (
        pesos["cosseno"] * cos100
        + pesos["token_set"] * token_set
        + pesos["token_sort"] * token_sort
        + pesos["cobertura"] * cobertura
    )
    return Medidas(cosseno, token_set, token_sort, cobertura, pontuacao)


def ordenar(
    candidatos: Iterable[dict],
) -> list[dict]:
    """Ordem final: sem conflito de especificação primeiro, depois pontuação maior.

    Cada candidato precisa das chaves 'conflito' (bool), 'pontuacao',
    'cosseno' e 'chave' (código do item, para desempate estável).
    """
    return sorted(
        candidatos,
        key=lambda c: (c["conflito"], -c["pontuacao"], -c["cosseno"], c["chave"]),
    )
