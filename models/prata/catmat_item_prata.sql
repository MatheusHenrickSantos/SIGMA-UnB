{{ config(
    materialized='table',
    schema='prata',
    alias='catmat_item'
) }}

SELECT DISTINCT
    codigo_item,
    codigo_pdm,
    descricao_item,
    status_item
FROM {{ ref('catmat_bronze') }}