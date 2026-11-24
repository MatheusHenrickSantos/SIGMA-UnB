CREATE SCHEMA IF NOT EXISTS raw;

-- =====================================================
-- Tabela: estoque
-- Origem: Dados abertos da UnB
-- =====================================================
CREATE TABLE IF NOT EXISTS raw.estoque (
    dado_bruto JSONB NOT NULL,
    hash_do_arquivo CHAR(64) UNIQUE NOT NULL,
    mes_de_referencia SMALLINT NOT NULL CHECK (mes_de_referencia BETWEEN 1 AND 12),
    ano_de_referencia SMALLINT NOT NULL
);



-- =====================================================
-- Tabela: compras
-- Origem: Gov.br
-- =====================================================
CREATE TABLE IF NOT EXISTS raw.compras (
    dado_bruto JSONB NOT NULL,
    hash_do_arquivo CHAR(64) UNIQUE NOT NULL,
    data_da_insercao TIMESTAMP NOT NULL DEFAULT now()
);

-- Checkpoint persistente das consultas à API, inclusive códigos sem resultados.
CREATE TABLE IF NOT EXISTS raw.compras_coleta (
    codigo_item_catalogo INTEGER NOT NULL,
    data_inicio DATE NOT NULL,
    data_fim DATE NOT NULL,
    total_registros INTEGER NOT NULL DEFAULT 0 CHECK (total_registros >= 0),
    concluida_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (codigo_item_catalogo, data_inicio, data_fim),
    CHECK (data_inicio <= data_fim)
);



-- =====================================================
-- Tabela: catmat
-- Origem: Gov.br
-- =====================================================
CREATE TABLE IF NOT EXISTS raw.catmat (
    dado_bruto JSONB NOT NULL,
    hash_do_arquivo CHAR(64) UNIQUE NOT NULL,
    data_da_insercao TIMESTAMP NOT NULL DEFAULT now()
);

-- Snapshot atual e cache persistente do catálogo baixado por completo.
CREATE TABLE IF NOT EXISTS raw.catmat_coleta (
    id_coleta SMALLINT PRIMARY KEY CHECK (id_coleta = 1),
    completa BOOLEAN NOT NULL,
    total_paginas INTEGER NOT NULL CHECK (total_paginas > 0),
    total_itens INTEGER NOT NULL CHECK (total_itens >= 0),
    hash_do_arquivo CHAR(64) NOT NULL,
    atualizada_em TIMESTAMP NOT NULL DEFAULT now()
);
