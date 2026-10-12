-- V2: índices para a captura de mudanças (CDC por consulta) da E2
--
-- O capturar_mudancas.py busca, a cada execução, só as linhas alteradas
-- desde a última marca d'água:  WHERE <coluna> > :marca
-- Sem índice, cada execução varreria a tabela inteira.
--
-- Tabelas com upsert usam atualizado_em, que o carregar.py só altera quando
-- algum campo muda de verdade (WHERE ... IS DISTINCT FROM EXCLUDED).
-- Tabelas insert-only (estoque, cotação) e cadastros sem atualizado_em
-- usam carregado_em.
-- material, almoxarifado, natureza_despesa e credor são pequenas: sem índice.

CREATE INDEX ix_unidade_atualizado    ON unidade (atualizado_em);
CREATE INDEX ix_empenho_atualizado    ON empenho (atualizado_em);
CREATE INDEX ix_requisicao_atualizado ON requisicao_servico (atualizado_em);
CREATE INDEX ix_gasto_atualizado      ON gasto (atualizado_em);
CREATE INDEX ix_estoque_carregado     ON estoque_saldo (carregado_em);
CREATE INDEX ix_cotacao_carregado     ON cotacao_online (carregado_em);
