
from database.bancodedados import conectar

conexao = conectar()

if conexao:
    print("Teste realizado com sucesso!")

    conexao.close()
else:
    print("Falha na conexão!")
