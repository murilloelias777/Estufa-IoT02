
from database.bancodedados import conectar

from werkzeug.security import generate_password_hash, check_password_hash

from getpass import getpass
from mysql.connector import Error


# ==========================================
# ESTUFA IOT 02
# SISTEMA DE CADASTRO E LOGIN
# ==========================================


def verificar_tabela(conexao):

    cursor = conexao.cursor()

    cursor.execute("""
        SELECT TABLE_NAME
        FROM information_schema.tables
        WHERE TABLE_SCHEMA = 'estufa_iot02'
        AND TABLE_NAME IN ('usuario', 'usuarios')
    """)

    resultado = cursor.fetchone()

    cursor.close()

    if resultado:
        return resultado[0]

    return None


# ==========================================
# CADASTRO DE USUÁRIO
# ==========================================

def cadastrar_usuario():

    print("\n========== CADASTRO DE USUÁRIO ==========")

    nome = input("Nome completo: ").strip()
    email = input("E-mail: ").strip().lower()
    senha = getpass("Senha: ")
    confirmar_senha = getpass("Confirme a senha: ")

    if not nome or not email or not senha:
        print("\nPreencha todos os campos!")
        return

    if senha != confirmar_senha:
        print("\nAs senhas não são iguais!")
        return

    conexao = conectar()

    if conexao is None:
        print("Não foi possível conectar ao banco.")
        return

    cursor = None

    try:

        tabela = verificar_tabela(conexao)

        if tabela is None:
            print("Tabela usuario/usuarios não encontrada.")
            return

        cursor = conexao.cursor()

        # Verifica se o e-mail já está cadastrado
        cursor.execute(
            f"SELECT idusuario FROM {tabela} WHERE email = %s",
            (email,)
        )

        if cursor.fetchone():
            print("\nEste e-mail já está cadastrado!")
            return

        # Criptografa a senha
        senha_hash = generate_password_hash(senha)

        # Insere o usuário
        cursor.execute(
            f"""
            INSERT INTO {tabela}
            (nome, email, senha)
            VALUES (%s, %s, %s)
            """,
            (nome, email, senha_hash)
        )

        conexao.commit()

        print("\n========================================")
        print("USUÁRIO CADASTRADO COM SUCESSO!")
        print("========================================")

    except Error as erro:
        print(f"\nErro ao cadastrar usuário: {erro}")

    finally:

        if cursor:
            cursor.close()

        conexao.close()


# ==========================================
# LOGIN DE USUÁRIO
# ==========================================

def fazer_login():

    print("\n============== LOGIN ===================")

    email = input("E-mail: ").strip().lower()
    senha = getpass("Senha: ")

    conexao = conectar()

    if conexao is None:
        print("Não foi possível conectar ao banco.")
        return

    cursor = None

    try:

        tabela = verificar_tabela(conexao)

        if tabela is None:
            print("Tabela usuario/usuarios não encontrada.")
            return

        cursor = conexao.cursor(dictionary=True)

        cursor.execute(
            f"""
            SELECT idusuario, nome, email, senha
            FROM {tabela}
            WHERE email = %s
            """,
            (email,)
        )

        usuario = cursor.fetchone()

        if usuario is None:
            print("\nUsuário não encontrado!")
            return

        # Confere a senha criptografada
        if check_password_hash(usuario["senha"], senha):

            print("\n========================================")
            print("LOGIN REALIZADO COM SUCESSO!")
            print("========================================")

            print(f"Bem-vindo(a), {usuario['nome']}!")
            print(f"ID: {usuario['idusuario']}")
            print(f"E-mail: {usuario['email']}")

        else:

            print("\nSenha incorreta!")

    except Error as erro:
        print(f"\nErro ao realizar login: {erro}")

    finally:

        if cursor:
            cursor.close()

        conexao.close()


# ==========================================
# MENU PRINCIPAL
# ==========================================

def menu():

    while True:

        print("\n")
        print("========================================")
        print("          ESTUFA IOT 02")
        print("       SISTEMA DE USUÁRIOS")
        print("========================================")

        print("1 - Cadastrar usuário")
        print("2 - Fazer login")
        print("0 - Sair")

        print("========================================")

        opcao = input("Escolha uma opção: ").strip()

        if opcao == "1":

            cadastrar_usuario()

        elif opcao == "2":

            fazer_login()

        elif opcao == "0":

            print("\nSistema encerrado!")
            break

        else:

            print("\nOpção inválida! Tente novamente.")


# ==========================================
# EXECUÇÃO
# ==========================================

if __name__ == "__main__":

    menu()

print ("ola")