{{ config(
    materialized = 'table',
    schema = 'bronze',
    alias='catmat'
) }}

SELECT
    NULLIF(item ->> 'codigoItem', '')::INTEGER AS codigo_item,
    NULLIF(item ->> 'codigoGrupo', '')::INTEGER AS codigo_grupo,
    item ->> 'nomeGrupo' AS nome_grupo,
    NULLIF(item ->> 'codigoClasse', '')::INTEGER AS codigo_classe,
    item ->> 'nomeClasse' AS nome_classe,
    NULLIF(item ->> 'codigoPdm', '')::INTEGER AS codigo_pdm,
    item ->> 'nomePdm' AS nome_pdm,
    item ->> 'descricaoItem' AS descricao_item,

    NULLIF(item ->> 'statusItem', '')::BOOLEAN AS status_item,
    NULLIF(item ->> 'itemSustentavel', '')::BOOLEAN AS item_sustentavel,

    NULLIF(item ->> 'codigo_ncm', '')::INTEGER AS codigo_ncm,
    item ->> 'descricao_ncm' AS descricao_ncm,
    NULLIF(item ->> 'aplica_margem_preferencia', '')::BOOLEAN
        AS aplica_margem_preferencia,

    NULLIF(item ->> 'dataHoraAtualizacao', '')::TIMESTAMP
        AS data_hora_atualizacao,

    catmat.hash_do_arquivo,
    catmat.data_da_insercao

FROM {{ source('raw', 'catmat') }} AS catmat

CROSS JOIN LATERAL
    jsonb_array_elements(catmat.dado_bruto) AS elemento(item)