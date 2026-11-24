# Revisão do portfólio de ADRs e dos gatilhos de revisão (E4)

Releitura de todos os ADRs em 24/11/2026: cada um tem a opção nula, uma medição e um gatilho? Algum gatilho já disparou? Se disparou e a decisão não foi revista, está registrado abaixo.

## Portfólio

| ADR | Decisão | Status | Opção nula | Medição | Gatilho com número | Situação |
|---|---|---|:-:|:-:|:-:|---|
| [1](adr/adr-1.md) | Modelo *current-state* com snapshots append-only | aceito | sim | sim | parcial (sem limiares) | Texto descreve o pipeline da E2 (CDC, Delta), que está na branch `e2-entrega` e não na `main` |
| [0002](adr/0002-mecanismo-de-ingestao-e-formato-aberto.md) | Ingestão e formato aberto da camada bruta | **modelo não preenchido** | — | — | — | O ADR real (Delta Lake + Parquet ZSTD) está em `adr-2.md` na branch `e2-entrega`, e foi superado pelo 0007 (ouro em PostgreSQL com dbt) e pelo 0009 (raw direto) |
| [0003](adr/0003-validacao-de-volume-na-carga_1.md) | Queda de volume vira aviso | aceito | sim | sim | sem número | Descreve `codigos/carregar.py`, que foi removido; hoje a regra é o teste dbt `volume_estoque_mensal` com exceções em semente |
| [0004](adr/0004-adotar-dados-de-estoque-e-precos-publicos.md) | Estoque + preços públicos como foco | aceito | sim | sim | sim (50%) | Dois dos três gatilhos estão disparados ou indeterminados (abaixo) |
| [0005](adr/0005-busca-semantica-com-pgvector.md) | Busca por embeddings no pgvector, exata | proposto | sim | sim (vetores aleatórios) | sim | Medição com vetores reais pendente; gatilho 3 disparou e gerou o 0006 |
| [0006](adr/0006-busca-hibrida-e-decisoes-por-agentes.md) | Busca híbrida e decisões por agentes | proposto | sim | sim | sim | Gatilho 1 abaixo do limiar; gatilho 2 sem como avaliar |
| [0007](adr/0007-modelo-estrela-para-comparacao-de-precos.md) | Modelo estrela, grão mensal, dbt + Dagster | proposto | sim | tabela de grão (sem seção própria) | sim | Nenhum gatilho disparado; tensão com a minimização do fornecedor (0012) |
| 0008 *(branch `feat/prata-correspondencias-busca-tecnica`)* | Correspondência na prata; schema `busca` | aceito | descartada, sem seção de opção nula | não | **não** | Sem medição nem gatilho |
| 0009 *(idem)* | Gravar as APIs direto na raw | aceito | não | não | **não** | Sem opção nula, medição nem gatilho |
| [0010](adr/0010-camada-semantica-de-metricas-em-macros-dbt.md) | Métricas em macros dbt | proposto | sim | sim | sim | Novo (E4) |
| [0011](adr/0011-etl-reverso-por-arquivo-e-tabela-com-destino-que-puxa.md) | ETL reverso por arquivo e tabela, destino puxa | proposto | sim (CSV) | sim | sim | Novo (E4) |
| [0012](adr/0012-governanca-lgpd-e-controle-de-acesso.md) | Minimização e controle de acesso por papéis | proposto | sim | sim | sim | Novo (E4) |

Quatro dos sete ADRs da `main` ainda estão **propostos**, sem revisão da Squad (0005, 0006, 0007 e os novos). Um ADR proposto que sustenta o pipeline em produção local é decisão tomada sem revisão: item de retrospectiva.

## Gatilhos que dispararam (ou não podem ser avaliados)

