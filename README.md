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

Um único comando sobe três serviços, nesta ordem:

| Serviço   | O que faz                                                                                              | Termina? |
|-----------|--------------------------------------------------------------------------------------------------------|----------|
| `db`      | PostgreSQL 16: o banco transacional (OLTP).                                                            | Não, fica rodando |
| `migrate` | Flyway: aplica os arquivos `db/migrations/V*.sql` em ordem, a partir do banco vazio.                   | Sim |
| `ingest`  | Python: baixa os 5 datasets do portal da UnB para `dados/bruto/` e carrega no banco.                    | Sim |

`migrate` só começa quando o banco está pronto, e `ingest` só começa se todas as migrações tiverem sido aplicadas com sucesso.

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
4. `ingest-1 | Buscando datasets no portal de dados abertos da UnB...` e uma linha `baixando: ...` por arquivo. Na primeira vez são cerca de 850 MB (os empenhos são a maior parte); o portal às vezes responde `502` e o script tenta de novo sozinho.
5. `ingest-1 | [unidades]`, `[estoque]`, ... com uma linha `N gravadas, M rejeitadas` por arquivo carregado, a tabela **Linhas por tabela** e `ingest-1 exited with code 0`. A carga completa leva alguns minutos.
6. **O terminal fica parado mostrando os logs do banco.** Isso é esperado: o banco continua rodando. Para parar, `Ctrl+C`.

Para subir em segundo plano e liberar o terminal, use `docker compose up --build -d` e acompanhe com `docker compose logs -f`.

---

## Verificar que funcionou

**Estado dos serviços** — `migrate` e `ingest` devem aparecer como `Exited (0)` e `db` como `Up (healthy)`:

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
| Medições do ADR 0001                            | `docker compose run --rm ingest python medir_adr0001.py` |
| Aplicar migrações novas                         | `docker compose run --rm migrate` |
| Parar (mantém os dados do banco)                | `docker compose down` |
| **Apagar o banco e recomeçar do zero**          | `docker compose down -v` |

`down -v` apaga o volume do Postgres. Use-o para testar que a plataforma sobe do zero, como numa máquina limpa.

---

## Configuração

Todas as variáveis têm valor padrão, então **o `.env` é opcional**. Crie-o a partir de `.env.example` só para mudar algo:

| Variável            | Padrão  | Para que serve |
|---------------------|---------|----------------|
| `POSTGRES_DB`       | `sigma` | Nome do banco |
| `POSTGRES_USER`     | `sigma` | Usuário |
| `POSTGRES_PASSWORD` | `sigma` | Senha |
| `POSTGRES_PORT`     | `5432`  | Porta **na sua máquina** (dentro da rede do Compose é sempre 5432) |

O `.env` está no `.gitignore` e não deve ser versionado.

---

## Estrutura do repositório

```
SIGMA-UnB/
├── docker-compose.yml          # sobe db, migrate e ingest
├── .env.example                # modelo de configuração
├── codigos/
│   ├── Dockerfile              # imagem Python do serviço ingest
│   ├── requirements.txt        # dependências Python
│   ├── baixar_dados.py         # portal da UnB -> dados/bruto/ (+ manifesto.json)
│   ├── carregar.py             # dados/bruto/ -> PostgreSQL
│   ├── normalizar.py           # funções de limpeza de texto e números
│   ├── inspecionar_bruto.py    # resumo da camada bruta
│   ├── medir_adr0001.py        # medições do ADR 0001
│   └── coletar_precos_mercado_livre.py
├── db/
│   └── migrations/             # V1__descricao.sql, V2__..., aplicados em ordem pelo Flyway
├── docs/                       # site mkdocs: ADRs, diário, uso de IA
│   ├── adr/                    # decisões de arquitetura (0001, 0002, ...)
│   └── diario/                 # registro semanal da Squad
├── modelagem/                  # diagrama ER, modelo relacional e fonte .drawio
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
| Migrações versionadas (Flyway) | ✅ `V1__esquema_inicial.sql` |
| Download automatizado dos 5 datasets, com manifesto | ✅ |
| Carga dos dados no banco, idempotente, com rejeitados registrados | ✅ |
| ADR da E1 ([`docs/adr/0001-modelagem-da-origem.md`](docs/adr/0001-modelagem-da-origem.md)) | ✅ |
| Diário ([`docs/diario/`](docs/diario/)) | ✅ |
| Registro de uso de IA ([`docs/ai-usage.md`](docs/ai-usage.md)) | ✅ |
| Cotações de mercado no banco | ⏳ Tabela criada; coleta entra na E2 |
