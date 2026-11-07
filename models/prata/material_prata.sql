{{ config(
    materialized='incremental',
    schema='prata',
    alias='material',
    unique_key='identificador_material',
    on_schema_change='fail'
) }}

WITH materiais_origem AS (
    SELECT DISTINCT
        TRIM(material) AS material_original
    FROM {{ ref('estoque_bronze') }}
    WHERE material IS NOT NULL
      AND TRIM(material) <> ''
),

novos_materiais AS (
    SELECT origem.material_original
    FROM materiais_origem AS origem
    {% if is_incremental() %}
    LEFT JOIN {{ this }} AS existente
        ON existente.material_original = origem.material_original
    WHERE existente.identificador_material IS NULL
    {% endif %}
),

ultimo_identificador AS (
    {% if is_incremental() %}
    SELECT COALESCE(MAX(SUBSTRING(identificador_material FROM 4)::INTEGER), 0) AS numero
    FROM {{ this }}
    {% else %}
    SELECT 0 AS numero
    {% endif %}
),

materiais_numerados AS (
    SELECT
        material_original,
        ROW_NUMBER() OVER (ORDER BY material_original) AS numero_linha
    FROM novos_materiais
)

SELECT
    {{ gerar_identificador(
        'mat',
        'ultimo_identificador.numero + materiais_numerados.numero_linha'
    ) }} AS identificador_material,

    SPLIT_PART(material_original, ',', 1)::CHAR(50) AS nome,

    COALESCE(
        NULLIF(TRIM(SUBSTRING(material_original FROM POSITION(',' IN material_original) + 1)), ''),
        material_original
    )::CHAR(100) AS descricao,

    material_original
FROM materiais_numerados
CROSS JOIN ultimo_identificador
