# Backlog da E2 — Ingestão em lote e captura de mudanças

Prazo oficial: 13/10/2026 · Entrega: tag `e2` · Peso: 12% da nota final

**Prioridades:** P0 = MVP (necessário para cumprir o checklist de aceite) · P1 = desejável · P2 = se sobrar tempo.

---

## MVP

O menor fluxo que cumpre o checklist de aceite da E2: dois caminhos de natureza diferente chegando à mesma camada analítica aberta.

```
dados.unb.br ──(lote)──► Postgres (OLTP) ──(CDC)──► Redpanda ──► consumidor ──► Parquet + Iceberg ◄── DuckDB (leitura)
                              ▲
                  script que altera linhas
```

### Escolhas do MVP

| Decisão | Escolha | Motivo |
|---|---|---|
| Formato de tabela | **Iceberg** (PyIceberg) | Evolução de esquema e de particionamento sem reescrever dados, e leitura por vários motores (DuckDB, Trino, Spark). Delta é comparado no ADR 2. |
| Catálogo | **SQLite** (catálogo SQL do PyIceberg) | Sem servidor extra; basta um arquivo no volume. |
| CDC | **Debezium** (decodificação lógica do WAL, plugin `pgoutput`) | É o que o enunciado descreve; o polling por `atualizado_em` fica como plano B. |
| Broker | **Redpanda** | Compatível com a API do Kafka, em um único container, sem ZooKeeper. |
| Motor de leitura | **DuckDB** | Lê Parquet e Iceberg direto, sem servidor. |
| Armazenamento | **Volume local** (`dados/analitico/`) | Evita MinIO no MVP. O formato é aberto de qualquer forma. |
| Compressão | **zstd** no Parquet, sujeita à medição do item 2.3 | A confirmar com número, não por padrão da ferramenta. |
| Linguagem | **Python**, reaproveitando `codigos/` | A equipe já conhece; mantém a imagem `ingest`. |

### Tabelas do MVP

- **`estoque_saldo`** — fato mensal, insert-only. Exercita o lote e o particionamento por mês.
- **`empenho`** — atualizado pela chave natural (upsert). É a que muda de verdade, então exercita o CDC.

As demais (`gasto`, `requisicao_servico`, cadastros) só entram se sobrar tempo.

---

## Épico 0 — Base

| # | Item | Prio |
|---|---|---|
| 0.1 | Corrigir a trava de queda de 30% do estoque em `codigos/carregar.py`: hoje 30 dos 40 meses são rejeitados, porque a comparação usa o último mês aceito. O lote precisa carregar tudo. | P0 |
| 0.2 | Reconciliar os números do ADR 1 com o banco real e corrigir os links quebrados do README (ADR, diário e `modelagem/`). | P1 |

## Épico 1 — Ingestão em lote

