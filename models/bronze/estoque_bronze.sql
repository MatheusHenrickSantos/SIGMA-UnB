-- modelos/bronze/estoque.sql
{{ config(
    materialized = 'table',
    schema = 'bronze',
    alias='estoque'
) }}

SELECT
    elemento ->> 'material' AS material,
    elemento ->> 'almoxarifado' AS almoxarifado,

    (elemento ->> 'saldo')::NUMERIC AS saldo,

    REPLACE(
        REPLACE(
            REGEXP_REPLACE(elemento ->> 'preco', '[^0-9,.]', '', 'g'),
            '.',
            ''
        ),
        ',',
        '.'
    )::NUMERIC AS preco,

    REPLACE(
        REPLACE(
            REGEXP_REPLACE(elemento ->> 'valor_total', '[^0-9,.]', '', 'g'),
            '.',
            ''
        ),
        ',',
        '.'
    )::NUMERIC AS valor_total,

    estoque.mes_de_referencia,
    estoque.ano_de_referencia,
    estoque.hash_do_arquivo

FROM {{ source('raw', 'estoque') }} AS estoque

CROSS JOIN LATERAL jsonb_array_elements(estoque.dado_bruto) AS item(elemento)