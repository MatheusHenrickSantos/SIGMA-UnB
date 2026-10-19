# Semana 06 — Organização para Entrega E2

**Período:** 11/10/2026 a 19/10/2026
**Entrega relacionada:** E2
**Participantes:** Matheus, Israel, Samara e Magno

## Objetivo da semana

Fechar a E2 (ingestão em lote e captura de mudanças). Isso significava migrar o site da documentação para o Docsify e versionar a modelagem e o ADR 1. Também era preciso destravar a carga completa do estoque, implementar o CDC e a camada analítica em formato aberto, ligar a coleta de preços ao banco e documentar tudo nas páginas da E2.

## O que foi feito

Responsável atribuído pelo autor do commit. Os itens marcados como *branch `e2-entrega`* estão no repositório, mas ainda não foram integrados à `main`.

| Tarefa | Responsável | Status | Evidência (PR, commit, arquivo) |
|---|---|---|---|
| Troca do MkDocs pelo Docsify e correção do workflow de deploy (`worflows` → `workflows`) | Matheus | ✅ concluído | `ba3fc72`, `64342e4` (11/10) — `docs/index.html`, `.github/workflows/deploy.yml` |
| Reorganização das pastas (`modelagem/` → `docs/modelagem/`, diagramas em `docs/assets/diagramas/`) | Matheus | ✅ concluído | `f4882fe` (11/10), `29d16c2` (12/10) |
| ADR 1 versionado no repositório | Matheus | ✅ concluído | `9076efa` (11/10) — `docs/adr/adr-1.md` |
| Páginas do diagrama ER e do modelo relacional | Matheus | ✅ concluído | `b3bd890`, `ab925dc` (12/10) |
| Dicionário de dados | Matheus | ✅ concluído | `48d34fc` (12/10), ampliado em `590b69c` (19/10) |
| Diagrama de arquitetura Bronze/Prata/Ouro (v1.1) e ER/relacional v1.2 | Matheus e Israel | ✅ concluído | `50c793b` (12/10), `590b69c`, `71c589e` (19/10) |
| Backlog do produto (MoSCoW, por etapa) | Magno | ✅ concluído | `a7d789a`, `c7d077c`, `ccf30f2`, PR #5 (19/10) — `docs/backlog.md` |
| Templates de documentação da E2 | Samara | ✅ concluído | `ddcad07` (19/10) |
| Diário das semanas 01 a 05 | Samara | ✅ concluído | `bb5b598`, `324eb83` (19/10) — `docs/diario/` |
| Domínio e pergunta de gestão | Samara | ✅ concluído | `51d62a8` — `docs/dominio-e-pergunta.md` |
| Fontes e histórico da origem | Samara | ✅ concluído | `2dd6482` — `docs/fontes-e-historico-da-origem.md` |
| Caracterização da carga e ADR 0003 (queda de volume vira aviso) | Samara | ✅ concluído | `6d489c5`, `618c33d` — `docs/caracterizacao-da-carga.md`, `docs/adr/0003-validacao-de-volume-na-carga_1.md`, `codigos/carregar.py` |
| Arquitetura em camadas e consultas sobre estoque e almoxarifado | Samara | ✅ concluído | `3ee766f` — `docs/arquitetura-em-camadas.md`, `docs/consultas.md` |
| Registro de uso de IA atualizado | Samara e Magno | ✅ concluído | `a7d789a`, `6a47e76` — `docs/ai-usage.md` |
| Carga completa do estoque (30 meses que eram rejeitados) | Magno | 🔄 branch `e2-entrega` | `dc67d85` — `codigos/carregar.py` |
| CDC por decodificação lógica (pgoutput) | Magno | 🔄 branch `e2-entrega` | `5bf6c5e` — `db/migrations/V2__cdc_publicacao.sql`, `codigos/cdc_consumidor.py`, `codigos/cdc_demo.py` |
| Teste de queda do consumidor do CDC | Magno | 🔄 branch `e2-entrega` | `ce34cd5` — `codigos/testar_queda_cdc.py` |
| Camada analítica em Delta Lake com carga idempotente (`MERGE`) | Magno | 🔄 branch `e2-entrega` | `a4aeb00` — `codigos/lake.py`, `codigos/demo_lake.py` |
| ADR 2: formato e particionamento da camada analítica | Magno | 🔄 branch `e2-entrega` | `f35ee1e` — `docs/adr/adr-2.md`, `codigos/medir_adr0002.py` |
| Coleta semanal de preços gravando em `cotacao_online` | Magno | 🔄 branch `e2-entrega` (sem teste real) | `fcd9525` — `codigos/coletar_precos_mercado_livre.py`, `db/migrations/V3__cotacao_semanal.sql` |
| Serviços `cdc` e `coleta` no Compose, com `wal_level=logical` | Magno | 🔄 branch `e2-entrega` | `e00bd0e` — `docker-compose.yml` |
| README atualizado com o que entrou na E2 | Magno | 🔄 branch `e2-entrega` | `8b184a1` |

