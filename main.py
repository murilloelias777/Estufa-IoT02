
from database.bancodedados import conectar
from sessao import Sessao

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from mysql.connector import Error
from getpass import getpass


# ==================================================
# FUNÇÕES AUXILIARES
# ==================================================

def pausar():
    input("\nPressione ENTER para continuar...")


def validar_email(email):
    return "@" in email and "." in email.split("@")[-1]


# ==================================================
# CADASTRO DE USUÁRIO
# ==================================================

def cadastrar_usuario():
    print("\n========== CADASTRO DE USUÁRIO ==========")

    nome = input("Nome: ").strip()
    email = input("E-mail: ").strip()
    senha = getpass("Senha: ")

    if not nome or not email or not senha:
        print("Todos os campos são obrigatórios.")
        return

    if not validar_email(email):
        print("E-mail inválido.")
        return

    conexao = conectar()

    if conexao is None:
        return

    cursor = conexao.cursor()

    try:
        cursor.execute(
            "SELECT idusuario FROM usuario WHERE email = %s",
            (email,)
        )

        if cursor.fetchone():
            print("Este e-mail já está cadastrado.")
            return

        senha_hash = generate_password_hash(senha)

        cursor.execute(
            """
            INSERT INTO usuario (nome, email, senha)
            VALUES (%s, %s, %s)
            """,
            (nome, email, senha_hash)
        )

        conexao.commit()

        print("\nUsuário cadastrado com sucesso!")

    except Error as erro:
        conexao.rollback()
        print(f"Erro ao cadastrar usuário: {erro}")

    finally:
        cursor.close()
        conexao.close()


# ==================================================
# LOGIN
# ==================================================

def login():
    print("\n========== LOGIN ==========")

    email = input("E-mail: ").strip()
    senha = getpass("Senha: ")

    conexao = conectar()

    if conexao is None:
        return

    cursor = conexao.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT idusuario, nome, email, senha
            FROM usuario
            WHERE email = %s
            """,
            (email,)
        )

        usuario = cursor.fetchone()

        if usuario and check_password_hash(usuario["senha"], senha):
            Sessao.iniciar(usuario)
            print(f"\nBem-vindo(a), {usuario['nome']}!")

        else:
            print("\nE-mail ou senha incorretos.")

    except Error as erro:
        print(f"Erro ao realizar login: {erro}")

    finally:
        cursor.close()
        conexao.close()


# ==================================================
# CADASTRAR SENSOR
# ==================================================

def cadastrar_sensor():
    if not Sessao.autenticada():
        print("Faça login para cadastrar sensores.")
        return

    print("\n========== CADASTRAR SENSOR ==========")

    tipo = input("Tipo do sensor: ").strip()
    descricao = input("Descrição: ").strip()
    unidade = input("Unidade de medida: ").strip()

    if not tipo or not descricao or not unidade:
        print("Todos os campos são obrigatórios.")
        return

    conexao = conectar()

    if conexao is None:
        return

    cursor = conexao.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO sensor
            (tipo, descricao, unidade_medida, status,
             id_usuario_cadastro)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                tipo,
                descricao,
                unidade,
                1,
                Sessao.obter_id_usuario()
            )
        )

        conexao.commit()

        print("\nSensor cadastrado com sucesso!")

    except Error as erro:
        conexao.rollback()
        print(f"Erro ao cadastrar sensor: {erro}")

    finally:
        cursor.close()
        conexao.close()


# ==================================================
# LISTAR SENSORES
# ==================================================

def listar_sensores():
    conexao = conectar()

    if conexao is None:
        return

    cursor = conexao.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                s.idsensor,
                s.tipo,
                s.descricao,
                s.unidade_medida,
                s.status,
                u.nome AS usuario_cadastro
            FROM sensor s
            LEFT JOIN usuario u
                ON s.id_usuario_cadastro = u.idusuario
            ORDER BY s.idsensor
            """
        )

        sensores = cursor.fetchall()

        print("\n========== SENSORES CADASTRADOS ==========")

        if not sensores:
            print("Nenhum sensor cadastrado.")
            return

        for sensor in sensores:
            status = "Ativo" if sensor["status"] else "Inativo"

            print("--------------------------------------")
            print(f"ID: {sensor['idsensor']}")
            print(f"Tipo: {sensor['tipo']}")
            print(f"Descrição: {sensor['descricao']}")
            print(f"Unidade: {sensor['unidade_medida']}")
            print(f"Status: {status}")
            print(
                f"Cadastrado por: "
                f"{sensor['usuario_cadastro'] or 'Não identificado'}"
            )

    except Error as erro:
        print(f"Erro ao consultar sensores: {erro}")

    finally:
        cursor.close()
        conexao.close()


# ==================================================
# CONSULTAR SENSOR INDIVIDUAL
# ==================================================

