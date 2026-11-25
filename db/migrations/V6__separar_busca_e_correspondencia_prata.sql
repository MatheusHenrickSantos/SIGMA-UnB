-- V6: separar artefatos técnicos da busca das correspondências de negócio.
--
-- O schema `semantica` era o espaço operacional da busca vetorial, não a
-- camada semântica analítica prevista para depois da Ouro. Vetores e execuções
-- ficam em `busca`; candidatos e decisões passam a integrar a Prata.

ALTER SCHEMA semantica RENAME TO busca;
CREATE SCHEMA IF NOT EXISTS prata;
COMMENT ON SCHEMA busca IS
    'Artefatos técnicos da busca de correspondência: descrições vetorizadas, embeddings, modelos e execuções.';

-- Recria as visões depois de mover as tabelas de negócio para prata.
DROP VIEW busca.v_fila_revisao;
DROP VIEW busca.v_item_aprovado;
DROP VIEW busca.v_candidato_catmat;

ALTER TABLE busca.candidato_catmat SET SCHEMA prata;
ALTER TABLE busca.revisao_correspondencia SET SCHEMA prata;
ALTER TABLE busca.revisao_material SET SCHEMA prata;

COMMENT ON TABLE prata.candidato_catmat IS
    'Candidatos material–CATMAT gerados pela busca; são sugestões, não equivalências aprovadas.';
COMMENT ON TABLE prata.revisao_correspondencia IS
    'Decisões por par material–CATMAT, feitas por pessoa ou sugeridas por agente.';
COMMENT ON TABLE prata.revisao_material IS
    'Decisão sobre o material como um todo, inclusive quando não há CATMAT correspondente.';

CREATE VIEW prata.v_candidato_catmat AS
SELECT
    c.id_execucao,
    e.id_modelo,
    e.metodo,
    m.chave_origem   AS identificador_material,
    m.texto_original AS material,
    c.posicao,
    k.chave_origem   AS codigo_item,
    k.texto_original AS descricao_catmat,
    c.similaridade,
    c.pontuacao,
    COALESCE(c.pontuacao, c.similaridade) - lead(COALESCE(c.pontuacao, c.similaridade)) OVER (
        PARTITION BY c.id_execucao, c.id_descricao_material ORDER BY c.posicao
    )                AS vantagem_sobre_proximo,
    c.situacao_especificacao,
    c.especificacoes,
    c.medidas,
    c.recuperado_por,
    r.decisao,
    r.revisor,
    r.revisada_em,
    r.tipo_revisor
FROM prata.candidato_catmat AS c
JOIN busca.execucao_correspondencia AS e ON e.id_execucao = c.id_execucao
JOIN busca.descricao AS m ON m.id_descricao = c.id_descricao_material
JOIN busca.descricao AS k ON k.id_descricao = c.id_descricao_catmat
LEFT JOIN prata.revisao_correspondencia AS r
    ON r.hash_original_material = m.hash_original
   AND r.codigo_item = k.chave_origem;

CREATE VIEW prata.v_item_aprovado AS
SELECT
    m.chave_origem   AS identificador_material,
    m.texto_original AS material,
    r.codigo_item,
    r.tipo_revisor,
    r.revisor,
    r.revisada_em
FROM prata.revisao_correspondencia AS r
JOIN busca.descricao AS m
  ON m.origem = 'estoque' AND m.hash_original = r.hash_original_material AND m.ativa
WHERE r.decisao = 'equivalente';

CREATE VIEW prata.v_fila_revisao AS
WITH ultima AS (
    SELECT DISTINCT ON (id_modelo) id_execucao
    FROM busca.execucao_correspondencia
    WHERE finalizada_em IS NOT NULL
    ORDER BY id_modelo, id_execucao DESC
),
resolvido_por_pessoa AS (
    SELECT hash_original_material FROM prata.revisao_correspondencia
    WHERE decisao = 'equivalente' AND tipo_revisor = 'pessoa'
    UNION
    SELECT hash_original_material FROM prata.revisao_material
    WHERE sem_correspondente AND tipo_revisor = 'pessoa'
)
SELECT
    v.*,
    rm.sem_correspondente AS sugestao_sem_correspondente,
    rm.confianca AS confianca_sugestao
FROM prata.v_candidato_catmat AS v
JOIN ultima AS u ON u.id_execucao = v.id_execucao
JOIN busca.descricao AS m
  ON m.origem = 'estoque' AND m.chave_origem = v.identificador_material
LEFT JOIN prata.revisao_material AS rm ON rm.hash_original_material = m.hash_original
WHERE NOT EXISTS (
    SELECT 1 FROM resolvido_por_pessoa AS p
    WHERE p.hash_original_material = m.hash_original
);
