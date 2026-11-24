"""Validação da camada semântica: confere se as etapas rodaram na ordem certa.

A ordem do serviço `semantica` é

    sincronizar -> embeddings -> corresponder -> importar -> validar

e cada etapa pressupõe a anterior: a busca só enxerga o que tem vetor, e os
vetores só existem para o que foi sincronizado; as decisões só valem para
materiais sincronizados e itens CATMAT ativos. Esta etapa roda por último e
confere esses pressupostos e a coerência das decisões, para o pipeline não
seguir (compras, camada ouro) com a camada semântica pela metade.

Cada verificação tem gravidade:

- erro: o pipeline não pode seguir (`python -m semantica validar` sai com 1);
- aviso: o dado é usável, mas merece conferência (revisão, não bloqueio).
"""

from __future__ import annotations

from dataclasses import dataclass

import psycopg


@dataclass(frozen=True)
class Verificacao:
    nome: str
    gravidade: str  # 'erro' | 'aviso'
    quantidade: int
    descricao: str

    @property
    def passou(self) -> bool:
        return self.quantidade == 0


# (nome, gravidade, descrição, SQL que devolve a quantidade de violações)
_VERIFICACOES: list[tuple[str, str, str, str]] = [
    (
        "descricao_valida_sem_vetor",
        "erro",
        "Descrições ativas e válidas (estoque ou CATMAT) sem vetor do modelo: a etapa embeddings "
        "não rodou, ou rodou antes da sincronização.",
        """
        SELECT count(*) FROM busca.descricao d
        WHERE d.ativa AND d.situacao = 'valida'
          AND NOT EXISTS (SELECT 1 FROM busca.embedding e
                          WHERE e.id_descricao = d.id_descricao AND e.id_modelo = %(modelo)s)
        """,
    ),
    (
        "busca_nao_cobre_materiais",
        "erro",
        "Materiais ativos e válidos que ficaram fora da última busca finalizada: a etapa "
        "corresponder rodou antes de sincronizar/embeddings, ou não rodou.",
        """
        SELECT GREATEST(
            (SELECT count(*) FROM busca.descricao
             WHERE origem = 'estoque' AND ativa AND situacao = 'valida')
            - COALESCE((SELECT materiais FROM busca.execucao_correspondencia
                        WHERE id_modelo = %(modelo)s AND finalizada_em IS NOT NULL
                        ORDER BY id_execucao DESC LIMIT 1), 0),
            0)
        """,
    ),
    (
        "decisao_do_material_incoerente",
        "erro",
        "Material marcado como sem correspondente que também tem item equivalente (ou o contrário): "
        "revisao_material e revisao_correspondencia se contradizem.",
        """
        SELECT count(*) FROM prata.revisao_material rm
        WHERE rm.sem_correspondente = EXISTS (
            SELECT 1 FROM prata.revisao_correspondencia r
            WHERE r.hash_original_material = rm.hash_original_material AND r.decisao = 'equivalente')
        """,
    ),
    (
        "decisao_de_material_inexistente",
        "aviso",
        "Decisões cujo texto de material não existe mais (a descrição mudou na origem): ficam "
        "guardadas, mas não valem para nenhum material.",
        """
        SELECT count(*) FROM prata.revisao_material rm
        WHERE NOT EXISTS (SELECT 1 FROM busca.descricao d
                          WHERE d.origem = 'estoque' AND d.ativa
                            AND d.hash_original = rm.hash_original_material)
        """,
    ),
    (
        "item_aprovado_inativo",
        "aviso",
        "Itens CATMAT aprovados como equivalentes que não estão ativos e válidos no catálogo: "
        "seguem na busca de compras sem serem do catálogo vigente.",
        """
        SELECT count(*) FROM prata.revisao_correspondencia r
        WHERE r.decisao = 'equivalente'
          AND NOT EXISTS (SELECT 1 FROM busca.descricao k
                          WHERE k.origem = 'catmat' AND k.chave_origem = r.codigo_item
                            AND k.ativa AND k.situacao = 'valida')
        """,
    ),
    (
        "material_sem_decisao",
        "aviso",
        "Materiais ativos e válidos sem nenhuma decisão (nem item equivalente, nem sem correspondente).",
        """
        SELECT count(*) FROM busca.descricao d
        WHERE d.origem = 'estoque' AND d.ativa AND d.situacao = 'valida'
          AND NOT EXISTS (SELECT 1 FROM prata.revisao_material rm
                          WHERE rm.hash_original_material = d.hash_original)
          AND NOT EXISTS (SELECT 1 FROM prata.revisao_correspondencia r
                          WHERE r.hash_original_material = d.hash_original AND r.decisao = 'equivalente')
        """,
    ),
    (
        "equivalente_com_conflito_tecnico",
        "aviso",
        "Pares aprovados como equivalentes cuja checagem de especificações, na última busca, "
        "apontou conflito técnico (ex.: AA × AAA): conferir antes de confiar no preço.",
        """
        WITH ultima AS (
            SELECT id_execucao FROM busca.execucao_correspondencia
            WHERE id_modelo = %(modelo)s AND finalizada_em IS NOT NULL
            ORDER BY id_execucao DESC LIMIT 1)
        SELECT count(*) FROM prata.revisao_correspondencia r
        JOIN busca.descricao m ON m.origem = 'estoque' AND m.ativa AND m.hash_original = r.hash_original_material
        JOIN busca.descricao k ON k.origem = 'catmat' AND k.chave_origem = r.codigo_item
        JOIN prata.candidato_catmat c
          ON c.id_descricao_material = m.id_descricao AND c.id_descricao_catmat = k.id_descricao
        JOIN ultima u ON u.id_execucao = c.id_execucao
        WHERE r.decisao = 'equivalente' AND c.situacao_especificacao = 'conflito_tecnico'
        """,
    ),
]


def validar(conn: psycopg.Connection, id_modelo: int) -> list[Verificacao]:
    """Roda todas as verificações para o modelo e devolve o resultado de cada uma."""
    resultado = []
    for nome, gravidade, descricao, sql in _VERIFICACOES:
        quantidade = conn.execute(sql, {"modelo": id_modelo}).fetchone()[0]
        resultado.append(Verificacao(nome, gravidade, int(quantidade), descricao))
    return resultado


def tem_erro(verificacoes: list[Verificacao]) -> bool:
    return any(v.gravidade == "erro" and not v.passou for v in verificacoes)
