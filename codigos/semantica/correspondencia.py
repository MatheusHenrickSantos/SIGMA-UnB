"""Correspondência semântica: os itens CATMAT mais próximos de cada material.

Para cada material válido do estoque, busca os top-K itens CATMAT pela
distância de cosseno entre os vetores (pgvector, operador <=>) e grava os
candidatos com:

- similaridade = 1 - distância de cosseno (1 = mesma direção);
- a checagem de especificações (especificacoes.py): conflito de medida,
  unidade, cor, código... entre o texto do estoque e o do CATMAT.

Similaridade alta NÃO prova equivalência: dois itens podem ser quase iguais
no texto e diferir justamente no que importa (AA x AAA, 10 kΩ x 1 kΩ).
Por isso o resultado é uma lista de candidatos para revisão humana; nada é
aprovado automaticamente. As decisões ficam em revisao_correspondencia.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from itertools import groupby
from typing import Sequence

import psycopg
from psycopg.types.json import Jsonb

from . import repositorio
from .especificacoes import VERSAO_REGRAS, comparar_especificacoes
from .normalizacao import VERSAO_NORMALIZACAO

# Padrão do pgvector para hnsw.ef_search. O índice devolve no máximo
# ef_search vizinhos por consulta, então ele nunca pode ficar abaixo de top_k.
EF_SEARCH_PADRAO = 40

# Índice HNSW que a V2 criava e a V3 removeu (ADR 0005): hoje a busca é exata.
# Usado pela medição (medir_adr0005.py) e pelos testes; para voltar a usá-lo,
# crie-o numa migração nova com este mesmo comando.
SQL_INDICE_HNSW = (
    "CREATE INDEX {nome} ON semantica.embedding "
    "USING hnsw (vetor vector_cosine_ops) WHERE origem = 'catmat'"
)

DECISOES = ("equivalente", "nao_equivalente", "incerto")


class ErroCorrespondencia(RuntimeError):
    """A correspondência não pode rodar com o estado atual do banco."""


@dataclass(frozen=True)
class ParametrosBusca:
    # quantos candidatos guardar por material
    top_k: int = 10
    # descarta candidatos abaixo deste valor (None = guarda os top_k).
    # Não há padrão calibrado: o valor depende do modelo e precisa ser
    # escolhido olhando pares revisados (ver docs/semantica.md).
    limiar_similaridade: float | None = None
    # True = proíbe índice mesmo que exista. Sem índice HNSW (situação desde a
    # V3), a busca já é exata nos dois casos.
    busca_exata: bool = False
    # só vale se houver índice HNSW; None = max(EF_SEARCH_PADRAO, top_k)
    ef_search: int | None = None

    def validar(self) -> None:
        if not 1 <= self.top_k <= 100:
            raise ValueError("top_k deve estar entre 1 e 100")
        if self.limiar_similaridade is not None and not -1 <= self.limiar_similaridade <= 1:
            raise ValueError("limiar_similaridade deve estar entre -1 e 1")
        if self.ef_search is not None and self.ef_search < self.top_k:
            raise ValueError("ef_search não pode ser menor que top_k")

    @property
    def ef_search_efetivo(self) -> int:
        return self.ef_search or max(EF_SEARCH_PADRAO, self.top_k)


@dataclass(frozen=True)
class ResumoCorrespondencia:
    id_execucao: int
    materiais: int
    materiais_sem_vetor: int
    materiais_sem_candidato: int
    candidatos: int
    candidatos_com_conflito: int


_BUSCA = """
SELECT m.id_descricao,
       m.texto_original,
       k.id_descricao,
       k.texto_original,
       1 - vizinho.distancia AS similaridade
FROM semantica.descricao AS m
JOIN semantica.embedding AS em
  ON em.id_descricao = m.id_descricao AND em.id_modelo = %(modelo)s
