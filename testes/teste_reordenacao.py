"""Testes da reordenação híbrida (cosseno + rapidfuzz), sem banco."""

from __future__ import annotations

import pytest

from semantica.reordenacao import (
    PESOS_PADRAO,
    Consulta,
    normalizar_lexico,
    ordenar,
    pontuar,
    termos_relevantes,
)


def teste_normalizar_lexico_tira_acentos_pontuacao_e_troca_virgula_decimal():
    assert normalizar_lexico("Pilha alcalina, AAA – 1,5V (cartela)") == "PILHA ALCALINA AAA 1.5V CARTELA"
    assert normalizar_lexico("água sanitária/clorada") == "AGUA SANITARIA CLORADA"
    assert normalizar_lexico(None) == ""
    assert normalizar_lexico("") == ""


def teste_normalizar_lexico_remove_porte_da_empresa():
    assert normalizar_lexico("CANETA AZUL ME/EPP") == "CANETA AZUL"


def teste_termos_relevantes_ignora_palavras_genericas():
    termos = termos_relevantes(normalizar_lexico("MATERIAL: PAPEL, TIPO: A4, COR: BRANCA, 75 G/M2"))
    assert termos == {"PAPEL", "A4", "BRANCA", "75", "G", "M2"}


def teste_pesos_somam_um():
    assert sum(PESOS_PADRAO.values()) == pytest.approx(1.0)


def teste_texto_identico_com_cosseno_um_tem_pontuacao_maxima():
    consulta = Consulta.de("papel a4 75 g/m2 branco")
    medidas = pontuar(consulta, "papel a4 75 g/m2 branco", 1.0)
    assert medidas.pontuacao == pytest.approx(100.0)
    assert medidas.cobertura == pytest.approx(100.0)


def teste_cosseno_fora_do_intervalo_e_limitado():
    consulta = Consulta.de("papel a4")
    assert pontuar(consulta, "xyz", -0.3).cosseno == -0.3  # medida guardada como veio
    assert pontuar(consulta, "xyz", -0.3).pontuacao == pytest.approx(
        pontuar(consulta, "xyz", 0.0).pontuacao
    )


def teste_texto_parecido_vence_vetor_um_pouco_mais_proximo():
    """O caso que motivou a reordenação: o modelo põe na frente um item de outra natureza."""
    consulta = Consulta.de("resistor 1,2 kohm 1/4 w")
    certo = pontuar(consulta, "resistor, resistencia: 1,2 kohm, potencia: 1/4 w", 0.86)
    errado = pontuar(consulta, "capacitor ceramico 1,2 nf 50 v", 0.88)
    assert certo.pontuacao > errado.pontuacao


def teste_cobertura_mede_termos_do_material_presentes_no_catmat():
    consulta = Consulta.de("luva latex tamanho m")
    medidas = pontuar(consulta, "luva procedimento, material: latex, tamanho: g", 0.9)
    # LUVA, LATEX, TAMANHO presentes; M ausente
    assert medidas.cobertura == pytest.approx(75.0)


def teste_ordenar_poe_conflito_por_ultimo_e_desempata_pelo_codigo():
    candidatos = [
        {"chave": "3", "conflito": True, "pontuacao": 99.0, "cosseno": 0.99},
        {"chave": "2", "conflito": False, "pontuacao": 80.0, "cosseno": 0.80},
        {"chave": "1", "conflito": False, "pontuacao": 80.0, "cosseno": 0.80},
        {"chave": "4", "conflito": False, "pontuacao": 85.0, "cosseno": 0.70},
    ]
    assert [c["chave"] for c in ordenar(candidatos)] == ["4", "1", "2", "3"]


def teste_medidas_como_dict_tem_as_quatro_medidas():
    medidas = pontuar(Consulta.de("caneta azul"), "caneta esferografica azul", 0.9)
    assert set(medidas.como_dict()) == {"cosseno", "token_set", "token_sort", "cobertura"}
