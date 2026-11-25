{{ config(
    materialized = 'table',
    schema = 'bronze',
    alias='catmat'
) }}

WITH catalogos_enumerados AS (
    SELECT
        dado_bruto,
        hash_do_arquivo,
        data_da_insercao,
        ROW_NUMBER() OVER (
            ORDER BY data_da_insercao DESC, hash_do_arquivo DESC
        ) AS posicao
    FROM {{ source('raw', 'catmat') }}
),

snapshot_mais_recente AS (
    SELECT
        dado_bruto,
        hash_do_arquivo,
        data_da_insercao
    FROM catalogos_enumerados
    WHERE posicao = 1
)

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

    NULLIF(item ->> 'dataHoraAtualizacao', '')::TIMESTAMP
        AS data_hora_atualizacao,

    snapshot_mais_recente.hash_do_arquivo,
    snapshot_mais_recente.data_da_insercao

FROM snapshot_mais_recente

CROSS JOIN LATERAL
    jsonb_array_elements(snapshot_mais_recente.dado_bruto) AS elemento(item)