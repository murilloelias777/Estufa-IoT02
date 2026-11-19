
from database.bancodedados import conectar
from sessao import Sessao

from werkzeug.security import generate_password_hash, check_password_hash
from mysql.connector import Error

from getpass import getpass


# ==========================================
# IDENTIFICAR TABELA DE USUARIOS
# ==========================================

def verificar_tabela_usuario(conexao):

    cursor = conexao.cursor()

    cursor.execute("""
        SELECT TABLE_NAME
        FROM information_schema.tables
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME IN ('usuario', 'usuarios')
        ORDER BY FIELD(TABLE_NAME, 'usuario', 'usuarios')
        LIMIT 1
    """)

    resultado = cursor.fetchone()
    cursor.close()

    return resultado[0] if resultado else None


# ==========================================
# CADASTRO DE USUARIO
# ==========================================

def cadastrar_usuario():

    print("\n========== CADASTRO DE USUARIO ==========")

    nome = input("Nome: ").strip()
    email = input("E-mail: ").strip().lower()
    senha = getpass("Senha: ")
    confirmar = getpass("Confirmar senha: ")

    if not nome or not email or not senha:
        print("\nPreencha todos os campos!")
        return

    if len(nome) > 50 or len(email) > 100:
        print("\nNome ou e-mail ultrapassa o limite permitido.")
        return

    if senha != confirmar:
        print("\nAs senhas nao conferem!")
        return

    if len(senha) < 8:
        print("\nA senha precisa ter pelo menos 8 caracteres.")
        return

    conexao = conectar()

    if conexao is None:
        return

    cursor = None

    try:

        tabela = verificar_tabela_usuario(conexao)

        if not tabela:
            print("Tabela de usuarios nao encontrada.")
            return

        cursor = conexao.cursor()

        cursor.execute(
            f"SELECT idusuario FROM `{tabela}` WHERE email = %s",
            (email,)
        )

        if cursor.fetchone():
            print("\nE-mail ja cadastrado!")
            return

        senha_hash = generate_password_hash(senha)

        cursor.execute(
            f"""
            INSERT INTO `{tabela}` (nome, email, senha)
            VALUES (%s, %s, %s)
            """,
            (nome, email, senha_hash)
        )

        conexao.commit()

        print("\nUsuario cadastrado com sucesso!")

    except Error as erro:

        conexao.rollback()
        print(f"Erro no cadastro: {erro}")

    finally:

        if cursor:
            cursor.close()

        conexao.close()


# ==========================================
# LOGIN
# ==========================================

def fazer_login():

    print("\n============== LOGIN ==============")

    email = input("E-mail: ").strip().lower()
    senha = getpass("Senha: ")

    conexao = conectar()

    if conexao is None:
        return

    cursor = None

    try:

        tabela = verificar_tabela_usuario(conexao)

        if not tabela:
            print("Tabela de usuarios nao encontrada.")
            return

        cursor = conexao.cursor(dictionary=True)

        cursor.execute(
            f"""
            SELECT idusuario, nome, email, senha
            FROM `{tabela}`
            WHERE email = %s
            """,
            (email,)
        )

        usuario = cursor.fetchone()

        if usuario is None:
            print("\nUsuario nao encontrado!")
            return

        if check_password_hash(usuario["senha"], senha):

            Sessao.iniciar(usuario)

            print("\n===================================")
            print("LOGIN REALIZADO COM SUCESSO!")
            print("===================================")
            print(f"Bem-vindo(a), {usuario['nome']}!")

        else:

            print("\nSenha incorreta!")

    except Error as erro:

        print(f"Erro no login: {erro}")

    finally:

        if cursor:
            cursor.close()

        conexao.close()


# ==========================================
# CADASTRO DE SENSOR
# ==========================================

