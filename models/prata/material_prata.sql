{{ config(
    materialized='incremental',
    schema='prata',
    alias='material',
    unique_key='identificador_material',
    on_schema_change='fail'
) }}

WITH materiais_origem AS (
    SELECT DISTINCT
        TRIM(normalizacao.descricao_normalizada) AS descricao_normalizada

    FROM {{ ref('estoque_bronze') }} AS estoque

    INNER JOIN {{ ref('materiais_normalizados') }} AS normalizacao
        ON TRIM(estoque.material) = TRIM(normalizacao.descricao_original)

    WHERE normalizacao.descricao_normalizada IS NOT NULL
      AND TRIM(normalizacao.descricao_normalizada) <> ''
),

novos_materiais AS (
    SELECT origem.descricao_normalizada

    FROM materiais_origem AS origem

    {% if is_incremental() %}
    LEFT JOIN {{ this }} AS existente
        ON existente.descricao_normalizada = origem.descricao_normalizada

    WHERE existente.identificador_material IS NULL
    {% endif %}
),

ultimo_identificador AS (
    {% if is_incremental() %}
    SELECT
        COALESCE(
            MAX(SUBSTRING(identificador_material FROM 4)::INTEGER),
            0
        ) AS numero
    FROM {{ this }}
    {% else %}
    SELECT 0 AS numero
    {% endif %}
),

materiais_numerados AS (
    SELECT
        descricao_normalizada,
        ROW_NUMBER() OVER (
            ORDER BY descricao_normalizada
        ) AS numero_linha

    FROM novos_materiais
)

SELECT
    {{ gerar_identificador(
        'ma',
        'ultimo_identificador.numero + materiais_numerados.numero_linha'
    ) }} AS identificador_material,

    SPLIT_PART(
        descricao_normalizada,
        ',',
        1
    )::CHAR(50) AS nome,

    COALESCE(
        NULLIF(
            TRIM(
                SUBSTRING(
                    descricao_normalizada
                    FROM POSITION(',' IN descricao_normalizada) + 1
                )
            ),
            ''
        ),
        descricao_normalizada
    )::CHAR(200) AS descricao,

    descricao_normalizada

FROM materiais_numerados
CROSS JOIN ultimo_identificador
