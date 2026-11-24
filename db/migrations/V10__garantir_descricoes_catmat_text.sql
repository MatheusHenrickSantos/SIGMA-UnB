-- CATMAT admite descrições longas. TEXT elimina limite físico e preserva o conteúdo.
DO $$
BEGIN
    IF to_regclass('prata.catmat_item') IS NOT NULL THEN
        ALTER TABLE prata.catmat_item
            ALTER COLUMN descricao_item TYPE TEXT
            USING descricao_item::TEXT;
    END IF;
END
$$;
