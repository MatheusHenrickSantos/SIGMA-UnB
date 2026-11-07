{{ config(
    materialized='incremental',
    schema='prata',
    alias='almoxarifado',
    unique_key='identificador_almoxarifado',
    on_schema_change='fail'
) }}

WITH almoxarifados_origem AS (
    SELECT DISTINCT
        UPPER(TRIM(almoxarifado)) AS nome
    FROM {{ ref('estoque_bronze') }}
    WHERE almoxarifado IS NOT NULL
      AND TRIM(almoxarifado) <> ''
),

novos_almoxarifados AS (
    SELECT origem.nome
    FROM almoxarifados_origem AS origem
    {% if is_incremental() %}
    LEFT JOIN {{ this }} AS existente
        ON existente.nome = origem.nome
    WHERE existente.identificador_almoxarifado IS NULL
    {% endif %}
),

ultimo_identificador AS (
    {% if is_incremental() %}
    SELECT COALESCE(MAX(SUBSTRING(identificador_almoxarifado FROM 4)::INTEGER), 0) AS numero
    FROM {{ this }}
    {% else %}
    SELECT 0 AS numero
    {% endif %}
),

almoxarifados_numerados AS (
    SELECT
        nome,
        ROW_NUMBER() OVER (ORDER BY nome) AS numero_linha
    FROM novos_almoxarifados
)

SELECT
    {{ gerar_identificador(
        'alm',
        'ultimo_identificador.numero + almoxarifados_numerados.numero_linha'
    ) }} AS identificador_almoxarifado,

    nome::CHAR(20) AS nome
FROM almoxarifados_numerados
CROSS JOIN ultimo_identificador
