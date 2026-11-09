"""Fonte de leitura para materiais vindos da camada bronze do banco."""
from __future__ import annotations

from typing import Protocol

from codigos.banco_de_dados.conectar_com_banco_de_dados import conectar


class FonteEstoqueBanco:
    def carregar(self) -> list[str]:
        """Consulta os materiais distintos da camada bronze, tabela estoque."""

        conexao = conectar()
        cursor = conexao.cursor()
        try:
            cursor.execute(
                """
                SELECT DISTINCT material
                FROM bronze.estoque
                WHERE material IS NOT NULL
                  AND TRIM(material) <> ''
                ORDER BY material
                """
            )
            linhas = cursor.fetchall()
        finally:
            if hasattr(cursor, "close"):
                cursor.close()
            if hasattr(conexao, "close"):
                conexao.close()

        materiais: list[str] = []
        for linha in linhas:
            if not linha or linha[0] is None:
                continue
            material = str(linha[0]).strip()
            if material:
                materiais.append(material)

        return materiais
