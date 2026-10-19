# Caracterização e volume da carga

Medições da carga dos dados abertos da UnB no PostgreSQL. Os números aqui embasam o [ADR 1](adr/adr-1.md).

**Data da medição:** DD/MM/AAAA
**Commit medido:** `[hash]`
**Máquina:** [CPU, RAM, SO, Docker Desktop/Engine versão]

## Como reproduzir

```bash
docker compose down -v          # começa do zero
docker compose up --build       # baixa e carrega
docker compose run --rm ingest python inspecionar_bruto.py
docker compose run --rm ingest python medir_adr0001.py
```

## Camada bruta (`dados/bruto/`)

| Dataset | Arquivos | Tamanho (MB) | Linhas | Colunas | Período coberto |
|---|---|---|---|---|---|
| Estoque do almoxarifado | | | | | |
| Unidades acadêmicas | | | | | |
| Gastos por unidade | | | | | |
| Empenhos | | | | | |
| Requisições de serviços | | | | | |
| **Total** | | | | | |

## Carga no banco

| Tabela | Linhas gravadas | Linhas rejeitadas | % rejeitado | Tamanho da tabela (MB) | Tempo de carga (s) |
|---|---|---|---|---|---|
| `estoque_saldo` | | | | | |
| [tabela] | | | | | |

Consulta usada:

```sql
SELECT dataset, count(*), sum(linhas_gravadas), sum(linhas_rejeitadas)
FROM carga_execucao GROUP BY 1;

SELECT relname, pg_size_pretty(pg_total_relation_size(relid))
FROM pg_catalog.pg_statio_user_tables ORDER BY pg_total_relation_size(relid) DESC;
```

## Perfil da carga de trabalho

| Característica | Observação |
|---|---|
| Frequência de atualização na origem | [diária / mensal / esporádica] |
| Tipo de operação predominante | [inserção / atualização / leitura analítica] |
| Crescimento estimado | [linhas/mês] |
| Principais motivos de rejeição | [ex.: data inválida, valor não numérico] |

## Qualidade dos dados

- [Colunas com muitos nulos]
- [Inconsistências entre datasets — ex.: códigos de unidade que não batem]
- [Duplicidades encontradas]

## Conclusões

[O que os números mostram e como influenciaram a modelagem.]
