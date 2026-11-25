{{ config(materialized='table', schema='ouro', alias='catalogo_metrica') }}

{#- Definição de cada métrica, tal como está em macros/metricas.sql: o painel
    mostra esta tabela, então a documentação nunca diverge da fórmula. -#}

{% for m in metricas_base() %}
SELECT '{{ m.nome }}' AS metrica, 'base' AS tipo, '{{ m.unidade }}' AS unidade, {{ m.versao }} AS versao,
       '{{ m.descricao | replace("'", "''") }}' AS descricao, '{{ m.expressao | replace("'", "''") }}' AS formula
UNION ALL
{% endfor %}
{% for m in metricas_derivadas() %}
SELECT '{{ m.nome }}', 'derivada', '{{ m.unidade }}', {{ m.versao }},
       '{{ m.descricao | replace("'", "''") }}', '{{ m.expressao | replace("'", "''") }}'
{{ 'UNION ALL' if not loop.last }}
{% endfor %}
