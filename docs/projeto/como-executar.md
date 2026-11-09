# Como executar

Versão resumida do README para o site da documentação.

## Escopo deste passo a passo

Os comandos abaixo sobem o pipeline Docker já existente. O serviço `ingest` ainda baixa os cinco datasets da configuração anterior do portal da UnB; não baixa o CATMAT nem consulta preços públicos. A coleta do CATMAT e a exploração da API de preços são feitas por scripts separados e ainda não estão integradas à execução do Compose. Consulte o [teste de viabilidade](../testes/teste-de-viabilidade.md) para esse fluxo.

## Pré-requisitos

- Docker (Docker Desktop no Windows, Docker Engine no Linux) com Compose v2 (`docker compose`)
- Git
- Internet (imagens e dados da UnB; ~850 MB na primeira carga)

## Passo a passo

```bash
git clone https://github.com/MatheusHenrickSantos/SIGMA-UnB.git
cd SIGMA-UnB
cp .env.example .env        # opcional
docker compose up --build
```

## Conferir

```bash
docker compose ps -a        # migrate e ingest: Exited (0); db: Up (healthy)
docker compose exec db psql -U sigma -d sigma -c "SELECT count(*) FROM estoque_saldo;"
```

## Comandos úteis

| Para… | Comando |
|---|---|
| Recarregar só o que mudou no pipeline atual | `docker compose run --rm ingest` |
| Aplicar migrações novas | `docker compose run --rm migrate` |
| Parar | `docker compose down` |
| Recomeçar do zero | `docker compose down -v` |

## Problemas comuns

Ver a seção *Problemas comuns* do [README](https://github.com/MatheusHenrickSantos/SIGMA-UnB#problemas-comuns).
