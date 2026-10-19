# Release Notes 2 — Banco de Dados 2

**Nome do grupo:** SIGMA-UnB (Squad 13)
**Integrantes:**
- Israel Thalles Dutra dos Santos — `<190014776>`
- Magno Luiz Vale Vieira — `<180042696>`
- Matheus Henrick Dutra dos Santos — `<190018101>`
- Samara Letícia Alves dos Santos — `<221008445>`

**Data:** 19/10/2026
**Domínio:** gestão de materiais de consumo dos almoxarifados da Universidade de Brasília (UnB)

---

## 1. Domínio, perguntas e valor de negócio

**Domínio de aplicação:**
O SIGMA-UnB (Sistema Integrado de Gestão de Materiais e Almoxarifado) organiza os dados abertos da UnB sobre estoque, empenhos, gastos e unidades. O problema abordado é a falta de visão histórica do custo dos materiais. Hoje não é simples saber quais materiais encareceram mais rápido, onde estão estocados e com quais fornecedores a universidade gasta.

**Perguntas que o projeto pretende responder:**
1. **(principal)** Entre 2021 e 2025, quais materiais de consumo do almoxarifado da UnB apresentaram a maior taxa anualizada de aumento do preço unitário registrado?
2. Quais materiais e almoxarifados concentram o maior saldo e o maior valor em estoque?
3. Quais credores concentram os valores empenhados pela UnB, e como esses valores evoluíram no período? *(em nível de empenho; a ligação empenho ↔ material não existe nos dados de origem)*
4. *(complementar, futura)* Quais materiais tiveram o preço registrado acima do preço de mercado em lojas online?

**Valor de negócio dos dados gerados:**

| Público | Decisão que os dados apoiam |
|---|---|
| Áreas de compras e gestores da UnB | Priorizar a revisão de contratos e compras dos materiais com maior alta de preço |
| Gestores de almoxarifado | Acompanhar a evolução do custo registrado e o valor parado em estoque |
| Chefes de departamento e Centros Acadêmicos | Acompanhar gastos por unidade e natureza da despesa |

O ganho esperado é concentrar a revisão de compras nos poucos materiais que explicam a maior parte do aumento de custo, em vez de revisar o catálogo inteiro.

## 2. Fontes de dados

