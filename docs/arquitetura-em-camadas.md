# Pipeline e arquitetura em camadas

O SIGMA-UnB organiza os dados em três camadas (arquitetura *medallion*): **Bronze**, **Prata** e **Ouro**. Os dados saem do portal de dados abertos da UnB e das lojas online e terminam em um modelo dimensional que responde à [pergunta de gestão](dominio-e-pergunta.md).

<div align="center">
  <p><strong>Figura 1 – Arquitetura do Banco (Versão 1.1)</strong></p>
  <img src="https://raw.githubusercontent.com/MatheusHenrickSantos/SIGMA-UnB/refs/heads/main/docs/assets/diagramas/Arquitetura do banco.v1.1.png">
  <p>Fonte: <a href="#/modelagem/diagrama-de-arquitetura">Diagrama de Arquitetura</a>.</p>
</div>

## Visão geral

```text
 FONTES                 BRONZE                     PRATA                       OURO
┌──────────────────┐   ┌───────────────────────┐   ┌────────────────────────┐   ┌──────────────────────┐
│ dados.unb.br     │──▶│ dados/bruto/<dataset>/│──▶│ PostgreSQL 16          │──▶│ Parquet + DuckDB     │
│ (API CKAN)       │   │ + manifesto.json      │   │ esquema Flyway (V1)    │   │ modelo estrela:      │
│                  │   │                       │   │ material, almoxarifado,│   │ FatoAvaliacaoEstoque │
│ Lojas online     │──▶│ dados/coletas/        │──▶│ estoque_saldo,         │   │ + DimMaterial        │
│ (Mercado Livre)  │   │ mercado_livre/*.json  │   │ cotacao_online, ...    │   │ + DimAlmoxarifado    │
└──────────────────┘   └───────────────────────┘   └────────────────────────┘   │ + DimLoja + DimTempo │
                         baixar_dados.py             carregar.py                └──────────────────────┘
                         coletar_precos_...py        (Flyway: migrate)            [E3]
```

## Resumo das camadas

| | Bronze | Prata | Ouro |
|---|---|---|---|
| **Papel** | Cópia fiel do que veio da fonte | Dados limpos, tipados e relacionados | Dados prontos para responder à pergunta de gestão |
| **Onde fica** | `dados/bruto/` e `dados/coletas/` | Banco PostgreSQL (`db`) | Arquivos Parquet lidos com DuckDB |
| **Formato** | Arquivos originais do portal (JSON ou CSV) e JSON da coleta | Tabelas relacionais (3FN) | Modelo estrela (fato + dimensões) |
| **Quem escreve** | `baixar_dados.py`, `coletar_precos_mercado_livre.py` | `carregar.py` + migrações Flyway | [script/serviço de transformação] |
| **Pode ser recriada?** | Não: é a fonte da verdade local | Sim, a partir da Bronze | Sim, a partir da Prata |
| **Situação** | ✅ Estoque e demais datasets · ⏳ cotações | ✅ Esquema e carga · ⏳ `cotacao_online` vazia | ⏳ Planejada para a E3 |

---

## Bronze — dados brutos

**Objetivo:** guardar os dados exatamente como vieram da fonte, sem nenhuma transformação, para poder reprocessar tudo se a lógica da carga mudar.

### Portal de dados abertos da UnB

O `codigos/baixar_dados.py` consulta a API CKAN do portal (`https://dados.unb.br/api/3/action`) e baixa os recursos de cada dataset para `dados/bruto/<dataset>/`.

| Dataset | Pasta | Obrigatório |
|---|---|---|
| Estoque do almoxarifado | `dados/bruto/estoque/` | Sim |
| Unidades acadêmicas | `dados/bruto/unidades/` | Sim |
| Gastos por unidade | `dados/bruto/gastos/` | Não |
| Empenhos | `dados/bruto/empenhos/` | Não |
| Requisições de serviços | `dados/bruto/requisicoes/` | Não |

O `dados/bruto/manifesto.json` registra, para cada arquivo, a URL de origem, a data de modificação no portal, o tamanho e o **sha256**. O sha256 é o que garante a linhagem e evita baixar ou carregar o mesmo conteúdo duas vezes.

### Lojas online

O `codigos/coletar_precos_mercado_livre.py` busca cada material na API pública do Mercado Livre (`/sites/MLB/search`) e salva a resposta em `dados/coletas/mercado_livre/precos_mercado_livre_<data-hora>.json`. A lista de materiais vem de `dados/processados/almoxarifado_normalizado.json`, gerado pelo `normalizar.py`, que também cria o `termo_busca` de cada material.

