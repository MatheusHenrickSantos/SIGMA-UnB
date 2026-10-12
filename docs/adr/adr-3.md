# Armazenar a camada analítica em Parquet no MinIO, lida por DuckDB

- **Status:** proposto (passa a aceito quando a tabela de Medição estiver preenchida)
- **Data:** 2026-10-12
- **Decisores:** Squad SIGMA-UnB (confirmar nomes na revisão)

## Contexto

A E2 exige que o dado saia da origem (PostgreSQL, ADR 1) e chegue a um
armazenamento analítico **em formato aberto**, rodando em Docker Compose, sem
nuvem paga. A planilha de acompanhamento previa o Supabase Storage para isso.

Carga analítica do domínio:

- **Escrita:** em lote, uma vez por mês, depois da publicação do portal; o CDC
  roda logo depois da carga.
- **Leitura:** agregações por unidade, natureza da despesa e período sobre
  poucas colunas (planilha, aba 3, consultas 2, 3, 7 e 10). Empenhos são o maior
  volume: cerca de 10 mil registros por mês (planilha, aba 1).
- **Latência tolerada:** segundos por relatório; não há uso em tempo real.
- **Restrições:** tudo sobe com `docker compose up` numa máquina limpa; licença
  livre; a equipe conhece SQL, não Spark.

## Alternativas consideradas

### A. Opção nula: consultar o próprio PostgreSQL

Zero infraestrutura nova, e o volume do projeto cabe com folga no Postgres. Mas
relatório pesado roda no banco transacional, o formato não é aberto (a E2 pede
explicitamente formato aberto) e não há separação entre origem e análise para o
CDC da E2 e o dbt da E3 se apoiarem.

### B. Supabase Storage (o que a planilha previa)

Compatível com S3 e gratuito, mas é serviço na nuvem: não sobe no
`docker compose`, exige conta e chave de cada integrante e pausa o projeto após
uma semana sem uso no plano gratuito. Fere o requisito de reprodutibilidade em
máquina limpa.

### C. Parquet no MinIO, lido por DuckDB

O MinIO dá uma API S3 local dentro do compose. O Parquet é colunar e comprimido:
as consultas analíticas leem só as colunas que usam. O DuckDB lê Parquet direto
do MinIO e é o motor que o dbt usará na E3 (dbt-duckdb). A escrita é feita com
pyarrow, sem extensões baixadas em tempo de execução.

### D. Tabelas Delta Lake ou Apache Iceberg sobre o MinIO

Também são formatos abertos, com transações, *time travel* e evolução de esquema.
Custam um catálogo ou bibliotecas a mais, e a equipe nunca usou. As garantias que
elas trazem (escrita concorrente, atualização no lugar) não são necessárias: a
bronze é só acréscimo, com um escritor por vez.

## Medição

Medido com os dados reais do portal, depois de `docker compose up --build`:

```
docker compose run --rm --no-deps extract python medir_e2.py
```

Tamanho em disco (seção "ADR 3" da saída):

| Dataset | Bruto do portal (JSON/CSV) | Parquet zstd | Redução |
|---|---|---|---|
| empenhos → empenho | _preencher_ | _preencher_ | _preencher_ |
| gastos → gasto | _preencher_ | _preencher_ | _preencher_ |
| estoque → estoque_saldo | _preencher_ | _preencher_ | _preencher_ |
| requisicoes → requisicao_servico | _preencher_ | _preencher_ | _preencher_ |
| unidades → unidade | _preencher_ | _preencher_ | _preencher_ |

Consulta "gasto por unidade no último mês publicado" (mediana de 5 execuções):

| Alternativa | Mediana |
|---|---|
| A — PostgreSQL | _preencher_ |
| C — DuckDB sobre Parquet no MinIO | _preencher_ |

Atenção ao ler o resultado: no volume deste projeto o Postgres pode ser mais
rápido nessa consulta, porque as tabelas são pequenas e têm índice. Se for o
caso, isso precisa aparecer aqui. A escolha de C não se apoia só em tempo de
consulta: apoia-se no formato aberto exigido, em tirar a análise do banco
transacional e em servir de base para o dbt na E3.

## Decisão

Escolhemos C: Parquet com compressão zstd no MinIO, particionado por data de
extração (`data_extracao=`) e de captura (`data_captura=`), lido por DuckDB.

## Consequências

**O que ganhamos:**

- Formato aberto, legível por DuckDB, pandas, Spark ou qualquer ferramenta S3,
  sem prender o projeto a um fornecedor.
- Relatórios deixam de competir com a carga no Postgres.
- Tudo local e reproduzível com um `docker compose up`.

**O que perdemos:**

- Dois serviços para manter coerentes (Postgres e MinIO). O `verificar_e2.py`
  existe para provar que eles batem depois de cada execução.
- Parquet não aceita atualização no lugar: corrigir uma linha é gravar um arquivo
  novo. A versão "atual" de cada linha precisa ser reconstruída na E3 (última
  versão por chave), trabalho que um Delta ou Iceberg faria sozinho.
- O MinIO parou de publicar imagens novas da edição comunitária em outubro de
  2025. A imagem está fixada numa tag que continua disponível, mas não vai receber
  correções. Se a tag sumir, a troca é por outro S3 local (SeaweedFS, Garage) ou
  por uma pasta montada como volume. O código usa só a API S3, então não muda.

**O que se torna irreversível:**

Pouco. Os arquivos são Parquet padrão: migrar para Delta ou Iceberg é converter
os arquivos existentes, sem perder dado. Trocar o MinIO por outro S3 é mudar o
`LAKE_ENDPOINT`.

## Gatilho de revisão

- Revisar se a E3 precisar atualizar ou apagar linhas na camada analítica
  (aí Delta ou Iceberg passam a compensar).
- Revisar se o volume total do lake passar de 10 GB.
- Revisar se a imagem fixada do MinIO deixar de baixar num `docker pull`.
