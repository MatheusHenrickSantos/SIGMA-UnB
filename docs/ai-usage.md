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

### 2026-10-19 — carga completa do estoque e pergunta de gestão no README (RD-03, RF-00)

- **Ferramenta:** Claude (sonnet 5.5), em modo agente com acesso ao repositório e ao Docker
- **Onde:** codigos/carregar.py, README.md, docs/backlog.md
- **O que foi pedido:** descobrir por que 30 meses de estoque eram rejeitados e corrigir; alinhar a pergunta de gestão do README à da página inicial.
- **O que foi aproveitado:** a causa (queda estrutural de ~1.800 para ~830 linhas em 11/2022, que travava todos os meses seguintes em cadeia) e a correção com a lista `QUEDAS_ACEITAS`. O texto do README.
- **Como foi verificado:** rodamos a carga antes e depois: 30 arquivos com erro caíram para zero e `estoque_saldo` passou de 18.848 para 41.116 linhas. Falta a Squad confirmar que a queda de 11/2022 é mesmo mudança de escopo do portal e não falha de publicação.
- **Quem revisou:** Magno pediu e acompanhou; revisão do código a confirmar pela Squad

### 2026-10-19 — captura de mudanças do OLTP (RD-05)

- **Ferramenta:** Claude (sonnet 5.5), em modo agente com acesso ao repositório e ao Docker
- **Onde:** db/migrations/V2__cdc_publicacao.sql, codigos/cdc_consumidor.py, codigos/cdc_demo.py, docker-compose.yml
- **O que foi pedido:** implementar CDC por decodificação lógica do Postgres, com consumidor e script que altera linhas e mostra o efeito. A escolha por pgoutput com consumidor em Python, em vez de Debezium + Kafka, foi discutida e decidida pela Squad, pelo prazo.
- **O que foi aproveitado:** o desenho inteiro: publicação com REPLICA IDENTITY FULL, leitura por *peek* e avanço do slot só depois de gravar o lote, e a demonstração.
- **Como foi verificado:** rodamos `cdc_demo.py` contra o banco real: insert, update (com antes e depois), delete e releitura sem eventos duplicados. Não testamos queda do processo entre gravar o lote e avançar o slot.
- **Quem revisou:** Magno pediu e acompanhou; revisão do código a confirmar pela Squad

### 2026-10-19 — camada analítica em Delta Lake e ADR 2 (RD-04, RD-06 a RD-10)

- **Ferramenta:** Claude (sonnet 5.5), em modo agente com acesso ao repositório e ao Docker
- **Onde:** codigos/lake.py, codigos/demo_lake.py, codigos/medir_adr0002.py, docs/adr/adr-2.md
- **O que foi pedido:** criar a camada em formato aberto, com carga idempotente, tratamento de dado atrasado e a justificativa de formato, compressão e partição.
- **O que foi aproveitado:** o código e a estrutura do ADR. A escolha de Delta em vez de Iceberg foi sugerida pela ferramenta e aceita pela Squad. Os gatilhos de revisão do ADR (5 milhões de linhas, 2 s) são propostas a revisar.
- **Como foi verificado:** `demo_lake.py` passou nos cinco cenários (evento novo, reprocessamento, evento atrasado, insert antigo após delete, janela reprocessada duas vezes). Os números do ADR vêm de `medir_adr0002.py` sobre o estoque real. Não testamos leitura por Spark ou Trino.
- **Quem revisou:** Magno pediu e acompanhou; revisão do código a confirmar pela Squad

### 2026-10-19 — coleta semanal de preços (RF-11, RF-12)

- **Ferramenta:** Claude (sonnet 5.5), em modo agente com acesso ao repositório e ao Docker
- **Onde:** db/migrations/V3__cotacao_semanal.sql, codigos/coletar_precos_mercado_livre.py, docker-compose.yml
- **O que foi pedido:** ligar o coletor ao banco, deduplicar por semana, filtrar anúncios de outro produto e agendar a execução.
- **O que foi aproveitado:** a gravação em `cotacao_online`, o filtro de relevância do título (mínimo de 60% das palavras do termo, número arbitrário a validar) e o serviço semanal do compose.
- **Como foi verificado:** só com resposta simulada da API: o filtro descartou o anúncio errado e a segunda rodada não duplicou. **A coleta real não foi testada**: a API respondeu com erro sem o token do Mercado Livre.
- **Quem revisou:** Magno pediu e acompanhou; revisão do código a confirmar pela Squad

### AAAA-MM-DD — [o que estava sendo feito]

- **Ferramenta:**
- **Onde:**
- **O que foi pedido:**
- **O que foi aproveitado:**
- **Como foi verificado:**
- **Quem revisou:**

---
