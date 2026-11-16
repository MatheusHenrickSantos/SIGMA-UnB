# 0006 — Ordenar candidatos CATMAT com busca híbrida, decidir a correspondência com agentes de IA sob revisão humana e buscar as compras públicas dos itens aprovados

- **Status:** proposto (falta a revisão da Squad; as decisões dos agentes ainda não foram conferidas por pessoas)
- **Data:** 2026-11-10
- **Decisores:** [a definir pela Squad] — proposta preparada com assistente de IA (ver [Uso de IA](../gestao/ai-usage.md))
- **Complementa:** [ADR 0005](0005-busca-semantica-com-pgvector.md) (pgvector, modelo e busca exata continuam valendo)

## Contexto

O ADR 0005 gera, para cada material do estoque, os itens CATMAT de vetor mais
próximo e deixa a decisão para revisão humana. Faltavam três coisas para
chegar à pergunta de gestão (preço pago pela UnB × preço de compras públicas):

1. **Ordem dos candidatos.** Com o modelo e os dados reais, o item correto
   costuma estar entre os vizinhos, mas raramente em primeiro (medição abaixo).
   Uma fila em que o certo aparece em 5º lugar custa caro para revisar.
2. **Decisão.** Revisar ~2.300 materiais à mão não cabe no prazo da Squad, e
   sem decisão não há código CATMAT para consultar preços.
3. **Compras.** A API de pesquisa de preços do Compras.gov.br só é consultada
   por código CATMAT; `raw.compras` existia vazia.

Carga: 2.306 materiais na Prata (`prata.material`), 346.140 itens no CATMAT
(250.587 ativos), lote mensal, latência de minutos aceitável.

## Alternativas consideradas

### Ordem dos candidatos

- **A. Manter só o cosseno (opção nula).** Nenhum código novo, mas a ordem
  fica como medida abaixo.
- **B. Busca híbrida: cosseno + trigramas, reordenados com rapidfuzz (escolhida).**
  Recupera também pelo texto (`pg_trgm`, já disponível no PostgreSQL) e
  reordena a união com medidas de sobreposição de termos. Sem serviço novo,
  sem custo, determinística e testável.
- **C. Cross-encoder local para reordenar.** Provavelmente ordena melhor, mas
  é mais um modelo na CPU para cada par (~70 por material) e não foi testado.
  Fica como próximo passo (ver gatilho).
- **D. LLM por API para reordenar.** Custo por material, dependência externa,
  resultado não reprodutível. Descartada como etapa automática do pipeline.

### Decisão da correspondência

- **E. Só revisão humana (opção nula).** Mais confiável, mas não termina no
  prazo e bloqueia a busca de preços.
- **F. Aprovação automática por limiar.** No conjunto de referência, um limiar
  com precisão de 95% aprovaria só ~4% dos materiais: não resolve.
- **G. Agentes de IA sugerem a decisão, pessoas conferem por prioridade (escolhida).**
  Os agentes leem os candidatos da busca e decidem, por material, os itens
  equivalentes (podem ser vários) ou "sem correspondente", com confiança e
  justificativa. A decisão é registrada como de **agente**, separada das de
  pessoas, e o pipeline segue com ela até alguém conferir.

### Compras

- **H. Script exploratório fora do Compose (situação anterior).**
- **I. Arquivos JSON por código em `dados/compras/` + carga pela mesma classe da raw (escolhida).**
  Segue o padrão de estoque e CATMAT (`InserirDadosNaCamadaRaw`), com cache por
  página para retomar downloads.

## Medição

Conjunto de referência: 150 materiais reais sorteados por almoxarifado e
família, rotulados por IA com conferência dos erros mais
evidentes (`codigos/semantica/referencia/rotulos_referencia.csv`); 103 têm
item equivalente. Reproduzir com
`docker compose run --rm semantica python -m semantica.medir_referencia`.

| Medida (103 materiais com item equivalente) | Só cosseno, top-10 (ADR 0005) | Híbrida (padrão) |
|---|---|---|
| Item correto entre os candidatos recuperados | 69,9% (10 vizinhos) | 88,3% (união de 50 por cosseno + 20 por trigramas) |
| Item correto entre os 10 gravados | 69,9% | **81,6%** |
| Item correto em 1º lugar | 40,8% | **59,2%** |

