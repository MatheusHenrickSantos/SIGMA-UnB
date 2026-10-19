-- Captura de mudanças (CDC) por decodificação lógica do WAL.
--
-- A publicação lista as tabelas cujas mudanças são entregues a jusante. O slot
-- de replicação é criado pelo consumidor (codigos/cdc_consumidor.py), porque
-- criar slot não pode acontecer dentro da transação de uma migração.
--
-- REPLICA IDENTITY FULL faz UPDATE e DELETE trazerem a linha inteira antes da
-- mudança (não só a chave), o que permite mostrar "antes e depois".

CREATE PUBLICATION sigma_cdc FOR TABLE
    material,
    credor,
    estoque_saldo,
    empenho,
    cotacao_online;

ALTER TABLE material       REPLICA IDENTITY FULL;
ALTER TABLE credor         REPLICA IDENTITY FULL;
ALTER TABLE estoque_saldo  REPLICA IDENTITY FULL;
ALTER TABLE empenho        REPLICA IDENTITY FULL;
ALTER TABLE cotacao_online REPLICA IDENTITY FULL;
