
import os
import mysql.connector

from dotenv import load_dotenv
from pathlib import Path
from mysql.connector import Error


# Localiza e carrega o arquivo .env na raiz do projeto
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)


def conectar():
    try:
        conexao = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            auth_plugin="caching_sha2_password"
        )

        if conexao.is_connected():
            print("Conectado ao banco estufa_iot02!")
            return conexao

    except Error as erro:
        print(f"Erro ao conectar ao MySQL: {erro}")
        return None

    except (TypeError, ValueError) as erro:
        print(f"Erro nas configurações do .env: {erro}")
        return None
