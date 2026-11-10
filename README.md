# SIGMA-UnB

O SIGMA-UnB é uma plataforma de dados para apoiar a gestão de materiais e as decisões de compra da Universidade de Brasília. A análise proposta reúne três fontes:

| Fonte | Papel |
| :---: | :---- |
| Estoque do almoxarifado da UnB | Materiais, almoxarifados, saldos e preços registrados. |
| Catálogo de Materiais (CATMAT) | Códigos e descrições para apoiar a identificação dos itens. |
| Pesquisa de preços públicos | Registros de preços observados em compras da Administração Pública. |

> **Pergunta de gestão:** _Para quais materiais do estoque da UnB é possível encontrar um item correspondente no CATMAT e em compras públicas comparáveis, e quais apresentam as maiores diferenças entre o preço registrado no estoque e os preços dessas compras, por almoxarifado e período?_

A comparação depende de validar a correspondência do item e a equivalência de unidade e período. Os preços de compras públicas são referências de compras, não cotações de lojas nem prova, por si só, de sobrepreço.

O banco e o pipeline Docker descritos abaixo podem ser executados localmente, sem instalar PostgreSQL nem Python na máquina. O Compose baixa o estoque da UnB e o catálogo CATMAT, transforma esses dados e gera candidatos de correspondência semântica. A consulta de preços públicos na API do Compras.gov.br permanece exploratória e fora do pipeline automatizado.

---

## Sumário

