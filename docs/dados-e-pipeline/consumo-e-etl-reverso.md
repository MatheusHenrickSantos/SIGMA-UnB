# Consumo duplo e ETL reverso

A plataforma é consumida de **duas formas** que leem as **mesmas definições**, e **devolve** um dado tratado a quem age.

```text
                          macros/metricas.sql  (definição única, versionada)
                                   │
                          ouro.metrica_mensal ── ouro.catalogo_metrica
                         ┌─────────┼───────────────────────────┐
                         ▼         ▼                           ▼
                  Painel (KPIs)   ouro.qualidade_dados   reverso.alerta_preco_compras ──▶ CSV em dados/saida
                  gestão          confiabilidade         compras e chefias de almoxarifado
```

## 1. Camada semântica de métricas

Cada métrica é definida **uma vez**, em [`macros/metricas.sql`](https://github.com/MatheusHenrickSantos/SIGMA-UnB/blob/main/macros/metricas.sql): nome, unidade, versão, descrição e fórmula SQL. O modelo `ouro.metrica_mensal` aplica as fórmulas e entrega o formato longo (métrica × mês × almoxarifado, com `TODOS` para o total). O painel, o registro de qualidade e o ETL reverso **leem** essa tabela ou usam as mesmas macros; nenhum reescreve a fórmula.

| Métrica | Tipo | Unidade | Definição |
|---|---|---|---|
| `valor_estoque` | base | R$ | Soma de saldo × preço no mês |
| `materiais_em_estoque` | base | materiais | Linhas do fato (material × almoxarifado) |
| `materiais_com_item_catmat` | base | materiais | Com ao menos um item CATMAT equivalente (versão vigente) |
| `materiais_com_preco_publico` | base | materiais | Com compra pública dos itens equivalentes na janela |
| `valor_com_preco_publico` | base | R$ | Valor do estoque dos materiais com preço público |
| `materiais_referencia_robusta` | base | materiais | Mediana pública de pelo menos `minimo_compras_referencia` (5) compras |
| `materiais_alertados` | base | materiais | Referência robusta + diferença ≥ `limiar_diferenca_pct` (30%) + correspondência utilizável |
| `economia_potencial` | base | R$ | Σ (preço − mediana) × saldo nos alertados |
| `diferenca_pct_mediana` | base | % | Mediana da diferença nos de referência robusta |
| `cobertura_item_catmat_pct` | derivada | % | com item CATMAT ÷ em estoque |
| `cobertura_preco_publico_pct` | derivada | % | com preço público ÷ com item CATMAT |
| `valor_comparavel_pct` | derivada | % | valor com preço público ÷ valor do estoque |
| `referencia_com_poucas_compras_pct` | derivada | % | (com preço − referência robusta) ÷ com preço |

Mudar uma definição: edite a macro, aumente `versao`, registre em `historico_metricas()` e rode o dbt; os três consumidores mudam juntos. O teste `tests/consistencia_metricas_e_alertas.sql` falha se o número de alertas ou a economia entregues a compras deixarem de bater com `materiais_alertados` e `economia_potencial`.

**Por que isso existe:** na revisão desta rodada, "cobertura de preço público" estava escrita de dois jeitos no próprio repositório (painel: ÷ materiais em estoque; registro de qualidade: ÷ materiais com item CATMAT). É o erro "dois números para a mesma métrica". Veja o [ADR 0010](adr/0010-camada-semantica-de-metricas-em-macros-dbt.md).

## 2. ETL reverso: alertas de preço para compras

| | |
|---|---|
| **Quem consome** | Setor de compras (todos os almoxarifados) e chefias de almoxarifado (só o seu) |
| **O que fazem com o dado** | Antes da próxima compra do material, conferem unidade e preço contra a mediana pública; se confirmado, renegociam ou revisam o fornecedor. É um sinal para investigar, não prova de sobrepreço |
| **O que é** | `reverso.alerta_preco_compras`: materiais do último mês com referência robusta, diferença ≥ 30% e correspondência utilizável (de pessoa, ou de agente com confiança alta ou média), ordenados por `economia_potencial` |
| **Caminho 1: arquivo** | Serviço `exportar` (e etapa `exportar_alertas` do Dagster) grava `dados/saida/alertas_preco_AAAA-MM.csv`, `alertas_preco_atual.csv` e um manifesto `.json` (linhas, sha256, `gerado_em`, versão das métricas). Escrita atômica |
| **Caminho 2: tabela** | Quem tem usuário do grupo `sigma_compras` ou `sigma_almoxarifado` lê a tabela direto, com recorte de coluna e de linha ([Controle de acesso](governanca/acesso.md)) |
| **Frequência** | Mensal, depois da carga do dia 20 ([orquestração](dados-e-pipeline/orquestracao.md)); o estoque só muda uma vez por mês |
| **Quem empurra** | **O destino puxa.** Nada é enviado para fora |
| **Destino fora do ar** | Nada se perde: a fonte da verdade é a tabela, o arquivo é regravado no mesmo nome na próxima execução e o consumidor vê no manifesto qual mês e quando foi gerado. Se o próprio `exportar` falhar, o Dagster refaz a etapa 3 vezes (30 s, 60 s, 120 s) e o arquivo anterior permanece intacto |

```bash
docker compose up --build            # termina em: transformar_ouro -> exportar
ls dados/saida                       # alertas_preco_AAAA-MM.csv, alertas_preco_atual.csv, .json
docker compose run --rm exportar     # só a exportação
```

### O que ainda é papel: o uso real

Um `SELECT` que grava numa tabela que ninguém lê não é ETL reverso. **Não há ainda evidência de que compras abra o arquivo.** O que existe: consumidor e ação definidos, formato escolhido (CSV com `;` e BOM, abre direto no Excel) e coluna `acao_sugerida`. Para fechar o ciclo falta registrar o retorno (alerta conferido, descartado por unidade diferente, ou renegociado); é o gatilho de revisão do [ADR 0011](adr/0011-etl-reverso-por-arquivo-e-tabela-com-destino-que-puxa.md).

## Medições {#medicoes}

Banco de teste local com o **estoque real** (39 arquivos, 39.182 linhas no fato) e **compras e correspondências sintéticas** para 680 materiais (a carga real do CATMAT e das compras não rodou nesta medição). Os números mostram custo e forma, **não** o resultado de gestão.

| Medida | Resultado |
|---|---|
| Construir `ouro.metrica_mensal` (1.521 linhas) | 2,7 s |
| Ler os KPIs de um mês: recalcular no fato × ler `metrica_mensal` | 2,7 ms × 0,085 ms |
| Série de todos os meses: recalcular no fato × ler `metrica_mensal` | 24,5 ms × 0,080 ms |
| Exportar 91 alertas para CSV | 0,14 s |
| Alertas × `materiais_alertados` × `economia_potencial` | 91 = 91; R$ 21.476 × R$ 21.475,51 (teste passa) |
