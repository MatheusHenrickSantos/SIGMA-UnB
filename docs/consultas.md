# Consultas

Consultas SQL sobre o estoque do almoxarifado que apoiam a [pergunta de gestão](dominio-e-pergunta.md). Elas usam só as tabelas `estoque_saldo`, `material`, `almoxarifado` e `unidade`. As consultas que comparam com o preço de mercado (`cotacao_online`) entram quando a coleta de cotações estiver no banco.

Para rodar:

```bash
docker compose exec db psql -U sigma -d sigma
```

**Como ler o estoque:** `estoque_saldo` guarda uma *foto mensal* do saldo (insert-only, ver [ADR 1](adr/adr-1.md)). Cada linha é um material em um almoxarifado em um mês (`data_referencia` é sempre o dia 1º). Por isso:

- para saber "como está agora", use o mês mais recente;
- `valor_total` é o valor **em estoque** (saldo × preço), e não o valor gasto na compra.

**Período:** todas as consultas filtram `data_referencia` entre `2026-01-01` e `2027-12-01`, o recorte da pergunta de gestão. Para mudar o período, troque as datas no bloco `periodo` de cada consulta.

---

## Q1 — Panorama dos almoxarifados no mês mais recente

**Objetivo:** mostrar quantos materiais cada almoxarifado tem e quanto valem, para dimensionar o problema e ver quais almoxarifados concentram valor.

```sql
WITH ultimo_mes AS (
    SELECT max(data_referencia) AS mes
    FROM estoque_saldo
    WHERE data_referencia BETWEEN DATE '2026-01-01' AND DATE '2027-12-01'
)
SELECT a.nome                                  AS almoxarifado,
       u.sigla                                 AS unidade,
       count(*)                                AS materiais,
       count(*) FILTER (WHERE e.saldo > 0)     AS materiais_com_saldo,
       round(sum(e.valor_total), 2)            AS valor_em_estoque,
       round(100.0 * sum(e.valor_total)
             / sum(sum(e.valor_total)) OVER (), 1) AS pct_do_total
FROM estoque_saldo e
JOIN ultimo_mes   um ON e.data_referencia = um.mes
JOIN almoxarifado a  USING (id_almoxarifado)
LEFT JOIN unidade u  ON u.id_unidade = a.id_unidade
GROUP BY a.nome, u.sigla
ORDER BY valor_em_estoque DESC NULLS LAST;
```

**Resultado (amostra):**

| almoxarifado | unidade | materiais | materiais_com_saldo | valor_em_estoque | pct_do_total |
|---|---|---|---|---|---|
| | | | | | |

**Interpretação:** [quais almoxarifados concentram a maior parte do valor]

---

## Q2 — Materiais com maior valor em estoque (prioridade para cotação)

**Objetivo:** listar os 30 materiais que mais pesam no estoque no mês mais recente. É por eles que a coleta de preços de mercado deve começar, porque são os que mais podem gerar economia.

```sql
WITH ultimo_mes AS (
    SELECT max(data_referencia) AS mes
    FROM estoque_saldo
    WHERE data_referencia BETWEEN DATE '2026-01-01' AND DATE '2027-12-01'
)
SELECT m.id_material,
       m.descricao                         AS material,
       count(DISTINCT e.id_almoxarifado)   AS almoxarifados,
       sum(e.saldo)                        AS saldo_total,
       round(avg(e.preco_unitario), 2)     AS preco_medio,
       round(sum(e.valor_total), 2)        AS valor_em_estoque
FROM estoque_saldo e
JOIN ultimo_mes um ON e.data_referencia = um.mes
JOIN material   m  USING (id_material)
WHERE e.preco_unitario > 0
GROUP BY m.id_material, m.descricao
ORDER BY valor_em_estoque DESC
LIMIT 30;
```

**Resultado (amostra):**

| id_material | material | almoxarifados | saldo_total | preco_medio | valor_em_estoque |
|---|---|---|---|---|---|
| | | | | | |

**Interpretação:** [os N primeiros materiais representam X% do valor em estoque]

---

## Q3 — Mesmo material com preços diferentes entre almoxarifados

**Objetivo:** antes de comparar com o mercado, comparar a UnB com ela mesma. Se o mesmo material aparece com preços diferentes em almoxarifados diferentes no mesmo mês, o menor preço interno serve de referência. A consulta mostra a diferença e quanto o estoque valeria a menos se todos tivessem o menor preço.

