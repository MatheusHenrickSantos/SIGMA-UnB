{{ config(
    materialized = 'table',
    schema = 'bronze',
    alias = 'compras'
) }}

{#-
    Compras públicas (Compras.gov.br, pesquisa de preços) em formato tabular.
    Cada linha de raw.compras é um arquivo com a lista de registros da API de
    um código CATMAT (codigos/inserir/baixar_compras.py).

    Deduplica por id_item_compra, a chave real da API: o par
    (id_compra, codigo_item_catalogo) se repete quando a compra tem vários
    itens do mesmo código ou fornecedores diferentes no mesmo item. Quando o
    mesmo registro chega em arquivos diferentes (janelas que se sobrepõem),
    fica o de atualização mais recente. Mantém todas as datas; o recorte da
    janela é feito na Prata.
-#}

WITH itens AS (
    SELECT
        compras.hash_do_arquivo,
        compras.data_da_insercao,
        elemento
    FROM {{ source('raw', 'compras') }} AS compras
    CROSS JOIN LATERAL jsonb_array_elements(compras.dado_bruto) AS item(elemento)
),

tipados AS (
    SELECT
        NULLIF(elemento ->> 'idItemCompra', '')::NUMERIC::BIGINT AS id_item_compra,
        NULLIF(elemento ->> 'idCompra', '') AS id_compra,
        NULLIF(elemento ->> 'codigoItemCatalogo', '')::NUMERIC::INTEGER AS codigo_item_catalogo,
        NULLIF(elemento ->> 'dataCompra', '')::DATE AS data_compra,
        NULLIF(elemento ->> 'dataHoraAtualizacaoItem', '')::TIMESTAMP AS data_hora_atualizacao_item,
        NULLIF(elemento ->> 'quantidade', '')::NUMERIC AS quantidade,
        NULLIF(elemento ->> 'precoUnitario', '')::NUMERIC AS preco_unitario,
        elemento ->> 'descricaoItem' AS descricao_item,
        elemento ->> 'forma' AS forma,
        elemento ->> 'siglaUnidadeFornecimento' AS sigla_unidade_fornecimento,
        elemento ->> 'nomeUnidadeFornecimento' AS nome_unidade_fornecimento,
        NULLIF(elemento ->> 'capacidadeUnidadeFornecimento', '')::NUMERIC
            AS capacidade_unidade_fornecimento,
        elemento ->> 'siglaUnidadeMedida' AS sigla_unidade_medida,
        hash_do_arquivo,
        data_da_insercao
    FROM itens
),

numerados AS (
    SELECT
        tipados.*,
        ROW_NUMBER() OVER (
            PARTITION BY id_item_compra
            ORDER BY data_hora_atualizacao_item DESC NULLS LAST,
                     data_da_insercao DESC,
                     hash_do_arquivo
        ) AS ordem
    FROM tipados
    WHERE id_item_compra IS NOT NULL
)

SELECT
    id_item_compra,
    id_compra,
    codigo_item_catalogo,
    data_compra,
    data_hora_atualizacao_item,
    quantidade,
    preco_unitario,
    descricao_item,
    forma,
    sigla_unidade_fornecimento,
    nome_unidade_fornecimento,
    capacidade_unidade_fornecimento,
    sigla_unidade_medida,
    hash_do_arquivo,
    data_da_insercao
FROM numerados
WHERE ordem = 1
