-- O catálogo raw é um snapshot: guarda-se a coleta vigente e evita buscar
-- novamente centenas de páginas em cada execução do Compose.
CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS raw.catmat_coleta (
    id_coleta SMALLINT PRIMARY KEY CHECK (id_coleta = 1),
    completa BOOLEAN NOT NULL,
    total_paginas INTEGER NOT NULL CHECK (total_paginas > 0),
    total_itens INTEGER NOT NULL CHECK (total_itens >= 0),
    hash_do_arquivo CHAR(64) NOT NULL,
    atualizada_em TIMESTAMP NOT NULL DEFAULT now()
);

-- Bancos existentes já podem conter o catálogo completo em raw.catmat.
-- Aproveita o documento maior como cache inicial; bancos novos ainda não têm
-- a tabela raw.catmat, pois ela é criada por ddl.sql após as migrações.
DO $$
BEGIN
    IF to_regclass('raw.catmat') IS NOT NULL THEN
        EXECUTE $sql$
            INSERT INTO raw.catmat_coleta
                (id_coleta, completa, total_paginas, total_itens,
                 hash_do_arquivo, atualizada_em)
            SELECT
                1,
                TRUE,
                1,
                jsonb_array_length(dado_bruto),
                hash_do_arquivo,
                data_da_insercao
            FROM raw.catmat
            WHERE jsonb_typeof(dado_bruto) = 'array'
            ORDER BY jsonb_array_length(dado_bruto) DESC, data_da_insercao DESC
            LIMIT 1
            ON CONFLICT (id_coleta) DO NOTHING
        $sql$;
    END IF;
END
$$;
