from pathlib import Path
from conectar_com_banco_de_dados import conectar
from typing import LiteralString, cast
import psycopg



class InicializarEsquema:
    """
    Responsável por criar a camada raw do banco de dados.

    A classe lê o script SQL de definição do esquema armazenado
    em um arquivo DDL e o executa em uma instância PostgreSQL.
    """

    def __init__(self) -> None:
        "Inicializa a classe configurando o caminho do arquivo SQL."

        self.arquivo_sql = (
            Path(__file__).resolve().parents[2]
            / "db/migrations/ddl.sql"
        )



    def _ler_arquivo(self) -> str:
        "Lê o conteúdo do arquivo DDL."

        return self.arquivo_sql.read_text(encoding="utf-8")



    def criar_camada_raw(self) -> None:
        """
        Cria a camada raw do banco de dados.

        O método realiza as seguintes operações:
        1. Lê o conteúdo do arquivo DDL.
        2. Estabelece conexão com o PostgreSQL.
        3. Executa o script SQL.
        4. Encerra automaticamente a conexão e o cursor.

        Lança `psycopg.Error` caso ocorra algum erro relacionado à conexão ou execução de comandos SQL.

        Lança `OSError` caso o arquivo DDL não possa ser acessado ou lido.
        
        Lança `ValueError` caso sejam encontrados valores inválidos durante o processo de inicialização.
        """

        try:
            sql = self._ler_arquivo()

            with conectar() as conexao:
                with conexao.cursor() as cursor:
                    cursor.execute(cast(LiteralString, sql))

            print("InicializarEsquema: Camada Raw criada com sucesso.")

        except(psycopg.Error, OSError, ValueError) as erro:
            print(f"ERRO no InicializarEsquema: {erro}")
            raise erro



if __name__ == "__main__":
    inicializador = InicializarEsquema()
    inicializador.criar_camada_raw()