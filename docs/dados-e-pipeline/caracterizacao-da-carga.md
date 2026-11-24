# Caracterização da carga

Esta página descreve a carga executada pelo Compose atual: estoque da UnB,
catálogo CATMAT, normalização versionada, correspondências, compras públicas e
modelo analítico Ouro. As contagens abaixo vêm da execução completa de
23/11/2026 no PostgreSQL 16 com pgvector. O CATMAT foi reaproveitado do cache
persistido no banco; a execução não fez o download frio do catálogo.

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

O CATMAT é mantido como snapshot em `raw.catmat`, com o estado da coleta em
`raw.catmat_coleta`. Depois que uma coleta completa é salva, execuções seguintes
reutilizam esse snapshot e pulam as centenas de requisições. Para buscar a versão
mais recente, execute `python codigos/inserir/baixar_catalogo_catmat.py
--atualizar`. Uma coleta parcial (por exemplo, com `--max-paginas`) não é marcada
como completa e, portanto, não ativa esse cache.

Os tempos abaixo são da execução com ingestão direta para a raw e normalização
integrada ao serviço `transformar`.

Para executar e consultar o estado dos containers:

```bash
docker compose up --build
docker compose ps -a
```

O pipeline também pode ser reproduzido em um banco já carregado; os hashes
evitam duplicar payloads iguais e os checkpoints evitam repetir códigos de
compras concluídos. O CATMAT é baixado em páginas e consolidado em memória antes
de substituir o snapshot no banco. Se a execução for interrompida antes da
gravação, a próxima tentativa precisa repetir a coleta; depois de gravado, o
snapshot funciona como cache entre execuções.

## Volume observado

Contagens consultadas após a conclusão do pipeline. Os tamanhos incluem índices
e armazenamento TOAST do PostgreSQL (`pg_total_relation_size`); são referências
do volume observado, não limites fixos.

| Área | Relação | Linhas/documentos | Tamanho aproximado |
|---|---|---:|---:|
| Raw | `raw.estoque` | 39 documentos | 1,3 MiB |
| Raw | `raw.catmat` | 2 documentos (snapshots) | 124 MiB |
| Raw | `raw.compras` | 2.459 documentos | 19 MiB |
| Bronze | `bronze.estoque` | 39.183 | 6,0 MiB |
| Bronze | `bronze.catmat` | 346.546 | 149 MiB |
| Bronze | `bronze.materiais_normalizados` (seed) | 2.327 | 0,3 MiB |
| Bronze | `bronze.compras` | 41.522 | 14 MiB |
| Prata | `prata.material` | 2.306 | 0,8 MiB |
| Prata | `prata.estoque` | 35.458 | 2,1 MiB |
| Prata | `prata.catmat_item` | 346.546 | 75 MiB |
| Prata | `prata.candidato_catmat` | 46.120 em 2 execuções | 24 MiB |
| Prata | `prata.compra_publica` | 41.522 | 4,0 MiB |
| Busca | `busca.descricao` | 253.299 | 378 MiB |
| Busca | `busca.embedding` | 253.298 | 503 MiB |
| Ouro | `ouro.fato_comparacao_preco` | 39.176 | 6,5 MiB |

O estoque cobre 39 referências mensais, de 06/2021 a 12/2025, com lacunas
publicadas pela fonte. O snapshot mais recente do CATMAT contém 346.546 itens.
O banco ainda guarda dois documentos CATMAT: a migração V8 aproveitou o maior
como cache inicial, sem apagar o documento histórico menor. A Bronze seleciona
o catálogo atual sem duplicar códigos. A execução consultou 3.388 códigos
CATMAT aprovados para compras; 2.459 documentos estão na raw e a Bronze contém
41.522 registros na janela 01/07/2025–31/12/2025.

O CSV `seeds/materiais_normalizados.csv` contém 2.327 descrições distintas
lidas da Bronze. O dbt o carrega como `bronze.materiais_normalizados`; as 2.327
descrições originais resultam em 2.306 descrições normalizadas distintas, que
formam `prata.material`.

## Duração da execução observada

Os horários vêm dos estados dos containers Docker. O tempo entre o início da
ingestão e o fim da transformação Ouro foi aproximadamente **31 min 53 s**.

| Serviço | Duração observada | Resultado |
|---|---:|---|
| `ingest` | 12 s | 39 recursos de estoque processados; CATMAT reconhecido no cache do banco |
| `transformar` | 26 s | normalização e seed executados; 86 testes passaram, 2 avisos e 0 erros |
| `semantica` | 20 min 56 s | 253.299 descrições sincronizadas; 23.060 candidatos nesta execução; 3.558 pares de decisão importados |
| `compras` | 10 min 05 s | 930 códigos pendentes consultados; 1 teve resultado (14 registros); 0 falhas finais |
| `transformar_ouro` | 11 s | 48 testes passaram; 0 avisos; 0 erros |

Esta execução usou o cache no banco e, portanto, **não mede um download frio do
CATMAT**. Um download completo pode levar mais de 20 minutos, conforme observado
pelo responsável pelo projeto. Esse tempo só é necessário na primeira carga ou
quando `--atualizar` for solicitado; a ingestão normal seguinte reutiliza o
snapshot salvo.

O serviço `compras` recebeu respostas HTTP 429 durante a coleta e precisou
repetir algumas requisições; as 930 consultas pendentes terminaram antes da
transformação Ouro. O tempo varia conforme os limites e a disponibilidade da
API. A sincronização semântica também recusou 236 linhas do CSV de decisões de
agentes porque elas ainda usam descrições anteriores à normalização atual.

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
