-- V12: minimização de dados pessoais em raw.compras (LGPD, art. 6º, III)
--
-- A API de pesquisa de preços devolve, em cada compra, o CNPJ/CPF e o nome do
-- fornecedor (niFornecedor, nomeFornecedor). A análise de preço não usa nenhum
-- dos dois, e fornecedor que seja empresário individual ou pessoa física é
-- dado pessoal. A função abaixo remove esses campos do JSON bruto; o dbt a
-- chama depois de construir bronze.compras (compras_bronze), então nada que a
-- análise usa se perde. Idempotente: rodar de novo não encontra mais o que remover.
--
-- Irreversível: para ter o fornecedor de volta é preciso baixar a API de novo
-- com a variável remover_identificacao_fornecedor: false no dbt_project.yml
-- (o hash do arquivo na raw é o do arquivo original, então um arquivo igual
-- não é recarregado por cima do já expurgado).

CREATE OR REPLACE FUNCTION raw.remover_identificacao_fornecedor() RETURNS bigint
LANGUAGE plpgsql AS $$
DECLARE
    linhas bigint;
BEGIN
    UPDATE raw.compras
    SET dado_bruto = (
        SELECT COALESCE(jsonb_agg(item.elemento - 'niFornecedor' - 'nomeFornecedor' ORDER BY item.posicao),
                        '[]'::jsonb)
        FROM jsonb_array_elements(raw.compras.dado_bruto) WITH ORDINALITY AS item(elemento, posicao)
    )
    WHERE jsonb_typeof(dado_bruto) = 'array'
      AND EXISTS (
          SELECT 1 FROM jsonb_array_elements(raw.compras.dado_bruto) AS e(elemento)
          WHERE e.elemento ? 'niFornecedor' OR e.elemento ? 'nomeFornecedor'
      );
    GET DIAGNOSTICS linhas = ROW_COUNT;
    RETURN linhas;
END
$$;

COMMENT ON FUNCTION raw.remover_identificacao_fornecedor() IS
    'Remove niFornecedor e nomeFornecedor de raw.compras (minimização LGPD); devolve quantos arquivos alterou';
