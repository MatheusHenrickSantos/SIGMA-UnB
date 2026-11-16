{% snapshot snap_correspondencia_material %}

{{ config(
    schema='ouro',
    unique_key='identificador_material',
    strategy='check',
    check_cols=['codigos_equivalentes', 'sem_correspondente', 'tipo_revisor'],
    hard_deletes='invalidate'
) }}

{#-
    Dimensão de variação lenta (SCD tipo 2) da correspondência material x CATMAT.

    A correspondência muda com o tempo: um agente de IA sugere os itens
    equivalentes e, depois, uma pessoa confirma, troca os itens ou marca
    "sem correspondente". Sobrescrever perderia a informação de qual item
    sustentava uma comparação de preço já publicada. O snapshot guarda uma
    versão nova sempre que muda o conjunto de itens equivalentes, a decisão
    "sem correspondente" ou quem decidiu (agente -> pessoa), com
    dbt_valid_from / dbt_valid_to.
-#}

SELECT
    descricao.chave_origem AS identificador_material,
    descricao.texto_original AS material,
    COALESCE(
        STRING_AGG(revisao.codigo_item, '|' ORDER BY revisao.codigo_item::BIGINT)
            FILTER (WHERE revisao.decisao = 'equivalente'),
        ''
    ) AS codigos_equivalentes,
    COALESCE(material_decidido.sem_correspondente, FALSE) AS sem_correspondente,
    COALESCE(
        material_decidido.tipo_revisor,
        MAX(revisao.tipo_revisor) FILTER (WHERE revisao.decisao = 'equivalente'),
        'sem_decisao'
    ) AS tipo_revisor,
    material_decidido.confianca
FROM {{ source('semantica', 'descricao') }} AS descricao
LEFT JOIN {{ source('semantica', 'revisao_correspondencia') }} AS revisao
    ON revisao.hash_original_material = descricao.hash_original
LEFT JOIN {{ source('semantica', 'revisao_material') }} AS material_decidido
    ON material_decidido.hash_original_material = descricao.hash_original
WHERE descricao.origem = 'estoque'
  AND descricao.ativa
GROUP BY
    descricao.chave_origem,
    descricao.texto_original,
    material_decidido.sem_correspondente,
    material_decidido.tipo_revisor,
    material_decidido.confianca

{% endsnapshot %}
