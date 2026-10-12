# Capturar mudanças por consulta, com marca d'água em atualizado_em

- **Status:** proposto (passa a aceito quando a tabela de Medição estiver preenchida)
- **Data:** 2026-10-12
- **Decisores:** Squad SIGMA-UnB (confirmar nomes na revisão)

## Contexto

A E2 pede dois caminhos de natureza diferente da origem até a bronze: um em
lote e um fluxo de mudanças (CDC ou streaming). O lote (`extrair_lote.py`) tira
uma foto completa de cada tabela. Falta o caminho que leva **só o que mudou**,
com o histórico de versões que a dimensão de variação lenta da E3 vai usar.

Como as mudanças acontecem no domínio:

- **Frequência:** o portal publica uma vez por mês; a carga roda logo depois.
  Não há escrita contínua, nem usuário editando o banco.
- **O que muda de verdade:** empenhos republicados com valores anulados,
  reforçados ou cancelados; requisições que mudam de status ou recebem
  autorização; unidades que mudam de nome ou sigla. Estoque e cotações são só
  inserção (uma foto por mês).
- **Remoções:** o `carregar.py` não apaga nenhuma linha.
- **O que a origem já oferece:** toda tabela tem `carregado_em`, e as tabelas com
  upsert têm `atualizado_em`. O `carregar.py` só altera `atualizado_em` quando um
  campo muda de verdade (`ON CONFLICT ... DO UPDATE ... WHERE ... IS DISTINCT FROM
  EXCLUDED`), e arquivos com o mesmo sha256 não são recarregados. Então
  recarregar não gera mudança falsa.
- **Latência tolerada:** horas; o dado de origem tem atraso de um mês.
- **Equipe:** conhece SQL e Python, nunca operou Kafka.

## Alternativas consideradas

### A. Opção nula: só o lote

Uma foto completa por execução já permite comparar fotos na E3. Mas a E2 exige
um segundo caminho de natureza diferente, e comparar fotos inteiras para achar
o que mudou custa reler e diferenciar tudo a cada mês.

### B. CDC por consulta (marca d'água)

A cada execução, para cada tabela: `WHERE atualizado_em > <marca anterior>`
(ou `carregado_em` nas insert-only), gravando um Parquet novo em `bronze/cdc/`
com `_operacao` (`insert`/`update`), `_capturado_em` e `_marca_anterior`. A marca
fica em `bronze/_controle/marcas_cdc.json` e só avança depois da gravação.
Só precisa de SQL e de um índice por tabela (migração V2).

### C. CDC por log (Debezium + Kafka/Redpanda)

Lê o WAL do Postgres e emite cada INSERT, UPDATE e DELETE como evento, inclusive
duas mudanças seguidas na mesma linha. É o CDC "de verdade". Custa três serviços
a mais (Kafka ou Redpanda, Kafka Connect com Debezium, um consumidor que grave
Parquet), `wal_level=logical` no Postgres e uma tecnologia que ninguém da
equipe operou, para um banco que muda uma vez por mês.

## Medição

Protocolo, com os dados reais do portal:

```
docker compose up --build -d                                # rodada 1: carga inicial
docker compose logs -f extract                              # espere o extract terminar
docker compose run --rm --no-deps extract python capturar_mudancas.py # rodada 2: sem mudança
docker compose exec -T db psql -U sigma -d sigma < db/demo/mudancas_demo.sql
docker compose run --rm --no-deps extract python capturar_mudancas.py # rodada 3: depois da mudança
docker compose run --rm --no-deps extract python verificar_e2.py
docker compose run --rm --no-deps extract python medir_e2.py          # seção "ADR 4"
```

Na rodada 3, o ideal é carregar um mês novo do portal em vez do script de
demonstração: aí as mudanças são reais.

| Rodada | Linhas capturadas | insert | update | Tempo |
|---|---|---|---|---|
| 1 — carga inicial | _preencher_ | _preencher_ | _preencher_ | _preencher_ |
| 2 — sem mudança | _preencher (esperado: 0)_ | | | _preencher_ |
| 3 — depois da mudança | _preencher_ | _preencher_ | _preencher_ | _preencher_ |

| Alternativa | Linhas lidas por execução | Tempo total (medir_e2.py) |
|---|---|---|
| A — lote completo | _preencher_ | _preencher_ |
| B — CDC por consulta | _preencher_ | _preencher_ |

Correção: o `verificar_e2.py` reconstrói o estado atual só a partir de
`bronze/cdc/` (última versão de cada chave) e exige as mesmas chaves e o mesmo
`atualizado_em`/`carregado_em` do Postgres. Resultado: _preencher (OK/DIVERGE)_.

## Decisão

Escolhemos B: CDC por consulta, com marca d'água por tabela.

## Consequências

**O que ganhamos:**

- Cada execução lê só o que mudou, usando índice (V2), em vez de reler tudo.
- `bronze/cdc/` vira o histórico de versões de cada linha, base da dimensão de
  variação lenta da E3 (unidade que muda de nome, empenho anulado).
- Nenhum serviço novo além do MinIO; a lógica é SQL que a equipe lê e testa.

**O que perdemos:**

- **DELETE não é capturado.** Uma linha apagada no Postgres continua "viva" na
  bronze/cdc. Hoje o risco é baixo porque o `carregar.py` não apaga nada; quem
  passar a apagar precisa trocar por exclusão lógica (coluna `excluido_em`).
- **Mudanças intermediárias se perdem.** Se uma linha mudar duas vezes entre duas
  capturas, só a última versão aparece. Com uma carga por mês e a captura logo
  depois, isso só acontece com edição manual no banco.
- **A marca depende do relógio do Postgres.** `now()` é a hora do início da
  transação; uma carga longa ainda não confirmada poderia gravar linhas com
  horário anterior à marca. O script se protege limitando a captura ao início da
  transação aberta mais antiga (testado com uma transação de 6 s aberta durante
  a captura: nenhuma linha perdida).
- **Atualização feita fora do `carregar.py`** precisa marcar `atualizado_em` à mão
  (o `db/demo/mudancas_demo.sql` faz isso); senão a mudança fica invisível.

**O que se torna irreversível:**

Nada na origem: o CDC só lê. Trocar por Debezium depois é acrescentar serviços,
e o histórico já capturado em `bronze/cdc/` continua válido como ponto de partida.

## Gatilho de revisão

- Revisar se alguma tabela passar a ter DELETE físico.
- Revisar se a latência tolerada cair para menos de 1 hora (aí rodar a consulta
  de minuto em minuto fica caro e o CDC por log passa a compensar).
- Revisar se o `verificar_e2.py` acusar versão faltando no CDC em qualquer
  execução.