| # | Item | Prio |
|---|---|---|
| 1.1 | Job `OLTP → Parquet` para `estoque_saldo` e `empenho`, com carga completa e incremental (marca-d'água por `atualizado_em` ou `id_carga`). | P0 |
| 1.2 | Idempotência: reexecutar não duplica (substituição de partição ou merge por chave). | P0 |
| 1.3 | Teste automatizado: rodar duas vezes e comparar as contagens. | P0 |

## Épico 2 — Armazenamento analítico aberto

| # | Item | Prio |
|---|---|---|
| 2.1 | Layout do Parquet: particionar por mês de `data_referencia`, com tamanho alvo de arquivo. | P0 |
| 2.2 | Tabela Iceberg por cima do Parquet, lida pelo DuckDB. | P0 |
| 2.3 | Medir serialização e compressão (snappy contra zstd: tamanho e tempo de consulta) e justificar pelo padrão de acesso. | P0 |
| 2.4 | Job de compactação: provocar o problema de arquivos pequenos, medir e corrigir. | P1 |
| 2.5 | Demonstrar evolução de esquema (adicionar uma coluna sem reescrever os dados). | P1 |

## Épico 3 — Captura de mudanças (CDC)

| # | Item | Prio |
|---|---|---|
| 3.1 | Postgres com `wal_level=logical`, publicação e slot; subir Redpanda e Debezium no Compose. | P0 |
| 3.2 | Conector Debezium para `empenho` (e `estoque_saldo`). | P0 |
| 3.3 | Consumidor que lê os eventos e grava no Iceberg, aplicando insert, update e delete. | P0 |
| 3.4 | **Script de mutação:** altera linhas no OLTP e mostra o efeito atravessando o fluxo até o Iceberg. | P0 |
| 3.5 | Tratar `DELETE` e tombstones. | P1 |

## Épico 4 — Semântica de entrega e dado atrasado

| # | Item | Prio |
|---|---|---|
| 4.1 | Declarar a semântica de entrega (provável: at-least-once com consumidor idempotente, resultando em efeito exactly-once). | P0 |
| 4.2 | **Demonstração:** reiniciar o consumidor ou rebobinar o offset e mostrar que os dados não mudam; mostrar também o contraexemplo, sem idempotência. | P0 |
| 4.3 | Política de dado atrasado: um evento com três dias de atraso vai para qual partição (data do evento ou data de ingestão)? Escolher e documentar. | P0 |
| 4.4 | Reprocessamento de janela: reescrever uma partição e mostrar que o resultado é o mesmo. | P1 |

## Épico 5 — Medição e ADR 2

| # | Item | Prio |
|---|---|---|
| 5.1 | Opção nula: `INSERT ... SELECT` agendado, medindo latência e custo operacional. | P0 |
| 5.2 | Latência do CDC, do evento no OLTP até o dado visível no Iceberg. | P0 |
| 5.3 | Comparar Iceberg e Delta com critérios explícitos (pode ser análise documental, sem implementar os dois). | P0 |
| 5.4 | Escrever o ADR 2 (mecanismo de ingestão) com as três decisões e o número de cada uma: CDC contra recarga, Iceberg contra Delta, semântica de entrega. | P0 |

## Épico 6 — Entrega

| # | Item | Prio |
|---|---|---|
| 6.1 | Diário de bordo das semanas 7 a 10, no formato medido / surpreendeu / decidido / pendências. | P0 |
| 6.2 | Atualizar o README (como subir o novo fluxo), a sidebar do Docsify e o diagrama de arquitetura. | P0 |
| 6.3 | Atualizar o registro de uso de IA. | P1 |
| 6.4 | Criar a tag `e2`. | P0 |

---

## Ordem sugerida

`0.1` → `1.x` → `2.1` e `2.2` → `3.1` → `3.2` → `3.3` → `3.4` → `4.x` → `5.x` → `6.x`

As medições (`5.x`) e o diário (`6.1`) devem ser preenchidos **durante** o trabalho, com o número na hora. Escrever de memória no fim perde a evidência.

## Mapa para o checklist de aceite

| Item do checklist | Backlog |
|---|---|
| Ingestão em lote da fonte pública, idempotente e reexecutável | 0.1, 1.1, 1.2, 1.3 |
| Fluxo de mudanças a partir do OLTP | 3.1, 3.2, 3.3, 3.4 |
| Armazenamento analítico em formato aberto (Parquet e Iceberg) | 2.1, 2.2 |
| Semântica de entrega declarada e demonstrada | 4.1, 4.2 |
| Dado atrasado e reprocessamento de janela | 4.3, 4.4 |
| Serialização e compressão justificadas pelo padrão de acesso | 2.3 |
| ADR sobre o mecanismo de ingestão, com a opção nula | 5.1 a 5.4 |
| Diário de bordo das semanas 7 a 10 | 6.1 |

## Riscos

- **Debezium + Redpanda + Iceberg** é a parte mais pesada. Se travar, o plano B é CDC por polling em `atualizado_em`. Ele cumpre "fluxo equivalente", mas isso precisa ficar explícito no ADR.
- **Prazo:** o prazo de 13/10/2026 já passou; confirmar com a monitoria se a entrega ainda vale.
- **Opção nula forte:** a fonte é publicada em lote mensal, então `INSERT ... SELECT` agendado pode bastar. O ADR deve dizer isso com número, mas o CDC ainda precisa ser implementado e demonstrado para cumprir o checklist.
