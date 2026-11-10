# 0007 — Modelar a camada analítica como estrela, com grão mensal por material e almoxarifado, em dbt orquestrado pelo Dagster

- **Status:** proposto (falta a revisão da Squad)
- **Data:** 2026-11-10
- **Decisores:** [a definir pela Squad] — proposta preparada com assistente de IA (ver [Uso de IA](../gestao/ai-usage.md))

## Contexto

A E3 pede que a plataforma responda à pergunta da E1: para quais materiais do
estoque existe preço de compras públicas comparável e quais têm as maiores
diferenças, por almoxarifado e período.

Evidência acumulada até a E2 e nesta entrega:

| Item | Valor |
|---|---|
| Fontes integradas | 3: estoque da UnB (mensal), CATMAT (catálogo), compras públicas (por código CATMAT) |
| Mudança de esquema na origem | baixa: os arquivos do estoque têm os mesmos 5 campos em 39 meses; as APIs do Compras.gov.br não mudaram de formato no período |
| Volume | 39.183 linhas de estoque (39 meses, 2 almoxarifados, ~2.300 materiais); 41.514 compras; 346 mil itens CATMAT |
| O que muda com o tempo | a correspondência material × CATMAT (sugerida por agente, corrigida por pessoas) |
| Frequência | o portal publica o estoque uma vez por mês |
| Consumo | um painel e consultas SQL da Squad; não há consulta interativa de alto volume |

## Alternativas consideradas

### Forma do modelo

- **Estrela (escolhida):** um fato com o grão da pergunta e dimensões
  conformadas. Simples de consultar e de testar; o volume é pequeno.
- **Data Vault:** feito para muitas fontes e esquemas que mudam; aqui são três
  fontes estáveis. Hubs, links e satélites triplicariam os modelos sem ganho.
- **One big table:** uma tabela larga por material × mês × compra seria fácil
  para o painel, mas repete as medidas do estoque em cada compra (agregação
  dupla silenciosa) e não guarda o histórico da correspondência.

### Grão do fato (medido em 10/11/2026)

| Grão | Linhas | Responde à pergunta? |
|---|---|---|
| material × almoxarifado × mês × compra pública | 738.489 | sim, mas soma de saldo duplica por compra |
| **material × almoxarifado × mês (escolhido)** | **39.176** | **sim: por almoxarifado e período** |
| material × mês (sem almoxarifado) | 39.170 | não: perde o almoxarifado (6 materiais têm preço diferente entre almoxarifados no mesmo mês) |
| material × almoxarifado (sem mês) | 2.307 | não: perde o período e a série |

O grão escolhido é quase o da linha de estoque (39.183): o estoque já é uma
fotografia mensal. As 7 linhas a menos vêm do material que aparece com dois
preços no mesmo mês (descrições unidas pela normalização), agregados por média
ponderada, e da linha com preço zero, excluída.

### Ferramenta de transformação

- **dbt (escolhida):** já usado em bronze e prata; snapshots resolvem o SCD
  tipo 2; testes genéricos, singulares e `source freshness` no mesmo lugar.
- **SQLMesh:** planos e backfill por intervalo nativos, mas trocaria a
  ferramenta no meio do projeto sem problema concreto que o dbt não resolva.

### Orquestração

- **Opção nula: cron chamando `docker compose up`.** Agenda, mas não tem grafo
  além do `depends_on`, não refaz uma etapa que falhou (só a cadeia inteira),
  não tem backfill por mês nem histórico de execuções.
- **Airflow:** completo, mas pede banco próprio, scheduler, webserver e
  workers; pesado para um pipeline mensal de uma Squad.
- **Dagster (escolhida):** grafo de jobs em Python, `RetryPolicy` por etapa,
  partições mensais com backfill pela interface ou linha de comando, agenda e
  histórico, rodando num único processo (`dagster dev`). Ver
  [Orquestração](../dados-e-pipeline/orquestracao.md).

## Decisão

1. Camada ouro em estrela: `fato_comparacao_preco` com **grão de uma linha por
   material, por almoxarifado, por mês de referência publicado**, e as
   dimensões `dim_material`, `dim_almoxarifado`, `dim_tempo` e `dim_item_catmat`.
2. `dim_material` é **SCD tipo 2** sobre a correspondência com o CATMAT
   (dbt snapshot). O fato é incremental por mês e guarda a versão usada.
3. Transformações em dbt; testes de volume, distribuição e domínio em `tests/`,
   com exceções investigadas em `seeds/excecoes_qualidade.csv`.
4. SLA: estoque do mês M no fato até 45 dias após o fim de M, medido por
   `dbt source freshness` e por `ouro.monitor_atualizacao`.
5. Orquestração com Dagster: job mensal agendado, retry por etapa e backfill
   por partição mensal.

## Consequências

- O painel lê uma tabela só, com grão explícito; a soma de saldo entre meses
  continua proibida (é fotografia) e está documentada no modelo.
- O histórico da correspondência é preservado: uma comparação antiga continua
  explicável depois que uma pessoa corrigir a decisão do agente.
- Mais uma dependência (Dagster) fora dos containers do pipeline; o compose
  continua funcionando sozinho, sem agenda.
- O preço público é uma mediana da janela de compras sem conversão de unidade
  de fornecimento: diferenças grandes podem ser unidade diferente (ex.: galão
  × frasco), por isso a unidade predominante vai junto no fato.

## Gatilho de revisão

- Reavaliar Data Vault se entrarem mais duas fontes ou se o esquema do estoque
  mudar duas vezes em seis meses.
- Reavaliar o grão se a pergunta passar a exigir o preço de cada compra (ex.:
  dispersão por fornecedor).
- Reavaliar a orquestração se o pipeline passar a rodar mais de uma vez por dia.
