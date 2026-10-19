-- Coleta semanal de preços de mercado: uma cotação por material, loja e anúncio
-- em cada semana. Reexecutar a coleta na mesma semana não duplica linhas.
-- `semana_coleta` é a segunda-feira da semana da coleta, calculada pelo coletor.

ALTER TABLE cotacao_online ADD COLUMN semana_coleta DATE NOT NULL;

ALTER TABLE cotacao_online
    ADD CONSTRAINT uq_cotacao_semana UNIQUE (id_material, loja, url, semana_coleta);
