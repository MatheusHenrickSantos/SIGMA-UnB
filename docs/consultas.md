# Consultas

Consultas SQL que respondem à [pergunta de gestão](dominio-e-pergunta.md). Rode com:

```bash
docker compose exec db psql -U sigma -d sigma
```

---

## Q1 — [Materiais com preço acima do mercado]

**Objetivo:** [o que a consulta responde]

```sql
-- [cole a consulta aqui]
SELECT ...
FROM ...
WHERE ...;
```

**Resultado (amostra):**

| material | almoxarifado | preco_unb | preco_mercado | sobrepreco_pct |
|---|---|---|---|---|
| | | | | |

**Tempo de execução:** [X ms] — `EXPLAIN ANALYZE` em [link/anexo]

**Interpretação:** [o que o resultado diz]

---

## Q2 — [Sobrepreço por almoxarifado]

**Objetivo:** [..]

```sql
SELECT ...;
```

**Resultado (amostra):** [..]

**Interpretação:** [..]

---

## Q3 — [Economia potencial total]

**Objetivo:** [..]

```sql
SELECT ...;
```

**Resultado:** [..]

**Interpretação:** [..]

---

## Índices criados para as consultas

| Índice | Tabela | Colunas | Migração |
|---|---|---|---|
| [..] | [..] | [..] | `V?__....sql` |