def consultar_sensor():
    listar_sensores()

    try:
        idsensor = int(input("\nDigite o ID do sensor: "))
    except ValueError:
        print("ID inválido.")
        return

    conexao = conectar()

    if conexao is None:
        return

    cursor = conexao.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                s.*,
                u.nome AS usuario_cadastro
            FROM sensor s
            LEFT JOIN usuario u
                ON s.id_usuario_cadastro = u.idusuario
            WHERE s.idsensor = %s
            """,
            (idsensor,)
        )

        sensor = cursor.fetchone()

        if not sensor:
            print("Sensor não encontrado.")
            return

        print("\n========== INFORMAÇÕES DO SENSOR ==========")
        print(f"ID: {sensor['idsensor']}")
        print(f"Tipo: {sensor['tipo']}")
        print(f"Descrição: {sensor['descricao']}")
        print(f"Unidade: {sensor['unidade_medida']}")
        print(
            f"Status: {'Ativo' if sensor['status'] else 'Inativo'}"
        )
        print(
            f"Cadastrado por: "
            f"{sensor['usuario_cadastro'] or 'Não identificado'}"
        )

    except Error as erro:
        print(f"Erro ao consultar sensor: {erro}")

    finally:
        cursor.close()
        conexao.close()

    while True:
        print("\n========== OPÇÕES DO SENSOR ==========")
        print("1 - Alterar informações")
        print("2 - Alterar status")
        print("3 - Excluir sensor")
        print("0 - Voltar")

        opcao = input("Escolha: ").strip()

        if opcao == "1":
            alterar_sensor(idsensor)
            break

        elif opcao == "2":
            alterar_status_sensor(idsensor)
            break

        elif opcao == "3":
            excluir_sensor(idsensor)
            break

        elif opcao == "0":
            break

        else:
            print("Opção inválida.")


# ==================================================
# ALTERAR SENSOR
# ==================================================

def alterar_sensor(idsensor):
    conexao = conectar()

    if conexao is None:
        return

    cursor = conexao.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT * FROM sensor WHERE idsensor = %s",
            (idsensor,)
        )

        sensor = cursor.fetchone()

        if not sensor:
            print("Sensor não encontrado.")
            return

        print("\nDeixe em branco para manter o valor atual.")

        tipo = input(f"Tipo ({sensor['tipo']}): ").strip()
        descricao = input(
            f"Descrição ({sensor['descricao']}): "
        ).strip()
        unidade = input(
            f"Unidade ({sensor['unidade_medida']}): "
        ).strip()

        cursor.execute(
            """
            UPDATE sensor
            SET tipo = %s,
                descricao = %s,
                unidade_medida = %s
            WHERE idsensor = %s
            """,
            (
                tipo if tipo else sensor["tipo"],
                descricao if descricao else sensor["descricao"],
                unidade if unidade else sensor["unidade_medida"],
                idsensor
            )
        )

        conexao.commit()

        print("Sensor atualizado com sucesso!")

    except Error as erro:
        conexao.rollback()
        print(f"Erro ao alterar sensor: {erro}")

    finally:
        cursor.close()
        conexao.close()


# ==================================================
# ALTERAR STATUS
# ==================================================

def alterar_status_sensor(idsensor):
    conexao = conectar()

    if conexao is None:
        return

    cursor = conexao.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT status FROM sensor WHERE idsensor = %s",
            (idsensor,)
        )

        sensor = cursor.fetchone()

        if not sensor:
            print("Sensor não encontrado.")
            return

        novo_status = 0 if bool(sensor["status"]) else 1

        cursor.execute(
            """
            UPDATE sensor
            SET status = %s
            WHERE idsensor = %s
            """,
            (novo_status, idsensor)
        )

        conexao.commit()

        print(
            "Status atualizado para "
            + ("Ativo." if novo_status else "Inativo.")
        )

    except Error as erro:
        conexao.rollback()
        print(f"Erro ao alterar status: {erro}")

    finally:
        cursor.close()
        conexao.close()


# ==================================================
# EXCLUIR SENSOR
# ==================================================

def excluir_sensor(idsensor):
    conexao = conectar()

    if conexao is None:
        return

    cursor = conexao.cursor()

    try:
        # Verifica se existem medições vinculadas.
        cursor.execute(
            """
            SELECT idmedicao
            FROM MEDICAO
            WHERE idsensor = %s
            LIMIT 1
            """,
            (idsensor,)
        )

        if cursor.fetchone():
            print(
                "Este sensor possui medições cadastradas. "
                "Não é possível excluí-lo sem tratar o histórico."
            )
            return

        confirmacao = input(
            "Deseja realmente excluir este sensor? (s/n): "
        ).strip().lower()

        if confirmacao != "s":
            print("Exclusão cancelada.")
            return

        cursor.execute(
            "DELETE FROM sensor WHERE idsensor = %s",
            (idsensor,)
        )

        conexao.commit()

        if cursor.rowcount > 0:
            print("Sensor excluído com sucesso!")
        else:
            print("Sensor não encontrado.")

    except Error as erro:
        conexao.rollback()
        print(f"Erro ao excluir sensor: {erro}")

    finally:
        cursor.close()
        conexao.close()


# ==================================================
# MENU DE SENSORES
# ==================================================

def menu_sensores():
    while True:
        print("\n========== SENSORES ==========")
        print("1 - Listar sensores")
        print("2 - Consultar sensor individual")
        print("0 - Voltar")

        opcao = input("Escolha: ").strip()

        if opcao == "1":
            listar_sensores()
            pausar()

        elif opcao == "2":
            consultar_sensor()
            pausar()

        elif opcao == "0":
            break

        else:
            print("Opção inválida.")


# ==================================================
# MEU PERFIL
# ==================================================

def meu_perfil():
    usuario = Sessao.usuario_atual()

    if not usuario:
        print("Nenhum usuário autenticado.")
        return

    print("\n========== MEU PERFIL ==========")
    print(f"ID: {usuario['idusuario']}")
    print(f"Nome: {usuario['nome']}")
    print(f"E-mail: {usuario['email']}")
    print("Senha: ********")

    print("\n1 - Alterar senha")
    print("0 - Voltar")

    opcao = input("Escolha: ").strip()

    if opcao == "1":
        alterar_senha()


# ==================================================
# ALTERAR SENHA
# ==================================================

def alterar_senha():
    usuario = Sessao.usuario_atual()

    if not usuario:
        print("Faça login para continuar.")
        return

    senha_atual = getpass("Senha atual: ")
    nova_senha = getpass("Nova senha: ")
    confirmar = getpass("Confirme a nova senha: ")

    if not nova_senha:
        print("A senha não pode ficar vazia.")
        return

    if nova_senha != confirmar:
        print("As senhas não coincidem.")
        return

    conexao = conectar()

    if conexao is None:
        return

    cursor = conexao.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT senha
            FROM usuario
            WHERE idusuario = %s
            """,
            (usuario["idusuario"],)
        )

        resultado = cursor.fetchone()

        if not resultado or not check_password_hash(
            resultado["senha"], senha_atual
        ):
            print("Senha atual incorreta.")
            return

        senha_hash = generate_password_hash(nova_senha)

        cursor.execute(
            """
            UPDATE usuario
            SET senha = %s
            WHERE idusuario = %s
            """,
            (senha_hash, usuario["idusuario"])
        )

        conexao.commit()

        usuario["senha"] = senha_hash
        Sessao.iniciar(usuario)

        print("Senha alterada com sucesso!")

    except Error as erro:
        conexao.rollback()
        print(f"Erro ao alterar senha: {erro}")

    finally:
        cursor.close()
        conexao.close()


