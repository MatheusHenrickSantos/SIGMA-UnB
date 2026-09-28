# SIGMA-UnB

Plataforma de dados construída sobre os **dados abertos do almoxarifado da Universidade de Brasília** ([dados.unb.br](https://dados.unb.br)), como Projeto Integrado da disciplina.

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
| `ingest`  | Python: baixa os dados do almoxarifado da API do portal da UnB e grava em `dados/`.                    | Sim |

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
4. `ingest-1 | Buscando recursos no portal de dados abertos da UnB...`, uma linha `Baixando: ...` por arquivo, `Concluído! ...` e `ingest-1 exited with code 0`.
5. **O terminal fica parado mostrando os logs do banco.** Isso é esperado: o banco continua rodando. Para parar, `Ctrl+C`.

Para subir em segundo plano e liberar o terminal, use `docker compose up --build -d` e acompanhe com `docker compose logs -f`.

---

## Verificar que funcionou

**Estado dos serviços** — `migrate` e `ingest` devem aparecer como `Exited (0)` e `db` como `Up (healthy)`:

```bash
docker compose ps -a
```

**Arquivos baixados** — deve existir a pasta `dados/almoxarifado/` com arquivos `.json`:

| Windows (PowerShell) | Linux |
|---|---|
| `Get-ChildItem dados\almoxarifado` | `ls -lh dados/almoxarifado` |

**Banco e migrações** — abra o `psql` dentro do container:

```bash
docker compose exec db psql -U sigma -d sigma
```

Dentro do `psql`:

```sql
\dt                                                      -- lista as tabelas
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
| Rodar só o download de novo                     | `docker compose run --rm ingest` |
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
│   └── buscar-dados-de-almoxarifado.py
├── db/
│   └── migrations/             # V1__descricao.sql, V2__..., aplicados em ordem pelo Flyway
├── modelagem/                  # diagrama ER, modelo relacional e fonte .drawio
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

**`ingest` para em `Buscando recursos...`**
O portal `dados.unb.br` não está respondendo. Tente de novo mais tarde com `docker compose run --rm ingest`.

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
| Migrações versionadas (Flyway) | ⚠️ Estrutura pronta, sem migrações ainda |
| Download automatizado dos dados da UnB | ✅ |
| Carga dos dados no banco | ❌ A fazer |
| ADRs (`docs/adr/`) | ❌ A fazer |
| Diário (`docs/diario/`) | ❌ A fazer |
| Registro de uso de IA (`AI-USAGE.md`) | ❌ A fazer |
