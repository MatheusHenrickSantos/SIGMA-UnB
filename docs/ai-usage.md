# AI-USAGE.md — Squad [nome]

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


### 2026-10-12 — implementação da E2 (ingestão em lote e captura de mudanças)

- **Ferramenta:** Claude (opus 5.5), em modo agente, com o repositório clonado num ambiente de nuvem
- **Onde:** `docker-compose.yml`, `.env.example`, `db/migrations/V2__indices_cdc.sql`, `db/demo/mudancas_demo.sql`, `codigos/lake.py`, `codigos/enviar_bruto.py`, `codigos/extrair_lote.py`, `codigos/capturar_mudancas.py`, `codigos/verificar_e2.py`, `codigos/medir_e2.py`, `docs/adr/adr-2.md` a `adr-4.md`, README, `docs/_sidebar.md`, `docs/home.md`, links para o repositório oficial
- **O que foi pedido:** a partir do feedback da professora (faltava ADR, faltava dizer *como*, usar ELT, repensar o armazenamento), um plano passo a passo da E2 e depois a implementação em commits pequenos.
- **O que foi aproveitado:** o código e os rascunhos dos ADRs 2, 3 e 4. Os ADRs ficaram como *proposto*: a IA escreveu contexto, alternativas e consequências, mas as tabelas de Medição estão em branco e precisam ser preenchidas pela Squad com a saída do `medir_e2.py` sobre os dados reais. A IA não teve acesso ao portal dados.unb.br nem ao Docker Hub, então não inventou números.
- **Como foi verificado:** pela IA, num Postgres 16 local com as migrações V1 e V2, um emulador de S3 no lugar do MinIO e dados **sintéticos** (não os do portal): lote, três rodadas de CDC (inicial, sem mudança = 0 linhas, depois do `mudancas_demo.sql` = só as 6 linhas alteradas), uma transação longa aberta durante a captura (nenhuma linha perdida) e o `verificar_e2.py` acusando divergência quando o CDC não roda. **Falta a Squad verificar:** `git clone` numa pasta nova, `docker compose up --build` com os dados reais, a imagem do MinIO baixando, e preencher a Medição dos ADRs.
- **Quem revisou:** _preencher_

### AAAA-MM-DD — [o que estava sendo feito]

- **Ferramenta:**
- **Onde:**
- **O que foi pedido:**
- **O que foi aproveitado:**
- **Como foi verificado:**
- **Quem revisou:**

---