def cadastrar_sensor():

    if not Sessao.autenticada():

        print("\nAcesso negado! Faca login primeiro.")
        return

    usuario = Sessao.usuario_atual()
    id_usuario = Sessao.obter_id_usuario()

    print("\n========== CADASTRO DE SENSOR ==========")
    print(f"Usuario responsavel: {usuario['nome']}")
    print("----------------------------------------")

    while True:

        print("\nDigite 0 no tipo para cancelar.")

        tipo = input("Tipo do sensor: ").strip()

        if tipo == "0":
            print("\nCadastro cancelado.")
            return

        descricao = input("Descricao: ").strip()
        unidade = input("Unidade de medida: ").strip()

        if not tipo or not descricao or not unidade:

            print("\nERRO: Todos os campos sao obrigatorios!")
            continue

        if len(tipo) > 30:
            print("\nO tipo deve ter no maximo 30 caracteres.")
            continue

        if len(descricao) > 255:
            print("\nA descricao deve ter no maximo 255 caracteres.")
            continue

        if len(unidade) > 5:
            print("\nA unidade deve ter no maximo 5 caracteres.")
            continue

        break

    conexao = conectar()

    if conexao is None:
        return

    cursor = None

    try:

        cursor = conexao.cursor()

        cursor.execute(
            """
            INSERT INTO sensor
            (
                tipo,
                descricao,
                unidade_medida,
                status,
                id_usuario_cadastro
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                tipo,
                descricao,
                unidade,
                1,
                id_usuario
            )
        )

        conexao.commit()

        id_sensor = cursor.lastrowid

        print("\n========================================")
        print("SENSOR CADASTRADO COM SUCESSO!")
        print("========================================")
        print(f"ID do sensor: {id_sensor}")
        print(f"Tipo: {tipo}")
        print(f"Descricao: {descricao}")
        print(f"Unidade: {unidade}")
        print("Status: ATIVO")
        print(f"Usuario responsavel: {usuario['nome']}")
        print(f"ID do usuario: {id_usuario}")
        print("========================================")

    except Error as erro:

        conexao.rollback()
        print(f"\nErro ao cadastrar sensor: {erro}")

    finally:

        if cursor:
            cursor.close()

        conexao.close()


# ==========================================
# CONSULTAR E SELECIONAR SENSORES
# ==========================================

def consultar_sensores():

    if not Sessao.autenticada():
        print("\nAcesso negado! Faca login primeiro.")
        return

    conexao = conectar()

    if conexao is None:
        return

    cursor = None

    try:

        cursor = conexao.cursor(dictionary=True)

        # Busca todos os sensores e seus responsaveis
        cursor.execute("""
            SELECT
                s.idsensor,
                s.tipo,
                s.descricao,
                s.unidade_medida,
                s.status,
                s.id_usuario_cadastro,
                u.nome AS usuario_responsavel

            FROM sensor s

            LEFT JOIN usuario u
                ON s.id_usuario_cadastro = u.idusuario

            ORDER BY s.idsensor ASC
        """)

        sensores = cursor.fetchall()

        print("\n========================================")
        print("          SENSORES CADASTRADOS")
        print("========================================")

        if not sensores:
            print("\nNenhum sensor cadastrado.")
            return

        # Lista os sensores disponiveis
        for sensor in sensores:

            status = sensor["status"]

            if status in (1, True, "1", "ativo", "ATIVO"):
                status_texto = "ATIVO"
            else:
                status_texto = "INATIVO"

            print(
                f"\nID: {sensor['idsensor']} | "
                f"Tipo: {sensor['tipo']} | "
                f"Status: {status_texto}"
            )

        print("\n----------------------------------------")
        print("0 - Voltar ao menu")
        print("----------------------------------------")

        while True:

            escolha = input(
                "\nDigite o ID do sensor que deseja consultar: "
            ).strip()

            if escolha == "0":
                print("\nVoltando ao menu...")
                return

            if not escolha.isdigit():
                print("\nDigite um ID valido!")
                continue

            id_sensor = int(escolha)

            sensor_selecionado = next(
                (
                    sensor for sensor in sensores
                    if sensor["idsensor"] == id_sensor
                ),
                None
            )

            if sensor_selecionado is None:
                print("\nSensor nao encontrado! Tente novamente.")
                continue

            status = sensor_selecionado["status"]

            if status in (1, True, "1", "ativo", "ATIVO"):
                status_texto = "ATIVO"
            else:
                status_texto = "INATIVO"

            print("\n")
            print("========================================")
            print("         INFORMACOES DO SENSOR")
            print("========================================")

            print(f"ID do sensor: {sensor_selecionado['idsensor']}")
            print(f"Tipo: {sensor_selecionado['tipo']}")
            print(f"Descricao: {sensor_selecionado['descricao']}")
            print(
                f"Unidade de medida: "
                f"{sensor_selecionado['unidade_medida']}"
            )
            print(f"Status: {status_texto}")

            print("----------------------------------------")

            print(
                f"ID do usuario: "
                f"{sensor_selecionado['id_usuario_cadastro']}"
            )

            print(
                f"Cadastrado por: "
                f"{sensor_selecionado['usuario_responsavel'] or 'Nao identificado'}"
            )

            print("========================================")

            opcao = input(
                "\nDeseja consultar outro sensor? (S/N): "
            ).strip().lower()

            if opcao != "s":
                break

    except Error as erro:

        print(f"\nErro ao consultar sensores: {erro}")

    finally:

        if cursor:
            cursor.close()

        conexao.close()


# ==========================================
# MENU DO USUARIO AUTENTICADO
# ==========================================

def menu_usuario():

    while Sessao.autenticada():

        usuario = Sessao.usuario_atual()

        print("\n")
        print("========================================")
        print("             ESTUFA IOT 02")
        print("========================================")
        print(f"Usuario conectado: {usuario['nome']}")
        print("----------------------------------------")
        print("1 - Cadastrar sensor")
        print("2 - Consultar sensores")
        print("3 - Encerrar sessao")
        print("0 - Sair do programa")
        print("========================================")

        opcao = input("Escolha uma opcao: ").strip()

        if opcao == "1":

            cadastrar_sensor()

        elif opcao == "2":

            consultar_sensores()

        elif opcao == "3":

            Sessao.encerrar()
            print("\nSessao encerrada com sucesso!")
            break

        elif opcao == "0":

            Sessao.encerrar()
            print("\nPrograma encerrado!")
            raise SystemExit

        else:

            print("\nOpcao invalida!")


# ==========================================
# MENU PRINCIPAL
# ==========================================

def menu_principal():

    while True:

        if Sessao.autenticada():

            menu_usuario()
            continue

        print("\n")
        print("========================================")
        print("             ESTUFA IOT 02")
        print("========================================")
        print("1 - Cadastrar usuario")
        print("2 - Fazer login")
        print("0 - Sair")
        print("========================================")

        opcao = input("Escolha uma opcao: ").strip()

        if opcao == "1":

            cadastrar_usuario()

        elif opcao == "2":

            fazer_login()

        elif opcao == "0":

            print("\nSistema encerrado!")
            break

        else:

            print("\nOpcao invalida!")


# ==========================================
# EXECUCAO DO SISTEMA
# ==========================================

if __name__ == "__main__":

    menu_principal()
