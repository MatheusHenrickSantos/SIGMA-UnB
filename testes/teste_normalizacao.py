"""Testes da normalização de descrições (codigos/semantica/normalizacao.py)."""

from __future__ import annotations

import hashlib
import re
from collections import Counter

import pytest

from semantica import normalizacao
from semantica.normalizacao import normalizar_descricao, normalizar_texto

# Descrições no estilo do estoque e do CATMAT (escritas à mão para o teste).
CASOS = [
    ("PAPEL A4, 75G/M2, BRANCO, 210 X 297MM, RESMA C/ 500 FOLHAS",
     "papel a4, 75 g/m2, branco, 210 x 297 mm, resma com 500 folhas"),
    ("CANETA ESFEROGR&Aacute;FICA PRETA, PONTA M&Eacute;DIA 1,0MM",
     "caneta esferografica preta, ponta media 1,0 mm"),
    ("ÁLCOOL ETÍLICO 70%, LÍQUIDO, FRASCO 1 LITRO",
     "alcool etilico 70%, liquido, frasco 1 litro"),
    ("RESISTOR 10K OHMS 1/4W", "resistor 10k ohms 1/4 w"),
    ("PILHA ALCALINA AAA 1,5V", "pilha alcalina aaa 1,5 v"),
    ("SACO P/ LIXO 100 LITROS, PRETO, PCT C/ 100",
     "saco para lixo 100 litros, preto, pacote com 100"),
    ("LUVA DE PROCEDIMENTO LÁTEX TAM. M, CX C/ 100",
     "luva de procedimento latex tamanho m, caixa com 100"),
    ("GRAMPO P/ GRAMPEADOR 26/6, CX C/ 5000",
     "grampo para grampeador 26/6, caixa com 5000"),
    ("CAPACITOR ELETROLÍTICO 100UF 25V", "capacitor eletrolitico 100 uf 25 v"),
    ("TONER HP CF283A PRETO", "toner hp cf283a preto"),
    ("Papel 75 g/m², A4", "papel 75 g/m2, a4"),
    ("FITA ADESIVA 12MM X 30M", "fita adesiva 12 mm x 30 m"),
    ("CANETA C/ TAMPA , S/ PRENDEDOR,,  P/ QUADRO ", "caneta com tampa, sem prendedor, para quadro"),
    ("RESISTÊNCIA: 10 KOHMS; POTÊNCIA: 1/4 W", "resistencia: 10 kohms; potencia: 1/4 w"),
    ("MANGUEIRA 1/2” – 10M", 'mangueira 1/2" - 10 m'),
    ("álcool  &amp;amp; água", "alcool & agua"),
    ("LÂMPADA\tLED TUBULAR​18W", "lampada led tubular 18 w"),
]


@pytest.mark.parametrize("original, esperado", CASOS)
def teste_casos_conhecidos(original, esperado):
    resultado = normalizar_descricao(original)
    assert resultado.situacao == "valida"
    assert resultado.texto == esperado


@pytest.mark.parametrize("original, _", CASOS)
def teste_idempotente(original, _):
    uma_vez = normalizar_texto(original)
    assert normalizar_texto(uma_vez) == uma_vez


@pytest.mark.parametrize("original", [
    "PAPEL A4, 75G/M2, BRANCO, 210 X 297MM, RESMA C/ 500 FOLHAS",
    "RESISTOR 10K OHMS 1/4W",
    "PILHA ALCALINA AA 1,5V",
    "CAPACITOR ELETROLÍTICO 100UF 25V",
    "GRAMPO 26/6 CX C/ 5000",
    "DISCO DE CORTE 7\" X 1/8\" X 7/8\", 4.400 RPM",
    "TONER HP CF283A PRETO, RENDIMENTO 1.500 PAGINAS",
])
def teste_numeros_e_codigos_sao_preservados(original):
    """Toda sequência de dígitos do original continua no texto normalizado."""
    texto = normalizar_descricao(original).texto
    assert Counter(re.findall(r"\d+", original)) == Counter(re.findall(r"\d+", texto))


@pytest.mark.parametrize("trecho", ["1/2", "26/6", "g/m2", "km/h", "cf283a", "hp664xl", "4k7", "a4", "aaa"])
def teste_fracoes_e_codigos_nao_sao_tratados_como_abreviacao(trecho):
    assert trecho in normalizar_texto(f"ITEM {trecho.upper()} TESTE")


def teste_variacoes_da_mesma_descricao_tem_o_mesmo_hash():
    variacoes = [
        "CANETA ESFEROGRAFICA AZUL, PONTA MEDIA 1,0MM",
        "caneta esferografica azul,  ponta media 1,0mm",
        "  Caneta Esferográfica Azul , Ponta Média 1,0 mm ",
        "CANETA ESFEROGR&Aacute;FICA AZUL, PONTA M&Eacute;DIA 1,0MM",
    ]
    hashes = {normalizar_descricao(v).hash_normalizado for v in variacoes}
    assert len(hashes) == 1


def teste_descricoes_diferentes_tem_hashes_diferentes():
    a = normalizar_descricao("PILHA ALCALINA AA 1,5V").hash_normalizado
    b = normalizar_descricao("PILHA ALCALINA AAA 1,5V").hash_normalizado
    assert a != b


def teste_original_e_preservado():
    original = "  SABÃƒO EM PÃ“ 1KG  "
    resultado = normalizar_descricao(original)
    assert resultado.original == original
    assert resultado.hash_original == hashlib.sha256(original.encode("utf-8")).hexdigest()
    assert resultado.texto == "sabao em po 1 kg"


def teste_hash_muda_com_a_versao_das_regras(monkeypatch):
    antes = normalizar_descricao("PAPEL A4").hash_normalizado
    monkeypatch.setattr(normalizacao, "VERSAO_NORMALIZACAO", "teste")
    assert normalizar_descricao("PAPEL A4").hash_normalizado != antes


@pytest.mark.parametrize("valor, situacao", [
    (None, "vazia"),
    ("", "vazia"),
    ("   \t ", "vazia"),
    ("***", "invalida"),
    ("--", "invalida"),
    ("1234", "invalida"),
    ("12,50", "invalida"),
    ("ab", "invalida"),
])
def teste_descricoes_sem_conteudo_sao_recusadas_com_motivo(valor, situacao):
    resultado = normalizar_descricao(valor)
    assert resultado.situacao == situacao
    assert resultado.motivo
    assert resultado.texto is None and resultado.hash_normalizado is None
    assert not resultado.valida


@pytest.mark.parametrize("original, esperado", [
    ("SABÃƒO EM PÃ“", "sabao em po"),
    ("CONCENTRAÃ‡ÃƒO 70%", "concentracao 70%"),
    ("SÃO PAULO", "sao paulo"),  # texto correto não é alterado
    ("TEMPERATURA 25Â°C", "temperatura 25°c"),
])
def teste_mojibake(original, esperado):
    assert normalizar_texto(original) == esperado


def teste_texto_longo_nao_e_truncado():
    original = ", ".join(f"ATRIBUTO {i}: VALOR {i}" for i in range(200))
    texto = normalizar_texto(original)
    assert texto.endswith("atributo 199: valor 199")


def teste_valor_nao_textual_vira_texto():
    assert normalizar_descricao(990001).situacao == "invalida"  # só dígitos
    assert normalizar_descricao(990001).original == "990001"
