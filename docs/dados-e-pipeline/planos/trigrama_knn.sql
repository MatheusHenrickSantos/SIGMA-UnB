-- Consulta otimizada (E3): vizinhos por trigramas da busca híbrida
-- (codigos/semantica/correspondencia.py, _HIBRIDA_TRIGRAMA), para 25 materiais.
-- Roda as três variantes do índice dentro de transações desfeitas no fim:
--   psql -f docs/dados-e-pipeline/planos/trigrama_knn.sql
\set materiais '''{ma0100,ma0200,ma0300,ma0400,ma0500,ma0600,ma0700,ma0800,ma0900,ma1000,ma1100,ma1200,ma1300,ma1400,ma1500,ma1600,ma1700,ma1800,ma1900,ma2000,ma2100,ma2200,ma2250,ma2280,ma2300}'''

\echo '=== ANTES: sem índice de trigramas (só o índice da PK) ==='
BEGIN;
DROP INDEX semantica.ix_descricao_catmat_trgm;
EXPLAIN (ANALYZE, BUFFERS)
SELECT m.chave_origem, vizinho.chave_origem
FROM semantica.descricao AS m
CROSS JOIN LATERAL (
    SELECT k.chave_origem FROM semantica.descricao AS k
    WHERE k.origem = 'catmat' AND k.situacao = 'valida' AND k.ativa
    ORDER BY k.texto_normalizado <-> m.texto_normalizado
    LIMIT 20
) AS vizinho
WHERE m.origem = 'estoque' AND m.chave_origem = ANY(:materiais::text[]);
ROLLBACK;

\echo '=== TENTATIVA: índice GIN (gin_trgm_ops), que não atende ORDER BY <-> ==='
BEGIN;
DROP INDEX semantica.ix_descricao_catmat_trgm;
CREATE INDEX ix_tmp_gin ON semantica.descricao USING gin (texto_normalizado gin_trgm_ops)
    WHERE origem = 'catmat' AND situacao = 'valida' AND ativa;
EXPLAIN (ANALYZE, BUFFERS)
SELECT m.chave_origem, vizinho.chave_origem
FROM semantica.descricao AS m
CROSS JOIN LATERAL (
    SELECT k.chave_origem FROM semantica.descricao AS k
    WHERE k.origem = 'catmat' AND k.situacao = 'valida' AND k.ativa
    ORDER BY k.texto_normalizado <-> m.texto_normalizado
    LIMIT 20
) AS vizinho
WHERE m.origem = 'estoque' AND m.chave_origem = ANY(:materiais::text[]);
ROLLBACK;

\echo '=== DEPOIS: índice GiST (gist_trgm_ops) da V4, busca KNN pelo índice ==='
EXPLAIN (ANALYZE, BUFFERS)
SELECT m.chave_origem, vizinho.chave_origem
FROM semantica.descricao AS m
CROSS JOIN LATERAL (
    SELECT k.chave_origem FROM semantica.descricao AS k
    WHERE k.origem = 'catmat' AND k.situacao = 'valida' AND k.ativa
    ORDER BY k.texto_normalizado <-> m.texto_normalizado
    LIMIT 20
) AS vizinho
WHERE m.origem = 'estoque' AND m.chave_origem = ANY(:materiais::text[]);

\echo '=== DEPOIS, repetição (páginas já em cache) ==='
EXPLAIN (ANALYZE, BUFFERS)
SELECT m.chave_origem, vizinho.chave_origem
FROM semantica.descricao AS m
CROSS JOIN LATERAL (
    SELECT k.chave_origem FROM semantica.descricao AS k
    WHERE k.origem = 'catmat' AND k.situacao = 'valida' AND k.ativa
    ORDER BY k.texto_normalizado <-> m.texto_normalizado
    LIMIT 20
) AS vizinho
WHERE m.origem = 'estoque' AND m.chave_origem = ANY(:materiais::text[]);
