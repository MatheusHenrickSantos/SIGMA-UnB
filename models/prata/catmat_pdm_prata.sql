{{ config(
    materialized='table',
    schema='prata',
    alias='catmat_pdm'
) }}

SELECT DISTINCT
    codigo_pdm,
    codigo_classe,
    nome_pdm
FROM {{ ref('catmat_bronze') }}