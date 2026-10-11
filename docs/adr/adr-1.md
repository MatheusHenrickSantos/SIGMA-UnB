# Adotar modelo transacional *current-state* com snapshots *append-only* no destino

- **Status:** aceito
- **Data:** 2026-09-27
- **Decisores:**  
  - Israel Thalles Dutra dos Santos  
  - Magno Luiz Vale Vieira  
  - Matheus Henrick Dutra dos Santos  
  - Samara Letícia Alves dos Santos  

## Contexto

A plataforma responde à pergunta: quais unidades da UnB concentraram maior demanda
 de materiais e gastos de almoxarifado no período disponível, e quais itens do
 estoque atual têm maior valor imobilizado? A fonte pública não oferece log
 completo de eventos e a carga é predominantemente analítica, com atualização
 periódica em lote. Portanto, o desenho do dado precisa refletir fielmente o estado
 publicado pela origem sem assumir uma semântica de evento que não exista de forma
 explícita.

A carga observada no recorte de dados do projeto é composta por 17.474 requisições
 de materiais, 1.933 registros de estoque, 1.358 gastos, 408 requisições de serviço
 e 98 unidades. O padrão de acesso é majoritariamente de leitura: consultas por
 período, unidade, grupo de material, status e almoxarifado; agregações por
 ano/mês; filtros por data e situação. A latência aceitável é de até 2 segundos
 para consultas interativas e até 5 minutos para a carga mensal. A integridade
 referencial precisa ser mantida sem descartar registros válidos, e o armazenamento
 deve ser controlado, pois snapshots futuros aumentam o volume de dados.

Além disso, há restrições não funcionais relevantes: consistência e integridade dos
 dados devem ser preservadas; a disponibilidade não exige tempo real, mas sim
 processamentos programados em lote; os custos de armazenamento devem ser
 administrados; a fonte é pública e não oferece histórico confiável de mudanças por
 evento; e a equipe já possui familiaridade com modelagem relacional, SQL e
 pipelines de carga em lote. Esse conhecimento da equipe é uma restrição legítima e
 influencia diretamente a escolha da arquitetura.

## Alternativas consideradas

### A. Opção nula — continuar como está

A alternativa sem mudança preserva o modelo atual de origem e é simples de operar,
 com pouco volume e alinhamento ao padrão normal de sistemas transacionais.
 Porém, ela perde o estado anterior quando há atualização e não permite reconstruir
 o histórico de mudanças. Também não preserva a evolução temporal dos registros,
 o que compromete análises comparativas entre cargas futuras e a semântica dos
 dados publicados pela origem.

### B. *Insert-only* / eventos a partir da origem

Essa alternativa preserva o histórico de forma explícita e facilita auditoria
 temporal. Ela oferece um modelo muito forte para rastreabilidade e análise de
 mudanças ao longo do tempo.

No entanto, ela atribui semântica de evento sem evidência na origem, porque a fonte
 pública do UnB não é um log de eventos e não publica versões históricas confiáveis
 de cada registro. Isso aumenta o volume de dados, exige deduplicação,
 versionamento e tratamento de estado atual, e pode levar a interpretações falsas
 sobre diferenças entre cargas como se fossem eventos de negócio reais.

### C. Modelo transacional *current-state* com snapshots *append-only* no destino

Essa alternativa representa fielmente o estado atual da origem, mantendo snapshots
 append-only no destino para preservar o que foi publicado em cada carga futura.
 Ela combina a semântica do estado corrente com a possibilidade de comparar
 diferentes versões do conjunto de dados sem apagar o passado.

Ela oferece o melhor equilíbrio entre integridade, representatividade da fonte e
 simplicidade operacional para um caso em que a origem não emite eventos de forma
 confiável. O custo é a necessidade de controlar volume, retenção e comparação de
 snapshots ao longo do tempo.

## Medição

Os dados usados como evidência foram os arquivos públicos do projeto de almoxarifado
 da UnB, com recorte contendo 17.474 requisições de materiais, 1.933 registros de
 estoque, 1.358 gastos, 408 requisições de serviço e 98 unidades. A consulta mais
 frequente foi a análise por unidade, período, material, status e almoxarifado,
 com agregações por ano e mês e filtros por data e situação.

A validação foi feita observando o padrão de leitura analítica e escrita em lote na
 ingestão da publicação, e confirmando que nem toda unidade das requisições aparece
 no cadastro acadêmico. Isso reforça a necessidade de manter a integridade
 referencial do dado e evitar a simplificação do modelo em direção a uma semântica
 de evento inexistente na fonte.



## Decisão

Escolhemos adotar o modelo transacional current-state com snapshots append-only no
 destino. Essa estrutura representa fielmente o estado publicado pela origem,
 preserva o histórico das cargas futuras sem assumir que a fonte é um event log,
 e mantém a integridade referencial, o acesso analítico e a operação em lote dentro
 de um modelo que a equipe consegue sustentar.

## Consequências

**O que ganhamos:**

- Representação fiel da semântica da fonte, sem inventar eventos que não existem.
- Reforço da integridade com PK, FK, NOT NULL, CHECK e UNIQUE.
- Preservação do estado anterior em snapshots futuros, sem perda de contexto histórico.
- Consultas analíticas por unidade, período e material mais previsíveis e eficientes.
- Possibilidade de comparar cargas futuras para análise temporal e evidência de
  mudanças de estado.

**O que perdemos:**

- O volume de armazenamento cresce com o acúmulo de snapshots.
- O histórico entre cargas exige comparação e versionamento explícito de snapshots.
- O banco precisa controlar política de retenção e organização dos dados do estado
  atual e do histórico.
- Não se pode afirmar que qualquer diferença entre cargas seja necessariamente um
  evento de negócio real. A ambiguidade entre data do evento e data de ingestão
  precisa ser tratada com cuidado.

**O que se torna irreversível:**

A decisão cria uma dependência de uma política de retenção e versionamento no
 destino. Migrar de volta para um modelo puramente current-state ou para um modelo
 de eventos exigirá reprocessamento dos dados, reescrita de regras de consulta e
 revisão do histórico acumulado.

## Gatilho de revisão

A decisão deve ser reaberta se o volume de snapshots crescer além do previsto, se a
 fonte pública passar a publicar eventos ou versões históricas confiáveis, ou se o
 desempenho operacional e os custos de armazenamento ultrapassarem os limites
 previstos pelo projeto. Em outras palavras, a revisão deve ocorrer quando a
 escalabilidade do modelo ou a evolução da fonte demonstrar que a hipótese atual não
 é mais sustentável.