## Decisões tomadas

- **Site da documentação:** o MkDocs foi trocado pelo Docsify, publicado pelo GitHub Pages a partir de `docs/`.
- **Arquitetura em camadas:** a squad adotou a arquitetura Bronze, Prata e Ouro.
  - **Bronze:** os arquivos brutos e a coleta de preços.
  - **Prata:** o PostgreSQL normalizado.
  - **Ouro:** o modelo estrela `FatoAvaliacaoEstoque` com as dimensões Material, Almoxarifado, Loja e Tempo.
- **Queda de volume no estoque (ADR 0003):** a trava de 30% recusava 30 dos 40 meses de estoque, porque o volume cai de ~1.800 para ~830 linhas em 11/2022 e se mantém nesse patamar. A queda deixou de recusar o arquivo e passou a gerar um aviso no log. Com isso, `estoque_saldo` passou de 18.848 para 41.116 linhas.
- **CDC:** a captura usa a decodificação lógica nativa do Postgres (`pgoutput`), com um consumidor em Python, em vez de Debezium + Kafka. O motivo foi o prazo. O slot só avança depois que o lote é gravado, então uma queda do processo não perde eventos.
- **Camada analítica (ADR 2):** Delta Lake sobre Parquet com compressão ZSTD, `estoque_saldo` particionada por ano e escrita sempre por `MERGE` com chave. A regra `ultimo_evento` e a exclusão lógica impedem que um evento atrasado ou repetido desfaça um estado mais novo.
- **Cotações:** a coleta é feita uma vez por semana. `semana_coleta` (a segunda-feira da semana) entra na chave única, então rodar a coleta de novo na mesma semana não duplica linhas. Anúncios cujo título não tem pelo menos 60% das palavras do termo de busca são descartados.
- **Pergunta de gestão:** o backlog adota como núcleo a pergunta da página inicial (2021–2025: preço subindo mais rápido e fornecedores). A comparação com o preço de mercado fica como complemento.

## Problemas e como foram resolvidos

| Problema | Causa | Solução / encaminhamento |
|---|---|---|
| 30 meses de estoque (11/2022 a 12/2025) eram recusados na carga | A trava de 30% comparava sempre com o último mês aceito (07/2022, com ~1.800 linhas) e recusava os meses seguintes em cadeia | Queda virou aviso (ADR 0003, `618c33d`). Na `e2-entrega` há uma correção diferente para o mesmo problema (`dc67d85`, lista `QUEDAS_ACEITAS`) |
| Causa da queda de 11/2022 desconhecida | Concentrada no almoxarifado PRC (1.660 → 695); os ~990 itens que sumiram tinham saldo positivo (~R$ 1,05 milhão); faltam os arquivos de 08 a 10/2022 | Pendente: confirmar com o portal dados.unb.br. Até lá, tratar a série do PRC com cautela |
| Coleta real do Mercado Livre não funcionou | A API respondeu com erro sem o token de acesso | Testado só com resposta simulada. Pendente: obter o token e rodar uma coleta real |
| Workflow de deploy não rodava | Pasta `.github/worflows/` com erro de digitação | Renomeada para `.github/workflows/` (`ba3fc72`) |
| ADR 0002 duplicado como `0002-...(2).md` | Arquivo copiado duas vezes no commit dos templates | Duplicata removida em `bb5b598` |
| Arquivo `.pyc` versionado e `semana-07.md` apagado por engano | Commit `51d62a8` incluiu `codigos/__pycache__/` e removeu o diário da semana 07 | Pendente: remover o `.pyc`, colocar `__pycache__/` no `.gitignore` e conferir se a semana 07 deveria existir |

