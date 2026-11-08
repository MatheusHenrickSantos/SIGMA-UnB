"""Convenções de acesso aos dados do estoque.

A etapa de normalização usa a camada bronze do banco como fonte principal.
O módulo mantém a leitura do banco concentrada em um único ponto e deixa a
escrita CSV para o utilitário de I/O.
"""
from __future__ import annotations

from .fonte_banco import FonteEstoqueBanco


def carregar_materials_do_bronze() -> list[str]:
    """Consulta os materiais distintos da camada bronze, tabela estoque."""

    return FonteEstoqueBanco().carregar()
