# Pipeline e arquitetura em camadas

Como os dados saem do portal dados.unb.br e chegam até a resposta da pergunta de gestão.

## Visão geral

```mermaid
flowchart LR
  A[dados.unb.br] -->|baixar_dados.py| B[(Bruto / Bronze<br/>dados/bruto)]
  M[Lojas online] -->|coletar_precos_mercado_livre.py| B
  B -->|carregar.py| C[(PostgreSQL<br/>OLTP)]
  C -->|[transformação]| D[(Prata<br/>[formato])]
  D -->|[agregação]| E[(Ouro / Analítica)]
  E --> F[Consultas / painel]
```

> Ajuste o diagrama ao que a squad decidiu no [ADR 0002](adr/0002-mecanismo-de-ingestao-e-formato-aberto.md).

## Camadas

| Camada | Onde fica | Formato | Conteúdo | Quem escreve |
|---|---|---|---|---|
| Bruta (bronze) | `dados/bruto/` | CSV original + `manifesto.json` | Cópia fiel do portal | `baixar_dados.py` |
| Transacional | PostgreSQL | Tabelas | Dados limpos e normalizados | `carregar.py` |
| Prata | [..] | [Parquet/..] | [..] | [..] |
| Ouro / analítica | [..] | [..] | Tabelas prontas para a pergunta de gestão | [..] |

## Etapas do pipeline

| # | Etapa | Script / serviço | Entrada | Saída | Idempotente? |
|---|---|---|---|---|---|
| 1 | Download | `ingest` → `baixar_dados.py` | Portal UnB | `dados/bruto/` | Sim (sha256 no manifesto) |
| 2 | Migrações | `migrate` (Flyway) | `db/migrations/` | Esquema | Sim |
| 3 | Carga | `ingest` → `carregar.py` | `dados/bruto/` | Tabelas | Sim |
| 4 | Coleta de preços de mercado | `coletar_precos_mercado_livre.py` | [..] | [..] | [..] |
| 5 | [Transformação] | [..] | [..] | [..] | [..] |

## Formato, serialização e compressão

| Item | Escolha | Motivo |
|---|---|---|
| Formato aberto | [..] | [..] |
| Compressão | [..] | [..] |
| Particionamento | [..] | [..] |

## Tratamento de falhas

- **Portal fora do ar (502):** até 5 tentativas; falhas registradas em `manifesto.json`.
- **Linhas inválidas:** [como são registradas e onde consultar]
- **Dado atrasado / reprocessamento:** [como a squad lida]

## Como executar

Ver [Como executar](como-executar.md).