CROSS JOIN LATERAL (
    -- só ORDER BY distância + LIMIT aqui dentro, para um índice HNSW, se
    -- existir, poder ser usado; sem índice é uma varredura exata
    SELECT c.id_descricao, c.vetor <=> em.vetor AS distancia
    FROM semantica.embedding AS c
    WHERE c.origem = 'catmat' AND c.id_modelo = %(modelo)s
    ORDER BY c.vetor <=> em.vetor
    LIMIT %(top_k)s
) AS vizinho
JOIN semantica.descricao AS k ON k.id_descricao = vizinho.id_descricao
WHERE m.origem = 'estoque' AND m.ativa AND m.situacao = 'valida'
  AND (%(limiar)s::float8 IS NULL OR 1 - vizinho.distancia >= %(limiar)s::float8)
  AND (%(chaves)s::text[] IS NULL OR m.chave_origem = ANY(%(chaves)s::text[]))
ORDER BY m.id_descricao, vizinho.distancia, k.chave_origem
"""


def _lista(texto: str, separador: str) -> list[str]:
    return [parte for parte in texto.split(separador) if parte]


def avaliar_especificacoes(texto_estoque: str, texto_catmat: str) -> tuple[str, dict]:
    """Situação e detalhes da checagem de especificações, prontos para JSONB."""
    resultado = comparar_especificacoes(texto_estoque, texto_catmat)
    return resultado["status_validacao"], {
        "estoque": json.loads(resultado["especificacoes_estoque"]),
        "catmat": json.loads(resultado["especificacoes_catmat"]),
        "compativeis": _lista(resultado["categorias_compativeis"], " | "),
        "ausentes_no_catmat": _lista(resultado["categorias_ausentes_no_catmat"], " | "),
        "conflitos": _lista(resultado["categorias_com_conflito"], " | "),
        "detalhes_conflitos": _lista(resultado["detalhes_conflitos"], " ; "),
    }


def executar_correspondencia(
    conn: psycopg.Connection,
    id_modelo: int,
    parametros: ParametrosBusca = ParametrosBusca(),
    chaves_material: Sequence[str] | None = None,
) -> ResumoCorrespondencia:
    """Roda a busca e grava uma execução completa, numa transação só."""
    repositorio.exigir_autocommit(conn)
    parametros.validar()

    with conn.transaction(), conn.cursor() as cur:
        if not cur.execute(
            "SELECT EXISTS (SELECT 1 FROM semantica.embedding "
            "WHERE origem = 'catmat' AND id_modelo = %s)",
            (id_modelo,),
        ).fetchone()[0]:
            raise ErroCorrespondencia(
                "não há vetores CATMAT para este modelo: rode antes a etapa de embeddings"
            )

        filtro = {"modelo": id_modelo, "chaves": list(chaves_material) if chaves_material else None}
        materiais, sem_vetor = cur.execute(
            """
            SELECT count(*),
                   count(*) FILTER (WHERE NOT EXISTS (
                       SELECT 1 FROM semantica.embedding e
                       WHERE e.id_descricao = d.id_descricao AND e.id_modelo = %(modelo)s))
            FROM semantica.descricao d
            WHERE d.origem = 'estoque' AND d.ativa AND d.situacao = 'valida'
              AND (%(chaves)s::text[] IS NULL OR d.chave_origem = ANY(%(chaves)s::text[]))
            """,
            filtro,
        ).fetchone()

        # SET LOCAL vale só dentro desta transação
        cur.execute(f"SET LOCAL hnsw.ef_search = {int(parametros.ef_search_efetivo)}")
        cur.execute("SET LOCAL hnsw.iterative_scan = strict_order")
        if parametros.busca_exata:
            cur.execute("SET LOCAL enable_indexscan = off")

        id_execucao = cur.execute(
            """
            INSERT INTO semantica.execucao_correspondencia
                (id_modelo, top_k, limiar_similaridade, busca_exata, ef_search,
                 versao_normalizacao, versao_regras)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id_execucao
            """,
            (id_modelo, parametros.top_k, parametros.limiar_similaridade,
             parametros.busca_exata, None if parametros.busca_exata else parametros.ef_search_efetivo,
             VERSAO_NORMALIZACAO, VERSAO_REGRAS),
        ).fetchone()[0]

        linhas = cur.execute(
            _BUSCA,
            {**filtro, "top_k": parametros.top_k, "limiar": parametros.limiar_similaridade},
        ).fetchall()

        candidatos = []
        com_conflito = 0
        for id_material, grupo in groupby(linhas, key=lambda linha: linha[0]):
            for posicao, (_, texto_material, id_catmat, texto_catmat, similaridade) in enumerate(grupo, 1):
                situacao, detalhes = avaliar_especificacoes(texto_material, texto_catmat)
                com_conflito += situacao == "conflito_tecnico"
                candidatos.append(
                    (id_execucao, id_material, posicao, id_catmat, similaridade, situacao, Jsonb(detalhes))
                )
        cur.executemany(
            """
            INSERT INTO semantica.candidato_catmat
                (id_execucao, id_descricao_material, posicao, id_descricao_catmat,
                 similaridade, situacao_especificacao, especificacoes)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            candidatos,
        )

        com_candidato = len({linha[0] for linha in linhas})
        sem_candidato = materiais - com_candidato
        cur.execute(
            """
            UPDATE semantica.execucao_correspondencia
            SET finalizada_em = now(), materiais = %s, materiais_sem_candidato = %s, candidatos = %s
            WHERE id_execucao = %s
            """,
            (materiais, sem_candidato, len(candidatos), id_execucao),
        )

    return ResumoCorrespondencia(
        id_execucao=id_execucao,
        materiais=materiais,
        materiais_sem_vetor=sem_vetor,
        materiais_sem_candidato=sem_candidato,
        candidatos=len(candidatos),
        candidatos_com_conflito=com_conflito,
    )


