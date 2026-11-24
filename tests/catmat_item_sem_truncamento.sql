{{ config(tags=['descricao']) }}

WITH catmat_prata AS (
    SELECT codigo_item, descricao_item
    FROM {{ ref('catmat_item_prata') }}
),

catmat_bronze AS (
    SELECT DISTINCT codigo_item, descricao_item
    FROM {{ ref('catmat_bronze') }}
)

SELECT p.*
FROM catmat_prata AS p
LEFT JOIN catmat_bronze AS b
  ON b.codigo_item = p.codigo_item
 AND b.descricao_item IS NOT DISTINCT FROM p.descricao_item
WHERE b.codigo_item IS NULL
