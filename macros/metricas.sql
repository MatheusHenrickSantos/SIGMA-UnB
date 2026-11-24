{#-
    CAMADA SEMÂNTICA DE MÉTRICAS — o único lugar onde uma métrica é definida.

    Quem consome (painel, qualidade_dados, ETL reverso) lê ouro.metrica_mensal
    ou usa as macros abaixo; nenhum consumidor reescreve a fórmula. Mudou uma
    definição? Altere aqui, aumente `versao`, registre a mudança em
    `historico_metricas()` e rode o dbt: todos os consumidores mudam juntos.

    Parâmetros de negócio (dbt_project.yml, vars):
      minimo_compras_referencia  compras públicas mínimas para a mediana valer como referência
      limiar_diferenca_pct       diferença (%) a partir da qual o material vira alerta

    As expressões rodam sobre o grão do fato (material x almoxarifado x mês)
    juntado a dim_material (alias `d`) e agregam por mês e almoxarifado.
-#}

{% macro minimo_compras() %}{{ var('minimo_compras_referencia', 5) }}{% endmacro %}
{% macro limiar_diferenca() %}{{ var('limiar_diferenca_pct', 30) }}{% endmacro %}

{# Condição única de "referência pública confiável" (usada por métricas e alertas). #}
{% macro referencia_robusta(compras='compras_publicas', tem_preco='tem_preco_publico') -%}
({{ tem_preco }} AND {{ compras }} >= {{ minimo_compras() }})
{%- endmacro %}

{% macro metricas_base() %}
  {% set lista = [
    {'nome': 'valor_estoque', 'unidade': 'R$', 'versao': 1,
     'descricao': 'Valor do estoque: soma de saldo x preço unitário no mês.',
     'expressao': 'SUM(f.valor_estoque)'},
    {'nome': 'materiais_em_estoque', 'unidade': 'materiais', 'versao': 1,
     'descricao': 'Materiais com saldo e preço positivos no mês (uma linha do fato por material e almoxarifado).',
     'expressao': 'COUNT(*)'},
    {'nome': 'materiais_com_item_catmat', 'unidade': 'materiais', 'versao': 1,
     'descricao': 'Materiais com ao menos um item CATMAT equivalente na versão vigente da correspondência.',
     'expressao': "COUNT(*) FILTER (WHERE d.codigos_equivalentes <> '')"},
    {'nome': 'materiais_com_preco_publico', 'unidade': 'materiais', 'versao': 1,
     'descricao': 'Materiais com ao menos uma compra pública dos itens equivalentes na janela.',
     'expressao': 'COUNT(*) FILTER (WHERE f.tem_preco_publico)'},
    {'nome': 'valor_com_preco_publico', 'unidade': 'R$', 'versao': 1,
     'descricao': 'Valor do estoque dos materiais que têm preço público para comparar.',
     'expressao': 'COALESCE(SUM(f.valor_estoque) FILTER (WHERE f.tem_preco_publico), 0)'},
    {'nome': 'materiais_referencia_robusta', 'unidade': 'materiais', 'versao': 1,
     'descricao': 'Materiais cuja mediana pública vem de pelo menos o mínimo de compras (minimo_compras_referencia).',
     'expressao': 'COUNT(*) FILTER (WHERE ' ~ referencia_robusta('f.compras_publicas', 'f.tem_preco_publico') ~ ')'},
    {'nome': 'materiais_acima_do_limiar', 'unidade': 'materiais', 'versao': 1,
     'descricao': 'Materiais de referência robusta com preço do estoque acima da mediana pública em pelo menos limiar_diferenca_pct.',
     'expressao': 'COUNT(*) FILTER (WHERE ' ~ referencia_robusta('f.compras_publicas', 'f.tem_preco_publico') ~ ' AND f.diferenca_pct >= ' ~ limiar_diferenca() ~ ')'},
    {'nome': 'economia_potencial', 'unidade': 'R$', 'versao': 1,
     'descricao': 'Quanto o estoque custaria a menos se cada material de referência robusta fosse avaliado pela mediana pública: soma de max(preço - mediana, 0) x saldo. Sinal para investigar, não sobrepreço comprovado (a unidade de fornecimento pode diferir).',
     'expressao': 'COALESCE(SUM(GREATEST(f.preco_estoque - f.preco_publico_mediano, 0) * f.quantidade) FILTER (WHERE ' ~ referencia_robusta('f.compras_publicas', 'f.tem_preco_publico') ~ '), 0)'},
    {'nome': 'diferenca_pct_mediana', 'unidade': '%', 'versao': 1,
     'descricao': 'Mediana da diferença percentual entre o preço do estoque e a mediana pública, nos materiais de referência robusta.',
     'expressao': 'PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY f.diferenca_pct) FILTER (WHERE ' ~ referencia_robusta('f.compras_publicas', 'f.tem_preco_publico') ~ ')'},
  ] %}
  {{ return(lista) }}
{% endmacro %}

{# Derivadas: razões entre métricas base, calculadas sobre as colunas já agregadas. #}
{% macro metricas_derivadas() %}
  {% set lista = [
    {'nome': 'cobertura_item_catmat_pct', 'unidade': '%', 'versao': 1,
     'descricao': 'Parte dos materiais em estoque que tem item CATMAT equivalente.',
     'expressao': '100.0 * materiais_com_item_catmat / NULLIF(materiais_em_estoque, 0)'},
    {'nome': 'cobertura_preco_publico_pct', 'unidade': '%', 'versao': 1,
     'descricao': 'Parte dos materiais com item CATMAT que tem preço público na janela.',
     'expressao': '100.0 * materiais_com_preco_publico / NULLIF(materiais_com_item_catmat, 0)'},
    {'nome': 'valor_comparavel_pct', 'unidade': '%', 'versao': 1,
     'descricao': 'Parte do valor do estoque que tem preço público para comparar.',
     'expressao': '100.0 * valor_com_preco_publico / NULLIF(valor_estoque, 0)'},
    {'nome': 'referencia_com_poucas_compras_pct', 'unidade': '%', 'versao': 1,
     'descricao': 'Parte das comparações cuja mediana pública vem de menos compras que o mínimo exigido.',
     'expressao': '100.0 * (materiais_com_preco_publico - materiais_referencia_robusta) / NULLIF(materiais_com_preco_publico, 0)'},
  ] %}
  {{ return(lista) }}
{% endmacro %}

{# Histórico de versões das definições: quando e por que cada métrica mudou. #}
{% macro historico_metricas() %}
  {{ return([
    {'metrica': '*', 'versao': 1, 'data': '2026-11-24', 'mudanca': 'Primeira definição centralizada; cobertura_preco_publico_pct = com preço ÷ com item CATMAT (antes o painel usava ÷ materiais em estoque).'},
  ]) }}
{% endmacro %}
