# Semana 04 — Finalização para Apresentação

**Período:** 20/09/2026 a 28/09/2026
**Entrega relacionada:** E1
**Participantes:** Matheus, Israel, Samara e Magno.

## Objetivo da semana

Fechar a E1: transformar a modelagem inicial em uma fonte transacional (OLTP) que sobe do zero com `docker compose up --build`, com esquema versionado, download e carga automatizados, documentação do repositório e a primeira decisão de modelagem registrada em ADR, para a apresentação.

## O que foi feito

Responsável atribuído pelo autor do commit. Os commits da semana começam em 27/09 (o repositório foi criado com um commit inicial nesse dia).

| Tarefa | Responsável | Status | Evidência (PR, commit, arquivo) |
|---|---|---|---|
| Modelagem inicial do banco (diagrama ER e modelo relacional v1.0) | Israel | ✅ concluído | `e53cc61` (27/09) |
| Segunda versão do desenho da arquitetura do banco | Israel | ✅ concluído | `2c0ea4f` (28/09) |
| Primeiro script de download do estoque do almoxarifado | Matheus | ✅ concluído (substituído) | `4c9b5b0` (27/09), removido em `55307a4` |
| Normalização dos dados do almoxarifado | Matheus | ✅ concluído | `229f80a` — `codigos/normalizar.py` |
| Download dos 5 datasets da UnB, com manifesto e retry | Samara | ✅ concluído | `55307a4` — `codigos/baixar_dados.py` |
| Migração inicial do esquema (Flyway V1) | Samara | ✅ concluído | `55307a4` — `db/migrations/V1__esquema_inicial.sql` |
| Carga idempotente no banco, com registro de rejeitados | Samara | ✅ concluído | `55307a4` — `codigos/carregar.py` |
| Inspeção da camada bruta e medições do ADR 0001 | Samara | ✅ concluído | `55307a4` — `codigos/inspecionar_bruto.py`, `codigos/medir_adr0001.py` |
| Ambiente Docker Compose (`db`, `migrate`, `ingest`) | Samara | ✅ concluído | `368a63c`, `55307a4` — `docker-compose.yml`, `codigos/Dockerfile` |
| README com instruções de instalação e uso | Matheus | ✅ concluído | `cab24c8` — `README.md` |
| Documentação: registro de IA, diário, template de ADR e site (mkdocs) | Samara | ✅ concluído | `7e00562`, `975a201` — `docs/ai-usage.md`, `docs/diario-de-bordo.md`, `docs/adr-template.md` |
| Coleta de preços do Mercado Livre (script) | Matheus | 🔄 em andamento | `c6e0cf9` — coleta gravada no banco entra na E2 |
| ADR 0001: modelagem da origem (status aceito) | Israel, Magno, Matheus, Samara (decisores) | ✅ decidido; 📄 versionado em 11/10 | `9076efa` — `docs/adr/adr-1.md` |
| Diário da semana no repositório | Equipe | 🔄 em andamento | Existe só localmente em `docs/diario/`; ainda não está no git |

## Decisões tomadas

