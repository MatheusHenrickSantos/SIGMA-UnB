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
- **Onde:** docs/backlog.md e docs/_sidebar.md
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

### AAAA-MM-DD — [o que estava sendo feito]

- **Ferramenta:**
- **Onde:**
- **O que foi pedido:**
- **O que foi aproveitado:**
- **Como foi verificado:**
- **Quem revisou:**

---
