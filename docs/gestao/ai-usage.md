# AI-USAGE.md — Squad [13]

Registro de uso de assistentes e agentes de IA no Projeto Integrado.

Este arquivo cumpre a [Política de Uso de IA](https://unb-bd2.github.io/Disciplina/uso-de-ia/)
da disciplina. Ele não é confissão nem formalidade: é o mesmo tipo de registro
que um ADR faz para decisões de arquitetura.

**Duas regras de forma.** Escreva **no momento do uso**, não na véspera da
Entrega — registro reconstruído de memória sai impreciso, e imprecisão aqui é o
que a política pune. E versione junto com o código: uma entrada por commit
relevante é melhor que um resumo mensal.

**Não precisa registrar** autocompletar de editor, correção ortográfica ou
tradução. Registre o que produziu artefato ou mudou uma decisão.

---

## Entradas

### 2026-09-12 — [o que estava sendo feito]

- **Ferramenta:** [Claude, opus 5.5]
- **Onde:** [codigos/baixar_dados.py]
- **O que foi pedido:** [Criar um script para baixar os dados do site da UnB que iremos usar.]
- **O que foi aproveitado:** [Tudo.]
- **Como foi verificado:** [Testamos nas nossas máquinas para ver se as instruções funcionavam]
- **Quem revisou:** [Samara Letícia]

### 2026-09-28 — [o que estava sendo feito]

- **Ferramenta:** [Claude, opus 5.5]
- **Onde:** [README.md]
- **O que foi pedido:** [Criar um readme para o projeto que explique como rodar o docker do projeto.]
- **O que foi aproveitado:** [Tudo.]
- **Como foi verificado:** [Testamos nas nossas máquinas para ver se as instruções funcionavam]
- **Quem revisou:** [Samara Letícia]

### 2026-09-28 — levantamento do que faltava para a E1

- **Ferramenta:** Claude (opus 5.5), em modo agente com acesso de leitura à pasta do repositório
- **Onde:** nenhum arquivo; resultado usado para planejar a E1
- **O que foi pedido:** comparar o repositório com o enunciado da E1 e listar o que faltava.
- **O que foi aproveitado:** a lista de pendências (migrações, carga no banco, falha silenciosa no download, pergunta de gestão, ADR, diário).
- **Como foi verificado:** conferimos item a item com a página da E1.
- **Quem revisou:** Samara Letícia


### 2026-10-19 — backlog do produto

- **Ferramenta:** Claude (sonnet 5.5), em modo agente com acesso ao repositório
- **Onde:** docs/gestao/backlog.md e docs/_sidebar.md
- **O que foi pedido:** escrever o backlog do produto (requisitos do que esperamos ter construído no fim da disciplina), a partir da pergunta de gestão, das fontes de dados, do que o repositório já tem e dos enunciados da E2, E3 e E4. Uma primeira versão tratava só do aceite da E2 e foi descartada.
- **O que foi aproveitado:** a estrutura (histórias, requisitos de dados e não funcionais, fora do escopo) e a situação de cada item. As prioridades e a divisão em requisitos são sugestões da ferramenta, a revisar pela Squad.
- **Como foi verificado:** a situação de cada item foi conferida contra o repositório e o banco; as etapas E2, E3 e E4 foram conferidas com os enunciados colados pela Squad; a pergunta de gestão e o tema do quinto ADR ainda precisam ser definidos.
- **Quem revisou:** Magno

### 2026-10-19 — subir o ambiente Docker no GitHub Codespaces
- **Ferramenta:** Claude (opus 5.5), no Cowork, como assistente de diagnóstico; os comandos foram executados por nós no terminal
- **Onde:** nenhum arquivo do repositório; ambiente de execução
- **O que foi pedido:** ajuda para rodar inspecionar_bruto.py e medir_adr0001.py. Os problemas, em ordem:
No Windows, rodar os scripts com o Python local falhava (python3 inexistente e falta do psycopg). A orientação foi rodar pelo Docker, como o README indica.
O Docker Desktop não abria (Virtualization support not detected). Seguimos a sugestão de usar o GitHub Codespaces em vez de mexer na BIOS.
No Codespaces, o primeiro docker compose up falhou porque o Docker ainda estava iniciando. Depois disso, o Flyway (migrate) ficou preso em Connect timed out tentando falar com o db.
A rede do Compose foi recriada com docker compose down e um novo docker compose up --build.
- **O que foi aproveitado:**
o diagnóstico (comandos colados juntos se atropelando; rede do Compose criada com o Docker ainda iniciando);
a sequência de comandos down/up;
o hábito de rodar um comando por vez e salvar saídas em arquivo (> medicao.txt).
- **Como foi verificado:** pelos logs: migrate-1 exited with code 0 com a migração V1 aplicada e o download dos 453 arquivos sem falhas.
- **Quem revisou:** Samara Letícia

### 2026-11-08 — busca semântica (embeddings + pgvector) para candidatos CATMAT

- **Ferramenta:** Claude (modelo configurado: claude-opus-5-5), em modo agente, num ambiente de nuvem com cópia do repositório; os commits da branch `busca-semantica-catmat` foram feitos pelo agente com a autoria de quem pediu
- **Onde:** `db/Dockerfile`, `db/migrations/V2__semantica_pgvector.sql` e `V3__semantica_sem_indice_hnsw.sql`, `codigos/semantica/`, `codigos/medir_adr0005.py`, `codigos/validacao_e_cobertura_precos.py` (extração das regras de especificação, sem mudar a lógica), `docker-compose.yml`, `.env.example`, `codigos/requirements.txt`, `testes/`, `docs/semantica.md`, ADR 0005, README
- **O que foi pedido:** avaliar o repositório e implementar, em commits incrementais, a normalização das descrições, os embeddings, o armazenamento e a busca por cosseno no PostgreSQL com pgvector, a integração com raw/bronze/prata (branch `configuracao_do_dbt`) e com o Docker Compose, com testes e documentação
- **O que foi aproveitado:** [a preencher pela Squad depois da revisão do PR]
- **Como foi verificado:** pelo agente, no ambiente dele: 143 testes automatizados (PostgreSQL 16 + pgvector 0.8.7 compilado localmente), incluindo a normalização sobre as 2.327 descrições reais de `seeds/materiais_normalizados.csv` (que revelou e levou a corrigir um erro com entidades HTML em maiúsculas); fluxo raw → dbt build → `python -m semantica` sobre a amostra escrita à mão; teste da biblioteca sentence-transformers real com um modelo de pesos aleatórios (o modelo real não pôde ser baixado); medições do ADR 0005 com vetores aleatórios no volume do domínio (que levaram a trocar o índice HNSW pela busca exata). **Não verificado:** build das imagens Docker, execução com o modelo real e com os dados reais, qualidade dos candidatos
- **Quem revisou:** [pendente]

### 2026-11-10 — busca híbrida, decisões por agentes de IA e compras públicas

- **Ferramenta:** Claude Code (claude-opus-5-5), em modo agente na máquina de magnluiz; nas decisões de correspondência, subagentes Claude Sonnet (rodada de 08/11/2026)
- **Onde:** `db/migrations/V4__semantica_busca_hibrida.sql` e `V5__semantica_revisao_por_material.sql`, `codigos/semantica/` (`reordenacao.py`, `decisoes.py`, `medir_referencia.py`, `decisoes/`, `referencia/`, ajustes em `correspondencia.py`, `fontes.py` e `__main__.py`), `codigos/inserir/baixar_compras.py`, `codigos/inserir/baixar_catalogo_catmat.py` (novas tentativas), `codigos/banco_de_dados/inserir_dados_na_camada_raw.py`, `models/` (compras), `dbt_project.yml`, `docker-compose.yml`, `testes/`, ADR 0006 e documentação
- **O que foi pedido:** levar para a estrutura da `main` (depois do PR #11) o trabalho da branch local `feature/banco-vetorial-pgvector`: reordenação híbrida com rapidfuzz, as decisões de correspondência e a ingestão das compras públicas nas camadas raw, bronze e prata
- **Decisões de correspondência:** os 2.394 materiais da carga anterior foram decididos por agentes Claude Sonnet em lotes de ~100, com os candidatos da busca híbrida; cada lote tinha ~6 materiais do conjunto de referência (150 materiais rotulados pelo Claude Opus, com 7 rótulos corrigidos após inspeção) escondidos como controle. Concordância de 80% (119/149). As decisões foram convertidas para a chave da Prata nova (`descricao_normalizada`), resultando em 2.306 materiais; materiais que a normalização uniu tiveram os códigos somados
- **O que foi aproveitado:** [a preencher pela Squad depois da revisão do PR]
- **Como foi verificado:** 174 testes automatizados com PostgreSQL + pgvector (os 143 anteriores, 3 ajustados para fixar o método por cosseno, e 31 novos); cadeia completa do `docker compose` num banco vazio com dados reais (CATMAT completo, modelo real): dbt 79/79 e 14/14, busca híbrida em 2.306 materiais, importação das 2.306 decisões sem recusa, 41.514 compras na Prata; medição no conjunto de referência (`python -m semantica.medir_referencia`).
- **Quem revisou:** Magno Luiz


### AAAA-MM-DD — [o que estava sendo feito]

- **Ferramenta:**
- **Onde:**
- **O que foi pedido:**
- **O que foi aproveitado:**
- **Como foi verificado:**
- **Quem revisou:**

---
