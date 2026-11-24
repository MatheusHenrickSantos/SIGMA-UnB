-- Checkpoints permitem retomar a coleta da API sem arquivos locais, inclusive
-- para CATMAT sem compras na janela consultada.
CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS raw.compras_coleta (
    codigo_item_catalogo INTEGER NOT NULL,
    data_inicio DATE NOT NULL,
    data_fim DATE NOT NULL,
    total_registros INTEGER NOT NULL DEFAULT 0 CHECK (total_registros >= 0),
    concluida_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (codigo_item_catalogo, data_inicio, data_fim),
    CHECK (data_inicio <= data_fim)
);
