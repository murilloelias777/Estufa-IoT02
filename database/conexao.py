import os
import mysql.connector 
from dotenv import load_dotenv

#carrega as variaveis dos arquivos .env
load_dotenv()

#traz as configurações do banco que esta no env
class Conexao:
    @staticmethod
    def conectar():
        host = os.getenv("DB_HOST")
        porta = os.getenv("DB_PORT")
        usuario = os.getenv("DB_USER")
        senha = os.getenv("DB_PASSWORD")
        banco = os.getenv ("DB_NAME")

#verifica se as configurações obrigatorias existem
        if not all ([host, porta, usuario, banco]):
            raise ValueError("Verifique as configurações do arquivo .env")

        conexao = mysql.connector.connect(
            host=host,
            port=int(porta),
            user=usuario,
            password=senha,
            database=banco
)
        return conexao

try: 
    conexao = Conexao.conectar()

    if conexao.is_connected():
        print("conexao realizada com sucesso")

except ValueError as erro:
    print(f"erro ao conectar com MySql {erro}")

finally:
    if "conexao" in locals() and conexao.is_connected():
        conexao.close()
        print("Conexao encerrada")
