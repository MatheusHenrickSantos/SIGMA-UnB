# 0010 — Definir as métricas em macros dbt, materializadas numa tabela, em vez de métricas MetricFlow ou SQL em cada consumidor

- **Status:** proposto (falta a revisão da Squad e a medição com a carga real)
- **Data:** 2026-11-24
- **Decisores:** [a definir pela Squad] — proposta preparada com assistente de IA (ver [Uso de IA](../gestao/ai-usage.md))

> Nome: aqui "camada semântica" é a **camada de métricas de consumo** depois da Ouro. Não confundir com o schema `semantica` (hoje `busca`), que guarda embeddings e candidatos CATMAT; ver ADR 0008.

## Contexto

O painel da E3 e o registro de qualidade escreviam fórmulas cada um por si. Na revisão desta rodada achamos uma métrica com **duas definições no mesmo repositório**: "cobertura de preço público" era *com preço ÷ materiais em estoque* no painel e *com preço ÷ materiais com item CATMAT* em `qualidade_dados`. Com o ETL reverso da E4 seriam três consumidores. Se duas telas mostram a "mesma" cobertura com valores diferentes, a plataforma perde autoridade.

Carga: fato com 39.182 linhas (06/2021 a 12/2025, 2 almoxarifados), 13 métricas, 3 consumidores (painel Streamlit, `qualidade_dados`, ETL reverso). Atualização mensal. Competência da equipe: SQL e dbt; ninguém usou MetricFlow. Restrição: o painel é Streamlit lendo PostgreSQL, sem serviço de API intermediário.

## Alternativas consideradas

### A. Opção nula — cada consumidor escreve a sua fórmula

Era o que existia. Zero código novo, e é a opção mais simples de ler isoladamente. Não escolhida porque já produziu duas definições divergentes; o custo aparece só quando alguém compara as telas.

### B. Métricas do dbt (`semantic_models` + `metrics`, MetricFlow)

Centraliza a definição em YAML e gera o SQL. Cobra: o pacote do MetricFlow, e consumo por CLI ou pela Semantic Layer API (serviço do dbt Cloud, pago). O painel Streamlit e o ETL reverso não consultariam as métricas sem uma dependência ou um serviço novo. Sem equipe que o conheça.

### C. Macros dbt + tabela materializada (`ouro.metrica_mensal`) — escolhida

A definição (nome, unidade, versão, descrição, fórmula) é uma lista em `macros/metricas.sql`. Um modelo aplica as fórmulas e grava o formato longo; outro grava o catálogo. Os consumidores leem a tabela ou usam as macros de condição (`condicao_alerta`). Sem dependência nova.

### D. Visões materializadas escritas à mão

Simples, e a divergência volta: cada visão é uma fórmula que ninguém compara com a outra.

## Medição

Banco local com estoque real e compras sintéticas (a carga real das compras ainda não rodou; os tempos dependem do volume do fato, não do conteúdo das compras).

Como reproduzir:

```bash
dbt build --select metrica_mensal catalogo_metrica consistencia_metricas_e_alertas
# tempos: EXPLAIN (ANALYZE) nas duas formas, como em docs/dados-e-pipeline/consumo-e-etl-reverso.md#medicoes
```

| Alternativa | Lugares onde a fórmula é escrita | Ler os KPIs de um mês | Série completa | Custo de construir |
|---|---|---|---|---|
| A — opção nula | 3 (painel, qualidade, ETL) | 2,7 ms (recalcula no fato) | 24,5 ms | 0 |
| C — macros + tabela | 1 | 0,085 ms | 0,080 ms | 2,7 s por carga |
| B — MetricFlow | 1 | não medido | não medido | dependência e serviço novos |
| D — visões à mão | 1 por visão | similar a C | similar a C | baixo |

Com 39 mil linhas todas as formas são rápidas: **a decisão não é de desempenho, é de definição única.** O que o teste `consistencia_metricas_e_alertas` mede é a divergência entre a métrica e o que o ETL reverso entrega (91 = 91 alertas; diferença de R$ 0,49 na economia, por arredondamento).

## Decisão

Escolhemos C: métricas em `macros/metricas.sql`, materializadas em `ouro.metrica_mensal`, com `ouro.catalogo_metrica` documentando cada uma e um histórico de versões na própria macro.

## Consequências

**O que ganhamos:** um lugar para mudar uma fórmula; painel, qualidade e alertas mudam juntos. Um teste (`consistencia_metricas_e_alertas`) pega divergência entre a métrica e o dado entregue. O catálogo no painel nunca fica diferente da fórmula, porque é gerado dela.

**O que perdemos:** só calcula o que está materializado (mês × almoxarifado, mais o total). Uma pergunta por dimensão nova (por grupo CATMAT, por fornecedor) exige mexer na macro e recalcular. Métricas não aditivas (mediana, razões) são recalculadas por grupo, e o total `TODOS` não é a soma dos almoxarifados. A fórmula é SQL em texto dentro de uma macro Jinja: quem edita precisa conhecer as duas coisas, e um erro só aparece na execução do dbt.

**O que se torna irreversível:** nada em dado. Migrar para MetricFlow custa reescrever 13 definições em YAML; as tabelas de saída e os consumidores continuam iguais se o formato longo for mantido.

## Gatilho de revisão

- Migrar para MetricFlow (alternativa B) se o painel precisar de uma dimensão que não está materializada em **mais de 3 perguntas por semestre**, ou se as métricas passarem de **25**.
- Reavaliar a materialização se `metrica_mensal` levar mais de **60 s** para construir ou o fato passar de **5 milhões de linhas**.
- Reabrir se o teste de consistência falhar por **duas cargas seguidas** (as definições passaram a divergir apesar da camada).
- Registrar a medição com a carga real (CATMAT e compras completos) e mudar o status para aceito.
