-- V11: papéis de acesso (privilégio mínimo) e schema do ETL reverso
--
-- Cada consumidor lê só o que precisa:
--   sigma_painel        lê a camada ouro (o painel). Não enxerga raw, bronze, prata,
--                       semantica nem reverso.
--   sigma_compras       setor de compras: lê todas as linhas de reverso.alerta_preco_compras,
--                       exceto a coluna da justificativa do agente de IA (recorte de COLUNA).
--   sigma_almoxarifado  chefias de almoxarifado: só as linhas dos almoxarifados que o seu
--                       usuário tem em reverso.acesso_almoxarifado (recorte de LINHA, RLS).
--
-- Os papéis são NOLOGIN (grupos). Crie um usuário por pessoa ou aplicação e
-- coloque-o no grupo, por exemplo:
--   CREATE ROLE ana_compras LOGIN PASSWORD '...' IN ROLE sigma_compras;
--   CREATE ROLE joao_prc    LOGIN PASSWORD '...' IN ROLE sigma_almoxarifado;
-- e registre joao_prc em seeds/acesso_almoxarifado.csv. As permissões de tabela
-- são reaplicadas pelo dbt a cada carga (hooks), porque o dbt recria as tabelas.

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sigma_painel') THEN
        CREATE ROLE sigma_painel NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sigma_compras') THEN
        CREATE ROLE sigma_compras NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sigma_almoxarifado') THEN
        CREATE ROLE sigma_almoxarifado NOLOGIN;
    END IF;
END
$$;

CREATE SCHEMA IF NOT EXISTS ouro;
CREATE SCHEMA IF NOT EXISTS reverso;

COMMENT ON SCHEMA reverso IS
    'Saída do ETL reverso: dados tratados que voltam a quem age (compras e almoxarifados)';

-- ninguém herda acesso por PUBLIC
REVOKE ALL ON SCHEMA reverso FROM PUBLIC;
REVOKE ALL ON SCHEMA ouro FROM PUBLIC;
GRANT USAGE ON SCHEMA ouro TO sigma_painel;
GRANT USAGE ON SCHEMA reverso TO sigma_compras, sigma_almoxarifado;
