# Caracterização da carga

Esta página descreve a carga executada pelo Compose atual: estoque da UnB,
catálogo CATMAT, normalização versionada, correspondências, compras públicas e
modelo analítico Ouro. As contagens abaixo vêm da execução completa de
23/11/2026 no PostgreSQL 16 com pgvector.

## Escopo e reprodução

O pipeline automatizado consulta três fontes:

| Fonte | Unidade consultada | Persistência na raw |
|---|---|---|
| Estoque do almoxarifado da UnB | Um recurso JSON por mês publicado | Uma linha por recurso em `raw.estoque` |
| CATMAT (Compras.gov.br) | Catálogo paginado, consolidado em um array | Um documento em `raw.catmat` |
| Pesquisa de preços (Compras.gov.br) | Um código aprovado e uma janela de datas | Um documento por código com resultados em `raw.compras`; checkpoints em `raw.compras_coleta` |

As respostas são inseridas como JSONB, sem arquivos de dados locais. O hash
SHA-256 do conteúdo impede inserir novamente um documento idêntico. A migração
V7 acrescenta checkpoints por código e janela para a coleta de compras,
inclusive quando não há resultados.

Os tempos registrados abaixo vêm da execução que terminou antes do commit da
ingestão direta. Ela usou o cache local de páginas do CATMAT e baixou compras
para arquivos antes de carregá-las na raw. As contagens descrevem os dados
resultantes; os tempos não medem a nova implementação sem cache local.

Para executar e consultar o estado dos containers:

```bash
docker compose up --build
docker compose ps -a
```

O pipeline também pode ser reproduzido em um banco já carregado; os hashes
evitam duplicar payloads iguais e os checkpoints evitam repetir códigos de
compras concluídos. O CATMAT completo é baixado em páginas e consolidado em
memória antes de ser gravado. Uma interrupção antes dessa gravação exige baixar
o catálogo novamente. A implementação atual não mantém cache de páginas: cada
execução consulta novamente o catálogo completo. O hash evita duplicar o
documento na raw, mas não evita as requisições à API.

## Volume observado

Contagens consultadas após a conclusão do pipeline. Os tamanhos incluem índices
e armazenamento TOAST do PostgreSQL (`pg_total_relation_size`); são referências
do volume observado, não limites fixos.

| Área | Relação | Linhas/documentos | Tamanho aproximado |
|---|---|---:|---:|
| Raw | `raw.estoque` | 39 documentos | 1,3 MiB |
| Raw | `raw.catmat` | 1 documento | 62,0 MiB |
| Raw | `raw.compras` | 2.458 documentos | 18,8 MiB |
| Bronze | `bronze.estoque` | 39.183 | 6,0 MiB |
| Bronze | `bronze.catmat` | 345.845 | 148,5 MiB |
| Bronze | `bronze.materiais_normalizados` (seed) | 2.327 | 0,3 MiB |
| Bronze | `bronze.compras` | 41.508 | 14,0 MiB |
| Prata | `prata.material` | 2.306 | 0,8 MiB |
| Prata | `prata.estoque` | 39.183 | 2,3 MiB |
| Prata | `prata.catmat_item` | 345.845 | 74,6 MiB |
| Prata | `prata.candidato_catmat` | 23.060 | 12,3 MiB |
| Prata | `prata.compra_publica` | 41.508 | 4,0 MiB |
| Busca | `busca.descricao` | 252.599 | 376,7 MiB |
| Busca | `busca.embedding` | 252.596 | 501,0 MiB |
| Ouro | `ouro.fato_comparacao_preco` | 39.176 | 6,5 MiB |

O estoque cobre 39 referências mensais, de 06/2021 a 12/2025, com lacunas
publicadas pela fonte. O CATMAT contém 345.845 itens. A execução consultou
3.526 códigos CATMAT aprovados para compras; 2.458 tiveram resultados na janela
01/07/2025–31/12/2025, totalizando 41.508 registros após a deduplicação da
Bronze.

O CSV `seeds/materiais_normalizados.csv` contém 2.327 descrições distintas
lidas da Bronze. O dbt o carrega como `bronze.materiais_normalizados`; as 2.327
descrições originais resultam em 2.306 descrições normalizadas distintas, que
formam `prata.material`.

## Duração da execução observada

Os horários vêm dos estados dos containers Docker. O tempo total entre o início
da ingestão e o fim da transformação Ouro foi aproximadamente **3 h 09 min**.

| Serviço | Duração observada | Resultado |
|---|---:|---|
| `ingest` | 45 s | Concluído; carregou os documentos de estoque e CATMAT |
| `transformar` | 31 s | 86 testes passaram; 2 avisos de qualidade; 0 erros |
| `semantica` | 1 h 59 min | 252.599 descrições sincronizadas, embeddings e 23.060 candidatos gravados |
| `compras` | 1 h 09 min | 3.526 códigos consultados; 2.458 com resultados; 41.508 registros; 0 falhas finais |
| `transformar_ouro` | 12 s | 48 testes passaram; 0 avisos; 0 erros |

O tempo de 45 s de `ingest` **não representa um download frio do CATMAT**: a
execução medida reutilizou o cache de páginas da implementação anterior. Um
download completo sem esse cache pode levar mais de 20 minutos, conforme
observado pelo responsável pelo projeto. A implementação atual repete esse
download em cada execução; o hash só deduplica a gravação no banco.

O serviço `compras` recebeu respostas HTTP 429 durante a coleta e precisou
repetir algumas requisições; todas as 3.526 consultas terminaram antes da
transformação Ouro. O tempo varia conforme os limites e a disponibilidade da
API.

## Avisos de qualidade observados

O `dbt build` de Bronze e Prata terminou com 86 testes aprovados, dois avisos
e nenhum erro:

| Teste | Resultado | Interpretação |
|---|---:|---|
| `preco_estoque_positivo` | 1 ocorrência | Há uma linha com preço não positivo; o teste emite aviso |
| `serie_material_some_e_volta` | 55 ocorrências | Há materiais que desaparecem e reaparecem entre referências; o teste emite aviso |

Esses resultados são alertas sobre a fonte, não falhas da execução. A
transformação Ouro terminou com 48 testes aprovados e nenhum aviso ou erro.

## Como obter as contagens

Conecte ao banco pelo `psql` e consulte, por exemplo:

```sql
SELECT count(*) FROM raw.estoque;
SELECT count(*) FROM raw.catmat;
SELECT count(*) FROM raw.compras;
SELECT count(*) FROM bronze.estoque;
SELECT count(*) FROM bronze.catmat;
SELECT count(*) FROM prata.candidato_catmat;
SELECT count(*) FROM ouro.fato_comparacao_preco;

SELECT schemaname, relname, n_live_tup,
       pg_size_pretty(pg_total_relation_size(relid)) AS tamanho
FROM pg_stat_user_tables
WHERE schemaname IN ('raw', 'bronze', 'prata', 'busca', 'ouro')
ORDER BY schemaname, relname;
```

As contagens de `pg_stat_user_tables.n_live_tup` são estimativas; use `count(*)`
quando precisar de uma contagem exata.
