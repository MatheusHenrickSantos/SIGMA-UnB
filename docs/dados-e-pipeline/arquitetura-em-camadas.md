# Arquitetura em camadas

O pipeline atual integra três fontes: estoque mensal da UnB, catálogo CATMAT e
preços de compras públicas. Os coletores gravam as respostas em JSONB na camada
`raw`; dbt transforma esses documentos em tabelas Bronze e Prata; o processo de
correspondência usa o schema técnico `busca` e grava candidatos e decisões na
Prata; por fim, o dbt materializa o modelo analítico na Ouro.

O schema `busca` é infraestrutura de recuperação de correspondências. Ele não
é a camada semântica analítica de consumo. Essa camada existe desde a E4 e vive na
Ouro: `ouro.metrica_mensal` e `ouro.catalogo_metrica`, com a definição das métricas
em `macros/metricas.sql` ([ADR 0010](../adr/0010-camada-semantica-de-metricas-em-macros-dbt.md)).



## Fluxo completo

<details>
  <summary>Figura 1 – Diagrama de fluxo da arquitetura
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Figura 1 – Diagrama Diagrama de fluxo da arquitetura (versão 1.0)</strong></p>
    <img src="https://raw.githubusercontent.com/MatheusHenrickSantos/SIGMA-UnB/refs/heads/main/docs/assets/diagramas/Arquitetura do banco-Resumo.v1.0.webp">
    <p>Autor: <a href="https://github.com/MatheusHenrickSantos">Matheus Henrick</a>.</p>
  </div>
</details>



## O que cada área guarda

| Área | Conteúdo | Como é produzida |
|---|---|---|
| `raw` | Payloads JSONB originais e hashes de estoque, CATMAT e compras | Coletores Python consultam as APIs e inserem diretamente no PostgreSQL |
| `bronze` | Estoque e CATMAT expandidos e tipados; compras expandidas quando a etapa de compras é executada; seeds de normalização e exceções de qualidade | `dbt build` usa modelos SQL e os CSVs de `seeds/` |
| `prata` | Materiais identificados, estoque relacionado, hierarquia CATMAT, preços públicos, candidatos e revisões | Modelos dbt e serviço de correspondência |
| `busca` | Descrições indexadas, vetores, modelo usado e execuções da busca | Serviço Python `semantica` |
| `ouro` | Dimensões, snapshot da correspondência, fato de comparação de preços e monitor de atualização | `transformar_ouro` executa dbt depois da coleta de compras |
| `reverso` | Alertas de preço para o setor de compras e mapa de acesso por almoxarifado (saída do ETL reverso, com permissão por papel) | `transformar_ouro` (dbt) e serviço `exportar`; ver [ADR 0011](../adr/0011-etl-reverso-por-arquivo-e-tabela-com-destino-que-puxa.md) |

### Raw e Bronze

O serviço `ingest` inicializa o esquema raw e chama os coletores do estoque da
UnB e do CATMAT. Cada payload é validado em memória e gravado como JSONB; o
SHA-256 torna a inserção idempotente. Não há arquivos de dados locais como
etapa intermediária.

Os modelos `bronze.estoque` e `bronze.catmat` expandem os arrays JSONB, convertem
os campos tipados e mantêm o hash de origem. Cada item CATMAT vira uma linha em
`bronze.catmat`; cada registro de estoque conserva mês e ano da publicação.

### Normalização e seed

As regras compartilhadas ficam em `codigos/normalizar/limpeza.py`. Depois de
materializar a Bronze, o serviço `transformar` chama
`python -m codigos.normalizar`: o script lê as descrições distintas de
`bronze.estoque`, aplica essas regras e grava o mapeamento original →
normalizado em `seeds/materiais_normalizados.csv`. Em seguida, o Compose roda
`dbt seed` e reconstrói os modelos Bronze e Prata. O CSV é versionado no
repositório e carregado pelo dbt em `bronze.materiais_normalizados`.

O CSV **não vai para `raw`**. Ele é um seed do dbt na Bronze. A Prata usa o seed
para criar `prata.material` e relacionar as linhas de `prata.estoque` com o
material normalizado. `seeds/excecoes_qualidade.csv` também é carregado na
Bronze e fornece exceções revisadas para os testes de qualidade.

Quando o seed muda, o arquivo atualizado fica no checkout que executou o
Compose; revise e versione essa mudança. O seed contém 2.327 descrições
originais, que resultam em 2.306 descrições normalizadas distintas em
`prata.material`.

### Prata e correspondência CATMAT

O dbt cria `prata.material`, `prata.almoxarifado`, `prata.estoque` e as tabelas
da hierarquia CATMAT (`catmat_grupo`, `catmat_classe`, `catmat_pdm` e
`catmat_item`). As fontes semânticas são `prata.material` e `prata.catmat_item`.

O serviço `semantica` mantém no schema `busca` os textos originais e
normalizados, embeddings pgvector, metadados do modelo e histórico de execução.
Depois da busca, os candidatos e revisões ficam na Prata:
`prata.candidato_catmat`, `prata.revisao_correspondencia` e
`prata.revisao_material`. As views `prata.v_candidato_catmat`,
`prata.v_fila_revisao` e `prata.v_item_aprovado` servem a revisão e as etapas
seguintes. Candidato é sugestão; somente itens aprovados entram na consulta de
preços.

### Compras públicas e Ouro

O serviço `compras` consulta os códigos aprovados em
`prata.v_item_aprovado`, na janela `COMPRAS_INICIO`–`COMPRAS_FIM`. As respostas
com registros são gravadas diretamente em `raw.compras`. A migração V7 cria
`raw.compras_coleta`, com um checkpoint por código e janela, mesmo quando não
há resultados. Respostas incompletas por limite de páginas não são marcadas
como concluídas.

`transformar_ouro` executa dbt para expandir `raw.compras` em
`bronze.compras`, filtrar os preços válidos na Prata, atualizar o snapshot das
decisões de correspondência e materializar Ouro. O snapshot preserva a versão
da decisão usada por cada dimensão/fato. A fato
`ouro.fato_comparacao_preco` tem grão material × almoxarifado × mês; o preço
público é calculado a partir dos códigos CATMAT equivalentes vigentes.

## Ordem dos serviços no Compose

```text
db saudável
  → Flyway (migrações)
  → ingest (inicializa raw, estoque e CATMAT)
  → transformar (seeds + dbt Bronze e Prata)
  → semantica (busca, vetores e candidatos)
  → compras (API → raw.compras)
  → transformar_ouro (compras Bronze/Prata, snapshot, Ouro, métricas e reverso)
  → exportar (CSV de alertas de preço em dados/saida)
```

O banco e o painel Streamlit permanecem ativos; os demais serviços terminam
depois de concluir sua etapa. Para os volumes e tempos observados, consulte
[Caracterização da carga](caracterizacao-da-carga.md). Para iniciar o projeto,
consulte [Como executar](../projeto/como-executar.md).
