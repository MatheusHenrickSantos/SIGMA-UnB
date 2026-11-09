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

INNER JOIN {{ ref('materiais_normalizados') }} AS normalizacao
    ON TRIM(normalizacao.descricao_original) = TRIM(origem.material)

INNER JOIN {{ ref('material_prata') }} AS material
    ON material.descricao_normalizada = normalizacao.descricao_normalizada

INNER JOIN {{ ref('almoxarifado_prata') }} AS almoxarifado
    ON almoxarifado.nome = UPPER(TRIM(origem.almoxarifado))
