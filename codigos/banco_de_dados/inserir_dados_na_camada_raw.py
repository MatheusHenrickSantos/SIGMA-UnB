import json
import sys
from pathlib import Path
from typing import Any, Literal, TypeAlias

PASTA_CODIGOS = Path(__file__).resolve().parents[1]

import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb

if __package__:
    from ..utilidades import calcular_hash
    from .conectar_com_banco_de_dados import conectar
else:
    sys.path.insert(0, str(PASTA_CODIGOS))
    from conectar_com_banco_de_dados import conectar
    from utilidades import calcular_hash

TipoDaTabela: TypeAlias = Literal["estoque", "compras", "catmat"]


class InserirDadosNaCamadaRaw:
    """
    Responsável por inserir arquivos JSON nas tabelas da camada Raw.
    """

    def __init__(self, pasta_dados: Path, padrao: str = "*.json") -> None:
        self.pasta_dados = pasta_dados
        # padrão de nome dos arquivos (glob); ex.: "*-12-2025.json" carrega um mês
        self.padrao = padrao



    def _listar_arquivos(self) -> list[Path]:
        """Lista os arquivos JSON da pasta de dados."""

        if not self.pasta_dados.is_dir():
            raise FileNotFoundError(
                f"Pasta não encontrada: {self.pasta_dados}"
            )

        return sorted(self.pasta_dados.glob(self.padrao))



    def _ler_arquivo(self, arquivo: Path) -> tuple[Jsonb, str]:
        """
        Lê e interpreta o arquivo JSON.

        Retorna o conteúdo interpretado e seu hash SHA-256.
        """

        conteudo = arquivo.read_text(encoding="utf-8")

        dado = json.loads(conteudo)
        hash_arquivo = calcular_hash(conteudo)

        return Jsonb(dado), hash_arquivo



    def _extrair_referencia(self, arquivo: Path) -> tuple[int, int]:
        """
        Extrai mês e ano do nome do arquivo de estoque.

        Exemplo: estoque-do-almoxarifado-12-2025.json
        Retorno: (12, 2025)
        """

        import re

        padrao = r"estoque-do-almoxarifado-(\d{2})-(\d{4})\.json"

        correspondencia = re.fullmatch(padrao, arquivo.name)

        if correspondencia is None:
            raise ValueError(
                f"Nome de arquivo inválido: {arquivo.name}"
            )

        mes, ano = map(int, correspondencia.groups())

        if not 1 <= mes <= 12:
            raise ValueError(f"Mês inválido: {arquivo.name}")

        return mes, ano



    def _preparar_insercao(
        self,
        tabela: TipoDaTabela,
        dado: Jsonb,
        hash_arquivo: str,
        arquivo: Path,
    ) -> tuple[sql.Composed, tuple[Any, ...]]:
        """Prepara a consulta SQL e seus parâmetros."""

        if tabela == "estoque":
            mes, ano = self._extrair_referencia(arquivo)

            comando = sql.SQL("""
                INSERT INTO raw.{} (
                    dado_bruto,
                    hash_do_arquivo,
                    mes_de_referencia,
                    ano_de_referencia
                )
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (hash_do_arquivo) DO NOTHING
            """).format(sql.Identifier(tabela))

            parametros = (dado, hash_arquivo, mes, ano)

        else:
            comando = sql.SQL("""
                INSERT INTO raw.{} (
                    dado_bruto,
                    hash_do_arquivo
                )
                VALUES (%s, %s)
                ON CONFLICT (hash_do_arquivo) DO NOTHING
            """).format(sql.Identifier(tabela))

            parametros = (dado, hash_arquivo)

        return comando, parametros



    def _inserir_arquivo(
        self,
        tabela: TipoDaTabela,
        arquivo: Path,
    ) -> bool:
        """
        Insere um arquivo na tabela indicada.

        Retorna True se inserido ou False se já existia.
        """

        dado, hash_arquivo = self._ler_arquivo(arquivo)

        comando, parametros = self._preparar_insercao(
            tabela,
            dado,
            hash_arquivo,
            arquivo,
        )

        with conectar() as conexao:
            with conexao.cursor() as cursor:
                cursor.execute(comando, parametros)
                return cursor.rowcount == 1



    def _inserir_arquivos(self, tabela: TipoDaTabela) -> int:
        """Coordena a ingestão dos arquivos de uma tabela. Devolve o número de falhas."""

        arquivos = self._listar_arquivos()

        inseridos = 0
        duplicados = 0
        falhas = 0

        for arquivo in arquivos:
            try:
                if self._inserir_arquivo(tabela, arquivo):
                    inseridos += 1
                else:
                    duplicados += 1

            except (OSError, ValueError, TypeError, psycopg.Error) as erro:
                falhas += 1
                print(f"ERRO ao processar {arquivo.name}: {erro}")

        print(
            f"Ingestão de {tabela} concluída: "
            f"{inseridos} inserido(s), "
            f"{duplicados} duplicado(s), "
            f"{falhas} falha(s)."
        )
        return falhas



    def inserir_estoque(self) -> int:
        """Insere arquivos de estoque na camada Raw."""

        return self._inserir_arquivos("estoque")



    def inserir_compras(self) -> int:
        """Insere arquivos de compras na camada Raw."""

        return self._inserir_arquivos("compras")



    def inserir_catmat(self) -> int:
        """Insere arquivos do CATMAT na camada Raw."""

        return self._inserir_arquivos("catmat")



if __name__ == "__main__":
    import argparse

    analisador = argparse.ArgumentParser(description="Carrega os JSON de dados/ na camada raw.")
    analisador.add_argument(
        "tabelas",
        nargs="*",
        help="estoque, catmat e/ou compras (padrão: estoque catmat; compras roda "
             "depois da busca semântica, ver docker-compose.yml)",
    )
    analisador.add_argument(
        "--mes",
        help="só o estoque deste mês, no formato MM-AAAA (backfill de uma partição mensal)",
    )
    argumentos = analisador.parse_args()
    tabelas = argumentos.tabelas or ["estoque", "catmat"]
    invalidas = set(tabelas) - {"estoque", "catmat", "compras"}
    if invalidas:
        analisador.error(f"tabela(s) desconhecida(s): {', '.join(sorted(invalidas))}")
    pasta_dados = PASTA_CODIGOS.parent / "dados"
    falhas = 0

    for tabela in tabelas:
        padrao = f"*-{argumentos.mes}.json" if argumentos.mes and tabela == "estoque" else "*.json"
        carga = InserirDadosNaCamadaRaw(pasta_dados / tabela, padrao)
        falhas += getattr(carga, f"inserir_{tabela}")()

    # Falha em qualquer arquivo = código de saída 1, para o compose e o
    # orquestrador não seguirem como se a carga tivesse dado certo.
    sys.exit(1 if falhas else 0)