- [O que sobe](#o-que-sobe)
- [Pré-requisitos](#pré-requisitos)
- [Subir no Windows](#subir-no-windows)
- [Subir no Linux](#subir-no-linux)
- [O que deve aparecer](#o-que-deve-aparecer)
- [Verificar que funcionou](#verificar-que-funcionou)
- [Comandos do dia a dia](#comandos-do-dia-a-dia)
- [Configuração](#configuração)
- [Estrutura do repositório](#estrutura-do-repositório)
- [Problemas comuns](#problemas-comuns)
- [Estado atual](#estado-atual)

---

## O que sobe

Um único comando sobe estes serviços, nesta ordem:

| Serviço | O que faz | Termina? |
| ------- | --------- | -------- |
| `db` | PostgreSQL 16 com a extensão pgvector (imagem construída em `db/Dockerfile`). | Não, fica rodando |
| `migrate` | Flyway: aplica os arquivos `db/migrations/V*.sql` em ordem, a partir do banco vazio. | Sim |
| `ingest` | Python: baixa o estoque e o catálogo CATMAT e grava no schema `raw`. | Sim |
| `transformar` | dbt: `raw` → `bronze` → `prata`, com os testes de dados (`dbt build`). | Sim |
| `semantica` | Python: embeddings das descrições, candidatos CATMAT para cada material (busca híbrida: cosseno + trigramas + rapidfuzz) e importação das decisões sugeridas por agentes de IA ([detalhes](docs/dados-e-pipeline/semantica.md)). | Sim |
| `compras` | Python: baixa as compras públicas (Compras.gov.br) dos itens CATMAT aprovados e grava em `raw.compras`. | Sim |
| `transformar_ouro` | dbt: compras (`bronze.compras`, `prata.compra_publica`), snapshot da correspondência (SCD tipo 2) e camada ouro (fato e dimensões). | Sim |
| `painel` | Streamlit em http://localhost:8501: maiores diferenças entre o preço do estoque e o das compras públicas, por almoxarifado e mês ([camada ouro](docs/dados-e-pipeline/camada-ouro.md)). | Não, fica rodando |

Cada serviço só começa quando o anterior termina com sucesso: `db` → `migrate` → `ingest` → `transformar` → `semantica` → `compras` → `transformar_ouro`. O `painel` lê a camada ouro e fica no ar.

Para rodar agendado, com retry por etapa e backfill por mês, use a orquestração com Dagster ([orquestração](docs/dados-e-pipeline/orquestracao.md)): `DAGSTER_HOME=$PWD/orquestracao/instancia dagster dev -f orquestracao/definicoes.py`.

O catálogo CATMAT tem centenas de páginas e o `semantica` baixa um modelo de linguagem (~0,5 GB) e calcula os vetores na CPU. Para um teste rápido, use `CATMAT_MAX_PAGINAS=5` no `.env`.

---

## Pré-requisitos

| | Windows 10/11 | Linux |
|---|---|---|
| **Docker** | [Docker Desktop](https://docs.docker.com/desktop/setup/install/windows-install/) com backend WSL 2 | [Docker Engine](https://docs.docker.com/engine/install/) |
| **Docker Compose** | Já vem com o Docker Desktop | Plugin `docker-compose-plugin` (comando `docker compose`, com espaço) |
| **Git** | [Git for Windows](https://git-scm.com/download/win) | `git` do gerenciador de pacotes |
| **Internet** | Para baixar imagens, dados da UnB e CATMAT e o modelo de embeddings | Idem |

Não é preciso ter Python nem PostgreSQL instalados.

---

## Subir no Windows

Use o **PowerShell**.

1. **Abra o Docker Desktop** e espere o ícone indicar *Engine running*. Sem ele aberto, nenhum comando `docker` funciona.

2. **Clone o repositório e entre na pasta:**

   ```powershell
   git clone https://github.com/samarawwleticia/SIGMA-UnB.git
   cd SIGMA-UnB
   ```

3. **(Opcional) Crie o `.env`** — só se quiser trocar senha ou porta (veja [Configuração](#configuração)):

   ```powershell
   Copy-Item .env.example .env
   ```

4. **Suba tudo:**

   ```powershell
   docker compose up --build
   ```

---

## Subir no Linux

1. **Confirme que o Docker está rodando:**

   ```bash
   docker info > /dev/null && echo "Docker OK"
   ```

   Se der erro de permissão (`permission denied ... docker.sock`), adicione seu usuário ao grupo `docker` e abra um novo terminal:

   ```bash
   sudo usermod -aG docker $USER
   ```

   (Ou prefixe os comandos abaixo com `sudo`.)

2. **Clone o repositório e entre na pasta:**

   ```bash
   git clone https://github.com/samarawwleticia/SIGMA-UnB.git
   cd SIGMA-UnB
   ```

3. **(Opcional) Crie o `.env`:**

   ```bash
   cp .env.example .env
   ```

4. **Suba tudo:**

   ```bash
   docker compose up --build
   ```

   > Use `docker compose` (com espaço). O antigo `docker-compose` (com hífen) é a versão 1, descontinuada.

---

## O que deve aparecer

Os comandos são os mesmos nos dois sistemas daqui em diante. No terminal, cada linha vem prefixada pelo serviço (`db-1 |`, `migrate-1 |`, `ingest-1 |`):

1. Download das imagens e build do container Python — **só na primeira vez**, pode levar alguns minutos.
2. `db-1 | ... database system is ready to accept connections`
3. `migrate-1 | ...` — o Flyway lista as migrações aplicadas, e depois `migrate-1 exited with code 0`.
4. `ingest-1 | ...` — baixa os arquivos de estoque e do CATMAT, inicializa o schema `raw` e carrega os dados.
5. `transformar-1 | ...` — executa `dbt deps` e `dbt build`.
6. `semantica-1 | ...` — calcula embeddings e candidatos CATMAT; na primeira execução baixa o modelo.
7. **O terminal fica parado mostrando os logs do banco.** Isso é esperado: o banco continua rodando. Para parar, `Ctrl+C`.

Para subir em segundo plano e liberar o terminal, use `docker compose up --build -d` e acompanhe com `docker compose logs -f`.

---

## Verificar que funcionou

**Estado dos serviços** — `migrate`, `ingest`, `transformar` e `semantica` devem aparecer como `Exited (0)` e `db` como `Up (healthy)`:

```bash
docker compose ps -a
```

**Arquivos baixados** — devem existir `dados/estoque/` e `dados/catmat/`:

| Windows (PowerShell) | Linux |
|---|---|
| `Get-ChildItem dados\estoque, dados\catmat` | `ls -lh dados/estoque dados/catmat` |

**Banco e migrações** — abra o `psql` dentro do container:

```bash
docker compose exec db psql -U sigma -d sigma
```

Dentro do `psql`:

```sql
\dt *.*                                                  -- lista tabelas de todos os schemas
SELECT count(*) FROM raw.estoque;                        -- documentos JSON de estoque carregados
SELECT count(*) FROM raw.catmat;                         -- documentos JSON do catálogo carregados
SELECT count(*) FROM bronze.estoque;                     -- registros de estoque transformados
SELECT count(*) FROM prata.material;                      -- materiais normalizados
SELECT count(*) FROM semantica.candidato_catmat;          -- candidatos gerados para revisão
SELECT version, description, success
  FROM flyway_schema_history ORDER BY installed_rank;    -- migrações aplicadas (existe após a 1ª)
\q                                                       -- sai
```

`raw.estoque` e `raw.catmat` contam arquivos/documentos JSON; `bronze.estoque` conta registros expandidos. Para conectar de fora (DBeaver, pgAdmin, VS Code): host `localhost`, porta publicada (por padrão `5432`), banco e usuário `sigma`, senha configurada no `.env`.

---

## Comandos do dia a dia

| Para…                                           | Comando |
|-------------------------------------------------|---------|
| Subir tudo (reconstruindo o que mudou)          | `docker compose up --build` |
| Subir em segundo plano                          | `docker compose up --build -d` |
| Ver logs de um serviço                          | `docker compose logs -f ingest` |
| Reexecutar a carga e etapas seguintes           | `docker compose up --build ingest transformar semantica compras transformar_ouro` |
| Aplicar migrações novas                         | `docker compose run --rm migrate` |
| Recalcular só a busca semântica (incremental)   | `docker compose run --rm semantica` |
| Exportar a fila de revisão de candidatos CATMAT | `docker compose run --rm semantica python -m semantica fila` (gera `dados/semantica/fila_revisao.csv`) |
| Registrar a revisão de um candidato             | `docker compose run --rm semantica python -m semantica revisar --material ma0001 --codigo 123456 --decisao equivalente --revisor "Nome"` |
| Importar decisões revisadas numa planilha (CSV) | `docker compose run --rm semantica python -m semantica importar --arquivo ARQUIVO.csv --revisor "Nome"` (formato em [semantica.md](docs/dados-e-pipeline/semantica.md#8-decisões-em-lote-agentes-de-ia-e-planilhas)) |
| Medir a busca no conjunto de referência         | `docker compose run --rm semantica python -m semantica.medir_referencia` |
| Rebaixar e recarregar só as compras             | `docker compose up --build compras transformar_ouro` |
| Medições do ADR 0005 (exata x HNSW, vetores reais) | `docker compose run --rm semantica python medir_adr0005.py real` |
| Parar (mantém os dados do banco)                | `docker compose down` |
| **Apagar o banco e recomeçar do zero**          | `docker compose down -v` |

`down -v` apaga o volume do Postgres. Use-o para testar que a plataforma sobe do zero, como numa máquina limpa.

---

## Configuração

Todas as variáveis têm valor padrão, então **o `.env` é opcional**. Crie-o a partir de `.env.example` só para mudar algo:

| Variável            | Padrão  | Para que serve |
|---------------------|---------|----------------|
| `HOST_DO_BANCO` | `localhost` | Host para conexões iniciadas fora do Compose (dentro do Compose é `db`) |
| `PORTA_DO_BANCO` | `5432` | Porta publicada na sua máquina (dentro do Compose é sempre `5432`) |
| `NOME_DO_BANCO` | `sigma` | Nome do banco |
| `USUARIO_DO_BANCO` | `sigma` | Usuário |
| `SENHA_DO_BANCO` | `sigma` | Senha |
| `CATMAT_MAX_PAGINAS` | vazio (todas) | Limita as páginas do CATMAT baixadas pelo `ingest` (500 itens cada) |
| `SEMANTICA_MODELO`  | `intfloat/multilingual-e5-small` | Modelo de embeddings (384 dimensões) |
| `SEMANTICA_TOP_K`   | `10`    | Candidatos CATMAT guardados por material |
| `SEMANTICA_LIMIAR`  | vazio   | Similaridade mínima para guardar um candidato (sem valor calibrado ainda) |
| `SEMANTICA_BUSCA_EXATA` | vazio | `1` = proíbe índice HNSW (hoje não há índice: a busca já é exata; ver ADR 0005) |

O Compose usa esses nomes em português para todos os serviços. `POSTGRES_DB`,
`POSTGRES_USER` e `POSTGRES_PASSWORD` aparecem apenas como nomes internos
exigidos pela imagem oficial do PostgreSQL; seus valores vêm das variáveis
portuguesas acima.

O `.env` está no `.gitignore` e não deve ser versionado.

---

## Estrutura do repositório

```
SIGMA-UnB/
├── docker-compose.yml          # sobe db, migrate, ingest, transformar, semantica, compras e transformar_ouro
├── .env.example                # modelo de configuração
├── codigos/
│   ├── Dockerfile              # imagem Python usada pelas etapas ingest e dbt
│   ├── requirements.txt        # dependências Python
│   ├── normalizar.py           # funções de limpeza de texto e números
│   ├── medir_adr0001.py        # medições do ADR 0001
│   ├── medir_adr0005.py        # medições do ADR 0005 (busca exata x HNSW)
│   ├── semantica/              # busca semântica: normalização, embeddings, pgvector, busca híbrida, decisões
│   ├── inserir/                # download do estoque, do CATMAT e das compras públicas
│   ├── banco_de_dados/         # carga dos arquivos na camada raw
│   └── validacao_e_cobertura_precos.py # exploração da API de preços públicos
├── db/
│   ├── Dockerfile              # postgres:16-alpine + pgvector
│   └── migrations/             # V1__descricao.sql, V2__..., aplicados em ordem pelo Flyway
├── docs/                       # site estático Docsify
│   ├── projeto/                # domínio, fontes, execução e glossário
│   ├── gestao/                 # backlog, diário e uso de IA
│   ├── adr/                    # decisões arquiteturais
│   ├── modelagem/              # diagramas, modelos e dicionário
│   ├── dados-e-pipeline/       # ingestão, camadas, consultas e validação
│   ├── testes/                 # testes de viabilidade
│   ├── assets/                 # imagens e diagramas
│   ├── home.md                 # página inicial do Docsify
│   ├── _sidebar.md             # navegação
│   └── index.html              # configuração do Docsify
├── modelagem/                  # diagrama ER, modelo relacional e fonte .drawio
├── AI-USAGE.md                 # aponta para docs/gestao/ai-usage.md
└── dados/                      # criado na execução; ignorado pelo git
```

**Convenção das migrações:** `V<número>__<descrição>.sql` (dois sublinhados), por exemplo `V1__esquema_inicial.sql`. Uma migração já aplicada **nunca** é editada — qualquer mudança vira um arquivo novo com o próximo número.

---

## Problemas comuns

**Nada acontece / `error during connect` / `Cannot connect to the Docker daemon`**
O Docker não está rodando. No Windows, abra o Docker Desktop e espere *Engine running*. No Linux, `sudo systemctl start docker`.

**`port is already allocated` ou o `db` não fica pronto**
Já existe algo usando a porta 5432 (geralmente um Postgres instalado na máquina). Crie o `.env` e troque a porta, por exemplo `PORTA_DO_BANCO=5433`. Para descobrir quem ocupa a porta:

| Windows (PowerShell) | Linux |
|---|---|
| `netstat -ano \| findstr :5432` | `sudo ss -ltnp \| grep 5432` |

**`ingest` mostra falha ao baixar dados**
Confira a conexão com a internet e os logs do serviço: `docker compose logs ingest`. CATMAT preserva o cache de páginas em `dados/catmat/cache_catmat_json`, que pode ser reutilizado na próxima execução.

**`ingest` sai com código diferente de zero**
Confira a mensagem do serviço `ingest`; a etapa seguinte (`transformar`) só é executada após a carga terminar com sucesso.

**`migrate` sai com erro de checksum**
Uma migração já aplicada foi editada. Desfaça a edição e crie uma migração nova — ou, só em desenvolvimento, recomece com `docker compose down -v`.

**Windows: erro de montagem de volume em `dados/`**
Confira em *Docker Desktop → Settings → Resources → File sharing* (ou na integração WSL) se a unidade onde está o repositório está compartilhada. Clonar dentro da sua pasta de usuário costuma evitar o problema.

**Mudei um arquivo Python e nada mudou**
Rode com `--build` para reconstruir a imagem: `docker compose up --build`.

---

## Estado atual

| Item | Situação |
|---|---|
| Banco PostgreSQL em Docker | ✅ |
| Migrações versionadas (Flyway) | ✅ `V1__esquema_inicial.sql`, `V2__semantica_pgvector.sql`, `V3__semantica_sem_indice_hnsw.sql`, `V4__semantica_busca_hibrida.sql`, `V5__semantica_revisao_por_material.sql` |
| Ingestão idempotente por hash em `raw.estoque` e `raw.catmat`, seguida da transformação dbt | ✅ |
| Download do estoque e do CATMAT, transformação dbt e candidatos semânticos | ✅ Integrados ao Compose |
| Camada ouro: fato com grão declarado, dimensões e SCD tipo 2 da correspondência (dbt snapshot) | ✅ [Camada ouro](docs/dados-e-pipeline/camada-ouro.md), [ADR 0007](docs/adr/0007-modelo-estrela-para-comparacao-de-precos.md) |
| Testes de volume, distribuição e domínio; freshness e SLA | ✅ `tests/`, `seeds/excecoes_qualidade.csv`, `dbt source freshness`, `ouro.monitor_atualizacao` |
| Consulta otimizada pelo plano de execução | ✅ [EXPLAIN (ANALYZE, BUFFERS) antes e depois](docs/dados-e-pipeline/consultas.md) |
| Orquestração agendada, retry e backfill | ✅ Dagster ([orquestração](docs/dados-e-pipeline/orquestracao.md)) |
| Painel analítico | ✅ Serviço `painel` (Streamlit, http://localhost:8501) |
| Compras públicas dos itens CATMAT aprovados (API Compras.gov.br) | ✅ Serviços `compras` e `transformar_ouro`: `raw.compras` → `bronze.compras` → `prata.compra_publica` |
| ADR da E1 ([`docs/adr/adr-1.md`](docs/adr/adr-1.md)) | ✅ |
| Diário ([`docs/gestao/diario/`](docs/gestao/diario/)) | ✅ |
| Registro de uso de IA ([`docs/gestao/ai-usage.md`](docs/gestao/ai-usage.md)) | ✅ |
| Cotações de lojas online | Fora da pergunta de gestão atual |
| Candidatos CATMAT por similaridade semântica (pgvector) | ✅ Execução real gerou 23.270 candidatos para 2.327 materiais; revisão e calibração do limiar pendentes ([documentação](docs/dados-e-pipeline/semantica.md)) |