- **Pergunta de gestão:** a pergunta foi reformulada no README para comparar o preço unitário registrado no almoxarifado da UnB com o preço de mercado em lojas online. Isso dá à E2 uma fonte externa de preços para cruzar com a origem.
- **Modelo de dado da origem (ADR 0001, datado de 27/09):** cadastros (unidade, material, almoxarifado, natureza, credor) são atualizados no lugar e guardam `atualizado_em`. Fatos com série no tempo (saldo de estoque e cotações) são insert-only: cada carga acrescenta linhas e nada é sobrescrito. O motivo é que a fonte pública não tem log de eventos, então o modelo não inventa eventos que não existem.
- **Alternativas de saldo de estoque:** o `medir_adr0001.py` compara três formas de guardar o saldo (CRUD, insert-only e CRUD com tabela de histórico por trigger) em duas consultas do Bloco 3. Escolhemos o insert-only.
- **Ambiente:** tudo roda em Docker Compose (PostgreSQL 16, Flyway 10 e ingestão em Python 3.12). Ninguém precisa instalar Postgres ou Python na máquina.
- **Camada bruta:** os arquivos são gravados exatamente como vieram do portal, em `dados/bruto/`, com `manifesto.json` (url, data, tamanho e sha256). Assim a carga pode ser refeita sem baixar de novo.
- **Carga:** cada arquivo entra em transação própria. O sha256 evita duplicar uma carga já feita. Registros inválidos vão para `carga_rejeitado` com o motivo. Se um mês cair mais de 30% em relação ao anterior, a carga daquele arquivo é desfeita, porque provavelmente o arquivo veio incompleto.
- **Falha de download:** se um dataset obrigatório (estoque ou unidades) não baixar, o `ingest` sai com código 1 e a carga não roda.
- **Cotações de mercado:** a tabela foi criada nesta semana, mas a coleta fica para a E2.

## Problemas e como foram resolvidos

| Problema | Causa | Solução / encaminhamento |
|---|---|---|
| O Dockerfile executava `buscar-dados-de-almoxarifado.py`, que já não existia | O script foi substituído por `baixar_dados.py`, mas o `CMD` não foi atualizado | `CMD` trocado para `python baixar_dados.py && python carregar.py` (`55307a4`) |
| Download do portal falhava sem aviso (502 do `dados.unb.br`) | Portal instável e nenhum retry | Até 5 tentativas por arquivo. Falhas ficam em `manifesto.json` e a próxima execução baixa só o que falta |
| Possível arquivo incompleto da fonte | A publicação pode vir parcial | Limite de queda de 30% por mês; a carga do arquivo é desfeita se ultrapassar |
| Workflow de deploy em `.github/worflows/` (erro de digitação) | Erro no nome da pasta no commit `975a201` | Corrigido depois: no HEAD atual a pasta é `.github/workflows/` |
| ADR 0001 referenciado no README como `0001-modelagem-da-origem.md`, mas o arquivo se chama `adr-1.md` | Nome fora do padrão e ADR versionado só em 11/10 (`9076efa`) | Pendente: alinhar nome e links (ver Próximos passos) |

## Uso de IA na semana

- Em 28/09, o Claude (Opus 5.5) escreveu o README de execução com Docker. O texto foi aproveitado integralmente, testado nas máquinas da equipe e revisado por Samara.
- No mesmo dia, o Claude fez um levantamento do que faltava para a E1, comparando o repositório com a página da E1. A lista de pendências foi conferida item a item.
- O registro detalhado fica em [Uso de IA](../ai-usage.md). A entrada modelo `AAAA-MM-DD` ainda está no arquivo.

## Aprendizados

- Dado público chega com instabilidade e mudanças de formato. Retry, manifesto com sha256 e registro de rejeitados não são opcionais.
- Verificar a integridade por mês e não só por arquivo pegou um risco que a carga por arquivo não veria.
- Renomear um script sem atualizar o Docker quebra o `docker compose up`. Vale testar a subida do zero antes de cada entrega.
- A decisão do ADR 0001 foi tomada na semana, mas o arquivo só entrou no git em outubro. Decisão e registro devem entrar no repositório juntos.

## Próximos passos

- [x] Versionar `docs/diario/` no repositório, incluindo esta semana — equipe
- [x] Alinhar o nome do ADR 0001 (`adr-1.md` ou `0001-modelagem-da-origem.md`) com os links do README — Matheus
- [x] Remover a entrada modelo `AAAA-MM-DD` de `docs/ai-usage.md` — Samara
- [x] Testar a subida do zero em máquina limpa (`git clone` e `docker compose up --build`) antes da apresentação — equipe
- [x] Definir a coleta de cotações do Mercado Livre para a E2 e gravar no banco — Matheus
