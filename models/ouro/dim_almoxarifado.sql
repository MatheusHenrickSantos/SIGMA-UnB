{{ config(materialized='table', schema='ouro', alias='dim_almoxarifado') }}

SELECT
    identificador_almoxarifado,
    TRIM(nome) AS nome
FROM {{ ref('almoxarifado_prata') }}
