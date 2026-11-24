-- V13: usuário de login do painel (privilégio mínimo)
--
-- O painel deixa de conectar como dono do banco: usa sigma_painel_app, membro
-- do grupo sigma_painel (V11), que só lê o schema ouro. A senha vem do
-- placeholder do Flyway `senha_painel` (variável SENHA_DO_PAINEL do compose).

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sigma_painel_app') THEN
        CREATE ROLE sigma_painel_app LOGIN PASSWORD '${senha_painel}' IN ROLE sigma_painel;
    ELSE
        ALTER ROLE sigma_painel_app PASSWORD '${senha_painel}';
    END IF;
END
$$;
