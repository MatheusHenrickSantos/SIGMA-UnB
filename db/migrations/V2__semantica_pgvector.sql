-- V2: busca semântica com pgvector (embeddings de descrições e candidatos CATMAT)
--
-- Tudo fica no schema `semantica`, separado de raw/bronze/prata:
--   * quem escreve aqui é o pipeline Python (codigos/semantica), não o dbt;
--   * os vetores dependem do modelo e da versão da normalização, e não
--     podem ser reconstruídos só com SQL a partir da Bronze;
--   * tudo pode ser recalculado a partir da Prata, EXCETO as decisões
--     humanas em revisao_correspondencia.
-- Decisões e alternativas: docs/adr/0005-busca-semantica-com-pgvector.md.

CREATE EXTENSION IF NOT EXISTS vector;

CREATE SCHEMA semantica;
COMMENT ON SCHEMA semantica IS
    'Embeddings de descrições (estoque e CATMAT) e candidatos de correspondência. Derivado da Prata.';

-- ---------------------------------------------------------------------------
-- Modelos de embedding. Vetores só são comparáveis dentro do mesmo modelo.
-- ---------------------------------------------------------------------------

CREATE TABLE semantica.modelo_embedding (
    id_modelo         SMALLSERIAL PRIMARY KEY,
    nome              TEXT        NOT NULL CHECK (btrim(nome) <> ''),
    -- commit do repositório do modelo no Hugging Face (ou 'desconhecida')
    revisao           TEXT        NOT NULL CHECK (btrim(revisao) <> ''),
    dimensao          SMALLINT    NOT NULL CHECK (dimensao > 0),
    -- prefixos exigidos pela família e5 ('query: ' / 'passage: ')
    prefixo_consulta  TEXT        NOT NULL DEFAULT '',
    prefixo_documento TEXT        NOT NULL DEFAULT '',
    -- versões de bibliotecas e outros detalhes do ambiente que gerou os vetores
    metadados         JSONB       NOT NULL DEFAULT '{}'::jsonb,
    registrado_em     TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_modelo UNIQUE (nome, revisao, prefixo_consulta, prefixo_documento)
);

-- ---------------------------------------------------------------------------
-- Descrições de origem: uma linha por material do estoque ou item CATMAT.
-- Guarda o texto original exatamente como veio da Prata e o texto
-- normalizado que foi de fato enviado ao modelo.
-- ---------------------------------------------------------------------------

CREATE TABLE semantica.descricao (
    id_descricao        BIGSERIAL   PRIMARY KEY,
    origem              TEXT        NOT NULL CHECK (origem IN ('estoque', 'catmat')),
    -- prata.material.identificador_material ou prata.catmat_item.codigo_item
    chave_origem        TEXT        NOT NULL CHECK (btrim(chave_origem) <> ''),
    texto_original      TEXT,
    hash_original       CHAR(64),
    texto_normalizado   TEXT,
    -- sha256 de (versão da normalização + texto normalizado): muda quando o
    -- texto ou a regra de normalização mudam, e aí o vetor fica desatualizado
    hash_normalizado    CHAR(64),
    versao_normalizacao TEXT        NOT NULL,
    situacao            TEXT        NOT NULL CHECK (situacao IN ('valida', 'vazia', 'invalida')),
    motivo              TEXT,
    -- false quando a chave sumiu da origem na última sincronização
    ativa               BOOLEAN     NOT NULL DEFAULT true,
    sincronizada_em     TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizada_em       TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_descricao_origem UNIQUE (origem, chave_origem),
    -- alvo da chave estrangeira composta de embedding
    CONSTRAINT uq_descricao_id_origem UNIQUE (id_descricao, origem),
    CONSTRAINT ck_descricao_hash_original
        CHECK ((texto_original IS NULL) = (hash_original IS NULL)),
    CONSTRAINT ck_descricao_valida
        CHECK ((situacao = 'valida') = (texto_normalizado IS NOT NULL AND hash_normalizado IS NOT NULL)),
    CONSTRAINT ck_descricao_motivo
        CHECK ((situacao = 'valida') = (motivo IS NULL))
);

-- reaproveitar o vetor de textos idênticos em outra chave da mesma origem
CREATE INDEX ix_descricao_hash ON semantica.descricao (origem, hash_normalizado);

-- ---------------------------------------------------------------------------
-- Vetores. vector(384) é a dimensão do modelo padrão
-- (intfloat/multilingual-e5-small). Um modelo de outra dimensão exige uma
-- nova migração; o pipeline confere a dimensão antes de gravar.
-- ---------------------------------------------------------------------------

CREATE TABLE semantica.embedding (
    id_descricao     BIGINT      NOT NULL,
    -- cópia de descricao.origem (garantida pela FK composta) para permitir
    -- o índice parcial só com os itens CATMAT
    origem           TEXT        NOT NULL,
    id_modelo        SMALLINT    NOT NULL REFERENCES semantica.modelo_embedding (id_modelo),
    -- texto que gerou o vetor; diferente de descricao.hash_normalizado = desatualizado
    hash_normalizado CHAR(64)    NOT NULL,
    vetor            vector(384) NOT NULL,
    gerado_em        TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT pk_embedding PRIMARY KEY (id_descricao, id_modelo),
    CONSTRAINT fk_embedding_descricao FOREIGN KEY (id_descricao, origem)
        REFERENCES semantica.descricao (id_descricao, origem) ON DELETE CASCADE
);

