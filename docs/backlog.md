# Backlog do produto

Requisitos do SIGMA-UnB: o que esperamos ter construído no fim da disciplina. A coluna **Etapa** indica a Entrega em que cada item deve ficar pronto; os itens já entregues estão marcados.

**Prioridade (MoSCoW):** **Must** = exigido pelo checklist de aceite da Entrega ou necessário para responder à pergunta de gestão · **Should** = importante, entra se o prazo permitir · **Could** = desejável · **Won't** = fora do escopo, de propósito.

**Situação:** ✅ pronto · 🚧 parcial · ⏳ não iniciado

---

## Visão

O SIGMA-UnB mostra os materiais disponíveis no almoxarifado da UnB e monitora seus preços em lojas online ao longo do tempo, para evitar compras acima do preço de mercado e facilitar o acompanhamento de disponibilidade e custo.

**Usuários:** gestores da UnB, chefes de departamento e Centro Acadêmico.

**Pergunta de gestão** (base: [página inicial](home.md)):

> Entre 2021 e 2025, quais materiais de consumo do almoxarifado da UnB tiveram o preço unitário registrado subindo mais rápido, e quais fornecedores concentraram os empenhos desses materiais?

A comparação com o preço de mercado em lojas online (a pergunta que o [README](../README.md) traz hoje) fica como complemento, não como núcleo.

## Etapas

| Etapa | Tema | Prazo | Peso | Estado |
|---|---|---|---|---|
| E1 | Modelagem e carga da origem (OLTP) | — | — | ✅ tag `e1` |
| E2 | Ingestão em lote e captura de mudanças | 19/10/2026 | 12% | 🚧 |
| E3 | Camada analítica transformada, testada e orquestrada | 03/11/2026 | 14% | ⏳ |
| E4 | Plataforma completa, governada e defendida | 24/11/2026 | 14% | ⏳ |

---

## Requisitos funcionais

Cada item é uma história: **como** [usuário], **quero** [capacidade], **para** [benefício].

### Preço e gasto (o núcleo da pergunta de gestão)

| ID | História | Prio | Etapa | Situação |
|---|---|---|---|---|
| RF-00 | Como equipe, quero a mesma pergunta de gestão no README e na página inicial, para que o escopo, o painel e as métricas respondam a ela. A pergunta base é a da página inicial; o README ainda traz a antiga. | Must | E2 | 🚧 |
| RF-01 | Como gestor, quero ver a evolução do preço unitário de cada material ao longo do tempo, para identificar os que subiram mais rápido. | Must | E3 | ⏳ |
| RF-02 | Como gestor, quero um ranking dos materiais com maior alta de preço no período, para priorizar a revisão de compras. | Must | E3 | ⏳ |
| RF-03 | Como gestor, quero ver quais fornecedores (credores) concentraram os empenhos de cada material, para avaliar dependência e concorrência. | Must | E3 | ⏳ |
| RF-04 | Como gestor, quero comparar o preço unitário registrado no almoxarifado com o preço de mercado em lojas online, para identificar compras acima do mercado. Complemento da pergunta base. | Should | E3 | ⏳ |
| RF-05 | Como gestor, quero estimar quanto a UnB gastaria a menos se tivesse pago o preço de mercado, para dimensionar a economia possível. | Could | E3 | ⏳ |
| RF-06 | Como chefe de departamento, quero filtrar os gastos e as requisições por unidade, período e natureza da despesa, para acompanhar meu departamento. | Should | E3 | ⏳ |

### Estoque e disponibilidade

| ID | História | Prio | Etapa | Situação |
|---|---|---|---|---|
| RF-07 | Como gestor, quero consultar o saldo atual de cada material por almoxarifado, para saber o que está disponível. | Must | E3 | ⏳ |
| RF-08 | Como gestor, quero ver o valor imobilizado em estoque por material e por almoxarifado, para identificar o capital parado. | Should | E3 | ⏳ |
| RF-09 | Como gestor, quero ver o histórico do saldo de um material mês a mês, para entender o consumo. | Should | E3 | ⏳ |
| RF-10 | Como Centro Acadêmico, quero ver a demanda e os gastos por unidade acadêmica, para acompanhar como a universidade usa os recursos. | Could | E3 | ⏳ |

### Preços de mercado

| ID | História | Prio | Etapa | Situação |
|---|---|---|---|---|
| RF-11 | Como sistema, quero coletar toda semana o preço de cada material em lojas online, para ter uma série de preços de mercado. | Should | E2 | 🚧 script existe, sem execução agendada |
| RF-12 | Como sistema, quero ligar cada material do almoxarifado a uma busca confiável (`termo_busca`), para que a cotação seja do produto certo. | Should | E2 | 🚧 |
| RF-13 | Como gestor, quero que cotações atípicas (outliers, produto errado) sejam sinalizadas ou descartadas, para que a comparação de preço seja confiável. | Should | E3 | ⏳ |

