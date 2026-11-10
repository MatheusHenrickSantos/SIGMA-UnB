-- V5: decisão por material e origem das revisões (pessoa ou agente de IA)
--
-- semantica.revisao_correspondencia guarda decisões por par (material, item
-- CATMAT). Faltava:
--   * registrar a decisão sobre o material como um todo, em especial "não
--     existe item CATMAT equivalente", que não tem código para apontar;
--   * distinguir decisões de pessoas das sugeridas por agentes de IA. As
--     decisões de agentes servem para seguir com o pipeline (busca de preços),
--     mas continuam na fila até uma pessoa confirmar.
--
-- Regras:
--   * a chave continua sendo o hash do texto original do material (vale para
--     aquele texto exato e sobrevive a reprocessamentos);
--   * uma decisão de pessoa sobre o mesmo par substitui a do agente (mesma PK);
--   * itens CATMAT aprovados = pares 'equivalente' em revisao_correspondencia,
--     de pessoa ou de agente (ver semantica.v_item_aprovado).

ALTER TABLE semantica.revisao_correspondencia
    ADD COLUMN tipo_revisor TEXT NOT NULL DEFAULT 'pessoa'
        CHECK (tipo_revisor IN ('pessoa', 'agente'));

COMMENT ON COLUMN semantica.revisao_correspondencia.tipo_revisor IS
    'pessoa = conferido pela squad; agente = sugerido por agente de IA, ainda sem conferência';

CREATE TABLE semantica.revisao_material (
    hash_original_material CHAR(64)    PRIMARY KEY,
    -- true quando não há item CATMAT ativo equivalente
    sem_correspondente     BOOLEAN     NOT NULL,
    -- alta = inequívoco; media = com inferência; baixa = palpite (prioridade de revisão)
    confianca              TEXT        NOT NULL CHECK (confianca IN ('alta', 'media', 'baixa')),
    justificativa          TEXT,
    revisor                TEXT        NOT NULL CHECK (btrim(revisor) <> ''),
    tipo_revisor           TEXT        NOT NULL DEFAULT 'pessoa'
        CHECK (tipo_revisor IN ('pessoa', 'agente')),
    -- cópia do texto revisado, para leitura humana
    texto_material         TEXT        NOT NULL,
    revisada_em            TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE semantica.revisao_material IS
    'Decisão sobre o material como um todo; os itens equivalentes ficam em revisao_correspondencia';

-- Itens CATMAT aprovados por material ativo (entrada da busca de preços de compras).
CREATE VIEW semantica.v_item_aprovado AS
SELECT
    m.chave_origem   AS identificador_material,
    m.texto_original AS material,
    r.codigo_item,
    r.tipo_revisor,
    r.revisor,
    r.revisada_em
FROM semantica.revisao_correspondencia AS r
JOIN semantica.descricao AS m
  ON m.origem = 'estoque' AND m.hash_original = r.hash_original_material AND m.ativa
WHERE r.decisao = 'equivalente';

-- Fila: sai da fila o material resolvido POR PESSOA (item equivalente ou
-- "sem correspondente"). Os resolvidos só por agente continuam, com a decisão
-- sugerida visível em decisao/tipo_revisor, para conferência.
DROP VIEW semantica.v_fila_revisao;

CREATE VIEW semantica.v_fila_revisao AS
WITH ultima AS (
    SELECT DISTINCT ON (id_modelo) id_execucao
    FROM semantica.execucao_correspondencia
    WHERE finalizada_em IS NOT NULL
    ORDER BY id_modelo, id_execucao DESC
),
resolvido_por_pessoa AS (
    SELECT hash_original_material FROM semantica.revisao_correspondencia
    WHERE decisao = 'equivalente' AND tipo_revisor = 'pessoa'
    UNION
    SELECT hash_original_material FROM semantica.revisao_material
    WHERE sem_correspondente AND tipo_revisor = 'pessoa'
)
SELECT v.*, rm.sem_correspondente AS sugestao_sem_correspondente, rm.confianca AS confianca_sugestao
FROM semantica.v_candidato_catmat AS v
JOIN ultima AS u ON u.id_execucao = v.id_execucao
JOIN semantica.descricao AS m
  ON m.origem = 'estoque' AND m.chave_origem = v.identificador_material
LEFT JOIN semantica.revisao_material AS rm ON rm.hash_original_material = m.hash_original
WHERE NOT EXISTS (
    SELECT 1 FROM resolvido_por_pessoa AS p WHERE p.hash_original_material = m.hash_original
);