Para cada material, o arquivo guarda:

- até 5 anúncios, com título, preço, condição, vendedor e link;
- um resumo com os preços mínimo, médio, mediano e máximo;
- a variação da mediana em relação ao preço unitário do estoque.

Cada execução gera um arquivo novo, então a coleta é *append-only*: nada é sobrescrito.

### Atributos de linhagem

O diagrama prevê que cada registro da Bronze carregue de onde veio:

| Atributo (diagrama) | Como está implementado hoje |
|---|---|
| `ArquivoDeOrigem` | Nome do arquivo em `dados/bruto/` + `carga_execucao.arquivo` |
| `LinhaDoArquivo` | ⏳ Não é guardado por linha (só a linha rejeitada vai para `carga_rejeitado.registro`) |
| `DataDaInserção` | `carga_execucao.iniciado_em` e `carregado_em` em cada tabela |
| `TermoDaBusca`, `DataDaBusca`, `Link` | Campos `termo_busca`, `data_coleta` e `url` no JSON da coleta |

---

## Prata — dados limpos e relacionados

**Objetivo:** dados com tipos corretos, sem duplicatas, com chaves e relacionamentos, prontos para consulta. A Prata corresponde ao [modelo entidade-relacionamento](modelagem/diagrama-entidade-relacionamento.md) e ao [modelo relacional](modelagem/modelo-relacional.md).

O esquema é criado pelo Flyway a partir de `db/migrations/V1__esquema_inicial.sql`. A carga é feita pelo `codigos/carregar.py`, que usa as funções de limpeza de `normalizar.py`.

### Correspondência com o diagrama

| Entidade / relacionamento (diagrama) | Tabela no PostgreSQL | Tipo de tabela |
|---|---|---|
| Material | `material` (`descricao`, `termo_busca`) | Cadastro (CRUD) |
| Almoxarifado | `almoxarifado` (`nome`, `id_unidade`) | Cadastro (CRUD) |
| Possui / Estoque (Preço, Quantidade) | `estoque_saldo` (`preco_unitario`, `saldo`, `valor_total`) | Foto mensal *insert-only* |
| Vende / PrecoOnline (Preço, Data) | `cotacao_online` (`preco`, `data_coleta`) | *Insert-only* |
| Loja | Coluna `loja` em `cotacao_online` | — |

Tabelas de apoio que também ficam na Prata:

- **Contexto da pergunta:** `unidade`, `gasto`, `empenho`, `natureza_despesa`, `credor` e `requisicao_servico`.
- **Controle de carga:** `carga_execucao` e `carga_rejeitado`.

### Regras aplicadas na passagem Bronze → Prata

| Regra | Onde |
|---|---|
| Limpeza de texto (entidades HTML, espaços repetidos) e conversão de números no formato brasileiro | `normalizar.py` |
| `termo_busca`: descrição sem acentos, em minúsculas e com unidades separadas, para buscar nas lojas | `normalizar.py` (`gerar_termo_busca`) |
| Material e almoxarifado viram cadastro com chave substituta (deduplicados pela descrição/nome) | `carregar.py` (`Cadastro`) |
| Estoque: uma foto por material × almoxarifado × mês (`data_referencia` sempre no dia 1º) | PK + `CHECK` em `estoque_saldo` |
| `valor_total` ausente é calculado como `saldo × preco_unitario` | `gravar_estoque` |
| Preço negativo é recusado | `CHECK (preco_unitario >= 0)` |
| Linha inválida não interrompe a carga: vai para `carga_rejeitado` com o motivo | `carregar.py` |
| Arquivo com o mesmo sha256 não é carregado de novo (idempotência) | `UNIQUE (dataset, sha256)` em `carga_execucao` |

As decisões de modelagem (cadastros CRUD, fatos *insert-only*) estão justificadas no [ADR 1](adr/adr-1.md).

---

## Ouro — modelo analítico

**Objetivo:** uma tabela fato e quatro dimensões que respondem diretamente quais materiais foram pagos acima do mercado, em quais almoxarifados e quanto se economizaria.

**Formato:** Parquet, lido com DuckDB ([ver ADR 0002](adr/0002-mecanismo-de-ingestao-e-formato-aberto.md)).
**Situação:** ⏳ planejada para a E3. Os campos abaixo são a proposta e devem ser confirmados pela squad.