# ==================================================
# ENCERRAR SESSÃO
# ==================================================

def encerrar_sessao():
    Sessao.encerrar()
    print("\nSessão encerrada com sucesso!")


# ==================================================
# MENU DO USUÁRIO
# ==================================================

def menu_usuario():
    while Sessao.autenticada():

        usuario = Sessao.usuario_atual()

        if not usuario:
            break

        print("\n========================================")
        print("              ESTUFA IOT 02")
        print("========================================")
        print(f"Usuário: {usuario['nome']}")
        print("========================================")
        print("1 - Cadastrar sensores")
        print("2 - Consultar sensores")
        print("3 - Meu perfil")
        print("4 - Encerrar sessão")
        print("0 - Sair do programa")
        print("========================================")

        opcao = input("Escolha: ").strip()

        if opcao == "1":
            cadastrar_sensor()
            pausar()

        elif opcao == "2":
            menu_sensores()

        elif opcao == "3":
            meu_perfil()
            pausar()

        elif opcao == "4":
            encerrar_sessao()
            break

        elif opcao == "0":
            raise SystemExit

        else:
            print("Opção inválida.")


# ==================================================
# MENU PRINCIPAL
# ==================================================

def menu_principal():
    while True:
        print("\n========================================")
        print("              ESTUFA IOT 02")
        print("========================================")
        print("1 - Fazer login")
        print("2 - Cadastrar usuário")
        print("0 - Sair")
        print("========================================")

        opcao = input("Escolha: ").strip()

        if opcao == "1":
            login()

            if Sessao.autenticada():
                menu_usuario()

        elif opcao == "2":
            cadastrar_usuario()
            pausar()

        elif opcao == "0":
            print("\nEncerrando o sistema...")
            break

        else:
            print("Opção inválida.")


# ==================================================
# EXECUÇÃO
# ==================================================

if __name__ == "__main__":
    try:
        menu_principal()

    except KeyboardInterrupt:
        print("\nSistema interrompido.")

    except SystemExit:
        print("\nEncerrando o programa...")

    except Exception as erro:
        print(f"\nErro inesperado: {erro}")

    finally:
        if Sessao.autenticada():
            Sessao.encerrar()

        print("Sistema finalizado.")
