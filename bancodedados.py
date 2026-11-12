import mysql.connector
from dotenv import load_dotenv
import os
try:
    # 1. Estabelece a conexão com o banco
    conexao = mysql.connector.connect(
        host="localhost",          # Endereço do servidor (ex: localhost ou IP)
        user="root",               # Seu usuário do MySQL
        password=os.getenv ("DB_PASSWORD"), # Sua senha do MySQL
        database="estufa_iot01"   # Nome do banco que você já criou
    )

    if conexao.is_connected():
        print("Conectado ao MySQL com sucesso!")
        
        # 2. Cria um cursor para executar comandos SQL
        cursor = conexao.cursor()
        
        # Exemplo: listando as tabelas do banco
        cursor.execute("SHOW TABLES;")
        for tabela in cursor:
            print(tabela)

except mysql.connector.Error as erro:
    print(f"Erro ao conectar ao MySQL: {erro}")

finally:
    # 3. Fecha o cursor e a conexão por segurança
    if 'conexao' in locals() and conexao.is_connected():
        cursor.close()
        conexao.close()
        print("Conexão encerrada.")