Só por trigramas, 65,0% dos itens corretos estão entre os 20 vizinhos; só por
cosseno, 86,4% estão entre os 50. As duas buscas se completam.

Tempo da etapa `corresponder` para os 2.306 materiais: ~13 min na híbrida,
~6 min só com cosseno. Candidatos com conflito de especificação entre os 10
gravados: 103 na híbrida (vão para o fim da lista) contra 2.546 só com cosseno.

Decisões dos agentes (rodada de 08/11/2026, lotes de ~100
materiais; cada lote tinha ~6 materiais do conjunto de referência escondidos
como controle): concordância de **80% (119/149)** com os rótulos de referência
nos itens de controle. As divergências são, na maioria, conservadoras (o
agente marca "sem correspondente" onde a referência aponta um item).

| Decisões importadas (2.306 materiais da Prata) | Valor |
|---|---|
| Com item equivalente | 1.620 (70%), 3.528 códigos CATMAT distintos |
| Sem correspondente | 686 (30%) |
| Confiança alta / média / baixa | 554 / 1.216 / 536 |
| Valor do estoque de 12/2025 em materiais com item equivalente | 83,1% |

Compras (janela 01/07/2025 a 31/12/2025): 2.458 dos 3.528 códigos aprovados
(70%) têm compra, com 41.514 registros em `prata.compra_publica`; 1.255
materiais ganham preço público de referência, somando **50,9% do valor do
estoque de 12/2025**.

## Decisão

1. A etapa `corresponder` passa a usar, por padrão, a **busca híbrida**:
   50 vizinhos por cosseno + 20 por trigramas (índice GiST, V4), reordenados
   por `0,40·cosseno·100 + 0,20·token_set + 0,15·token_sort + 0,25·cobertura`,
   com conflito de especificação por último (`codigos/semantica/reordenacao.py`).
   O método só por cosseno continua disponível (`--metodo cosseno`).
2. **Nada é aprovado automaticamente pela pontuação.**
3. As decisões sugeridas por agentes de IA ficam versionadas em
   `codigos/semantica/decisoes/decisoes_agentes.csv` e são importadas com
   `tipo_revisor = 'agente'` (V5). Decisão de pessoa sempre prevalece; o
   material só sai da fila de revisão quando uma pessoa decide.
4. Os itens equivalentes (de pessoa ou de agente) em `semantica.v_item_aprovado`
   alimentam o serviço `compras`, que grava `raw.compras`; o dbt gera
   `bronze.compras` (deduplicado por `id_item_compra`) e `prata.compra_publica`
   (janela `COMPRAS_INICIO`–`COMPRAS_FIM`, preço > 0).

## Consequências

**Ganhos**

- O item correto sobe na fila de revisão, o que reduz o trabalho de quem confere.
- O pipeline chega aos preços públicos sem esperar a revisão completa, e cada
  decisão diz quem decidiu (pessoa ou agente), com que confiança e por quê.
- `docker compose up` sobe a cadeia inteira até `prata.compra_publica`.

**Perdas e riscos**

- **As decisões de agente podem estar erradas** (~1 em 5 divergiu da
  referência nos controles) e a própria referência foi rotulada por IA, não por
  especialistas. Preço comparado com item errado gera conclusão errada: as
  análises da camada Ouro devem informar o `tipo_revisor` da correspondência.
- Mais uma dependência Python (`rapidfuzz`) e uma etapa a mais na busca
  (trigramas): a etapa `corresponder` leva ~13 min para os 2.306 materiais,
  contra ~6 min só com cosseno (~180 ms a mais por material).
- A janela de compras é curta (um semestre): itens com correspondente, mas
  sem compra no período, ficam sem preço de referência.

**Irreversível:** pouco. Pesos e método são configuração versionada
(`versao_reordenacao`); as decisões estão em CSV e podem ser reimportadas.

## Gatilho de revisão

- Testar a reordenação com cross-encoder local (alternativa C) se, depois da
  revisão humana, o top-1 híbrido no conjunto de referência corrigido ficar
  abaixo de 70%.
- Rever a política de decisão por agentes se a conferência humana das
  decisões de confiança `baixa` e dos materiais de maior valor alterar mais de
  20% delas.
- Ampliar a janela de compras se menos da metade do valor do estoque tiver
  preço público de referência.