| ADR | Gatilho | Estado | Evidência | O que fazer |
|---|---|---|---|---|
| 0003 | A UnB explicar a quebra de 11/2022 | **Aberto desde 10/11** | Nenhuma resposta registrada; a série tem ainda 16 de 55 meses sem arquivo | Pedir via Fala.BR; manter a exceção `PRC 2022-11` na semente |
| 0003 | (implícito) a decisão "aviso, não recusa" deixou de valer | **Superada sem ADR** | `carregar.py` saiu em 09/11; `tests/volume_estoque_mensal.sql` faz o build falhar a menos que a ocorrência esteja em `seeds/excecoes_qualidade.csv`: voltou a ser recusa com lista de exceções | Atualizar o 0003 (status "parcialmente substituído") ou escrever um ADR novo para o teste |
| 0004 | Menos de 50% dos materiais com correspondência **revisada** e preço público | **Indeterminado, provavelmente disparado** | 0 de 2.306 correspondências revisadas por pessoa; só por agente, 1.255 de 2.306 (54%) têm preço público (carga de 10/11) | Definir "revisada" (pessoa?) e conferir uma amostra |
| 0004 | Dados não permitem verificar unidade ou período em mais da metade dos preços | **Disparado para a unidade** | O estoque não informa unidade de fornecimento (100% das linhas); o teste `distribuicao_preco_compra_publica` já registrava 5,86% de compras a mais de 10× da mediana por unidades diferentes (carga de 10/11); `qualidade_dados` passa a medir a divergência de unidade com a carga real; o painel avisa a limitação | Registrar no escopo que a comparação é um sinal; avaliar conversão de unidade (ADR 0011, gatilho) |
| 0005 | Medição com vetores reais | **Pendente** | Só há medição com vetores aleatórios | Rodar `medir_adr0005.py real` depois da carga completa (em andamento) e mudar o status |
| 0005 | Menos de 70% com item equivalente entre os candidatos | **Disparou para o cosseno puro (69,9%) e gerou o 0006** | 0006 mede 88,3% recuperados na busca híbrida | É o exemplo de gatilho que funcionou |
| 0006 | Top-1 híbrido abaixo de 70% depois da revisão humana | **Abaixo (59,2%)**, mas o conjunto de referência é rotulado por IA | Não existe referência corrigida por pessoa | Testar o cross-encoder (alternativa C) ou rotular uma amostra por pessoas |
| 0006 | Conferência humana altera mais de 20% das decisões de confiança baixa | **Não avaliável** | 0% conferido por pessoa | Priorizar a [fila de conferência](dados-e-pipeline/consumo-e-etl-reverso.md) por valor × confiança |
| 0006 | Menos da metade do valor do estoque com preço público | **Por 0,9 ponto não disparou** (50,9%) | `qualidade_dados` marca `comparacao_valor_comparavel_pct` em *atenção* (limite 60) | Ampliar a janela de compras e medir de novo |
| 0007 | Grão mensal insuficiente se a pergunta exigir fornecedor | **Em tensão** | O backlog original (RF-03) pergunta por fornecedores; o 0012 remove o fornecedor da raw | Decidir com a Squad: reter só CNPJ de pessoa jurídica com acesso restrito (gatilho do 0012) |

## Lacunas do portfólio

- **ADR 0002**: preencher ou marcar como substituído. É o único com todos os campos ainda entre colchetes.
- **ADRs 0008 e 0009** (na branch de outra pessoa da Squad): faltam a opção nula, uma medição e o gatilho com limiar, que são o que a revisão desta Entrega confere.
- **Status "proposto"** em 0005, 0006 e 0007: pedir a revisão da Squad nesta Entrega.
- **Gatilhos sem número** (ADR 1, ADR 0003): trocar "volume além do previsto" por um limiar medido.

## Como manter

A cada Entrega: reler este quadro, medir os números que os gatilhos citam (todos têm consulta ou script) e anotar aqui o que disparou. Os números do painel de qualidade (`ouro.qualidade_dados`) já cobrem boa parte: frescor, cobertura, unidade, correspondência conferida.
