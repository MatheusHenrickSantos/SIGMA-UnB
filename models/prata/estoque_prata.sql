{{ config(
    materialized='table',
    schema='prata',
    alias='estoque'
) }}

SELECT
    material.identificador_material,
    almoxarifado.identificador_almoxarifado,
    origem.mes_de_referencia,
    origem.ano_de_referencia,
    origem.saldo AS quantidade,
    origem.preco
FROM {{ ref('estoque_bronze') }} AS origem
INNER JOIN {{ ref('material_prata') }} AS material
    ON material.material_original = TRIM(origem.material)
INNER JOIN {{ ref('almoxarifado_prata') }} AS almoxarifado
    ON almoxarifado.nome = UPPER(TRIM(origem.almoxarifado))
