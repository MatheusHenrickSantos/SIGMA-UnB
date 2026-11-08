{{ config(
    materialized='table',
    schema='prata',
    alias='catmat_classe'
) }}

SELECT DISTINCT
    codigo_classe,
    codigo_grupo,
    nome_classe
FROM {{ ref('catmat_bronze') }}