### Consumo e devolução ao operacional (E4)

| ID | História | Prio | Etapa | Situação |
|---|---|---|---|---|
| RF-14 | Como gestor, quero um painel analítico que responda diretamente à pergunta de gestão, sem gráficos que não ajudam a decidir. | Must | E3 | ⏳ |
| RF-15 | Como gestor, quero que cada métrica (por exemplo, variação de preço e economia potencial) tenha uma definição única e versionada, para que duas telas nunca mostrem valores diferentes. | Must | E4 | ⏳ |
| RF-16 | Como setor de compras ou almoxarifado, quero receber a lista de materiais com preço acima do mercado em um sistema onde eu aja (tabela lida por uma aplicação, arquivo ou API), para renegociar ou rever a próxima compra. | Must | E4 | ⏳ |
| RF-17 | Como gestor, quero exportar os resultados (CSV ou PDF), para levar a análise a reuniões. | Could | E4 | ⏳ |

---

## Requisitos de dados e plataforma

### Origem e ingestão (E1 e E2)

| ID | Requisito | Prio | Etapa | Situação |
|---|---|---|---|---|
| RD-01 | Ingerir os cinco datasets do portal dados.unb.br de forma automatizada, com manifesto (url, data, sha256). | Must | E1 | ✅ |
| RD-02 | Carregar os dados em um banco transacional PostgreSQL com esquema versionado (Flyway), integridade referencial e registro de rejeitados. | Must | E1 | ✅ |
| RD-03 | A carga completa deve funcionar: todos os meses de estoque carregados (hoje 30 meses são rejeitados pela trava de queda de 30%). | Must | E2 | 🚧 |
| RD-04 | Ingestão em lote idempotente e reexecutável, sem duplicar linhas. | Must | E2 | 🚧 idempotente no OLTP; falta o destino analítico |
| RD-05 | Captura de mudanças do OLTP (CDC por decodificação lógica ou fluxo equivalente), entregue a jusante, com script que altera linhas e mostra o efeito. | Must | E2 | ⏳ |
| RD-06 | Camada analítica em formato aberto: Parquet, com tabela Iceberg ou Delta por cima. | Must | E2 | ⏳ |
| RD-07 | Parquet particionado e compactado, com serialização e compressão justificadas pelo padrão de acesso. | Must | E2 | ⏳ |
| RD-08 | Semântica de entrega declarada e demonstrada (reprocessar não muda o resultado). | Must | E2 | ⏳ |
| RD-09 | Tratamento explícito de dado atrasado e de reprocessamento de janela. | Must | E2 | ⏳ |
| RD-10 | Histórico de cargas: snapshots append-only do estoque, para comparar versões (ADR 1). | Should | E2 | 🚧 `estoque_saldo` é insert-only |

### Modelagem, transformação e orquestração (E3)

| ID | Requisito | Prio | Etapa | Situação |
|---|---|---|---|---|
| RD-11 | Modelo dimensional com fato e dimensão, **granularidade declarada por extenso** em cada fato (por exemplo, "uma linha por material por almoxarifado por mês"). | Must | E3 | ⏳ |
| RD-12 | Ao menos uma dimensão de variação lenta com histórico preservado (tipo 2), e não sobrescrita. Candidatas: unidade (nome, sigla e hierarquia mudam) e credor (razão social). | Must | E3 | ⏳ |
| RD-13 | Transformações em ferramenta declarativa e versionada (dbt ou SQLMesh), organizadas em camadas (por exemplo, *staging*, intermediária e *marts*). | Must | E3 | ⏳ |
| RD-14 | Testes de dados: esquema, volume, unicidade, integridade referencial e ao menos um de distribuição. Os testes devem pegar sujeira real do domínio (valor negativo, salto de série, material que some entre dois meses), não só `not_null` em coluna que nunca é nula. | Must | E3 | ⏳ |
| RD-15 | Orquestração agendada, com grafo de dependência e retry exercitado (derrubar uma dependência de propósito e mostrar o resultado). | Must | E3 | ⏳ |
| RD-16 | Backfill executado de verdade e demonstrável. | Must | E3 | ⏳ |
| RD-17 | Ao menos uma consulta otimizada a partir do plano de execução, com `EXPLAIN (ANALYZE, BUFFERS)` antes e depois no repositório. | Must | E3 | ⏳ |
| RD-18 | Métrica de freshness e SLA declarado para ao menos uma tabela de consumo. | Must | E3 | ⏳ |
| RD-19 | A coleta semanal de preços de mercado roda agendada dentro da mesma orquestração. | Should | E3 | ⏳ |
| RD-20 | Consultas analíticas de até 2 segundos para uso interativo (meta do ADR 1). | Should | E3 | ⏳ |

### Disponibilização e governança (E4)

