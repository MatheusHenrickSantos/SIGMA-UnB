{{ config(
    materialized = 'table',
    schema = 'prata',
    alias = 'compra_publica'
) }}

{#-
    Compras públicas na janela de análise (vars compras_inicio e compras_fim
    do dbt_project.yml) com preço positivo. Preço nulo ou <= 0 é descartado.
    identificador_item_compra é a chave; identificador_compra repete quando a
    compra tem vários itens.
-#}

SELECT
    id_item_compra AS identificador_item_compra,
    id_compra AS identificador_compra,
    codigo_item_catalogo AS codigo_item,
    quantidade,
    preco_unitario,
    sigla_unidade_fornecimento AS unidade_fornecimento,
    nome_unidade_fornecimento,
    capacidade_unidade_fornecimento,
    sigla_unidade_medida,
    data_compra

FROM {{ ref('compras_bronze') }}

WHERE data_compra BETWEEN '{{ var("compras_inicio") }}'::DATE
                      AND '{{ var("compras_fim") }}'::DATE
  AND preco_unitario > 0
