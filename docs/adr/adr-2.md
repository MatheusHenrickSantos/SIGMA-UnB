# Adotar Delta Lake com Parquet ZSTD particionado por ano na camada analítica

- **Status:** aceito
- **Data:** 2026-10-19
- **Decisores:**  
  - Israel Thalles Dutra dos Santos  
  - Magno Luiz Vale Vieira  
  - Matheus Henrick Dutra dos Santos  
  - Samara Letícia Alves dos Santos  

## Contexto

A camada analítica recebe duas entradas: a carga em lote do OLTP (estoque mensal)
e os eventos de captura de mudanças (CDC). O fato principal, `estoque_saldo`,
tem 41.116 linhas em 40 meses (2020 a 2025), 9 colunas, e cresce cerca de 700
linhas por mês. O acesso é de leitura analítica: filtro por período e agregação
de poucas colunas (saldo, preço, valor). A escrita é em lote mensal, mais
eventos esparsos do CDC. A meta de latência para consulta interativa é de 2 s
(ADR 1).

Restrições: a carga precisa ser **idempotente** (reprocessar não duplica nem muda
o resultado), tolerar **dado atrasado**, e rodar em um laptop com Docker Compose.
A equipe conhece Python e SQL, não Java; isso pesa contra opções que exigem JVM.

## Alternativas consideradas

### A. Opção nula — CSV/JSON em pasta, sem tabela

Funciona para o volume atual. Não tem esquema, transação nem `MERGE`: a
idempotência teria de ser reimplementada à mão em cada escrita, e uma falha no
meio da escrita deixa a pasta em estado parcial.

### B. Parquet puro em pasta

Resolve tamanho e leitura por coluna. Continua sem transação atômica e sem
`MERGE`: atualizar uma linha significa reescrever arquivos manualmente.

### C. Apache Iceberg (`pyiceberg`)

Formato de tabela aberto, com evolução de esquema e partição oculta. Exige um
catálogo (REST, SQL ou Glue) além dos arquivos, e o suporte a `MERGE` por Python
ainda é limitado; o caminho completo passa por Spark ou Trino.

### D. Delta Lake (`deltalake`, em Python)

Parquet mais um log de transações em JSON. Escrita atômica, `MERGE`, histórico
de versões (time travel) e `OPTIMIZE`, tudo em Python, sem JVM nem catálogo.

## Medição

Dado: `estoque_saldo` real, 41.116 linhas.

Como reproduzir:

```
docker compose run --rm --no-deps ingest python lake.py carga
docker compose run --rm --no-deps ingest python medir_adr0002.py
```

| Serialização / compressão | Tamanho |
|---|---|
| JSON Lines | 9.684 KiB |
| CSV | 3.019 KiB |
| Parquet sem compressão | 303 KiB |
| Parquet Snappy | 226 KiB |
| Parquet ZSTD | 138 KiB |
| Parquet GZIP | 140 KiB |

| Consulta (soma do valor de 2024, melhor de 5) | Tempo |
|---|---|
| CSV, lê tudo | 4,1 ms |
| Parquet ZSTD, arquivo único | 2,0 ms |
| Parquet ZSTD, particionado por ano | 1,1 ms |

Com este volume todas as consultas ficam muito abaixo da meta de 2 s; a diferença
entre os formatos aparece sobretudo no **tamanho** (CSV é 22 vezes maior que
Parquet ZSTD) e na leitura por coluna, que cresce com os snapshots futuros.

## Decisão

Escolhemos **Delta Lake sobre Parquet com compressão ZSTD (nível 3)**, com
`estoque_saldo` **particionada por ano** e escrita sempre por `MERGE` com chave.

- **Parquet colunar:** a consulta lê 2 a 3 de 9 colunas; formato por linha (JSON,
  CSV) lê todas.
- **ZSTD:** menor que Snappy (138 contra 226 KiB) e equivalente ao GZIP, com
  descompressão rápida. Escrevemos pouco e lemos muito, então o custo extra na
  escrita não pesa.
- **Partição por ano:** o filtro típico é por período. Por ano, não por mês:
  são 6 partições de cerca de 7 mil linhas; por mês seriam 40 arquivos minúsculos
  (problema de arquivos pequenos) sem ganho de leitura.
- **Delta em vez de Iceberg:** entrega `MERGE` e atomicidade em Python puro.

## Consequências

**O que ganhamos:** idempotência por construção (o `MERGE` por chave e a regra
`ultimo_evento` tornam reprocessar seguro); histórico de versões para auditoria;
sem servidor nem catálogo para operar.

**O que perdemos:** só o `deltalake`/Python escreve com garantia; ler de Spark ou
Trino funciona, mas não testamos. O runtime nativo do `deltalake` às vezes aborta
ao encerrar o interpretador, e contornamos com saída direta (`os._exit`) nos
scripts. A tabela precisa de `lake.py compactar` periodicamente, para juntar
arquivos pequenos criados por `MERGE`; quem paga é quem opera a carga.

**O que se torna irreversível:** nada grave. Os dados são Parquet padrão;
migrar para Iceberg é reescrever o log de transações (o Iceberg lê Parquet
existente via *add files*), sem reconverter dados.

## Gatilho de revisão

Revisar a escolha de partição se `estoque_saldo` passar de **5 milhões de
linhas** ou se uma consulta típica passar de **2 s**; revisar o formato de tabela
se o destino passar a ser consumido por Spark ou Trino em produção.
