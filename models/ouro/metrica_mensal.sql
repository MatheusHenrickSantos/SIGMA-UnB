{{ config(materialized='table', schema='ouro', alias='metrica_mensal') }}

{#-
    Métricas em formato longo: uma linha por (métrica, mês, almoxarifado).
    almoxarifado = 'TODOS' é o total (calculado do zero, não a soma de razões).
    As fórmulas vêm de macros/metricas.sql; este modelo só as aplica.
-#}

{% set base = metricas_base() %}
{% set derivadas = metricas_derivadas() %}

WITH fato AS (
    SELECT
        f.*,
        TRIM(a.nome) AS almoxarifado
    FROM {{ ref('fato_comparacao_preco') }} AS f
    INNER JOIN {{ ref('dim_almoxarifado') }} AS a USING (identificador_almoxarifado)
),

agregadas AS (
    SELECT
        f.mes_referencia,
        COALESCE(f.almoxarifado, 'TODOS') AS almoxarifado,
        {% for m in base %}
        {{ m.expressao }} AS {{ m.nome }}{{ ',' if not loop.last }}
        {% endfor %}
    FROM fato AS f
    INNER JOIN {{ ref('dim_material') }} AS d ON d.sk_material = f.sk_material
    GROUP BY GROUPING SETS ((f.mes_referencia, f.almoxarifado), (f.mes_referencia))
),

completas AS (
    SELECT
        agregadas.*,
        {% for m in derivadas %}
        {{ m.expressao }} AS {{ m.nome }}{{ ',' if not loop.last }}
        {% endfor %}
    FROM agregadas
)

{% for m in base + derivadas %}
SELECT mes_referencia, almoxarifado, '{{ m.nome }}' AS metrica, {{ m.nome }}::NUMERIC AS valor,
       '{{ m.unidade }}' AS unidade, {{ m.versao }} AS versao_definicao
FROM completas
{{ 'UNION ALL' if not loop.last }}
{% endfor %}
