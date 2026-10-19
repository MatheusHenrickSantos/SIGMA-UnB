# ADR 0002 — [Mecanismo de ingestão e formato aberto da camada bruta]

| Campo | Valor |
|---|---|
| Status | Proposto \| Aceito \| Substituído por ADR XXXX |
| Data | DD/MM/AAAA |
| Entrega | E2 |
| Autores | [nomes] |
| ADRs relacionados | [ADR 1](adr/adr-1.md) |

## Contexto

[Descreva a situação atual. Ex.: hoje `codigos/baixar_dados.py` salva os 5 datasets do dados.unb.br em `dados/bruto/` no formato original (CSV) e `carregar.py` grava direto no PostgreSQL. A E2 pede uma camada em formato aberto e um mecanismo de ingestão reprodutível. Qual problema essa decisão resolve?]

Forças em jogo:

- [Volume: ~850 MB brutos, sendo a maior parte empenhos]
- [Reprocessamento: precisamos recarregar sem baixar tudo de novo]
- [Ferramentas que a squad domina]
- [Restrições da disciplina]

## Alternativas consideradas

### A. Opção nula — manter CSV bruto + carga direta no PostgreSQL

- **Prós:** [..]
- **Contras:** [..]

### B. [ex.: Parquet particionado por dataset/data de coleta]

- **Prós:** [..]
- **Contras:** [..]

### C. [ex.: DuckDB lendo os arquivos abertos / outra engine]

- **Prós:** [..]
- **Contras:** [..]

## Medição

[Números que embasam a decisão. Rode o script e cole os resultados.]

| Métrica | Alternativa A | Alternativa B | Alternativa C |
|---|---|---|---|
| Tamanho em disco (MB) | | | |
| Tempo de escrita (s) | | | |
| Tempo de leitura / consulta-teste (s) | | | |
| Compressão usada | — | [snappy/zstd] | |

Como reproduzir: `docker compose run --rm ingest python [script_de_medicao].py`

## Decisão

[Adotamos a alternativa X porque …]

## Consequências

- **Positivas:** [..]
- **Negativas / custos:** [..]
- **O que muda no repositório:** [novos serviços no `docker-compose.yml`, novas pastas, migrações]

## Gatilho de revisão

[Em que situação esta decisão deve ser revista. Ex.: volume passar de X GB, nova fonte em formato diferente.]
