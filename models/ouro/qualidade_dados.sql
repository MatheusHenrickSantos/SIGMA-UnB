{{ config(materialized='table', schema='ouro', alias='qualidade_dados') }}

{#-
    Registro de confiabilidade dos dados: uma linha por verificação, com o
    valor medido, os limites e a situação (ok, atencao, critico, sem_dado).
    É o que o painel mostra na aba de qualidade; os testes do dbt (tests/ e
    os *.yml) continuam sendo o que derruba o build, e este modelo mede o que
    não derruba mas muda o quanto se pode confiar na comparação de preços.

    sentido = 'max': quanto MENOR, melhor.
        ok se valor <= limite_atencao; atencao se <= limite_critico; senão critico.
    sentido = 'min': quanto MAIOR, melhor.
        ok se valor >= limite_atencao; atencao se >= limite_critico; senão critico.

    Os limites são de projeto, não da fonte: calibrados com os dados de
    06/2021 a 12/2025 e revisáveis pela Squad (docs/dados-e-pipeline/confiabilidade.md).
-#}

WITH ultimo_mes AS (
    SELECT MAX(mes_referencia) AS mes FROM {{ ref('fato_comparacao_preco') }}
),

fato AS (
    SELECT fato.*
    FROM {{ ref('fato_comparacao_preco') }} AS fato
    INNER JOIN ultimo_mes ON ultimo_mes.mes = fato.mes_referencia
),

-- ---------------------------------------------------------------- estoque
estoque_bronze AS (
    SELECT
        COUNT(*) AS linhas,
        COUNT(*) FILTER (WHERE preco IS NULL OR preco <= 0) AS preco_nao_positivo,
        SUM(ABS(saldo * preco - valor_total)) AS divergencia,
        SUM(valor_total) AS valor
    FROM {{ ref('estoque_bronze') }}
),

estoque_prata AS (
    SELECT COUNT(*) AS linhas FROM {{ ref('estoque_prata') }}
),

meses AS (
    SELECT
        COUNT(*) AS total,
        COUNT(*) FILTER (WHERE NOT publicado) AS sem_publicacao
    FROM {{ ref('dim_tempo') }}
),

-- ---------------------------------------------------------------- compras
mediana_por_item AS (
    SELECT
        codigo_item,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY preco_unitario) AS mediana,
        MODE() WITHIN GROUP (ORDER BY unidade_fornecimento) AS unidade_predominante,
        COUNT(*) AS compras
    FROM {{ ref('compra_publica_prata') }}
    GROUP BY 1
),

compras_avaliadas AS (
    SELECT
        COUNT(*) AS registros,
        COUNT(*) FILTER (
            WHERE compra.preco_unitario > 10 * item.mediana
               OR compra.preco_unitario < item.mediana / 10
        ) AS fora_da_faixa,
        COUNT(*) FILTER (
            WHERE compra.unidade_fornecimento IS DISTINCT FROM item.unidade_predominante
        ) AS unidade_divergente
    FROM {{ ref('compra_publica_prata') }} AS compra
    INNER JOIN mediana_por_item AS item USING (codigo_item)
    WHERE item.compras >= 5
),

-- ---------------------------------------------------------------- correspondência
materiais_atuais AS (
    SELECT
        COUNT(*) AS total,
        COUNT(*) FILTER (WHERE tipo_revisor = 'pessoa') AS por_pessoa,
        COUNT(*) FILTER (WHERE tipo_revisor = 'sem_decisao') AS sem_decisao,
        COUNT(*) FILTER (WHERE confianca = 'baixa') AS confianca_baixa,
        COUNT(*) FILTER (WHERE tipo_revisor <> 'sem_decisao') AS decididos
    FROM {{ ref('dim_material') }}
    WHERE atual
),

execucao AS (
    SELECT MAX(id_execucao) AS id_execucao
    FROM {{ source('semantica', 'execucao_correspondencia') }}
    WHERE finalizada_em IS NOT NULL
),

