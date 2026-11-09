import os
from dotenv import load_dotenv
import psycopg

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Constantes de conexão lidas das variáveis de ambiente
HOST_DO_BANCO = os.getenv("HOST_DO_BANCO")
NOME_DO_BANCO = os.getenv("NOME_DO_BANCO")
USUARIO_DO_BANCO = os.getenv("USUARIO_DO_BANCO")
SENHA_DO_BANCO = os.getenv("SENHA_DO_BANCO")
PORTA_DO_BANCO = os.getenv("PORTA_DO_BANCO")



def conectar() -> psycopg.Connection:
    "Cria uma conexão com o banco de dados PostgreSQL."

    return psycopg.connect(
        host=HOST_DO_BANCO,
        dbname=NOME_DO_BANCO,
        user=USUARIO_DO_BANCO,
        password=SENHA_DO_BANCO,
        port=PORTA_DO_BANCO,
    )