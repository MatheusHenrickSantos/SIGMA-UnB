-- V3: remove o índice HNSW criado na V2; a correspondência passa a usar
-- busca exata (varredura completa por material).
--
-- Motivo (medição em docs/adr/0005-busca-semantica-com-pgvector.md,
-- script codigos/medir_adr0005.py, 345 mil vetores de 384 dimensões):
--   * busca exata: ~107 ms por material -> ~4 min para os ~2.400 materiais
--     do estoque, aceitável para uma carga mensal;
--   * o índice ocupa mais que a própria tabela (691 MB x 547 MB) e derruba a
--     inserção para ~111 vetores/s (~52 min a mais na primeira carga);
--   * o resultado da HNSW é aproximado e o recall ainda não foi medido com
--     vetores reais.
-- O código continua pronto para usar um índice HNSW se uma migração futura
-- o recriar (ver o gatilho de revisão no ADR 0005).

DROP INDEX IF EXISTS semantica.ix_embedding_catmat_hnsw;
