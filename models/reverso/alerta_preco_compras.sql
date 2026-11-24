{{ config(
    materialized='table',
    schema='reverso',
    alias='alerta_preco_compras',
    post_hook=[
        "ALTER TABLE {{ this }} ENABLE ROW LEVEL SECURITY",
        "DROP POLICY IF EXISTS compras_ve_tudo ON {{ this }}",
        "CREATE POLICY compras_ve_tudo ON {{ this }} FOR SELECT TO sigma_compras USING (true)",
        "DROP POLICY IF EXISTS almoxarifado_ve_o_seu ON {{ this }}",
        "CREATE POLICY almoxarifado_ve_o_seu ON {{ this }} FOR SELECT TO sigma_almoxarifado USING (almoxarifado IN (SELECT acesso.almoxarifado FROM {{ ref('acesso_almoxarifado') }} AS acesso WHERE acesso.usuario = current_user))",
        "GRANT SELECT ON {{ ref('acesso_almoxarifado') }} TO sigma_almoxarifado",
        "GRANT SELECT (mes_referencia, identificador_material, material, almoxarifado, quantidade, preco_estoque, preco_publico_mediano, diferenca_pct, diferenca_absoluta, economia_potencial, compras_publicas, unidade_fornecimento_predominante, codigos_equivalentes, tipo_revisor_correspondencia, confianca_correspondencia, acao_sugerida, versao_definicao_metricas, gerado_em) ON {{ this }} TO sigma_compras, sigma_almoxarifado"
    ]
) }}

{#-
    ETL REVERSO: lista de materiais cujo preço no estoque está acima da mediana
    das compras públicas, para quem decide a próxima compra agir.

    Consumidor: setor de compras (todos os almoxarifados) e chefias de
    almoxarifado (só o seu). Ação: conferir unidade e preço antes da próxima
    compra e, se confirmado, renegociar ou trocar de fornecedor. É um sinal
    para investigar, não prova de sobrepreço.

    Regras (as mesmas das métricas, via macros/metricas.sql):
      - último mês publicado do fato;
      - referência robusta (compras >= minimo_compras_referencia);
      - diferenca_pct >= limiar_diferenca_pct;
      - fora os materiais cuja correspondência CATMAT o agente marcou com
        confiança baixa (palpite): só entra correspondência alta, média ou de pessoa.

    Recortes de acesso (migração V11):
      - coluna: justificativa_agente (texto livre do agente) NÃO é concedida
        aos consumidores; só o dono (dbt) lê;
      - linha: sigma_almoxarifado só vê os almoxarifados de
        reverso.acesso_almoxarifado (RLS); sigma_compras vê tudo.
-#}

WITH ultimo AS (
    SELECT MAX(mes_referencia) AS mes FROM {{ ref('fato_comparacao_preco') }}
),

versao AS (
    SELECT MAX(versao_definicao) AS versao FROM {{ ref('metrica_mensal') }}
)

SELECT
    f.mes_referencia,
    f.identificador_material,
    r.material,
    TRIM(a.nome) AS almoxarifado,
    f.quantidade,
    f.preco_estoque,
    f.preco_publico_mediano,
    f.diferenca_pct,
    f.diferenca_absoluta,
    ROUND(GREATEST(f.preco_estoque - f.preco_publico_mediano, 0) * f.quantidade, 2) AS economia_potencial,
    f.compras_publicas,
    f.unidade_fornecimento_predominante,
    r.codigos_equivalentes,
    f.tipo_revisor_correspondencia,
    r.confianca AS confianca_correspondencia,
    r.justificativa AS justificativa_agente,
    'Conferir unidade e preço antes da próxima compra; se confirmado, renegociar ou rever o fornecedor.'
        AS acao_sugerida,
    versao.versao AS versao_definicao_metricas,
    CURRENT_TIMESTAMP AS gerado_em
FROM {{ ref('fato_comparacao_preco') }} AS f
INNER JOIN ultimo ON ultimo.mes = f.mes_referencia
INNER JOIN {{ ref('dim_almoxarifado') }} AS a USING (identificador_almoxarifado)
INNER JOIN {{ ref('resumo_correspondencia') }} AS r USING (identificador_material)
CROSS JOIN versao
WHERE {{ referencia_robusta('f.compras_publicas', 'f.tem_preco_publico') }}
  AND f.diferenca_pct >= {{ limiar_diferenca() }}
  AND (r.tipo_revisor = 'pessoa' OR COALESCE(r.confianca, 'baixa') <> 'baixa')
ORDER BY economia_potencial DESC
