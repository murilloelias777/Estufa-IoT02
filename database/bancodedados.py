
import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()


def conectar():
    try:
        conexao = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "estufa_iot01")
        )

        if conexao.is_connected():
            return conexao

    except Error as erro:
        print(f"Erro ao conectar ao MySQL: {erro}")
        return None


def testar_conexao():
    conexao = conectar()

    if conexao is None:
        return False

    cursor = None

    try:
        cursor = conexao.cursor()
        cursor.execute("SELECT DATABASE()")
        resultado = cursor.fetchone()

        print("Conexão realizada com sucesso!")
        print(f"Banco conectado: {resultado[0]}")

        return True

    except Error as erro:
        print(f"Erro ao testar banco: {erro}")
        return False

    finally:
        if cursor:
            cursor.close()

        conexao.close()
