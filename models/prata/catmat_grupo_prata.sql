{{ config(
    materialized='table',
    schema='prata',
    alias='catmat_grupo'
) }}

SELECT DISTINCT
    codigo_grupo,
    nome_grupo
FROM {{ ref('catmat_bronze') }}