```sql
WITH periodo AS (
    SELECT *
    FROM estoque_saldo
    WHERE data_referencia BETWEEN DATE '2026-01-01' AND DATE '2027-12-01'
      AND preco_unitario > 0
),
referencia AS (
    SELECT id_material, data_referencia,
           min(preco_unitario) AS menor_preco,
           max(preco_unitario) AS maior_preco
    FROM periodo
    GROUP BY id_material, data_referencia
    HAVING count(DISTINCT id_almoxarifado) > 1
       AND max(preco_unitario) > min(preco_unitario)
)
SELECT m.descricao                                          AS material,
       to_char(p.data_referencia, 'YYYY-MM')                AS mes,
       a.nome                                               AS almoxarifado,
       p.preco_unitario,
       r.menor_preco,
       round(100 * (p.preco_unitario / r.menor_preco - 1), 1) AS acima_do_menor_pct,
       p.saldo,
       round((p.preco_unitario - r.menor_preco) * p.saldo, 2) AS diferenca_em_estoque
FROM periodo p
JOIN referencia   r USING (id_material, data_referencia)
JOIN material     m USING (id_material)
JOIN almoxarifado a USING (id_almoxarifado)
WHERE p.preco_unitario > r.menor_preco
ORDER BY diferenca_em_estoque DESC
LIMIT 50;
```

**Resultado (amostra):**

| material | mes | almoxarifado | preco_unitario | menor_preco | acima_do_menor_pct | saldo | diferenca_em_estoque |
|---|---|---|---|---|---|---|---|
| | | | | | | | |

**Interpretação:** [materiais com maior diferença interna; possíveis causas: compras em datas diferentes, fornecedores diferentes, unidade de medida diferente]

> ⚠️ Antes de concluir, confira se a diferença não vem de unidade de medida diferente (caixa × unidade) ou de descrições iguais para produtos diferentes.

---

## Q4 — Diferença interna por almoxarifado (resumo da Q3)

**Objetivo:** responder "em quais almoxarifados" usando a referência interna. Considera só o mês mais recente, para não somar o mesmo estoque em vários meses.

```sql
WITH ultimo_mes AS (
    SELECT max(data_referencia) AS mes
    FROM estoque_saldo
    WHERE data_referencia BETWEEN DATE '2026-01-01' AND DATE '2027-12-01'
),
foto AS (
    SELECT e.*
    FROM estoque_saldo e
    JOIN ultimo_mes um ON e.data_referencia = um.mes
    WHERE e.preco_unitario > 0
),
referencia AS (
    SELECT id_material, min(preco_unitario) AS menor_preco
    FROM foto
    GROUP BY id_material
    HAVING count(DISTINCT id_almoxarifado) > 1
)
SELECT a.nome                                                   AS almoxarifado,
       count(*) FILTER (WHERE f.preco_unitario > r.menor_preco) AS materiais_acima_do_menor,
       count(*)                                                 AS materiais_comparaveis,
       round(sum(f.valor_total), 2)                             AS valor_em_estoque,
       round(sum((f.preco_unitario - r.menor_preco) * f.saldo), 2) AS diferenca_em_estoque,
       round(100 * sum((f.preco_unitario - r.menor_preco) * f.saldo)
             / nullif(sum(f.valor_total), 0), 1)                AS diferenca_pct
FROM foto f
JOIN referencia   r USING (id_material)
JOIN almoxarifado a USING (id_almoxarifado)
GROUP BY a.nome
ORDER BY diferenca_em_estoque DESC;
```

**Resultado (amostra):**

| almoxarifado | materiais_acima_do_menor | materiais_comparaveis | valor_em_estoque | diferenca_em_estoque | diferenca_pct |
|---|---|---|---|---|---|
| | | | | | |

**Interpretação:** [..]

---

## Q5 — Materiais cujo preço unitário mais subiu no período

**Objetivo:** encontrar materiais cujo preço registrado subiu muito entre o primeiro e o último mês em que aparecem no mesmo almoxarifado. Uma alta muito acima da inflação do período é candidata a sobrepreço.

