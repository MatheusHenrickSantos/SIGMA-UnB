# ADR 0003 — Queda de volume entre meses vira aviso, não recusa

| Campo | Valor |
|---|---|
| Status | Aceito |
| Data | 19/10/2026 |
| Entrega | E1 / E2 |
| Autores | [nomes] |
| ADRs relacionados | [ADR 1](adr/adr-1.md) |

## Contexto

O `carregar.py` tinha uma regra de segurança, a função `verificar_queda`. Para estoque e gastos, se um mês tivesse mais de 30% menos linhas que o mês anterior já carregado, o arquivo era **recusado**: a transação era desfeita e o `ingest` terminava com código 1. A intenção era impedir que um arquivo incompleto do portal entrasse no banco.

Na primeira carga completa (19/10/2026), a regra recusou **30 dos 40 meses de estoque**, de 11/2022 a 12/2025. Investigando:

- O estoque cai de 1.800 linhas (07/2022) para 830 (11/2022) e segue estável depois disso, descendo devagar até 680.
- Os 4 arquivos publicados para 11/2022 são cópias idênticas (mesmo md5). Não é um arquivo corrompido.
- A queda está concentrada no almoxarifado PRC (1.660 → 695). O Central quase não muda (140 → 135).
- Os 991 materiais que sumiram tinham saldo positivo, então não é apenas a omissão de itens zerados.
- Não existem arquivos de 08, 09 e 10/2022, e a mudança acontece dentro dessa lacuna.

Como a regra compara sempre com o último mês **aceito**, todos os meses seguintes eram comparados com as 1.800 linhas de 07/2022 e recusados em cadeia. O banco ficava sem estoque depois de 07/2022, justamente o período mais relevante para a pergunta de gestão.

## Alternativas consideradas

### A. Opção nula — manter a recusa

- **Prós:** protege contra arquivos truncados.
- **Contras:** uma mudança real na origem bloqueia permanentemente todos os meses seguintes. Hoje isso significa perder 30 de 40 meses de estoque.

### B. Desligar a verificação

- **Prós:** simples.
- **Contras:** perde o sinal de que algo mudou na origem; uma quebra como a de 11/2022 passaria despercebida.

### C. Manter a verificação, mas como aviso

- **Prós:** carrega o dado real, mantém o sinal visível no log e encadeia as comparações pelo mês realmente carregado, de modo que só o mês da quebra gera aviso.
- **Contras:** um arquivo realmente truncado também entraria no banco; a detecção passa a depender de alguém ler os avisos.

### D. Lista de exceções aprovadas (ex.: "estoque 11/2022 é quebra conhecida")

- **Prós:** mantém a recusa para casos novos.
- **Contras:** exige editar código ou configuração a cada mudança da origem; pouco ganho para o volume atual.

## Medição

| Situação | Meses de estoque no banco | Avisos | `ingest` |
|---|---:|---:|---|
| A — recusa (antes) | 10 (09/2020 a 07/2022) | — | código 1, 30 erros |
| C — aviso (depois) | 40 (09/2020 a 12/2025) | 1 (11/2022) | código 0 |

Verificação:

```sql
SELECT to_char(data_referencia,'YYYY-MM') mes, count(*)
FROM estoque_saldo GROUP BY 1 ORDER BY 1;
```

## Decisão

Adotamos a **alternativa C**. `verificar_queda` passa a devolver uma mensagem em vez de levantar `RuntimeError`, e `carregar_arquivo` imprime essa mensagem como `AVISO:` e grava o arquivo normalmente.

A quebra de 11/2022 fica registrada como **mudança de patamar na origem, de causa não identificada**, em [Caracterização da carga](caracterizacao-da-carga.md#_5-qualidade-dos-dados).

## Consequências

- **Positivas:**
  - Os 40 meses de estoque ficam disponíveis.
  - O `ingest` volta a terminar com código 0.
  - A quebra continua visível no log.
- **Negativas:**
  - Um arquivo truncado pelo portal também seria aceito.
  - Comparações de **quantidade de itens** antes e depois de 11/2022 precisam de ressalva. Comparações de **preço**, que são o foco da pergunta de gestão, não são afetadas.
- **O que mudou no repositório:** `codigos/carregar.py` (`verificar_queda` e a chamada em `carregar_arquivo`).
- **Sugestão futura:** gravar o aviso em `carga_execucao` (exige uma nova migração), para que ele possa ser consultado no banco e não só no log.

## Gatilho de revisão

- A UnB explicar a quebra de 11/2022 (pedido via Fala.BR ou contato do dados.unb.br).
- Um novo aviso de queda aparecer em uma carga futura.
- Ser confirmado que o portal trunca arquivos (como parece acontecer com empenhos, sempre com 10.000 registros). Nesse caso, a recusa para arquivos suspeitos pode voltar a fazer sentido.