aprovados AS (
    SELECT
        COUNT(*) AS pares,
        COUNT(*) FILTER (WHERE candidato.situacao_especificacao = 'conflito_tecnico') AS com_conflito
    FROM {{ source('semantica', 'revisao_correspondencia') }} AS revisao
    INNER JOIN {{ source('semantica', 'descricao') }} AS material
        ON material.origem = 'estoque' AND material.ativa
       AND material.hash_original = revisao.hash_original_material
    LEFT JOIN {{ source('semantica', 'descricao') }} AS item
        ON item.origem = 'catmat' AND item.chave_origem = revisao.codigo_item
    LEFT JOIN execucao ON TRUE
    LEFT JOIN {{ source('semantica', 'candidato_catmat') }} AS candidato
        ON candidato.id_execucao = execucao.id_execucao
       AND candidato.id_descricao_material = material.id_descricao
       AND candidato.id_descricao_catmat = item.id_descricao
    WHERE revisao.decisao = 'equivalente'
),

-- ---------------------------------------------------------------- fato (último mês)
comparaveis AS (
    SELECT
        COUNT(*) AS materiais,
        COUNT(*) FILTER (WHERE EXISTS (
            SELECT 1 FROM {{ ref('dim_material') }} AS dim
            WHERE dim.sk_material = fato.sk_material AND dim.codigos_equivalentes <> ''
        )) AS com_item,
        COUNT(*) FILTER (WHERE tem_preco_publico) AS com_preco,
        COUNT(*) FILTER (WHERE tem_preco_publico AND compras_publicas < 5) AS com_poucas_compras,
        COUNT(*) FILTER (WHERE tem_preco_publico AND (diferenca_pct > 900 OR diferenca_pct < -90))
            AS diferenca_extrema,
        COALESCE(SUM(valor_estoque), 0) AS valor,
        COALESCE(SUM(valor_estoque) FILTER (WHERE tem_preco_publico), 0) AS valor_comparavel,
        COALESCE(SUM(valor_estoque) FILTER (
            WHERE tem_preco_publico AND tipo_revisor_correspondencia <> 'pessoa'
        ), 0) AS valor_nao_conferido
    FROM fato
),

atraso AS (
    SELECT atraso_dias, sla_dias
    FROM {{ ref('monitor_atualizacao') }}
    WHERE tabela = 'ouro.fato_comparacao_preco'
),

