"""De onde vêm as descrições: tabelas da camada Prata geradas pelo dbt.

Para acrescentar uma origem (por exemplo, descrições de compras públicas),
basta uma consulta aqui que devolva (chave, texto), o papel dela na busca e
o valor no CHECK de semantica.descricao.origem (nova migração).
"""

from __future__ import annotations

import psycopg

from .embeddings import PAPEL_CONSULTA, PAPEL_DOCUMENTO

# material do estoque procura; item CATMAT é onde se procura
PAPEL_POR_ORIGEM = {"estoque": PAPEL_CONSULTA, "catmat": PAPEL_DOCUMENTO}

_TABELAS = {"estoque": "prata.material", "catmat": "prata.catmat_item"}


class ErroFonte(RuntimeError):
    """A tabela da Prata ainda não existe."""


def consulta(origem: str, incluir_catmat_inativo: bool = False) -> str:
    """SQL que devolve (chave, texto original) na ordem da chave.

    Estoque: descricao_normalizada é a descrição integral do material (a
    Prata agrupa as variações de escrita do estoque pelo seed
    materiais_normalizados); as colunas nome e descricao são truncadas
    (CHAR(50)/CHAR(200)) e não servem aqui.
    CATMAT: por padrão só itens ativos (status_item não falso), porque
    códigos inativos não servem para novas compras.
    """
    if origem == "estoque":
        return (
            "SELECT identificador_material, descricao_normalizada "
            "FROM prata.material ORDER BY identificador_material"
        )
    if origem == "catmat":
        filtro = "" if incluir_catmat_inativo else "WHERE status_item IS NOT FALSE "
        return (
            "SELECT codigo_item::text, descricao_item FROM prata.catmat_item "
            f"{filtro}ORDER BY codigo_item, descricao_item"
        )
    raise ValueError(f"origem desconhecida: {origem!r}")


def ler(conn: psycopg.Connection, origem: str, incluir_catmat_inativo: bool = False) -> list[tuple]:
    tabela = _TABELAS[origem]
    if conn.execute("SELECT to_regclass(%s)", (tabela,)).fetchone()[0] is None:
        raise ErroFonte(f"{tabela} não existe: gere a Prata antes (dbt build)")
    return conn.execute(consulta(origem, incluir_catmat_inativo)).fetchall()
