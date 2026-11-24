# Retrospectiva do ciclo de vida (E4)

**Período:** 30/08/2026 a 24/11/2026 · **Entregas:** E1 a E4
**Rascunho preparado com assistente de IA a partir do repositório, dos ADRs e do diário; a Squad deve revisar e completar com o que viveu.**

Segue o formato do [diário de bordo](gestao/diario-de-bordo.md): o que foi medido, o que surpreendeu, o que foi decidido, o que fica pendente.

## O ciclo percorrido

| Entrega | Etapa do ciclo | O que ficou de pé | Onde está |
|---|---|---|---|
| E1 | Fonte e modelagem transacional | Tema (estoque da UnB + preços públicos, ADR 4), modelo ER/relacional, esquema OLTP (V1) | `docs/modelagem/`, `db/migrations/V1` |
| E2 | Ingestão em lote e captura de mudanças | Carga do estoque (39 meses), ADR 0003; CDC e Delta Lake **só na branch `e2-entrega`** | `docs/dados-e-pipeline/caracterizacao-da-carga.md` |
| E3 | Camada analítica transformada, testada e orquestrada | raw → bronze → prata → ouro com dbt, testes de volume/distribuição, busca semântica, snapshot SCD 2, Dagster, painel | `models/`, `tests/`, `orquestracao/`, `painel/` |
| E4 | Disponibilização e governança | Camada de métricas, ETL reverso, catálogo e linhagem, LGPD, acesso por papéis | `macros/metricas.sql`, `models/reverso/`, `docs/governanca/` |

## O que foi medido

- **Estoque (39 arquivos, 39.191 linhas):** 1 preço não positivo; 0 chaves repetidas; diferença líquida de 0,05% entre `valor_total` do portal e saldo × preço; 16 de 55 meses sem arquivo (29%). [Confiabilidade](dados-e-pipeline/confiabilidade.md).
- **Correspondência material × CATMAT:** 2.306 decisões, **todas de agentes de IA, 0 conferidas por pessoa**. Concordância 80% (119/149), mas os rótulos de referência também são de IA.
- **Cobertura:** 54% dos materiais e 50,9% do valor do estoque com preço público (carga de 10/11).
- **Camada de métricas:** 13 métricas, 1 definição cada (antes 3 lugares); ler um mês: 0,085 ms contra 2,7 ms recalculando; construir: 2,7 s.
- **LGPD:** a amostra de 60 códigos (408 compras) só tinha CNPJ, mas a contagem nas 41.522 compras reais achou 11 CPF; o gatilho do ADR 0012 disparou. O JSON bruto trazia o fornecedor, que a análise não usa, e a V12 o remove da raw.
- **ADRs:** 12 no portfólio, 4 de 7 na `main` ainda "propostos"; ver [revisão dos gatilhos](adr/revisao-dos-gatilhos.md).

## O que surpreendeu

1. **Uma métrica com duas definições no mesmo repositório.** "Cobertura de preço público" estava ÷ materiais em estoque no painel e ÷ materiais com item CATMAT no registro de qualidade. Só apareceu ao montar a camada de métricas.
2. **A ordem do pipeline estava errada.** `transformar` construía `compras_bronze` antes de `raw.compras` existir; os testes rodavam sobre uma tabela vazia e passavam.
3. **A validação da correspondência era circular.** Os 150 rótulos de referência coincidem em 98,7% com as decisões dos agentes: medir um contra o outro não é validação independente.
4. **O dado pessoal estava na raw sem ninguém ter decidido isso.** O fornecedor vinha no JSON da API e foi guardado por inércia.
5. **Dois nomes para "semântica".** O schema `semantica` (busca vetorial) e a camada semântica de métricas da E4 são coisas diferentes; a branch de Matheus renomeia o schema para `busca` (ADR 0008).
6. **Trabalho que não chegou à `main`.** CDC, Delta Lake e o ADR 2 reais estão na `e2-entrega`; o ADR 0002 da `main` é o modelo em branco. A decisão foi superada (ouro em PostgreSQL) sem registro.
7. **O estoque some e volta.** 29% dos meses não foram publicados; a queda de 11/2022 segue sem explicação.

## O que foi decidido

| Decisão | Onde |
|---|---|
| Métricas em macros dbt, materializadas | [ADR 0010](adr/0010-camada-semantica-de-metricas-em-macros-dbt.md) |
| ETL reverso por CSV e tabela, destino puxa | [ADR 0011](adr/0011-etl-reverso-por-arquivo-e-tabela-com-destino-que-puxa.md) |
| Minimizar fornecedor na raw; papéis, coluna e RLS | [ADR 0012](adr/0012-governanca-lgpd-e-controle-de-acesso.md) |
| Corrigir a ordem do pipeline (`transformar` sem compras; `semantica tudo` com `validar`) | branch `fix/ordem-pipeline` |
| Painel com tema fixo da UnB, busca de produto, qualidade e fila de revisão | branch `feat/painel-unb` |

## Gatilhos que dispararam e não foram revistos

Veja o quadro completo em [Revisão dos gatilhos](adr/revisao-dos-gatilhos.md). Os que doem:

- **ADR 0004:** unidade verificável em menos da metade dos preços (o estoque não tem unidade) e correspondência "revisada" em 0% dos materiais. O escopo foi mantido sem registrar a decisão de manter.
- **ADR 0006:** top-1 da busca em 59,2% (limiar 70%). O cross-encoder previsto não foi testado.
- **ADR 0003:** a decisão "aviso, não recusa" foi desfeita por um teste dbt sem atualizar o ADR.
- **ADR 0005:** a medição com vetores reais, condição para sair de "proposto", ficou para depois.

## O que deixaríamos diferente

- **Começar a governança antes.** LGPD, acesso e linhagem dependem de decisões da raw: o fornecedor ficou lá sem decisão explícita, e a minimização de agora é irreversível. Decidir na E3 evitaria isso.
- **Rotular uma amostra por pessoas na E3**, não por IA. Sem isso, os gatilhos do 0006 não são avaliáveis e a correspondência fica em "palpite revisado por palpite".
- **Um ADR por decisão, no dia, com a medição.** Hoje 0005, 0006 e 0007 seguem "propostos" e 0008 e 0009 não têm opção nula, medição nem gatilho.
- **Integrar a `e2-entrega` ou descartá-la com um ADR**, em vez de deixá-la como branch paralela por um mês.

## Pendências

- [ ] Revisão da Squad dos ADRs 0005, 0006, 0007, 0010, 0011 e 0012 (mudar de "proposto") — [a definir]
- [ ] Conferir por pessoas as correspondências de confiança baixa e de maior valor — [a definir]
- [ ] Preencher ou marcar como substituído o ADR 0002; completar 0008 e 0009 — [a definir]
- [x] Painel conectado como `sigma_painel_app` (V13), testado.
- [x] Cache de compras e dump de segurança expurgados do fornecedor (24/11/2026); o dump com o dado foi apagado.
- [ ] Combinar com compras um retorno do alerta (conferido, descartado, renegociado) — [a definir]
- [ ] Integrar a branch `feat/prata-correspondencias-busca-tecnica` com as desta rodada (conflito conhecido em `models/fontes.yml`; as fontes do dbt passam de `semantica` para `busca` e `prata`) — [a definir]
