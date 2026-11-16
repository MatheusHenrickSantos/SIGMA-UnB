{{ config(tags=['distribuicao']) }}
{#-
    Teste de DISTRIBUIÇÃO: o preço unitário registrado de um material, no
    mesmo almoxarifado, não pode multiplicar ou dividir por 5 ou mais de um mês
    publicado para o seguinte. Um salto assim indica troca de unidade (caixa x
    unidade), vírgula decimal perdida ou erro de digitação, e distorce a
    comparação com o preço público sem quebrar nenhum tipo.
    Na carga de 10/11/2026 o teste achou 2 casos reais, investigados e
    registrados em seeds/excecoes_qualidade.csv; qualquer outro derruba o build.
-#}
WITH preco_mensal AS (
    SELECT
        identificador_material,
        identificador_almoxarifado,
        MAKE_DATE(ano_de_referencia, mes_de_referencia, 1) AS mes,
        AVG(preco) AS preco
    FROM {{ ref('estoque_prata') }}
    WHERE preco > 0
    GROUP BY 1, 2, 3
),

serie AS (
    SELECT
        *,
        LAG(preco) OVER (
            PARTITION BY identificador_material, identificador_almoxarifado ORDER BY mes
        ) AS preco_anterior
    FROM preco_mensal
)

SELECT *
FROM serie
WHERE preco_anterior IS NOT NULL
  AND (preco >= 5 * preco_anterior OR preco_anterior >= 5 * preco)
  AND NOT EXISTS (
      SELECT 1 FROM {{ ref('excecoes_qualidade') }} AS excecao
      WHERE excecao.teste = 'distribuicao_salto_preco_estoque'
        AND excecao.chave = TRIM(serie.identificador_material) || ' '
            || TRIM(serie.identificador_almoxarifado) || ' ' || TO_CHAR(serie.mes, 'YYYY-MM')
  )
