-- Remove o esquema OLTP legado criado pela V1; a ingestão atual usa raw/dbt.
-- Sem CASCADE: dependências externas devem interromper a migração.
DROP TABLE IF EXISTS public.cotacao_online;
DROP TABLE IF EXISTS public.requisicao_servico;
DROP TABLE IF EXISTS public.empenho;
DROP TABLE IF EXISTS public.gasto;
DROP TABLE IF EXISTS public.estoque_saldo;
DROP TABLE IF EXISTS public.almoxarifado;
DROP TABLE IF EXISTS public.carga_rejeitado;
DROP TABLE IF EXISTS public.material;
DROP TABLE IF EXISTS public.natureza_despesa;
DROP TABLE IF EXISTS public.credor;
DROP TABLE IF EXISTS public.unidade;
DROP TABLE IF EXISTS public.carga_execucao;
