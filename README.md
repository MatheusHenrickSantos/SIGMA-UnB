# SIGMA-UnB

Plataforma de dados construída sobre os **dados abertos da Universidade de Brasília** ([dados.unb.br](https://dados.unb.br)) — estoque do almoxarifado, unidades acadêmicas, gastos por unidade, empenhos e requisições de serviços — como Projeto Integrado da disciplina.

> **Pergunta de gestão:** _Quais materiais do almoxarifado da UnB tiveram o preço unitário registrado acima do preço de mercado em lojas online entre 2026 e 2027, em quais almoxarifados, e quanto a UnB gastaria a menos se tivesse pago o preço de mercado?._

Tudo roda localmente em Docker Compose, sem instalar Postgres nem Python na máquina.

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

Um único comando sobe cinco serviços, nesta ordem:

| Serviço   | O que faz                                                                                              | Termina? |
|-----------|--------------------------------------------------------------------------------------------------------|----------|
| `db`      | PostgreSQL 16: o banco transacional (OLTP).                                                            | Não, fica rodando |
| `migrate` | Flyway: aplica os arquivos `db/migrations/V*.sql` em ordem, a partir do banco vazio.                   | Sim |
| `ingest`  | Python: baixa os 5 datasets do portal da UnB para `dados/bruto/` e carrega no banco.                    | Sim |
| `minio`   | MinIO: armazenamento compatível com S3, o data lake. Sobe em paralelo com o banco.                     | Não, fica rodando |
| `extract` | Python (E2): envia o bruto para a bronze, extrai o lote e captura as mudanças do Postgres em Parquet, e verifica o resultado. | Sim |

`migrate` só começa quando o banco está pronto, `ingest` só começa se todas as migrações tiverem sido aplicadas com sucesso, e `extract` só começa depois do `ingest` terminar e do MinIO estar pronto.

### Os dois caminhos da E2

O `extract` leva o dado do Postgres até a camada **bronze** do bucket `sigma-lake`, em Parquet, por dois caminhos de natureza diferente:

| Caminho | Script | O que grava | Onde |
|---|---|---|---|
| Bruto do portal (ELT) | `enviar_bruto.py` | Os arquivos originais, sem alteração | `bronze/portal/<dataset>/<sha256>/` |
| 1. Lote | `extrair_lote.py` | Foto completa de cada tabela | `bronze/lote/<tabela>/data_extracao=AAAA-MM-DD/` |
| 2. Captura de mudanças | `capturar_mudancas.py` | Só as linhas alteradas desde a última execução, com `_operacao` (`insert`/`update`) | `bronze/cdc/<tabela>/data_captura=AAAA-MM-DD/` |

Por que assim: [ADR 2](docs/adr/adr-2.md) (ELT), [ADR 3](docs/adr/adr-3.md) (Parquet no MinIO) e [ADR 4](docs/adr/adr-4.md) (CDC por consulta).

---

## Pré-requisitos

| | Windows 10/11 | Linux |
|---|---|---|
| **Docker** | [Docker Desktop](https://docs.docker.com/desktop/setup/install/windows-install/) com backend WSL 2 | [Docker Engine](https://docs.docker.com/engine/install/) |
| **Docker Compose** | Já vem com o Docker Desktop | Plugin `docker-compose-plugin` (comando `docker compose`, com espaço) |
| **Git** | [Git for Windows](https://git-scm.com/download/win) | `git` do gerenciador de pacotes |
| **Internet** | Para baixar as imagens e os dados da UnB | Idem |

Não é preciso ter Python nem PostgreSQL instalados.

---

## Subir no Windows

Use o **PowerShell**.

1. **Abra o Docker Desktop** e espere o ícone indicar *Engine running*. Sem ele aberto, nenhum comando `docker` funciona.

2. **Clone o repositório e entre na pasta:**

   ```powershell
   git clone https://github.com/samarawwleticia/SIIGMA-UnB.git
   cd SIIGMA-UnB
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
   git clone https://github.com/samarawwleticia/SIIGMA-UnB.git
   cd SIIGMA-UnB
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
4. `ingest-1 | Buscando datasets no portal de dados abertos da UnB...` e uma linha `baixando: ...` por arquivo. Na primeira vez são cerca de 850 MB (os empenhos são a maior parte); o portal às vezes responde `502` e o script tenta de novo sozinho.
5. `ingest-1 | [unidades]`, `[estoque]`, ... com uma linha `N gravadas, M rejeitadas` por arquivo carregado, a tabela **Linhas por tabela** e `ingest-1 exited with code 0`. A carga completa leva alguns minutos.
6. `extract-1 | bronze/portal: N arquivo(s) enviado(s)`, depois a tabela da extração em lote, a tabela da captura de mudanças (na primeira vez tudo aparece como `insert`) e, no fim, `Tudo certo: lote e CDC batem com o Postgres.` e `extract-1 exited with code 0`.
7. **O terminal fica parado mostrando os logs do banco e do MinIO.** Isso é esperado: o banco continua rodando. Para parar, `Ctrl+C`.

Para subir em segundo plano e liberar o terminal, use `docker compose up --build -d` e acompanhe com `docker compose logs -f`.

---

## Verificar que funcionou

**Estado dos serviços** — `migrate`, `ingest` e `extract` devem aparecer como `Exited (0)`, e `db` e `minio` como `Up (healthy)`:

```bash
docker compose ps -a
```

**Arquivos baixados** — deve existir a pasta `dados/bruto/` com uma subpasta por dataset e o `manifesto.json` (url, data no portal e sha256 de cada arquivo):

| Windows (PowerShell) | Linux |
|---|---|
| `Get-ChildItem dados\bruto` | `ls -lh dados/bruto` |

**Banco e migrações** — abra o `psql` dentro do container:

```bash
docker compose exec db psql -U sigma -d sigma
```

Dentro do `psql`:

```sql
\dt                                                      -- lista as tabelas
SELECT count(*) FROM estoque_saldo;                      -- deve ter dezenas de milhares de linhas
SELECT dataset, count(*), sum(linhas_gravadas), sum(linhas_rejeitadas)
  FROM carga_execucao GROUP BY 1;                        -- resumo da carga por dataset
SELECT version, description, success
  FROM flyway_schema_history ORDER BY installed_rank;    -- migrações aplicadas (existe após a 1ª)
\q                                                       -- sai
```

Para conectar de fora (DBeaver, pgAdmin, VS Code): host `localhost`, porta `5432`, banco `sigma`, usuário `sigma`, senha `sigma` — ou os valores do seu `.env`.

**Data lake (E2)** — abra o console do MinIO em [http://localhost:9001](http://localhost:9001) (usuário `sigma`, senha `sigma12345`) e navegue em `sigma-lake/bronze/`: devem existir `portal/`, `lote/` e `cdc/`. Para conferir pelo terminal:

```bash
docker compose run --rm --no-deps extract python verificar_e2.py
```

Ele compara cada tabela do Postgres com a foto do lote e com o estado reconstruído só a partir do CDC, e sai com erro se algo não bater.

**Ver o CDC funcionando** — sem mudar nada, uma nova captura não pega nenhuma linha; depois de uma mudança, só as linhas alteradas aparecem:

```bash
docker compose run --rm --no-deps extract python capturar_mudancas.py   # TOTAL 0
docker compose exec -T db psql -U sigma -d sigma < db/demo/mudancas_demo.sql
docker compose run --rm --no-deps extract python capturar_mudancas.py   # só as linhas alteradas, como update
```

O `db/demo/mudancas_demo.sql` aplica poucas mudanças marcadas com `[demo E2]`. Para desfazer, `docker compose down -v`.

---

## Comandos do dia a dia

| Para…                                           | Comando |
|-------------------------------------------------|---------|
| Subir tudo (reconstruindo o que mudou)          | `docker compose up --build` |
| Subir em segundo plano                          | `docker compose up --build -d` |
| Ver logs de um serviço                          | `docker compose logs -f ingest` |
| Baixar e carregar de novo (só o que mudou)      | `docker compose run --rm ingest` |
| Só baixar                                       | `docker compose run --rm ingest python baixar_dados.py` |
| Só carregar                                     | `docker compose run --rm ingest python carregar.py` |
| Resumir a camada bruta (linhas, colunas)        | `docker compose run --rm ingest python inspecionar_bruto.py` |
| Medições do ADR 1                               | `docker compose run --rm ingest python medir_adr0001.py` |
| Rodar de novo os dois caminhos da E2            | `docker compose run --rm --no-deps extract` |
| Só a extração em lote                           | `docker compose run --rm --no-deps extract python extrair_lote.py` |
| Só a captura de mudanças                        | `docker compose run --rm --no-deps extract python capturar_mudancas.py` |
| Verificar lote e CDC contra o Postgres          | `docker compose run --rm --no-deps extract python verificar_e2.py` |
| Medições dos ADRs 2, 3 e 4                      | `docker compose run --rm --no-deps extract python medir_e2.py` |
| Aplicar migrações novas                         | `docker compose run --rm migrate` |
| Parar (mantém os dados do banco)                | `docker compose down` |
| **Apagar o banco e o lake e recomeçar do zero** | `docker compose down -v` |

`down -v` apaga os volumes do Postgres e do MinIO. Use-o para testar que a plataforma sobe do zero, como numa máquina limpa.

---

## Configuração

Todas as variáveis têm valor padrão, então **o `.env` é opcional**. Crie-o a partir de `.env.example` só para mudar algo:

| Variável            | Padrão  | Para que serve |
|---------------------|---------|----------------|
| `POSTGRES_DB`       | `sigma` | Nome do banco |
| `POSTGRES_USER`     | `sigma` | Usuário |
| `POSTGRES_PASSWORD` | `sigma` | Senha |
| `POSTGRES_PORT`     | `5432`  | Porta **na sua máquina** (dentro da rede do Compose é sempre 5432) |
| `MINIO_USER`        | `sigma` | Usuário do MinIO |
| `MINIO_PASSWORD`    | `sigma12345` | Senha do MinIO (mínimo 8 caracteres) |
| `MINIO_PORT`        | `9000`  | Porta da API S3 na sua máquina |
| `MINIO_CONSOLE_PORT`| `9001`  | Porta do console web na sua máquina |

O `.env` está no `.gitignore` e não deve ser versionado.

---

## Estrutura do repositório

```
SIIGMA-UnB/
├── docker-compose.yml          # sobe db, migrate, ingest, minio e extract
├── .env.example                # modelo de configuração
├── codigos/
│   ├── Dockerfile              # imagem Python dos serviços ingest e extract
│   ├── requirements.txt        # dependências Python
│   ├── baixar_dados.py         # portal da UnB -> dados/bruto/ (+ manifesto.json)
│   ├── carregar.py             # dados/bruto/ -> PostgreSQL
│   ├── normalizar.py           # funções de limpeza de texto e números
│   ├── inspecionar_bruto.py    # resumo da camada bruta
│   ├── medir_adr0001.py        # medições do ADR 1
│   ├── lake.py                 # E2: acesso ao MinIO e exportação Postgres -> Parquet
│   ├── enviar_bruto.py         # E2: dados/bruto/ -> bronze/portal/
│   ├── extrair_lote.py         # E2, caminho 1: foto completa -> bronze/lote/
│   ├── capturar_mudancas.py    # E2, caminho 2: só o que mudou -> bronze/cdc/
│   ├── verificar_e2.py         # E2: confere lote e CDC contra o Postgres
│   ├── medir_e2.py             # medições dos ADRs 2, 3 e 4
│   └── coletar_precos_mercado_livre.py
├── db/
│   ├── migrations/             # V1__descricao.sql, V2__..., aplicados em ordem pelo Flyway
│   └── demo/                   # mudanças de demonstração do CDC (fora do Flyway)
├── docs/                       # site estático Docsify
│   ├── index.html              # configuração do Docsify
│   ├── _sidebar.md             # navegação
│   ├── home.md                 # página inicial
│   ├── adr/                    # decisões de arquitetura (adr-1.md, adr-2.md, ...)
│   ├── dicionarios/            # dicionários de dados dos 5 datasets do portal
│   ├── modelagem/              # diagrama ER, modelo relacional e fonte .drawio
│   └── ...                     # demais páginas e assets da documentação
├── AI-USAGE.md                 # aponta para docs/ai-usage.md
└── dados/                      # criado na execução; ignorado pelo git
```

**Convenção das migrações:** `V<número>__<descrição>.sql` (dois sublinhados), por exemplo `V1__esquema_inicial.sql`. Uma migração já aplicada **nunca** é editada — qualquer mudança vira um arquivo novo com o próximo número.

---

## Problemas comuns

**Nada acontece / `error during connect` / `Cannot connect to the Docker daemon`**
O Docker não está rodando. No Windows, abra o Docker Desktop e espere *Engine running*. No Linux, `sudo systemctl start docker`.

**`port is already allocated` ou o `db` não fica pronto**
Já existe algo usando a porta 5432 (geralmente um Postgres instalado na máquina). Crie o `.env` e troque a porta, por exemplo `POSTGRES_PORT=5433`. Para descobrir quem ocupa a porta:

| Windows (PowerShell) | Linux |
|---|---|
| `netstat -ano \| findstr :5432` | `sudo ss -ltnp \| grep 5432` |

**`ingest` mostra `tentativa N falhou: 502 Server Error`**
O portal `dados.unb.br` oscila. O script tenta até 5 vezes por arquivo; se ainda assim falhar, o arquivo aparece como `FALHOU` e fica registrado em `falhas` no `manifesto.json`. Rode `docker compose run --rm ingest` de novo: só o que falta é baixado.

**`extract` diz `DIVERGE` ou sai com código 1**
O `verificar_e2.py` encontrou diferença entre o Postgres e a bronze. Se o banco mudou depois da foto do lote, rode `docker compose run --rm --no-deps extract` de novo. Se a diferença estiver no CDC, a captura perdeu alguma versão: anote no diário, porque é gatilho de revisão do ADR 4.

**`minio` não sobe ou `pull access denied` na imagem do MinIO**
A imagem está fixada numa tag de 2025, porque a MinIO parou de publicar imagens novas da edição comunitária. Confira com `docker pull minio/minio:RELEASE.2025-04-22T22-12-26Z`. Se a porta 9000 ou 9001 estiver ocupada, troque `MINIO_PORT`/`MINIO_CONSOLE_PORT` no `.env`.

**`ingest` sai com código 1**
Um dataset obrigatório (estoque ou unidades) não baixou nada, ou algum arquivo deu erro na carga. A mensagem no fim do log diz qual. Os arquivos que deram certo continuam no banco.

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
| Migrações versionadas (Flyway) | ✅ `V1__esquema_inicial.sql`, `V2__indices_cdc.sql` |
| Download automatizado dos 5 datasets, com manifesto | ✅ |
| Carga dos dados no banco, idempotente, com rejeitados registrados | ✅ |
| ADR da E1 ([`docs/adr/adr-1.md`](docs/adr/adr-1.md)) | ✅ |
| Diário ([`docs/diario/`](docs/diario/)) | ⏳ Só o modelo; faltam as semanas |
| Registro de uso de IA ([`docs/ai-usage.md`](docs/ai-usage.md)) | ✅ |
| Cotações de mercado no banco | ⏳ Tabela criada; coleta ainda não roda no compose |
| E2: MinIO no compose e bruto do portal na bronze | ✅ |
| E2: extração em lote para Parquet | ✅ `extrair_lote.py` |
| E2: captura de mudanças (CDC por consulta) | ✅ `capturar_mudancas.py` + migração V2 |
| E2: verificação lote/CDC x Postgres | ✅ `verificar_e2.py` |
| ADRs da E2 ([2](docs/adr/adr-2.md), [3](docs/adr/adr-3.md), [4](docs/adr/adr-4.md)) | ⏳ Propostos; falta preencher a Medição com `medir_e2.py` |
