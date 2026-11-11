{{ config(materialized='table', schema='ouro', alias='monitor_atualizacao') }}

{#-
    Freshness das tabelas de consumo e SLA declarado (E3).

    SLA do fato_comparacao_preco: o estoque do mês M deve estar no fato até
    45 dias depois do fim de M (o portal da UnB publica o arquivo do mês no
    mês seguinte; 45 dias dão folga para a carga mensal).
    SLA da compra_publica: compras com no máximo 60 dias de defasagem em
    relação ao fim da janela consultada.

    atraso_dias = dias entre o fim do período do último dado e a data desta
    medição. O dbt source freshness (freshness em models/fontes.yml) mede o
    mesmo na camada raw e avisa/falha pelo mesmo critério.
-#}

WITH medidas AS (
    SELECT
        'ouro.fato_comparacao_preco' AS tabela,
        (MAX(mes_referencia) + INTERVAL '1 month' - INTERVAL '1 day')::DATE AS ultimo_dado,
        MAX(carregado_em) AS ultima_carga,
        45 AS sla_dias
    FROM {{ ref('fato_comparacao_preco') }}

    UNION ALL

    SELECT
        'prata.compra_publica',
        MAX(data_compra),
        NULL::TIMESTAMPTZ,
        60
    FROM {{ ref('compra_publica_prata') }}
)

SELECT
    tabela,
    ultimo_dado,
    ultima_carga,
    CURRENT_DATE - ultimo_dado AS atraso_dias,
    sla_dias,
    CASE WHEN CURRENT_DATE - ultimo_dado <= sla_dias THEN 'dentro do SLA' ELSE 'fora do SLA' END
        AS situacao_sla,
    CURRENT_TIMESTAMP AS medido_em
FROM medidas