def registrar_revisao(
    conn: psycopg.Connection,
    identificador_material: str,
    codigo_item: str,
    decisao: str,
    revisor: str,
    observacao: str | None = None,
) -> None:
    """Grava (ou troca) a decisão humana sobre um par material x item CATMAT."""
    repositorio.exigir_autocommit(conn)
    if decisao not in DECISOES:
        raise ValueError(f"decisão deve ser uma de {DECISOES}")
    if not revisor or not revisor.strip():
        raise ValueError("informe quem revisou")

    with conn.transaction(), conn.cursor() as cur:
        material = cur.execute(
            "SELECT hash_original, texto_original FROM semantica.descricao "
            "WHERE origem = 'estoque' AND chave_origem = %s",
            (identificador_material,),
        ).fetchone()
        if material is None or material[0] is None:
            raise ErroCorrespondencia(f"material {identificador_material!r} não encontrado")
        if cur.execute(
            "SELECT 1 FROM semantica.descricao WHERE origem = 'catmat' AND chave_origem = %s",
            (codigo_item,),
        ).fetchone() is None:
            raise ErroCorrespondencia(f"item CATMAT {codigo_item!r} não encontrado")

        ultima_execucao = cur.execute(
            """
            SELECT max(c.id_execucao)
            FROM semantica.candidato_catmat c
            JOIN semantica.descricao m ON m.id_descricao = c.id_descricao_material
            JOIN semantica.descricao k ON k.id_descricao = c.id_descricao_catmat
            WHERE m.origem = 'estoque' AND m.chave_origem = %s AND k.chave_origem = %s
            """,
            (identificador_material, codigo_item),
        ).fetchone()[0]

        cur.execute(
            """
            INSERT INTO semantica.revisao_correspondencia
                (hash_original_material, codigo_item, decisao, revisor, observacao,
                 texto_material, id_execucao)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (hash_original_material, codigo_item) DO UPDATE SET
                decisao = EXCLUDED.decisao,
                revisor = EXCLUDED.revisor,
                observacao = EXCLUDED.observacao,
                id_execucao = EXCLUDED.id_execucao,
                revisada_em = now()
            """,
            (material[0], codigo_item, decisao, revisor.strip(), observacao, material[1],
             ultima_execucao),
        )
