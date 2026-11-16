#!/usr/bin/env bash
# Demonstração do retry da orquestração: derruba o banco de propósito, dispara
# a recarga de um mês e só religa o banco depois que o Dagster registrar a
# primeira falha e agendar a nova tentativa.
#
# Pré-requisitos: `dagster dev` rodando (http://localhost:3000) com
# DAGSTER_HOME=orquestracao/instancia e o pipeline já carregado uma vez.
#
# Uso (na raiz do repositório):
#   SIGMA_PROJETO=sigma-unb bash orquestracao/demonstrar_retry.sh 2025-12-01
set -euo pipefail

PROJETO="${SIGMA_PROJETO:-sigma-unb}"
PARTICAO="${1:-2025-12-01}"
GRAPHQL="${DAGSTER_URL:-http://localhost:3000}/graphql"

consulta() { curl -s -H "Content-Type: application/json" -d "{\"query\":\"$1\"}" "$GRAPHQL"; }

echo "[$(date +%T)] derrubando o banco do projeto $PROJETO"
docker compose -p "$PROJETO" stop db

echo "[$(date +%T)] disparando recarga_mensal, partição $PARTICAO"
dagster job backfill -f orquestracao/definicoes.py -j recarga_mensal \
    --partitions "$PARTICAO" --noprompt | grep -E "Launched"

# espera o run aparecer
until RUN=$(consulta "{ runsOrError(limit: 1) { ... on Runs { results { runId status } } } }" \
        | python -c "import json,sys;r=json.load(sys.stdin)['data']['runsOrError']['results'];print(r[0]['runId'] if r and r[0]['status'] in ('STARTED','STARTING') else '')") \
      && [ -n "$RUN" ]; do sleep 2; done
echo "[$(date +%T)] run $RUN em execução"

# espera a primeira falha com nova tentativa agendada
until consulta "{ logsForRun(runId: \\\"$RUN\\\") { ... on EventConnection { events { __typename } } } }" \
        | grep -q ExecutionStepUpForRetryEvent; do sleep 2; done
echo "[$(date +%T)] etapa falhou e o Dagster agendou nova tentativa; religando o banco"
docker compose -p "$PROJETO" start db

# espera o fim do run
until STATUS=$(consulta "{ runOrError(runId: \\\"$RUN\\\") { ... on Run { status } } }" \
        | python -c "import json,sys;print(json.load(sys.stdin)['data']['runOrError']['status'])") \
      && [[ "$STATUS" =~ SUCCESS|FAILURE|CANCELED ]]; do sleep 5; done
echo "[$(date +%T)] run $RUN terminou: $STATUS"

consulta "{ logsForRun(runId: \\\"$RUN\\\") { ... on EventConnection { events { __typename ... on MessageEvent { timestamp message stepKey } } } } }" \
    | python -c "
import json, sys, datetime
for e in json.load(sys.stdin)['data']['logsForRun']['events']:
    if e['__typename'] in ('ExecutionStepStartEvent', 'ExecutionStepUpForRetryEvent',
                           'ExecutionStepRestartEvent', 'ExecutionStepSuccessEvent',
                           'ExecutionStepFailureEvent', 'RunSuccessEvent', 'RunFailureEvent'):
        hora = datetime.datetime.fromtimestamp(int(e.get('timestamp') or 0) / 1000).strftime('%H:%M:%S')
        print(hora, e['__typename'].replace('Event', ''), e.get('stepKey') or '', '|', (e.get('message') or '')[:110])
"