```sql
WITH periodo AS (
    SELECT *
    FROM estoque_saldo
    WHERE data_referencia BETWEEN DATE '2026-01-01' AND DATE '2027-12-01'
      AND preco_unitario > 0
),
extremos AS (
    SELECT DISTINCT
           id_material, id_almoxarifado,
           first_value(preco_unitario)  OVER w AS preco_inicial,
           first_value(data_referencia) OVER w AS mes_inicial,
           last_value(preco_unitario)   OVER w AS preco_final,
           last_value(data_referencia)  OVER w AS mes_final
    FROM periodo
    WINDOW w AS (PARTITION BY id_material, id_almoxarifado
                 ORDER BY data_referencia
                 ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)
)
SELECT m.descricao                                           AS material,
       a.nome                                                AS almoxarifado,
       to_char(x.mes_inicial, 'YYYY-MM')                     AS de,
       to_char(x.mes_final,   'YYYY-MM')                     AS ate,
       x.preco_inicial,
       x.preco_final,
       round(100 * (x.preco_final / x.preco_inicial - 1), 1) AS variacao_pct
FROM extremos x
JOIN material     m USING (id_material)
JOIN almoxarifado a USING (id_almoxarifado)
WHERE x.mes_final > x.mes_inicial
  AND x.preco_final > x.preco_inicial
ORDER BY variacao_pct DESC
LIMIT 30;
```

**Resultado (amostra):**

| material | almoxarifado | de | ate | preco_inicial | preco_final | variacao_pct |
|---|---|---|---|---|---|---|
| | | | | | | |

**Interpretação:** [compare com o IPCA do período]

---

## Q6 — Evolução mensal do valor em estoque por almoxarifado

**Objetivo:** mostrar como o valor em estoque de cada almoxarifado muda mês a mês. Serve para o gráfico do painel e para achar meses com saltos estranhos (possível erro de carga).

```sql
SELECT to_char(e.data_referencia, 'YYYY-MM') AS mes,
       a.nome                                AS almoxarifado,
       count(*)                              AS materiais,
       round(sum(e.valor_total), 2)          AS valor_em_estoque,
       round(100 * (sum(e.valor_total)
             / nullif(lag(sum(e.valor_total)) OVER (PARTITION BY a.nome
                                                    ORDER BY e.data_referencia), 0)
             - 1), 1)                        AS variacao_mes_anterior_pct
FROM estoque_saldo e
JOIN almoxarifado a USING (id_almoxarifado)
WHERE e.data_referencia BETWEEN DATE '2026-01-01' AND DATE '2027-12-01'
GROUP BY e.data_referencia, a.nome
ORDER BY a.nome, e.data_referencia;
```

**Resultado (amostra):**

| mes | almoxarifado | materiais | valor_em_estoque | variacao_mes_anterior_pct |
|---|---|---|---|---|
| | | | | |

**Interpretação:** [..]

---

## Q7 — Qualidade: registros que não entram na comparação de preços

**Objetivo:** contar os registros que as consultas acima descartam, para documentar o tamanho da perda e a cobertura da análise.

```sql
SELECT a.nome                                                         AS almoxarifado,
       count(*)                                                       AS registros,
       count(*) FILTER (WHERE e.preco_unitario IS NULL)               AS sem_preco,
       count(*) FILTER (WHERE e.preco_unitario = 0)                   AS preco_zero,
       count(*) FILTER (WHERE e.saldo < 0)                            AS saldo_negativo,
       count(*) FILTER (WHERE e.preco_unitario IS NOT NULL
                          AND abs(e.valor_total
                                  - e.saldo * e.preco_unitario) > 0.05) AS valor_total_inconsistente,
       round(100.0 * count(*) FILTER (WHERE e.preco_unitario > 0)
             / count(*), 1)                                           AS pct_utilizavel
FROM estoque_saldo e
JOIN almoxarifado a USING (id_almoxarifado)
WHERE e.data_referencia BETWEEN DATE '2026-01-01' AND DATE '2027-12-01'
GROUP BY a.nome
ORDER BY pct_utilizavel;
```

**Resultado (amostra):**

| almoxarifado | registros | sem_preco | preco_zero | saldo_negativo | valor_total_inconsistente | pct_utilizavel |
|---|---|---|---|---|---|---|
| | | | | | | |

**Interpretação:** [..]

---

## Índices usados pelas consultas

Os índices da `V1__esquema_inicial.sql` já atendem a estas consultas:

| Índice | Usado em |
|---|---|
| `ix_estoque_data (data_referencia)` | Filtro de período e de mês mais recente (todas) |
| `pk_estoque_saldo (id_material, id_almoxarifado, data_referencia)` | Agrupamentos por material e almoxarifado (Q3, Q5) |
| `ix_estoque_material_data (id_material, data_referencia DESC)` | Junção com a referência por material (Q3, Q4) |

Se o `EXPLAIN ANALYZE` mostrar lentidão com o volume real, registre o novo índice em uma migração `V<n>__indices_consultas.sql` e anote aqui.
