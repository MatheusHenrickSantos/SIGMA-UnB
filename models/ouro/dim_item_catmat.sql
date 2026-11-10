{{ config(materialized='table', schema='ouro', alias='dim_item_catmat') }}

SELECT
    item.codigo_item,
    item.descricao_item,
    item.status_item,
    pdm.codigo_pdm,
    pdm.nome_pdm,
    classe.codigo_classe,
    classe.nome_classe,
    grupo.codigo_grupo,
    grupo.nome_grupo
FROM {{ ref('catmat_item_prata') }} AS item
LEFT JOIN {{ ref('catmat_pdm_prata') }} AS pdm USING (codigo_pdm)
LEFT JOIN {{ ref('catmat_classe_prata') }} AS classe USING (codigo_classe)
LEFT JOIN {{ ref('catmat_grupo_prata') }} AS grupo USING (codigo_grupo)
