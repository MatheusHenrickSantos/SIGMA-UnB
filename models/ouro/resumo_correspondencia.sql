{{ config(materialized='table', schema='ouro', alias='resumo_correspondencia') }}

{#-
    Uma linha por material (versão vigente da dim_material): como ele foi
    ligado ao CATMAT, por quem, com que confiança, e o quanto vale conferir.
    Alimenta a aba de revisão do painel. prioridade_revisao ordena a fila:
    primeiro o que ainda não foi conferido por pessoa, de menor confiança e
    maior valor em estoque no último mês.
-#}

WITH ultimo_mes AS (
    SELECT MAX(mes_referencia) AS mes FROM {{ ref('fato_comparacao_preco') }}
),

valor AS (
    SELECT
        fato.identificador_material,
        SUM(fato.valor_estoque) AS valor_estoque,
        BOOL_OR(fato.tem_preco_publico) AS tem_preco_publico
    FROM {{ ref('fato_comparacao_preco') }} AS fato
    INNER JOIN ultimo_mes ON ultimo_mes.mes = fato.mes_referencia
    GROUP BY 1
),

execucao AS (
    SELECT MAX(id_execucao) AS id_execucao
    FROM {{ source('semantica', 'execucao_correspondencia') }}
    WHERE finalizada_em IS NOT NULL
),

melhor_candidato AS (
    SELECT
        material.chave_origem AS identificador_material,
        candidato.pontuacao,
        candidato.similaridade,
        candidato.situacao_especificacao
    FROM {{ source('semantica', 'candidato_catmat') }} AS candidato
    INNER JOIN execucao ON execucao.id_execucao = candidato.id_execucao
    INNER JOIN {{ source('semantica', 'descricao') }} AS material
        ON material.id_descricao = candidato.id_descricao_material
    WHERE candidato.posicao = 1
),

justificativa AS (
    SELECT
        hash_original_material,
        justificativa,
        revisor
    FROM {{ source('semantica', 'revisao_material') }}
)

SELECT
    dim.identificador_material,
    dim.descricao AS material,
    dim.tipo_revisor,
    dim.confianca,
    dim.sem_correspondente,
    dim.quantidade_itens_catmat,
    dim.codigos_equivalentes,
    justificativa.justificativa,
    justificativa.revisor,
    melhor_candidato.pontuacao AS pontuacao_melhor_candidato,
    melhor_candidato.similaridade AS similaridade_melhor_candidato,
    melhor_candidato.situacao_especificacao AS situacao_melhor_candidato,
    COALESCE(valor.valor_estoque, 0) AS valor_estoque,
    COALESCE(valor.tem_preco_publico, FALSE) AS tem_preco_publico,
    dim.tipo_revisor <> 'pessoa' AS pendente_conferencia,
    CASE WHEN dim.tipo_revisor = 'pessoa' THEN 0
         ELSE CASE COALESCE(dim.confianca, 'baixa') WHEN 'baixa' THEN 3 WHEN 'media' THEN 2 ELSE 1 END
              * COALESCE(valor.valor_estoque, 0)
    END AS prioridade_revisao
FROM {{ ref('dim_material') }} AS dim
LEFT JOIN {{ source('semantica', 'descricao') }} AS descricao
    ON descricao.origem = 'estoque' AND descricao.chave_origem = dim.identificador_material
LEFT JOIN justificativa ON justificativa.hash_original_material = descricao.hash_original
LEFT JOIN melhor_candidato ON melhor_candidato.identificador_material = dim.identificador_material
LEFT JOIN valor ON valor.identificador_material = dim.identificador_material
WHERE dim.atual
