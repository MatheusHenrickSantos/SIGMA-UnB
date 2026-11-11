# Orquestração

O `docker compose up` sobe a cadeia inteira uma vez, na ordem dos
`depends_on`, mas não agenda, não refaz uma etapa que falhou e não recarrega
um mês específico. Para isso o projeto usa o **Dagster**
(`orquestracao/definicoes.py`). A escolha e a opção nula (cron) estão no
[ADR 0007](adr/0007-modelo-estrela-para-comparacao-de-precos.md).

Cada etapa do Dagster roda um serviço do compose
(`docker compose run --rm --no-deps <serviço>`): o compose continua sendo a
forma de rodar cada etapa, e o Dagster cuida de ordem, agenda, novas
tentativas, backfill e histórico.

## Grafo e agenda

```text
pipeline_mensal (agenda: dia 20 de cada mês, 06:00, America/Sao_Paulo)

subir_banco → migrar → ingerir → transformar → buscar_correspondencias → baixar_compras → transformar_ouro
  (db)       (migrate) (ingest)  (transformar)      (semantica)            (compras)     (transformar_ouro)
```

- **Agenda:** `0 6 20 * *`. O portal publica o estoque do mês M no mês
  seguinte; rodando no dia 20, o mês M entra no fato antes de vencer o SLA de
  45 dias ([Camada ouro](dados-e-pipeline/camada-ouro.md#freshness-e-sla)).
- **Retry:** toda etapa tem `RetryPolicy(max_retries=3, delay=30, backoff=EXPONENTIAL)`,
  ou seja, 3 novas tentativas, a primeira 30 s depois. Cobre banco reiniciando
  e a API do Compras.gov.br, que devolve 400 de forma intermitente.
- **Concorrência:** os jobs que rodam o dbt compartilham a pasta do projeto
  (`dbt_packages/`, `target/`) e só rodam um por vez (tag `sigma/projeto-dbt`,
  limite em `orquestracao/instancia/dagster.yaml`). O limite surgiu de uma
  falha real na primeira demonstração de backfill (abaixo).

## Backfill por mês

`recarga_mensal` é particionado por mês de referência do estoque (06/2021 a
12/2025). Para a partição M:

1. `carregar_estoque_do_mes`: grava em `raw.estoque` o arquivo do mês M
   (`inserir_dados_na_camada_raw estoque --mes MM-AAAA`; idempotente pelo hash);
2. `refazer_bronze_prata`: `dbt build --select estoque_bronze+` (sem ouro);
3. `recalcular_fato_do_mes`: `dbt build --select fato_comparacao_preco monitor_atualizacao --vars '{mes_referencia: "AAAA-MM-01"}'`,
   que apaga e recalcula só o mês M do fato (incremental delete+insert).

## Como rodar

```bash
python -m venv .venv-orquestracao && . .venv-orquestracao/bin/activate   # Windows: .venv-orquestracao\Scripts\activate
pip install -r orquestracao/requirements.txt
export DAGSTER_HOME=$PWD/orquestracao/instancia     # histórico fica aqui, fora do git
export SIGMA_PROJETO=sigma-unb                      # nome do projeto do compose
dagster dev -f orquestracao/definicoes.py           # interface em http://localhost:3000

# backfill de três meses pela linha de comando (ou pela interface: Jobs > recarga_mensal > Backfill)
dagster job backfill -f orquestracao/definicoes.py -j recarga_mensal \
    --partitions 2025-10-01,2025-11-01,2025-12-01 --noprompt

# demonstração do retry (derruba o banco e religa após a primeira falha)
bash orquestracao/demonstrar_retry.sh 2025-12-01
```

O Dagster roda no host e chama o Docker; use uma venv só para ele (as
dependências dele conflitam com as do dbt local, que não é necessário porque o
dbt roda no container).

## Demonstrações (10/11/2026, banco do compose com os dados reais)

### 1. Backfill executado de verdade

Apagamos de propósito os meses 10, 11 e 12/2025 de `raw.estoque` e do fato
(2.060 linhas) e disparamos o backfill das três partições.

```text
## Depois de apagar 10, 11 e 12/2025 (raw e fato)
 (nenhuma linha)

$ dagster job backfill -j recarga_mensal --partitions 2025-10-01,2025-11-01,2025-12-01
Launched backfill job `gqdvowzo`

run       partição    backfill  status   início    fim       tentativas por etapa
5007e434  2025-10-01  gqdvowzo  SUCCESS  14:45:27  14:46:14  carregar 1, bronze/prata 1, fato 1
569f705a  2025-11-01  gqdvowzo  SUCCESS  14:46:18  14:47:03  carregar 1, bronze/prata 1, fato 1
d6acd85d  2025-12-01  gqdvowzo  SUCCESS  14:47:09  14:47:53  carregar 1, bronze/prata 1, fato 1

## Depois do backfill gqdvowzo
   tabela    |   mes   | count
-------------+---------+-------
 ouro.fato   | 2025-10 |   695
 ouro.fato   | 2025-11 |   685
 ouro.fato   | 2025-12 |   680
 raw.estoque | 2025-10 |     1
 raw.estoque | 2025-11 |     1
 raw.estoque | 2025-12 |     1
```

**O que a primeira tentativa revelou.** No primeiro backfill (`vrqfepmf`), as
três partições rodaram em paralelo e os três `dbt deps` disputaram a mesma
pasta `dbt_packages/` (`OSError: Directory not empty`, `No such file or
directory: dbt_packages/dbt_utils/dbt_project.yml`). O retry salvou as três
execuções (a etapa `refazer_bronze_prata` precisou de 2, 3 e 4 tentativas),
mas a causa era de projeto. A correção foi o limite de um run por vez entre os
jobs do dbt; no segundo backfill (acima) cada etapa passou na primeira tentativa.

### 2. Retry com uma dependência derrubada

`orquestracao/demonstrar_retry.sh` para o banco, dispara a recarga de 12/2025
e só religa o banco depois que o Dagster registra a falha:

```text
[14:48:39] derrubando o banco do projeto sigma-main
[14:48:40] disparando recarga_mensal, partição 2025-12-01
Launched backfill job `vfcnhmpm`
[14:49:00] etapa falhou e o Dagster agendou nova tentativa; religando o banco
14:48:53 ExecutionStepStart       carregar_estoque_do_mes | Started execution of step "carregar_estoque_do_mes".
14:48:58 ExecutionStepUpForRetry  carregar_estoque_do_mes | ... failed and has requested a retry in 30 seconds.
14:49:30 ExecutionStepRestart     carregar_estoque_do_mes | Started re-execution (attempt # 2) ...
14:49:31 ExecutionStepSuccess     carregar_estoque_do_mes | Finished execution ... in 1.11s.
14:49:33 ExecutionStepStart       refazer_bronze_prata
14:49:53 ExecutionStepSuccess     refazer_bronze_prata    | ... in 19.42s.
14:49:55 ExecutionStepStart       recalcular_fato_do_mes
14:50:14 ExecutionStepSuccess     recalcular_fato_do_mes  | ... in 18.76s.
14:50:14 RunSuccess
```

Para essa falha aparecer, a carga raw passou a sair com código 1 quando algum
arquivo falha (antes contava a falha e terminava com 0, e o pipeline seguia
como se a carga tivesse dado certo).

### 3. Execução completa agendável

`dagster job launch -j pipeline_mensal` sobre o banco já carregado (as etapas
são incrementais: o CATMAT e as compras vêm do cache, só a busca híbrida é
refeita por inteiro):

```text
run 7f691abf  pipeline_mensal  SUCCESS  14:50:53 -> 15:07:21
  subir_banco              SUCCESS  14:50:55 -> 14:50:56  tentativas 1
  migrar                   SUCCESS  14:50:58 -> 14:51:00  tentativas 1
  ingerir                  SUCCESS  14:51:02 -> 14:51:53  tentativas 1
  transformar              SUCCESS  14:51:55 -> 14:52:18  tentativas 1
  buscar_correspondencias  SUCCESS  14:52:20 -> 15:05:52  tentativas 1
  baixar_compras           SUCCESS  15:05:54 -> 15:06:56  tentativas 1
  transformar_ouro         SUCCESS  15:06:58 -> 15:07:21  tentativas 1
```

### Agenda

```text
pipeline_mensal_schedule  cron 0 6 20 * *  America/Sao_Paulo  RUNNING
próximas execuções: 2026-11-20 06:00, 2026-12-20 06:00
```
