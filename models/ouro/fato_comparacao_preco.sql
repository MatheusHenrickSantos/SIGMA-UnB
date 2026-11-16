{{ config(
    materialized='incremental',
    schema='ouro',
    alias='fato_comparacao_preco',
    unique_key=['identificador_material', 'identificador_almoxarifado', 'mes_referencia'],
    incremental_strategy='delete+insert',
    on_schema_change='fail'
) }}

{#-
    GRÃO: uma linha por material, por almoxarifado, por mês de referência
    publicado no portal de dados abertos da UnB.

    Responde à pergunta da E1: para cada material com estoque num almoxarifado
    e mês, qual o preço registrado no estoque, qual o preço de referência das
    compras públicas dos itens CATMAT equivalentes e qual a diferença.

    - preco_estoque: média do preço ponderada pela quantidade das linhas do
      mês (o mesmo material pode vir com dois preços no mesmo mês quando a
      normalização une duas descrições); linhas com preço <= 0 ficam de fora
      (teste preco_estoque_positivo);
    - preco_publico_mediano: mediana do preço unitário das compras públicas
      (prata.compra_publica, janela compras_inicio..compras_fim) dos itens
      CATMAT equivalentes ao material NA VERSÃO DA CORRESPONDÊNCIA VIGENTE
      QUANDO A LINHA FOI CARREGADA (sk_material aponta para essa versão da
      dim_material, SCD tipo 2);
    - diferenca_pct = (preco_estoque / preco_publico_mediano - 1) * 100. É um
      sinal para investigar, não prova de sobrepreço: a unidade de
      fornecimento das compras pode diferir da do estoque.

    Carga incremental por mês: uma execução comum só insere os meses que
    ainda não estão na tabela, então as linhas antigas mantêm a versão da
    correspondência com que foram calculadas. Backfill de um mês:
        dbt build --select fato_comparacao_preco --vars '{mes_referencia: "2025-12-01"}'
    recalcula só aquele mês (delete+insert), com a correspondência atual.
-#}

{% set mes_referencia = var('mes_referencia', none) %}

WITH estoque AS (
    SELECT
        identificador_material,
        identificador_almoxarifado,
        MAKE_DATE(ano_de_referencia, mes_de_referencia, 1) AS mes_referencia,
        SUM(quantidade) AS quantidade,
        CASE
            WHEN SUM(quantidade) > 0 THEN SUM(quantidade * preco) / SUM(quantidade)
            ELSE AVG(preco)
        END AS preco_estoque,
        SUM(quantidade * preco) AS valor_estoque,
        COUNT(*) AS linhas_origem
    FROM {{ ref('estoque_prata') }}
    WHERE preco > 0
    {% if mes_referencia %}
      AND MAKE_DATE(ano_de_referencia, mes_de_referencia, 1) = '{{ mes_referencia }}'::DATE
    {% elif is_incremental() %}
      AND MAKE_DATE(ano_de_referencia, mes_de_referencia, 1) NOT IN (
          SELECT DISTINCT mes_referencia FROM {{ this }}
      )
    {% endif %}
    GROUP BY 1, 2, 3
),

versao_atual AS (
    SELECT
        sk_material,
        identificador_material,
        codigos_equivalentes,
        tipo_revisor,
        sem_correspondente
    FROM {{ ref('dim_material') }}
    WHERE atual
),

item_do_material AS (
    SELECT
        versao_atual.identificador_material,
        codigo::INTEGER AS codigo_item
    FROM versao_atual
    CROSS JOIN LATERAL UNNEST(STRING_TO_ARRAY(NULLIF(versao_atual.codigos_equivalentes, ''), '|')) AS codigo
),

compras_do_material AS (
    SELECT
        item_do_material.identificador_material,
        compra.preco_unitario,
        compra.unidade_fornecimento,
        compra.codigo_item
    FROM item_do_material
    INNER JOIN {{ ref('compra_publica_prata') }} AS compra
        ON compra.codigo_item = item_do_material.codigo_item
),

referencia AS (
    SELECT
        identificador_material,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY preco_unitario) AS preco_publico_mediano,
        COUNT(*) AS compras_publicas,
        COUNT(DISTINCT codigo_item) AS itens_catmat_com_compra,
        MODE() WITHIN GROUP (ORDER BY unidade_fornecimento) AS unidade_fornecimento_predominante
    FROM compras_do_material
    GROUP BY 1
)

SELECT
    estoque.mes_referencia,
    estoque.identificador_material,
    estoque.identificador_almoxarifado,
    versao_atual.sk_material,
    COALESCE(versao_atual.tipo_revisor, 'sem_decisao') AS tipo_revisor_correspondencia,
    estoque.quantidade,
    ROUND(estoque.preco_estoque, 4) AS preco_estoque,
    estoque.valor_estoque,
    estoque.linhas_origem,
    ROUND(referencia.preco_publico_mediano::NUMERIC, 4) AS preco_publico_mediano,
    COALESCE(referencia.compras_publicas, 0) AS compras_publicas,
    COALESCE(referencia.itens_catmat_com_compra, 0) AS itens_catmat_com_compra,
    referencia.unidade_fornecimento_predominante,
    referencia.preco_publico_mediano IS NOT NULL AS tem_preco_publico,
    ROUND((estoque.preco_estoque - referencia.preco_publico_mediano::NUMERIC), 4) AS diferenca_absoluta,
    ROUND(
        ((estoque.preco_estoque / NULLIF(referencia.preco_publico_mediano, 0)::NUMERIC) - 1) * 100,
        2
    ) AS diferenca_pct,
    CURRENT_TIMESTAMP AS carregado_em
FROM estoque
LEFT JOIN versao_atual USING (identificador_material)
LEFT JOIN referencia USING (identificador_material)
