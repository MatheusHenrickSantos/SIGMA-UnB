-- As descrições normalizadas podem crescer além de CHAR(200).
-- Converter para TEXT evita truncamento físico e preserva os dados existentes.
DO $$
BEGIN
    IF to_regclass('prata.material') IS NOT NULL THEN
        ALTER TABLE prata.material
            ALTER COLUMN descricao TYPE TEXT
            USING descricao::TEXT;
    END IF;
END
$$;
