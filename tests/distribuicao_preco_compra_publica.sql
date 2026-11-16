{{ config(tags=['distribuicao']) }}
{#-
    Teste de DISTRIBUIÇÃO das compras públicas: entre os códigos CATMAT com 5
    ou mais compras na janela, a fração de registros com preço a mais de 10x
    (para cima ou para baixo) da mediana do próprio código não pode passar de
    8%. Na carga de 10/11/2026 ela é 5,86% (unidades de fornecimento
    diferentes, como embalagem x unidade). Uma subida brusca indica mudança de
    escala na API (centavos x reais) ou registros de outro item.
-#}
WITH mediana AS (
    SELECT
        codigo_item,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY preco_unitario) AS preco_mediano,
        COUNT(*) AS compras
    FROM {{ ref('compra_publica_prata') }}
    GROUP BY 1
),

medida AS (
    SELECT
        COUNT(*) AS registros,
        COUNT(*) FILTER (
            WHERE compra.preco_unitario > 10 * mediana.preco_mediano
               OR compra.preco_unitario < mediana.preco_mediano / 10
        ) AS fora_da_faixa
    FROM {{ ref('compra_publica_prata') }} AS compra
    INNER JOIN mediana USING (codigo_item)
    WHERE mediana.compras >= 5
)

SELECT
    registros,
    fora_da_faixa,
    ROUND(100.0 * fora_da_faixa / registros, 2) AS fora_da_faixa_pct
FROM medida
WHERE registros > 0
  AND fora_da_faixa > 0.08 * registros
