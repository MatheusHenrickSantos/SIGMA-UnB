# Como executar

Versão resumida do README para o site da documentação.

## Pré-requisitos

- Docker (Docker Desktop no Windows, Docker Engine no Linux) com Compose v2 (`docker compose`)
- Git
- Internet (imagens, dados da UnB e modelo de embeddings)

## Passo a passo

```bash
git clone https://github.com/MatheusHenrickSantos/SIGMA-UnB.git
cd SIGMA-UnB
cp .env.example .env        # opcional
docker compose up --build
```

## Conferir

```bash
docker compose ps -a        # migrate, ingest, transformar e semantica: Exited (0); db: Up (healthy)
docker compose exec db psql -U sigma -d sigma -c "SELECT count(*) FROM estoque_saldo;"
```

## Comandos úteis

| Para… | Comando |
|---|---|
| Reexecutar a carga e etapas seguintes | `docker compose up --build ingest transformar semantica` |
| Aplicar migrações novas | `docker compose run --rm migrate` |
| Parar | `docker compose down` |
| Recomeçar do zero | `docker compose down -v` |

## Problemas comuns

Ver a seção *Problemas comuns* do [README](https://github.com/MatheusHenrickSantos/SIGMA-UnB#problemas-comuns).
