"""Orquestração do SIGMA-UnB com Dagster.

Cada etapa é um serviço do docker-compose.yml, executado com
`docker compose run --rm --no-deps <serviço>`: o Dagster decide a ordem, refaz
a etapa que falhou (RetryPolicy) e guarda o histórico; o compose continua
sendo a forma de rodar cada etapa e de subir tudo sem agenda.

Jobs:

- pipeline_mensal: db -> migrate -> ingest -> transformar -> semantica ->
  compras -> transformar_ouro. Agendado todo dia 20, 06:00 (America/Sao_Paulo):
  o portal publica o estoque do mês no mês seguinte e o SLA é de 45 dias.
- recarga_mensal: particionado por mês de referência do estoque (06/2021 a
  12/2025). Para a partição M: grava em raw.estoque o arquivo do mês M (se
  faltar), refaz bronze/prata e recalcula SÓ o mês M do fato
  (`dbt build --vars mes_referencia`). É o job do backfill.

Variáveis: SIGMA_PROJETO (nome do projeto compose, padrão sigma-unb) e as
mesmas do .env (PORTA_DO_BANCO etc.), repassadas ao docker compose.

Rodar (na raiz do repositório):
    pip install -r orquestracao/requirements.txt       # de preferência numa venv só para isso
    DAGSTER_HOME=$PWD/orquestracao/instancia dagster dev -f orquestracao/definicoes.py
    # interface em http://localhost:3000
"""


import os
import subprocess
from pathlib import Path

from dagster import (
    Backoff,
    DefaultScheduleStatus,
    Definitions,
    Failure,
    In,
    MonthlyPartitionsDefinition,
    Nothing,
    OpExecutionContext,
    RetryPolicy,
    ScheduleDefinition,
    job,
    op,
)

RAIZ = Path(__file__).resolve().parents[1]

# 3 novas tentativas: 30 s, 60 s, 120 s. Cobre o banco reiniciando e a
# instabilidade das APIs (Compras.gov.br devolve 400 de forma intermitente).
RETRY = RetryPolicy(max_retries=3, delay=30, backoff=Backoff.EXPONENTIAL)

# Um run por vez entre os jobs que usam o projeto dbt (limite em
# orquestracao/instancia/dagster.yaml): eles compartilham dbt_packages/ e target/.
TAG_DBT = {"sigma/projeto-dbt": "1"}

PARTICOES = MonthlyPartitionsDefinition(
    start_date="2021-06-01", end_date="2026-01-01", timezone="America/Sao_Paulo"
)


def compose(context: OpExecutionContext, *argumentos: str) -> None:
    """Roda `docker compose -p <projeto> ...` na raiz do repositório; falha = Failure."""
    projeto = os.environ.get("SIGMA_PROJETO", "sigma-unb")
    comando = ["docker", "compose", "-p", projeto, *argumentos]
    context.log.info("$ " + " ".join(comando))
    processo = subprocess.run(
        comando, cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    saida = (processo.stdout + processo.stderr).strip()
    if saida:
        context.log.info(saida[-6000:])
    if processo.returncode != 0:
        raise Failure(
            description=f"{' '.join(argumentos)} terminou com código {processo.returncode}",
            metadata={"saida": saida[-2000:]},
        )


def etapa(nome: str, *argumentos: str, depois: bool = True):
    """Cria um op que roda uma etapa do compose, com retry."""

    @op(
        name=nome,
        ins={"anterior": In(Nothing)} if depois else None,
        retry_policy=RETRY,
        tags={"etapa": nome},
    )
    def _op(context: OpExecutionContext) -> None:
        compose(context, *argumentos)

    return _op


subir_banco = etapa("subir_banco", "up", "-d", "--wait", "db", depois=False)
migrar = etapa("migrar", "run", "--rm", "--no-deps", "migrate")
ingerir = etapa("ingerir", "run", "--rm", "--no-deps", "ingest")
transformar = etapa("transformar", "run", "--rm", "--no-deps", "transformar")
buscar_correspondencias = etapa("buscar_correspondencias", "run", "--rm", "--no-deps", "semantica")
baixar_compras = etapa("baixar_compras", "run", "--rm", "--no-deps", "compras")
transformar_ouro = etapa("transformar_ouro", "run", "--rm", "--no-deps", "transformar_ouro")


@job(description="Carga mensal completa: estoque, CATMAT, correspondências, compras e camada ouro.",
     tags=TAG_DBT)
def pipeline_mensal():
    transformar_ouro(baixar_compras(buscar_correspondencias(transformar(ingerir(migrar(subir_banco()))))))


# --- Backfill por mês ----------------------------------------------------------

def _mes(context: OpExecutionContext) -> tuple[str, str]:
    """(MM-AAAA do arquivo do portal, AAAA-MM-01 do fato) da partição."""
    inicio = context.partition_time_window.start
    return inicio.strftime("%m-%Y"), inicio.strftime("%Y-%m-01")


@op(retry_policy=RETRY)
def carregar_estoque_do_mes(context: OpExecutionContext) -> None:
    arquivo, _ = _mes(context)
    compose(context, "run", "--rm", "--no-deps", "ingest",
            "python", "-m", "codigos.banco_de_dados.inserir_dados_na_camada_raw",
            "estoque", "--mes", arquivo)


@op(ins={"anterior": In(Nothing)}, retry_policy=RETRY)
def refazer_bronze_prata(context: OpExecutionContext) -> None:
    compose(context, "run", "--rm", "--no-deps", "transformar", "sh", "-c",
            "dbt deps --quiet && dbt build --profiles-dir . --project-dir . "
            "--select estoque_bronze+ --exclude path:snapshots path:models/ouro")


@op(ins={"anterior": In(Nothing)}, retry_policy=RETRY)
def recalcular_fato_do_mes(context: OpExecutionContext) -> None:
    _, mes = _mes(context)
    compose(context, "run", "--rm", "--no-deps", "transformar_ouro", "sh", "-c",
            "dbt deps --quiet && dbt build --profiles-dir . --project-dir . "
            f"--select fato_comparacao_preco monitor_atualizacao "
            f"--vars '{{mes_referencia: \"{mes}\"}}'")


@job(partitions_def=PARTICOES, tags=TAG_DBT,
     description="Backfill de um mês de estoque: raw do mês, bronze/prata e o mês no fato.")
def recarga_mensal():
    recalcular_fato_do_mes(refazer_bronze_prata(carregar_estoque_do_mes()))


agenda_mensal = ScheduleDefinition(
    job=pipeline_mensal,
    cron_schedule="0 6 20 * *",
    execution_timezone="America/Sao_Paulo",
    default_status=DefaultScheduleStatus.RUNNING,
    description="Dia 20 de cada mês, 06:00: dentro do SLA de 45 dias após o fim do mês.",
)

defs = Definitions(jobs=[pipeline_mensal, recarga_mensal], schedules=[agenda_mensal])
