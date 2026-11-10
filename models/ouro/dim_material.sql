{{ config(materialized='table', schema='ouro', alias='dim_material') }}

{#-
    Dimensão material, SCD tipo 2: uma linha por VERSÃO da correspondência do
    material com o CATMAT (snapshots/snap_correspondencia_material.sql).
    sk_material identifica a versão; valido_de/valido_ate delimitam quando ela
    valeu; atual marca a versão vigente.
-#}

SELECT
    MD5(snapshot.identificador_material || '|' || snapshot.dbt_valid_from::TEXT) AS sk_material,
    snapshot.identificador_material,
    TRIM(material.nome) AS nome,
    snapshot.material AS descricao,
    snapshot.codigos_equivalentes,
    CASE
        WHEN snapshot.codigos_equivalentes = '' THEN 0
        ELSE ARRAY_LENGTH(STRING_TO_ARRAY(snapshot.codigos_equivalentes, '|'), 1)
    END AS quantidade_itens_catmat,
    snapshot.sem_correspondente,
    snapshot.tipo_revisor,
    snapshot.confianca,
    snapshot.dbt_valid_from AS valido_de,
    COALESCE(snapshot.dbt_valid_to, TIMESTAMP '9999-12-31') AS valido_ate,
    snapshot.dbt_valid_to IS NULL AS atual
FROM {{ ref('snap_correspondencia_material') }} AS snapshot
LEFT JOIN {{ ref('material_prata') }} AS material
    ON material.identificador_material = snapshot.identificador_material