### Modelo estrela

```text
              DimMaterial          DimAlmoxarifado
                    \                   /
                     FatoAvaliacaoEstoque
                    /                   \
               DimLoja                DimTempo
```

**Grão da fato:** um registro por **material × almoxarifado × mês × loja**.

| Tabela | Colunas propostas | Origem na Prata |
|---|---|---|
| `dim_material` | `sk_material`, `id_material`, `descricao`, `termo_busca` | `material` |
| `dim_almoxarifado` | `sk_almoxarifado`, `id_almoxarifado`, `nome`, `sigla_unidade`, `nome_unidade` | `almoxarifado` + `unidade` |
| `dim_loja` | `sk_loja`, `loja` | `cotacao_online.loja` (distintos) |
| `dim_tempo` | `sk_tempo`, `data`, `ano`, `mes`, `trimestre`, `semestre` | `estoque_saldo.data_referencia` |
| `fato_avaliacao_estoque` | `sk_material`, `sk_almoxarifado`, `sk_loja`, `sk_tempo`, `saldo`, `preco_unitario_unb`, `preco_mercado`, `qtd_cotacoes`, `sobrepreco_unitario`, `sobrepreco_pct`, `economia_potencial` | `estoque_saldo` + `cotacao_online` |

### Regras de cálculo da fato

| Medida | Regra |
|---|---|
| `preco_mercado` | Mediana dos preços de `cotacao_online` do material, na loja, no mesmo mês. A mediana reduz o efeito de anúncios muito fora da curva. |
| `sobrepreco_unitario` | `preco_unitario_unb - preco_mercado` |
| `sobrepreco_pct` | `(preco_unitario_unb / preco_mercado - 1) × 100` |
| `economia_potencial` | `sobrepreco_unitario × saldo` quando `sobrepreco_unitario > 0`; senão `0` |
| Filtros | Só entram registros com `preco_unitario > 0` e com pelo menos 1 cotação no mês |

---

## Etapas do pipeline

| # | Etapa | Script / serviço | Entrada | Saída | Idempotente? | Situação |
|---|---|---|---|---|---|---|
| 1 | Download dos datasets | `ingest` → `baixar_dados.py` | API CKAN dados.unb.br | `dados/bruto/` + `manifesto.json` | Sim (pula arquivos já baixados) | ✅ |
| 2 | Criação do esquema | `migrate` (Flyway) | `db/migrations/V*.sql` | Tabelas da Prata | Sim | ✅ |
| 3 | Carga Bronze → Prata | `ingest` → `carregar.py` | `dados/bruto/` | Tabelas da Prata | Sim (sha256) | ✅ |
| 4 | Coleta de preços | `coletar_precos_mercado_livre.py` | `dados/processados/almoxarifado_normalizado.json` | `dados/coletas/mercado_livre/*.json` | Append-only | 🔄 Protótipo (limitado a 3 materiais) |
| 5 | Carga das cotações | [a definir] | `dados/coletas/` | `cotacao_online` | [..] | ⏳ |
| 6 | Prata → Ouro | [a definir] | PostgreSQL | Parquet (estrela) | [..] | ⏳ E3 |

A ordem 1 → 2 → 3 é garantida pelo `docker-compose.yml`: o `migrate` só começa com o `db` saudável, e o `ingest` só começa se o `migrate` terminar com sucesso.

## Tratamento de falhas

| Situação | Comportamento |
|---|---|
| Portal responde 502 ou cai a conexão | Até 5 tentativas por arquivo; o que falhar fica em `falhas` no `manifesto.json` e é baixado na próxima execução |
| Dataset obrigatório (estoque ou unidades) não baixa | `ingest` termina com código 1 |
| Linha com erro (sem material, sem saldo, data inválida) | Linha vai para `carga_rejeitado`; o resto do arquivo é carregado |
| Mesmo arquivo publicado de novo no portal | Ignorado pelo sha256 |
| API do Mercado Livre falha ou demora | Até 3 tentativas com timeout de 30 s; o resultado de cada material fica registrado no campo `status` do JSON |

## Como executar

Ver [Como executar](como-executar.md).

---

## Histórico de versões

| Versão | Descrição | Autor(es) | Data |
|---|---|---|---|
| `1.0` | Criação do documento | Samara Letícia | 19/10/2026 |
