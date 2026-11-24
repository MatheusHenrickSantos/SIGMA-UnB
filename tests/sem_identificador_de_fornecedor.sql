{#-
    LGPD, minimização: o identificador do fornecedor (niFornecedor, CNPJ ou
    CPF) e o nome do fornecedor só existem na camada raw (JSON bruto da API).
    Nenhuma tabela de bronze, prata, ouro ou reverso pode ter coluna que os
    carregue; se um modelo novo trouxer, este teste falha.
-#}
SELECT table_schema, table_name, column_name
FROM information_schema.columns
WHERE table_schema IN ('bronze', 'prata', 'ouro', 'reverso')
  AND column_name ~* '(fornecedor|cpf|cnpj|^ni_)'