| ID | Requisito | Prio | Etapa | Situação |
|---|---|---|---|---|
| RD-21 | Camada semântica de métricas (métricas do dbt ou equivalente), com a definição de cada métrica versionada num único lugar; painel e ETL reverso leem a mesma definição. | Must | E4 | ⏳ |
| RD-22 | ETL reverso: ao menos uma métrica tratada volta a um sistema operacional, com consumidor e uso declarados, e com política para o destino fora do ar (empurra ou puxa, e com que frequência). | Must | E4 | ⏳ |
| RD-23 | Catálogo de dados publicado. | Must | E4 | ⏳ |
| RD-24 | Linhagem da fonte ao consumo: de uma coluna do painel até a fonte pública, passando pelo OLTP e pelas camadas analíticas. | Must | E4 | ⏳ |
| RD-25 | Análise de LGPD: cada dado pessoal identificado (credores pessoa física, requisições de serviço), a base legal, o prazo de retenção e o mecanismo de descarte; incluir o risco de reidentificação por cruzamento de bases. | Must | E4 | 🚧 credor já está em tabela separada |
| RD-26 | Controle de acesso demonstrado em ao menos um recorte de linha ou de coluna, com privilégio mínimo (por exemplo, papéis no banco e mascaramento do nome do credor). | Must | E4 | ⏳ |

---

## Requisitos não funcionais e de processo

| ID | Requisito | Prio | Etapa | Situação |
|---|---|---|---|---|
| RNF-01 | Tudo sobe do zero com um único `docker compose up --build`, em Windows e Linux. | Must | todas | ✅ (E1); manter nas demais etapas |
| RNF-02 | Reprodutibilidade: outra pessoa clona o repositório e obtém o mesmo resultado, com instruções no README. | Must | todas | 🚧 |
| RNF-03 | Cada Entrega marcada com uma tag no repositório público (`e2`, `e3`, `e4`). | Must | todas | 🚧 só `e1` |
| RNF-04 | Portfólio completo de 5 ADRs, cada um com a opção nula considerada, uma medição e gatilhos de revisão; reler os anteriores a cada Entrega para ver se algum gatilho disparou. | Must | E4 | 🚧 só o ADR 1 |
| RNF-05 | Diário de bordo semanal e registro de uso de IA mantidos durante o trabalho, com retrospectiva do ciclo no fim. | Must | todas | 🚧 diário ainda é o modelo em branco |
| RNF-06 | Documentação publicada (Docsify), com diagramas de arquitetura, modelo e dicionário de dados. | Must | todas | ✅ |
| RNF-07 | Defesa de 20 minutos com arguição, que sirva ao público técnico (como a métrica é calculada e por que naquela granularidade) e ao de gestão (o que a plataforma permite decidir que antes não se decidia). | Must | E4 | ⏳ |
| RNF-08 | Carga mensal em até 5 minutos (meta do ADR 1). | Should | E3 | ⏳ |
| RNF-09 | Custo de armazenamento controlado, com política de retenção dos snapshots. | Should | E3 | ⏳ |
| RNF-10 | O dado não fica refém do motor: qualquer leitor compatível consegue ler a camada analítica. | Must | E2 | ⏳ |

---

## Decisões (ADRs) previstas

| ADR | Etapa | Tema | Opção nula a considerar | Situação |
|---|---|---|---|---|
| 1 | E1 | Modelo transacional *current-state* com snapshots *append-only* | Continuar como está | ✅ |
| 2 | E2 | Mecanismo de ingestão: CDC ou recarga periódica; Iceberg ou Delta; semântica de entrega | `INSERT ... SELECT` agendado | ⏳ |
| 3 | E3 | Modelagem analítica (estrela, Data Vault ou *one big table*), granularidade do fato e ferramenta de transformação e orquestração | Cron com script SQL | ⏳ |
| 4 | E4 | Como o dado é disponibilizado: camada semântica ou visões à mão; leitura do warehouse, federação ou arquivo; ETL reverso empurra ou puxa | CSV agendado | ⏳ |
| 5 | — | A definir (o portfólio exige cinco; confirmar o tema do quinto com o enunciado da disciplina) | — | ⏳ |

---

## Fora do escopo (Won't)

- Tempo real estrito: a fonte é publicada em lote mensal, e o ADR 1 aceita processamento programado.
- Alterar os dados da UnB: o sistema só lê o portal público.
- Previsão de preços ou recomendação automática de compra.
- Login por usuário na interface do painel; o controle de acesso exigido é no nível do banco (RD-26).

## Pontos em aberto

- Alinhar o README à pergunta base da página inicial (RF-00). O painel da E3 e a camada semântica da E4 dependem dela.
- Decidir se a comparação com o mercado (RF-04, RF-05) entra no MVP; se entrar, sobem para Must e as cotações (RF-11, RF-12) também.
- Definir o tema do quinto ADR.
- Escolher as ferramentas das etapas seguintes (dbt ou SQLMesh; Airflow ou Dagster; ferramenta de catálogo e linhagem; ferramenta de painel). Cada escolha vira decisão registrada em ADR.