## Uso de IA na semana

- **Claude Sonnet 5.5, em modo agente, com revisão de Magno (todo o trabalho da `e2-entrega`):**
  - **Carga do estoque:** diagnóstico e correção dos 30 meses rejeitados.
  - **CDC:** implementação e teste de queda do consumidor.
  - **Camada Delta Lake e ADR 2:** a escolha de Delta em vez de Iceberg foi sugerida pela ferramenta e aceita pela squad.
  - **Coleta semanal de preços:** só foi testada com resposta simulada da API.
- **Claude (Cowork), usado por Samara:**
  - comparação do repositório com os de outros grupos de BD2, para listar os documentos que faltavam;
  - templates de documentação da E2;
  - consultas SQL sobre estoque e almoxarifado, testadas em um Postgres com o esquema V1 e dados fictícios;
  - página de arquitetura em camadas, escrita a partir do diagrama e do código;
  - este diário.
- **Backlog e Codespaces:** apoio na escrita do backlog do produto e para subir o ambiente Docker no GitHub Codespaces.
- O registro detalhado fica em [Uso de IA](../ai-usage.md).

## Aprendizados

- **Validações automáticas:** uma regra de segurança que compara com "o último mês aceito" pode travar todos os meses seguintes depois de uma mudança real na origem. Validação de volume deve avisar e não bloquear em cadeia.
- **Dado público:** pode mudar de patamar sem explicação. Investigar por almoxarifado e por saldo mostrou que não era arquivo truncado, mas a causa só a fonte pode confirmar.
- **CDC:** o ponto crítico é a ordem entre gravar o lote e avançar o slot. Simular a queda do processo foi o que provou que não há perda nem duplicação.
- **Trabalho em paralelo:** concentrar quase toda a entrega no último dia gerou duas correções diferentes para o mesmo problema (`618c33d` na `main` e `dc67d85` na `e2-entrega`) e documentação que descreve uma arquitetura diferente da implementada. Integrar a branch mais cedo teria evitado isso.

## Próximos passos

- [ ] Integrar a branch `e2-entrega` à `main`, escolhendo uma única correção para a queda de 11/2022 em `carregar.py` — Magno e Samara
- [ ] Unificar a numeração dos ADRs: hoje a `main` tem `0002-...` (template não preenchido) e `0003-...`, e a `e2-entrega` tem `adr-2.md` (Delta Lake) — equipe
- [ ] Atualizar `docs/arquitetura-em-camadas.md` para Delta Lake + ZSTD e incluir o CDC no pipeline — Samara
- [ ] Alinhar a pergunta de gestão entre README, `home.md`, backlog e `dominio-e-pergunta.md`, e ajustar `consultas.md` se o período mudar para 2021–2025 — equipe
- [ ] Obter o token do Mercado Livre e rodar uma coleta real — Magno
- [ ] Remover `codigos/__pycache__/` do repositório e adicioná-lo ao `.gitignore` — Samara
- [ ] Corrigir no `docs/diario/README.md` os rótulos das semanas 05 e 06 (aparecem como "Semana 06" e "Semana 07") — Samara
- [ ] Preencher os autores do ADR 0003 — Samara
- [ ] Pedir ao portal dados.unb.br a explicação da queda do estoque do PRC em 11/2022 — equipe
