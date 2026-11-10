{{ config(tags=['dominio'], warn_if='>0', error_if='>5') }}
{#-
    Sujeira do domínio: preço unitário zero ou negativo no estoque. Não entra
    na comparação de preços. Avisa a partir de 1 caso e falha acima de 5 (um
    arquivo inteiro com preço zerado, por exemplo). Em 10/11/2026 há 1 caso:
    avental hospitalar (ma0141) com preço 0,00 em 07/2022 no almoxarifado Central.
-#}
SELECT
    identificador_material,
    identificador_almoxarifado,
    ano_de_referencia,
    mes_de_referencia,
    quantidade,
    preco
FROM {{ ref('estoque_prata') }}
WHERE preco <= 0
