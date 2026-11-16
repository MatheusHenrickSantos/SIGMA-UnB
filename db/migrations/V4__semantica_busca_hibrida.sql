-- V4: busca híbrida (cosseno + trigramas + rapidfuzz) na correspondência com o CATMAT
--
-- A busca só por cosseno recupera bem e ordena mal (medição com dados reais em
-- docs/dados-e-pipeline/semantica.md, seção "Busca híbrida"). A execução
-- híbrida:
--   1. recupera os k_vetor vizinhos por cosseno (como antes, busca exata);
--   2. recupera os k_trigrama vizinhos por trigramas (pg_trgm, operador <->)
--      sobre o texto normalizado, o que acha itens com as mesmas palavras e
--      números que o modelo deixou passar;
--   3. reordena a união com rapidfuzz (codigos/semantica/reordenacao.py) e
--      grava os top_k pela pontuação, sem conflito de especificação primeiro.
-- A execução só por cosseno continua disponível (metodo = 'cosseno').

CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Vizinhos lexicais entre os itens CATMAT. GiST permite a busca KNN
-- (ORDER BY texto <-> consulta LIMIT k); com GIN o mesmo ORDER BY varre a tabela.
CREATE INDEX ix_descricao_catmat_trgm ON semantica.descricao
    USING gist (texto_normalizado gist_trgm_ops)
    WHERE origem = 'catmat' AND situacao = 'valida' AND ativa;

ALTER TABLE semantica.execucao_correspondencia
    ADD COLUMN metodo             TEXT     NOT NULL DEFAULT 'cosseno'
        CHECK (metodo IN ('cosseno', 'hibrido')),
    ADD COLUMN k_vetor            SMALLINT CHECK (k_vetor BETWEEN 1 AND 500),
    ADD COLUMN k_trigrama         SMALLINT CHECK (k_trigrama BETWEEN 0 AND 500),
    ADD COLUMN versao_reordenacao TEXT,
    ADD COLUMN pesos              JSONB,
    ADD CONSTRAINT ck_execucao_hibrida CHECK (
        metodo = 'cosseno'
        OR (k_vetor IS NOT NULL AND k_trigrama IS NOT NULL
            AND versao_reordenacao IS NOT NULL AND pesos IS NOT NULL)
    );

COMMENT ON COLUMN semantica.execucao_correspondencia.metodo IS
    'cosseno = ordem pela similaridade; hibrido = união cosseno + trigramas reordenada por pontuação';

ALTER TABLE semantica.candidato_catmat
    -- 0-100; NULL nas execuções só por cosseno
    ADD COLUMN pontuacao      DOUBLE PRECISION,
    -- token_set, token_sort, cobertura e cosseno que formaram a pontuação
    ADD COLUMN medidas        JSONB  NOT NULL DEFAULT '{}'::jsonb,
    -- por qual busca o candidato chegou: {vetor}, {trigrama} ou os dois
    ADD COLUMN recuperado_por TEXT[] NOT NULL DEFAULT '{vetor}';

-- Visões: acrescentam pontuacao e recuperado_por. vantagem_sobre_proximo passa a
-- usar a medida que define a ordem (pontuação 0-100 na híbrida, similaridade 0-1
-- na de cosseno).
DROP VIEW semantica.v_fila_revisao;
DROP VIEW semantica.v_candidato_catmat;

CREATE VIEW semantica.v_candidato_catmat AS
SELECT
    c.id_execucao,
    e.id_modelo,
    e.metodo,
    m.chave_origem   AS identificador_material,
    m.texto_original AS material,
    c.posicao,
    k.chave_origem   AS codigo_item,
    k.texto_original AS descricao_catmat,
    c.similaridade,
    c.pontuacao,
    coalesce(c.pontuacao, c.similaridade) - lead(coalesce(c.pontuacao, c.similaridade)) OVER (
        PARTITION BY c.id_execucao, c.id_descricao_material ORDER BY c.posicao
    )                AS vantagem_sobre_proximo,
    c.situacao_especificacao,
    c.especificacoes,
    c.medidas,
    c.recuperado_por,
    r.decisao,
    r.revisor,
    r.revisada_em
FROM semantica.candidato_catmat AS c
JOIN semantica.execucao_correspondencia AS e ON e.id_execucao = c.id_execucao
JOIN semantica.descricao AS m ON m.id_descricao = c.id_descricao_material
JOIN semantica.descricao AS k ON k.id_descricao = c.id_descricao_catmat
LEFT JOIN semantica.revisao_correspondencia AS r
    ON r.hash_original_material = m.hash_original
   AND r.codigo_item = k.chave_origem;

CREATE VIEW semantica.v_fila_revisao AS
WITH ultima AS (
    SELECT DISTINCT ON (id_modelo) id_execucao
    FROM semantica.execucao_correspondencia
    WHERE finalizada_em IS NOT NULL
    ORDER BY id_modelo, id_execucao DESC
)
SELECT v.*
FROM semantica.v_candidato_catmat AS v
JOIN ultima AS u ON u.id_execucao = v.id_execucao
WHERE NOT EXISTS (
    SELECT 1
    FROM semantica.descricao AS m
    JOIN semantica.revisao_correspondencia AS r ON r.hash_original_material = m.hash_original
    WHERE m.origem = 'estoque'
      AND m.chave_origem = v.identificador_material
      AND r.decisao = 'equivalente'
);
