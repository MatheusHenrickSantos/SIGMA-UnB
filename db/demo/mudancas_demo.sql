-- DEMONSTRAÇÃO DA E2 — NÃO é migração e NÃO roda no Flyway.
--
-- Aplica poucas mudanças marcadas com "[demo E2]" para mostrar que o
-- capturar_mudancas.py pega só o que mudou. Use quando não houver um mês
-- novo no portal para carregar (a mudança real é sempre preferível).
--
--   docker compose exec -T db psql -U sigma -d sigma < db/demo/mudancas_demo.sql
--   docker compose run --rm extract python capturar_mudancas.py
--
-- Para desfazer: docker compose down -v (recomeça o banco do zero).
--
-- Como aqui o UPDATE é direto (sem o upsert do carregar.py), atualizado_em
-- é marcado à mão, como o carregar.py faria.

BEGIN;

-- 1. Anulação parcial de 10% nos 3 empenhos com maior saldo
--    (o portal republica empenhos assim quando há anulação).
UPDATE empenho e
   SET valor_anulado = coalesce(e.valor_anulado, 0) + round(e.saldo_empenho * 0.10, 2),
       saldo_empenho = e.saldo_empenho - round(e.saldo_empenho * 0.10, 2),
       observacoes   = concat_ws(' ', e.observacoes, '[demo E2: anulação parcial]'),
       atualizado_em = now()
  FROM (SELECT id_unidade_gestora, ano, cod_empenho
          FROM empenho
         WHERE saldo_empenho > 0
         ORDER BY saldo_empenho DESC
         LIMIT 3) alvo
 WHERE (e.id_unidade_gestora, e.ano, e.cod_empenho)
     = (alvo.id_unidade_gestora, alvo.ano, alvo.cod_empenho);

-- 2. Uma unidade muda de nome (o caso clássico de dimensão de variação lenta da E3).
UPDATE unidade
   SET nome = nome || ' [demo E2]',
       atualizado_em = now()
 WHERE id_unidade = (SELECT min(id_unidade) FROM unidade WHERE fonte = 'cadastro');

-- 3. Duas requisições recebem autorização do chefe.
UPDATE requisicao_servico r
   SET data_autorizacao_chefe = r.data_envio,
       observacoes   = concat_ws(' ', r.observacoes, '[demo E2: autorizada]'),
       atualizado_em = now()
  FROM (SELECT ano, numero
          FROM requisicao_servico
         WHERE data_autorizacao_chefe IS NULL AND data_envio IS NOT NULL
         ORDER BY ano DESC, numero
         LIMIT 2) alvo
 WHERE (r.ano, r.numero) = (alvo.ano, alvo.numero);

COMMIT;

SELECT 'empenho' AS tabela, count(*) AS linhas_alteradas FROM empenho WHERE observacoes LIKE '%[demo E2%'
UNION ALL
SELECT 'unidade', count(*) FROM unidade WHERE nome LIKE '%[demo E2]'
UNION ALL
SELECT 'requisicao_servico', count(*) FROM requisicao_servico WHERE observacoes LIKE '%[demo E2%';
