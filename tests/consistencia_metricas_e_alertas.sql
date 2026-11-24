{#-
    Consistência entre a camada de métricas e o ETL reverso: no último mês, o
    número de alertas e a economia potencial da tabela entregue a compras têm
    de ser iguais aos das métricas materiais_alertados e economia_potencial
    (almoxarifado = 'TODOS'). Se alguém mudar a regra de um lado só, falha.
-#}
WITH ultimo AS (SELECT MAX(mes_referencia) AS mes FROM {{ ref('metrica_mensal') }}),

metrica AS (
    SELECT
        MAX(valor) FILTER (WHERE metrica = 'materiais_alertados') AS alertados,
        MAX(valor) FILTER (WHERE metrica = 'economia_potencial') AS economia
    FROM {{ ref('metrica_mensal') }}
    INNER JOIN ultimo ON ultimo.mes = mes_referencia
    WHERE almoxarifado = 'TODOS'
),

entrega AS (
    SELECT COUNT(*) AS alertados, COALESCE(SUM(economia_potencial), 0) AS economia
    FROM {{ ref('alerta_preco_compras') }}
)

SELECT metrica.alertados AS metrica_alertados, entrega.alertados AS entregues,
       metrica.economia AS metrica_economia, entrega.economia AS economia_entregue
FROM metrica CROSS JOIN entrega
WHERE metrica.alertados <> entrega.alertados
   OR ABS(metrica.economia - entrega.economia) > 1