-- Vizinhos mais próximos entre os itens CATMAT, por distância de cosseno.
-- HNSW é aproximado; a busca exata continua disponível desligando o uso de
-- índices na sessão (o pipeline faz isso com --busca-exata).
CREATE INDEX ix_embedding_catmat_hnsw ON semantica.embedding
    USING hnsw (vetor vector_cosine_ops)
    WHERE origem = 'catmat';

-- ---------------------------------------------------------------------------
-- Execuções da correspondência e candidatos encontrados.
-- Um candidato é uma SUGESTÃO para revisão, nunca uma equivalência aprovada.
-- ---------------------------------------------------------------------------

CREATE TABLE semantica.execucao_correspondencia (
    id_execucao             BIGSERIAL   PRIMARY KEY,
    id_modelo               SMALLINT    NOT NULL REFERENCES semantica.modelo_embedding (id_modelo),
    top_k                   SMALLINT    NOT NULL CHECK (top_k BETWEEN 1 AND 100),
    -- candidatos abaixo deste valor não são gravados (NULL = sem filtro)
    limiar_similaridade     REAL        CHECK (limiar_similaridade BETWEEN -1 AND 1),
    busca_exata             BOOLEAN     NOT NULL,
    ef_search               SMALLINT    CHECK (ef_search > 0),
    versao_normalizacao     TEXT        NOT NULL,
    versao_regras           TEXT        NOT NULL,
    iniciada_em             TIMESTAMPTZ NOT NULL DEFAULT now(),
    finalizada_em           TIMESTAMPTZ,
    materiais               INTEGER     CHECK (materiais >= 0),
    materiais_sem_candidato INTEGER     CHECK (materiais_sem_candidato >= 0),
    candidatos              INTEGER     CHECK (candidatos >= 0)
);

CREATE TABLE semantica.candidato_catmat (
    id_execucao            BIGINT   NOT NULL
        REFERENCES semantica.execucao_correspondencia (id_execucao) ON DELETE CASCADE,
    id_descricao_material  BIGINT   NOT NULL REFERENCES semantica.descricao (id_descricao),
    posicao                SMALLINT NOT NULL CHECK (posicao >= 1),
    id_descricao_catmat    BIGINT   NOT NULL REFERENCES semantica.descricao (id_descricao),
    -- 1 - distância de cosseno
    similaridade           DOUBLE PRECISION NOT NULL,
    -- resultado de codigos/semantica/especificacoes.py (unidades, medidas, cores...)
    situacao_especificacao TEXT     NOT NULL CHECK (situacao_especificacao IN (
        'conflito_tecnico', 'sem_conflito_mas_incompleto',
        'sem_conflito_detectado', 'sem_especificacoes_verificaveis')),
    especificacoes         JSONB    NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT pk_candidato PRIMARY KEY (id_execucao, id_descricao_material, posicao),
    CONSTRAINT uq_candidato_par UNIQUE (id_execucao, id_descricao_material, id_descricao_catmat)
);

-- ---------------------------------------------------------------------------
-- Decisões humanas. É a única tabela que não pode ser recalculada.
-- A chave usa o hash do texto ORIGINAL do material, não o id da Prata: a
-- decisão vale para aquele texto exato e sobrevive a reprocessamentos.
-- ---------------------------------------------------------------------------

CREATE TABLE semantica.revisao_correspondencia (
    hash_original_material CHAR(64)    NOT NULL,
    codigo_item            TEXT        NOT NULL,
    decisao                TEXT        NOT NULL
        CHECK (decisao IN ('equivalente', 'nao_equivalente', 'incerto')),
    revisor                TEXT        NOT NULL CHECK (btrim(revisor) <> ''),
    observacao             TEXT,
    -- cópia do texto revisado, para leitura humana
    texto_material         TEXT        NOT NULL,
    id_execucao            BIGINT
        REFERENCES semantica.execucao_correspondencia (id_execucao) ON DELETE SET NULL,
    revisada_em            TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT pk_revisao PRIMARY KEY (hash_original_material, codigo_item)
);

-- ---------------------------------------------------------------------------
-- Visões de consumo
-- ---------------------------------------------------------------------------

-- Papel da entidade candidatoCatmat do diagrama de arquitetura (v2.1).
CREATE VIEW semantica.v_candidato_catmat AS
SELECT
    c.id_execucao,
    e.id_modelo,
    m.chave_origem   AS identificador_material,
    m.texto_original AS material,
    c.posicao,
    k.chave_origem   AS codigo_item,
    k.texto_original AS descricao_catmat,
    c.similaridade,
    c.similaridade - lead(c.similaridade) OVER (
        PARTITION BY c.id_execucao, c.id_descricao_material ORDER BY c.posicao
    )                AS vantagem_sobre_proximo,
    c.situacao_especificacao,
    c.especificacoes,
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

-- Candidatos da última execução concluída de cada modelo, só dos materiais
-- que ainda não têm nenhum item CATMAT revisado como 'equivalente'.
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
