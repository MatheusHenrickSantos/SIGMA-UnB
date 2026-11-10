{{ config(tags=['volume']) }}
{#-
    Teste de VOLUME: em cada almoxarifado, o número de linhas de estoque de um
    mês publicado não pode variar mais de 30% em relação ao mês publicado
    anterior. Pega carga parcial (arquivo truncado, almoxarifado faltando) que
    nenhum teste de esquema percebe.

    Exceções conhecidas ficam em seeds/excecoes_qualidade.csv, com o motivo:
    sem estar lá, a variação derruba o build.
-#}
WITH mensal AS (
    SELECT
        almoxarifado.nome AS almoxarifado,
        MAKE_DATE(estoque.ano_de_referencia, estoque.mes_de_referencia, 1) AS mes,
        COUNT(*) AS linhas
    FROM {{ ref('estoque_prata') }} AS estoque
    INNER JOIN {{ ref('almoxarifado_prata') }} AS almoxarifado
        USING (identificador_almoxarifado)
    GROUP BY 1, 2
),

comparado AS (
    SELECT
        almoxarifado,
        mes,
        linhas,
        LAG(linhas) OVER (PARTITION BY almoxarifado ORDER BY mes) AS linhas_mes_anterior
    FROM mensal
)

SELECT
    TRIM(almoxarifado) AS almoxarifado,
    mes,
    linhas,
    linhas_mes_anterior,
    ROUND(100.0 * (linhas - linhas_mes_anterior) / linhas_mes_anterior, 1) AS variacao_pct
FROM comparado
WHERE linhas_mes_anterior IS NOT NULL
  AND ABS(linhas - linhas_mes_anterior) > 0.30 * linhas_mes_anterior
  AND NOT EXISTS (
      SELECT 1 FROM {{ ref('excecoes_qualidade') }} AS excecao
      WHERE excecao.teste = 'volume_estoque_mensal'
        AND excecao.chave = TRIM(comparado.almoxarifado) || ' ' || TO_CHAR(comparado.mes, 'YYYY-MM')
  )
