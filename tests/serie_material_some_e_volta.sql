{{ config(tags=['dominio'], warn_if='>0', error_if='>200') }}
{#-
    Salto de série: material que está no estoque de um almoxarifado num mês
    publicado, some no mês publicado seguinte e reaparece no próximo. Pode ser
    saldo que zerou e voltou (legítimo) ou linha perdida na publicação; a
    série de saldo e preço desse material tem um buraco. Avisa sempre; falha
    acima de 200 casos (eram 55 em 10/11/2026), o que indicaria um mês
    publicado com linhas faltando.
-#}
WITH meses AS (
    SELECT
        mes,
        ROW_NUMBER() OVER (ORDER BY mes) AS ordem
    FROM (
        SELECT DISTINCT MAKE_DATE(ano_de_referencia, mes_de_referencia, 1) AS mes
        FROM {{ ref('estoque_prata') }}
    ) AS publicados
),

presenca AS (
    SELECT DISTINCT
        estoque.identificador_material,
        estoque.identificador_almoxarifado,
        meses.ordem,
        meses.mes
    FROM {{ ref('estoque_prata') }} AS estoque
    INNER JOIN meses
        ON meses.mes = MAKE_DATE(estoque.ano_de_referencia, estoque.mes_de_referencia, 1)
)

SELECT
    atual.identificador_material,
    atual.identificador_almoxarifado,
    atual.mes AS presente_em
FROM presenca AS atual
WHERE NOT EXISTS (
        SELECT 1 FROM presenca AS seguinte
        WHERE seguinte.identificador_material = atual.identificador_material
          AND seguinte.identificador_almoxarifado = atual.identificador_almoxarifado
          AND seguinte.ordem = atual.ordem + 1
    )
  AND EXISTS (
        SELECT 1 FROM presenca AS depois
        WHERE depois.identificador_material = atual.identificador_material
          AND depois.identificador_almoxarifado = atual.identificador_almoxarifado
          AND depois.ordem = atual.ordem + 2
    )
