{{ config(materialized='table', schema='ouro', alias='dim_tempo') }}

{#- Um mês por linha, do primeiro ao último mês com estoque. publicado = o
    portal publicou o estoque daquele mês (há meses sem arquivo). -#}

WITH limites AS (
    SELECT
        MIN(MAKE_DATE(ano_de_referencia, mes_de_referencia, 1)) AS primeiro,
        MAX(MAKE_DATE(ano_de_referencia, mes_de_referencia, 1)) AS ultimo
    FROM {{ ref('estoque_prata') }}
),

publicados AS (
    SELECT DISTINCT MAKE_DATE(ano_de_referencia, mes_de_referencia, 1) AS mes
    FROM {{ ref('estoque_prata') }}
)

SELECT
    serie.mes::DATE AS mes_referencia,
    EXTRACT(YEAR FROM serie.mes)::SMALLINT AS ano,
    EXTRACT(MONTH FROM serie.mes)::SMALLINT AS mes,
    TO_CHAR(serie.mes, 'YYYY-MM') AS ano_mes,
    publicados.mes IS NOT NULL AS publicado,
    serie.mes BETWEEN DATE_TRUNC('month', '{{ var("compras_inicio") }}'::DATE)
                  AND '{{ var("compras_fim") }}'::DATE AS na_janela_compras
FROM limites
CROSS JOIN LATERAL GENERATE_SERIES(limites.primeiro, limites.ultimo, INTERVAL '1 month') AS serie(mes)
LEFT JOIN publicados ON publicados.mes = serie.mes
