{{ config(tags=['descricao']) }}

WITH descricao_calculada AS (
    SELECT
        descricao_normalizada,
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
        ) AS descricao_esperada,
        descricao AS descricao_atual
    FROM {{ ref('material_prata') }}
)

SELECT *
FROM descricao_calculada
WHERE descricao_atual <> descricao_esperada