Todas as fontes vêm do [Portal de Dados Abertos da UnB](https://dados.unb.br/), via API CKAN. O detalhamento está em [Fontes e histórico da origem](docs/fontes-e-historico-da-origem.md).

| Fonte | Link | Formato | Período | Pergunta(s) que apoia |
|---|---|---|---|---|
| Estoque do almoxarifado | https://dados.unb.br/dataset/estoque-do-almoxarifado | JSON (API CKAN) | 2021-06 a 2025-12 | P1, P2 |
| Empenhos | https://dados.unb.br/dataset/empenhos | JSON (API CKAN) | 2021-06 a 2025-12 | P3 |
| Gastos por unidade | https://dados.unb.br/dataset/gastos-por-unidade | JSON (API CKAN) | 2021-07 a 2025-12 | Contexto (gastos por unidade) |
| Unidades acadêmicas | https://dados.unb.br/dataset/unidades-academicas | JSON (API CKAN) | 2022-02 a 2025-12 | P2, P3 (dimensão de unidade) |
| Requisições de serviços | https://dados.unb.br/dataset/requisicoes-de-servicos | JSON (API CKAN) | 2021-07 a 2025-12 | Contexto (demanda das unidades) |
| Preços de mercado *(futura)* | Mercado Livre — API pública de busca | JSON | Coleta semanal prevista | P4 |

**Volume bruto:** 453 arquivos, 1.182.543 registros, cerca de 813 MB. Os empenhos são 91% desse volume.

## 3. Escolha do banco de dados

**Banco escolhido:** PostgreSQL 16, em Docker, com o esquema versionado pelo Flyway 10.

**Principais argumentos:**
- **Workload:** carga em lote mensal e leitura analítica (filtros por período, almoxarifado e unidade; agregações por ano e mês). Não há exigência de tempo real. A meta é de até 2 s por consulta interativa e até 5 min para a carga mensal.
- **Modelo de dados:** os dados são relacionais, com muitas chaves estrangeiras entre unidade, almoxarifado, material, empenho e credor. A integridade referencial precisa ser garantida pelo banco.
- **Volume, custo e operação:** cerca de 150 mil linhas e 40 MB no banco. O PostgreSQL é gratuito, sobe com um único `docker compose up --build` e a equipe já domina SQL e modelagem relacional.
- **Modelagem (ADR 1):** os cadastros são atualizados no lugar; o estoque e as cotações são *snapshots insert-only*, porque a fonte não publica log de eventos.
- **Alternativas descartadas:**
  - Bancos NoSQL e de documentos, porque os dados são fortemente relacionais.
  - Soluções em nuvem paga, porque não cabem no orçamento e no prazo da disciplina.

**ADRs:**
- [ADR 1 — Modelo transacional *current-state* com snapshots *append-only*](docs/adr/adr-1.md)
- [ADR 0003 — Queda de volume entre meses vira aviso, não recusa](docs/adr/0003-validacao-de-volume-na-carga_1.md)

A justificativa da escolha do SGBD está em [Diário — Semana 03](docs/diario/semana-03.md).

## 4. Pipeline de dados (versão atual)

**Diagrama:** [Arquitetura do banco v1.1](docs/assets/diagramas/Arquitetura%20do%20banco.v1.1.png). A explicação de cada camada está em [Pipeline e arquitetura em camadas](docs/arquitetura-em-camadas.md).

**Etapas:**

| Etapa | O que faz | Ferramenta / script |
|---|---|---|
| Ingestão | Busca os 5 datasets na API CKAN do dados.unb.br, com até 5 tentativas por arquivo | `codigos/baixar_dados.py` (serviço `ingest`) |
| Armazenamento bruto (Bronze) | Grava os arquivos exatamente como vieram, com `manifesto.json` (URL, data no portal, tamanho e sha256) | `dados/bruto/<dataset>/` |
| Transformação | Limpa texto e números, deduplica cadastros e gera o termo de busca de cada material | `codigos/normalizar.py` |
| Carga (Prata) | Grava no PostgreSQL. Cada arquivo entra em uma transação, o sha256 evita carga duplicada e linhas inválidas vão para `carga_rejeitado` | `codigos/carregar.py` + Flyway (`db/migrations/V1__esquema_inicial.sql`) |
| Consumo | Consultas SQL sobre estoque e almoxarifado | [`docs/consultas.md`](docs/consultas.md) |

**Status atual:**

| Item | Situação |
|---|---|
| Ambiente Docker Compose (`db`, `migrate`, `ingest`) subindo do zero | ✅ |
| Download dos 5 datasets, com manifesto e sha256 | ✅ 453 arquivos, 0 falhas |
| Carga no PostgreSQL | ✅ 181 arquivos distintos, 0 linhas rejeitadas, 40 meses de estoque (41.116 linhas) |
| Camada Ouro (modelo estrela `FatoAvaliacaoEstoque`) | ⏳ prevista para a E3 |
| Coleta de preços do Mercado Livre gravada no banco | ⏳ script existe; `cotacao_online` ainda vazia |
| Captura de mudanças (CDC) | ⏳ prevista |
| Painéis e relatórios | ⏳ prevista para a E4 |

## 5. O que mudou desde a Release 1

**Adicionado**
- Site da documentação em Docsify, publicado no GitHub Pages:
  - diagrama ER e modelo relacional v1.2;
  - dicionário de dados;
  - diagrama de arquitetura Bronze/Prata/Ouro.
- Backlog do produto, com prioridade MoSCoW por entrega.
- Novas páginas de documentação:
  - domínio e pergunta de gestão;
  - fontes e histórico da origem;
  - caracterização da carga;
  - arquitetura em camadas;
  - consultas.
- ADR 0003 — validação de volume na carga.
- Diário de bordo das semanas 01 a 06 e registro de uso de IA.

**Alterado**
- A pergunta de gestão foi refinada para a taxa anualizada de aumento do preço unitário (2021–2025). A comparação com o mercado passou a ser um recorte complementar.
- A queda de volume entre meses deixou de recusar o arquivo e passou a gerar um aviso.

**Corrigido**
- 30 meses de estoque (11/2022 a 12/2025) eram recusados pela trava de queda de volume e agora estão carregados.
- O workflow de deploy não rodava por causa de um erro de digitação no nome da pasta (`.github/worflows` → `.github/workflows`).

**Limitações conhecidas**
- **Queda do estoque em 11/2022:** o volume cai de ~1.800 para ~830 linhas e se concentra no almoxarifado PRC. A causa ainda não foi confirmada com o portal. Comparações de quantidade de itens antes e depois dessa data precisam de ressalva.
- **Empenhos:** todos os arquivos têm exatamente 10.000 registros, o que sugere um limite de exportação do portal.
- **Empenho ↔ material:** os dados de origem não trazem uma chave que ligue empenhos a materiais. Por isso a P3 é respondida só em nível de credor.