medidas AS (
    SELECT 'frescor_estoque_atraso_dias' AS verificacao, 'Estoque' AS categoria,
        'Dias entre o fim do mês do estoque mais recente e hoje; o SLA é de 45 dias.' AS descricao,
        atraso.atraso_dias::NUMERIC AS valor, atraso.sla_dias::NUMERIC AS limite_atencao,
        (atraso.sla_dias + 30)::NUMERIC AS limite_critico, 'max' AS sentido, 'dias' AS unidade
    FROM atraso

    UNION ALL
    SELECT 'estoque_meses_sem_publicacao_pct', 'Estoque',
        'Meses entre o primeiro e o último estoque que o portal não publicou: a série tem buracos.',
        100.0 * sem_publicacao / NULLIF(total, 0), 25, 50, 'max', '%'
    FROM meses

    UNION ALL
    SELECT 'estoque_linhas_descartadas_pct', 'Estoque',
        'Linhas do estoque (bronze) que não chegaram à prata por material ou almoxarifado sem cadastro.',
        100.0 * GREATEST(bronze.linhas - prata.linhas, 0) / NULLIF(bronze.linhas, 0), 0.5, 2, 'max', '%'
    FROM estoque_bronze AS bronze CROSS JOIN estoque_prata AS prata

    UNION ALL
    SELECT 'estoque_valor_total_divergente_pct', 'Estoque',
        'Soma de |saldo × preço − valor_total| sobre o valor total do portal: o fato recalcula o valor, '
        'então divergência alta indica saldo ou preço errado na origem.',
        100.0 * divergencia / NULLIF(valor, 0), 0.5, 2, 'max', '%'
    FROM estoque_bronze

    UNION ALL
    SELECT 'estoque_preco_nao_positivo_pct', 'Estoque',
        'Linhas com preço nulo, zero ou negativo (ficam fora do fato).',
        100.0 * preco_nao_positivo / NULLIF(linhas, 0), 0.1, 1, 'max', '%'
    FROM estoque_bronze

    UNION ALL
    SELECT 'compras_fora_da_faixa_pct', 'Compras públicas',
        'Compras com preço a mais de 10× (ou menos de 1/10) da mediana do próprio item CATMAT '
        '(itens com 5+ compras): mudança de escala ou registro de outro item.',
        100.0 * fora_da_faixa / NULLIF(registros, 0), 8, 15, 'max', '%'
    FROM compras_avaliadas

    UNION ALL
    SELECT 'compras_unidade_divergente_pct', 'Compras públicas',
        'Compras cuja unidade de fornecimento difere da predominante do item (galão × frasco, '
        'caixa × unidade): o preço não é comparável sem converter.',
        100.0 * unidade_divergente / NULLIF(registros, 0), 20, 40, 'max', '%'
    FROM compras_avaliadas

    UNION ALL
    SELECT 'comparacao_cobertura_preco_publico_pct', 'Comparação',
        'Materiais com item CATMAT equivalente que têm preço público na janela (último mês).',
        100.0 * com_preco / NULLIF(com_item, 0), 70, 40, 'min', '%'
    FROM comparaveis

    UNION ALL
    SELECT 'comparacao_valor_comparavel_pct', 'Comparação',
        'Parte do valor do estoque (último mês) que tem preço público para comparar.',
        100.0 * valor_comparavel / NULLIF(valor, 0), 60, 30, 'min', '%'
    FROM comparaveis

    UNION ALL
    SELECT 'comparacao_referencia_com_poucas_compras_pct', 'Comparação',
        'Comparações cuja mediana pública vem de menos de 5 compras.',
        100.0 * com_poucas_compras / NULLIF(com_preco, 0), 25, 50, 'max', '%'
    FROM comparaveis

    UNION ALL
    SELECT 'comparacao_diferenca_extrema_pct', 'Comparação',
        'Comparações em que o estoque custa mais de 10× ou menos de 1/10 da mediana pública: '
        'quase sempre unidade diferente, não sobrepreço.',
        100.0 * diferenca_extrema / NULLIF(com_preco, 0), 10, 25, 'max', '%'
    FROM comparaveis

    UNION ALL
    SELECT 'correspondencia_conferida_por_pessoa_pct', 'Correspondência CATMAT',
        'Materiais cuja correspondência com o CATMAT foi conferida por uma pessoa (o resto é sugestão de agente de IA).',
        100.0 * por_pessoa / NULLIF(total, 0), 50, 10, 'min', '%'
    FROM materiais_atuais

    UNION ALL
    SELECT 'correspondencia_valor_nao_conferido_pct', 'Correspondência CATMAT',
        'Parte do valor comparável do estoque (último mês) cuja correspondência ainda não foi conferida por pessoa.',
        100.0 * valor_nao_conferido / NULLIF(valor_comparavel, 0), 50, 80, 'max', '%'
    FROM comparaveis

    UNION ALL
    SELECT 'correspondencia_confianca_baixa_pct', 'Correspondência CATMAT',
        'Materiais decididos pelo agente com confiança baixa (palpite): prioridade de revisão.',
        100.0 * confianca_baixa / NULLIF(decididos, 0), 15, 35, 'max', '%'
    FROM materiais_atuais

    UNION ALL
    SELECT 'correspondencia_materiais_sem_decisao_pct', 'Correspondência CATMAT',
        'Materiais sem nenhuma decisão (nem item equivalente, nem "sem correspondente").',
        100.0 * sem_decisao / NULLIF(total, 0), 0, 5, 'max', '%'
    FROM materiais_atuais

    UNION ALL
    SELECT 'correspondencia_aprovados_com_conflito_tecnico', 'Correspondência CATMAT',
        'Pares aprovados como equivalentes cuja checagem de especificações apontou conflito (ex.: AA × AAA).',
        com_conflito::NUMERIC, 0, 10, 'max', 'pares'
    FROM aprovados
)

SELECT
    verificacao,
    categoria,
    descricao,
    ROUND(valor, 2) AS valor,
    limite_atencao,
    limite_critico,
    sentido,
    unidade,
    CASE
        WHEN valor IS NULL THEN 'sem_dado'
        WHEN sentido = 'max' AND valor <= limite_atencao THEN 'ok'
        WHEN sentido = 'max' AND valor <= limite_critico THEN 'atencao'
        WHEN sentido = 'max' THEN 'critico'
        WHEN valor >= limite_atencao THEN 'ok'
        WHEN valor >= limite_critico THEN 'atencao'
        ELSE 'critico'
    END AS situacao,
    CURRENT_TIMESTAMP AS medido_em
FROM medidas
