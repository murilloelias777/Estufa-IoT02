
from getpass import getpass
from decimal import Decimal, InvalidOperation

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from mysql.connector import Error

from database.bancodedados import conectar
from sessao import Sessao
from medicao import Medicao


# =========================================================
# FUNÇÕES AUXILIARES
# =========================================================

def pausar():
    input("\nPressione ENTER para continuar...")


def obter_conexao():
    conexao = conectar()

    if conexao is None:
        print("Não foi possível conectar ao banco de dados.")

    return conexao


def usuario_exige_login():
    if not Sessao.autenticada():
        print("Você precisa estar autenticado.")
        return False

    return True


def ler_decimal(mensagem):
    while True:
        entrada = input(mensagem).strip().replace(",", ".")

        try:
            valor = Decimal(entrada)

            if not valor.is_finite():
                print("Digite um número válido.")
                continue

            if valor < Decimal("-99999999.99") or valor > Decimal("99999999.99"):
                print("Valor fora do limite permitido.")
                continue

            return valor.quantize(Decimal("0.01"))

        except InvalidOperation:
            print("Valor inválido. Exemplo: 25.50")


# =========================================================
# CADASTRO DE USUÁRIO
# =========================================================

def cadastrar_usuario():
    print("\n========== CADASTRO DE USUÁRIO ==========")

    nome = input("Nome: ").strip()
    email = input("E-mail: ").strip().lower()

    if not nome or not email:
        print("Nome e e-mail são obrigatórios.")
        return

    if len(nome) > 50 or len(email) > 100:
        print("Nome ou e-mail ultrapassam o limite permitido.")
        return

    senha = getpass("Senha: ")
    confirmar = getpass("Confirme a senha: ")

    if not senha:
        print("A senha não pode ficar vazia.")
        return

    if senha != confirmar:
        print("As senhas não correspondem.")
        return

    senha_hash = generate_password_hash(senha)

    conexao = obter_conexao()
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

        cursor.execute(
            """
            INSERT INTO usuario (nome, email, senha)
            VALUES (%s, %s, %s)
            """,
            (nome, email, senha_hash)
        )

        conexao.commit()
        print("Usuário cadastrado com sucesso!")

    except Error as erro:
        conexao.rollback()
        print(f"Erro ao cadastrar usuário: {erro}")

    finally:
        cursor.close()
        conexao.close()


# =========================================================
# LOGIN
# =========================================================

def login():
    print("\n========== LOGIN ==========")

    email = input("E-mail: ").strip().lower()
    senha = getpass("Senha: ")

    conexao = obter_conexao()
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

        if usuario is None:
            print("Usuário não encontrado.")
            return

        if not check_password_hash(usuario["senha"], senha):
            print("Senha incorreta.")
            return

        Sessao.iniciar(usuario)

        print(f"\nBem-vindo(a), {usuario['nome']}!")
        print("Login realizado com sucesso.")

    except Error as erro:
        print(f"Erro ao realizar login: {erro}")

    finally:
        cursor.close()
        conexao.close()


# =========================================================
# PERFIL DO USUÁRIO
# =========================================================

def meu_perfil():
    if not usuario_exige_login():
        return

    usuario = Sessao.usuario_atual()

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


def alterar_senha():
    if not usuario_exige_login():
        return

    usuario = Sessao.usuario_atual()

    senha_atual = getpass("Digite sua senha atual: ")

    if not check_password_hash(usuario["senha"], senha_atual):
        print("Senha atual incorreta.")
        return

    nova_senha = getpass("Digite a nova senha: ")
    confirmar = getpass("Confirme a nova senha: ")

    if not nova_senha:
        print("A senha não pode ficar vazia.")
        return

    if nova_senha != confirmar:
        print("As senhas não correspondem.")
        return

    senha_hash = generate_password_hash(nova_senha)

    conexao = obter_conexao()
    if conexao is None:
        return

    cursor = conexao.cursor()

    try:
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

        print("Senha alterada com sucesso!")

    except Error as erro:
        conexao.rollback()
        print(f"Erro ao alterar senha: {erro}")

    finally:
        cursor.close()
        conexao.close()


# =========================================================
# CADASTRAR SENSOR
# =========================================================

def cadastrar_sensor():
    if not usuario_exige_login():
        return

    print("\n========== CADASTRAR SENSOR ==========")

    tipo = input("Tipo: ").strip()
    descricao = input("Descrição: ").strip()
    unidade = input("Unidade de medida: ").strip()

    if not tipo or not descricao or not unidade:
        print("Todos os campos são obrigatórios.")
        return

    if len(tipo) > 30 or len(descricao) > 255 or len(unidade) > 5:
        print("Um ou mais campos ultrapassam o limite permitido.")
        return

    print("\n1 - Ativo")
    print("0 - Inativo")

    status = input("Status: ").strip()

    if status not in ("0", "1"):
        print("Status inválido.")
        return

    conexao = obter_conexao()
    if conexao is None:
        return

    cursor = conexao.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO sensor
                (tipo, descricao, unidade_medida, status, id_usuario_cadastro)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                tipo,
                descricao,
                unidade,
                int(status),
                Sessao.obter_id_usuario()
            )
        )

        conexao.commit()

        print("Sensor cadastrado com sucesso!")
        print(f"ID do sensor: {cursor.lastrowid}")

    except Error as erro:
        conexao.rollback()
        print(f"Erro ao cadastrar sensor: {erro}")

    finally:
        cursor.close()
        conexao.close()


# =========================================================
# CONSULTAR SENSORES
# =========================================================

def consultar_sensores():
    if not usuario_exige_login():
        return

    conexao = obter_conexao()
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
                s.id_usuario_cadastro,
                u.nome AS nome_usuario
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
            status = "ATIVO" if sensor["status"] else "INATIVO"

            print("------------------------------------------")
            print(f"ID: {sensor['idsensor']}")
            print(f"Tipo: {sensor['tipo']}")
            print(f"Descrição: {sensor['descricao']}")
            print(f"Unidade: {sensor['unidade_medida']}")
            print(f"Status: {status}")
            print(f"Cadastrado por: {sensor['nome_usuario']}")

        entrada = input(
            "\nDigite o ID do sensor para consultar "
            "(ou ENTER para voltar): "
        ).strip()

        if entrada:
            if not entrada.isdigit():
                print("ID inválido.")
                return

            consultar_sensor_individual(int(entrada))

    except Error as erro:
        print(f"Erro ao consultar sensores: {erro}")

    finally:
        cursor.close()
        conexao.close()


# =========================================================
# CONSULTAR SENSOR INDIVIDUAL
# =========================================================

def consultar_sensor_individual(id_sensor):
    if not usuario_exige_login():
        return

    conexao = obter_conexao()
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
                s.id_usuario_cadastro,
                u.nome AS nome_usuario
            FROM sensor s
            LEFT JOIN usuario u
                ON s.id_usuario_cadastro = u.idusuario
            WHERE s.idsensor = %s
            """,
            (id_sensor,)
        )

        sensor = cursor.fetchone()

        if sensor is None:
            print("Sensor não encontrado.")
            return

        print("\n========== INFORMAÇÕES DO SENSOR ==========")
        print(f"ID: {sensor['idsensor']}")
        print(f"Tipo: {sensor['tipo']}")
        print(f"Descrição: {sensor['descricao']}")
        print(f"Unidade: {sensor['unidade_medida']}")
        print(f"Status: {'ATIVO' if sensor['status'] else 'INATIVO'}")
        print(f"Usuário que cadastrou: {sensor['nome_usuario']}")

    except Error as erro:
        print(f"Erro ao consultar sensor: {erro}")
        return

    finally:
        cursor.close()
        conexao.close()

    menu_sensor(id_sensor)


# =========================================================
# MENU DO SENSOR
# =========================================================

def menu_sensor(id_sensor):
    while True:
        print("\n========== OPÇÕES DO SENSOR ==========")
        print("1 - Alterar informações")
        print("2 - Alterar status")
        print("3 - Excluir sensor")
        print("4 - Ver histórico de medições")
        print("0 - Voltar")

        opcao = input("Escolha: ").strip()

        if opcao == "1":
            alterar_sensor(id_sensor)

        elif opcao == "2":
            alterar_status_sensor(id_sensor)

        elif opcao == "3":
            excluir_sensor(id_sensor)
            return

        elif opcao == "4":
            historico_medicoes(id_sensor)

        elif opcao == "0":
            return

        else:
            print("Opção inválida.")


# =========================================================
# ALTERAR SENSOR
# =========================================================

def alterar_sensor(id_sensor):
    if not usuario_exige_login():
        return

    conexao = obter_conexao()
    if conexao is None:
        return

    cursor = conexao.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT * FROM sensor WHERE idsensor = %s",
            (id_sensor,)
        )

        sensor = cursor.fetchone()

        if sensor is None:
            print("Sensor não encontrado.")
            return

        print("\nDeixe vazio para manter o valor atual.")

        tipo = input(f"Tipo [{sensor['tipo']}]: ").strip()
        descricao = input(f"Descrição [{sensor['descricao']}]: ").strip()
        unidade = input(f"Unidade [{sensor['unidade_medida']}]: ").strip()

        tipo = tipo or sensor["tipo"]
        descricao = descricao or sensor["descricao"]
        unidade = unidade or sensor["unidade_medida"]

        if len(tipo) > 30 or len(descricao) > 255 or len(unidade) > 5:
            print("Um ou mais campos ultrapassam o limite permitido.")
            return

        cursor.execute(
            """
            UPDATE sensor
            SET tipo = %s,
                descricao = %s,
                unidade_medida = %s
            WHERE idsensor = %s
            """,
            (tipo, descricao, unidade, id_sensor)
        )

        conexao.commit()
        print("Sensor atualizado com sucesso!")

    except Error as erro:
        conexao.rollback()
        print(f"Erro ao alterar sensor: {erro}")

    finally:
        cursor.close()
        conexao.close()


# =========================================================
# ALTERAR STATUS
# =========================================================

def alterar_status_sensor(id_sensor):
    if not usuario_exige_login():
        return

    print("\n1 - Ativar sensor")
    print("0 - Desativar sensor")

    opcao = input("Escolha: ").strip()

    if opcao not in ("0", "1"):
        print("Opção inválida.")
        return

    conexao = obter_conexao()
    if conexao is None:
        return

    cursor = conexao.cursor()

    try:
        cursor.execute(
            """
            UPDATE sensor
            SET status = %s
            WHERE idsensor = %s
            """,
            (int(opcao), id_sensor)
        )

        conexao.commit()
        print("Status atualizado com sucesso!")

    except Error as erro:
        conexao.rollback()
        print(f"Erro ao alterar status: {erro}")

    finally:
        cursor.close()
        conexao.close()


# =========================================================
# EXCLUIR SENSOR
# =========================================================

def excluir_sensor(id_sensor):
    if not usuario_exige_login():
        return

    confirmacao = input(
        f"Confirma a exclusão do sensor {id_sensor}? (s/n): "
    ).strip().lower()

    if confirmacao != "s":
        print("Exclusão cancelada.")
        return

    conexao = obter_conexao()
    if conexao is None:
        return

    cursor = conexao.cursor()

    try:
        cursor.execute(
            "SELECT idsensor FROM sensor WHERE idsensor = %s",
            (id_sensor,)
        )

        if cursor.fetchone() is None:
            print("Sensor não encontrado.")
            return

        cursor.execute(
            "SELECT COUNT(*) FROM MEDICAO WHERE idsensor = %s",
            (id_sensor,)
        )

        if cursor.fetchone()[0] > 0:
            print("Não é possível excluir: o sensor possui medições.")
            return

        cursor.execute(
            "DELETE FROM sensor WHERE idsensor = %s",
            (id_sensor,)
        )

        conexao.commit()
        print("Sensor excluído com sucesso!")

    except Error as erro:
        conexao.rollback()
        print(f"Erro ao excluir sensor: {erro}")

    finally:
        cursor.close()
        conexao.close()


# =========================================================
# CONSULTAR SENSORES PARA MEDIÇÕES
# =========================================================

def consultar_sensores_disponiveis():
    conexao = obter_conexao()

    if conexao is None:
        return []

    cursor = conexao.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT idsensor, tipo, descricao, unidade_medida, status
            FROM sensor
            ORDER BY idsensor
            """
        )

        return cursor.fetchall()

    except Error as erro:
        print(f"Erro ao consultar sensores: {erro}")
        return []

    finally:
        cursor.close()
        conexao.close()


# =========================================================
# REGISTRAR MEDIÇÃO
# =========================================================

def registrar_medicao():
    if not Sessao.autenticada():
        print("\nFaça login para registrar medições.")
        return

    conexao = conectar()

    if not conexao:
        return

    cursor = conexao.cursor(dictionary=True)

    try:
        print("\n--- REGISTRAR MEDIÇÃO ---")

        id_sensor = input("Digite o ID do sensor: ")

        # Verifica se o sensor existe e se está ativo
        cursor.execute(
            """
            SELECT idsensor, tipo, descricao, unidade_medida, status
            FROM sensor
            WHERE idsensor = %s
            FOR UPDATE
            """,
            (id_sensor,)
        )

        sensor = cursor.fetchone()

        if not sensor:
            print("\nSensor não encontrado.")
            conexao.rollback()
            return

        # Impede o registro se o sensor estiver inativo
        if not sensor["status"]:
            print("\nNão é possível registrar medições!")
            print("Este sensor está INATIVO.")
            conexao.rollback()
            return

        print(f"\nSensor selecionado: {sensor['tipo']}")
        print(f"Descrição: {sensor['descricao']}")
        print(f"Unidade: {sensor['unidade_medida']}")

        valor = float(input("\nDigite o valor da medição: ").replace(",", "."))

        # Obtém o número da última medição daquele sensor
        cursor.execute(
            """
            SELECT COALESCE(MAX(numero_medicao), 0) AS ultima_medicao
            FROM MEDICAO
            WHERE idsensor = %s
            """,
            (id_sensor,)
        )

        resultado = cursor.fetchone()
        numero_medicao = resultado["ultima_medicao"] + 1

        # Registra a medição
        cursor.execute(
            """
            INSERT INTO MEDICAO
                (idsensor, numero_medicao, valor)
            VALUES (%s, %s, %s)
            """,
            (id_sensor, numero_medicao, valor)
        )

        id_medicao = cursor.lastrowid

        conexao.commit()

        print("\nMedição registrada com sucesso!")
        print(f"Identificação: {id_sensor}-{numero_medicao}")
        print(f"ID interno: {id_medicao}")
        print(f"Valor: {valor} {sensor['unidade_medida']}")

    except ValueError:
        conexao.rollback()
        print("\nValor inválido. Digite um número.")

    except Exception as erro:
        conexao.rollback()
        print(f"\nErro ao registrar medição: {erro}")

    finally:
        cursor.close()
        conexao.close()

# =========================================================
# HISTÓRICO DE MEDIÇÕES
# =========================================================

def historico_medicoes(id_sensor):
    if not usuario_exige_login():
        return

    conexao = obter_conexao()
    if conexao is None:
        return

    cursor = conexao.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                m.idmedicao,
                m.idsensor,
                m.numero_medicao,
                m.data_hora,
                m.valor,
                s.tipo,
                s.unidade_medida
            FROM MEDICAO m
            INNER JOIN sensor s
                ON m.idsensor = s.idsensor
            WHERE m.idsensor = %s
            ORDER BY m.numero_medicao DESC
            """,
            (id_sensor,)
        )

        medicoes = cursor.fetchall()

        print("\n========== HISTÓRICO DE MEDIÇÕES ==========")

        if not medicoes:
            print("Este sensor ainda não possui medições.")
            return

        for dados in medicoes:
            medicao = Medicao(
                id_sensor=dados["idsensor"],
                valor=dados["valor"],
                id_medicao=dados["idmedicao"],
                numero_medicao=dados["numero_medicao"],
                data_hora=dados["data_hora"]
            )

            print("------------------------------------------")
            print(f"ID da medição: {medicao.identificador()}")
            print(f"ID interno: {medicao.id_medicao}")
            print(f"Tipo: {dados['tipo']}")
            print(f"Data e hora: {medicao.data_hora}")
            print(f"Valor: {medicao.valor} {dados['unidade_medida']}")

    except Error as erro:
        print(f"Erro ao consultar histórico: {erro}")

    finally:
        cursor.close()
        conexao.close()


# =========================================================
# MENU DE MEDIÇÕES
# =========================================================

def menu_medicoes():
    if not usuario_exige_login():
        return

    while True:
        print("\n========== MENU DE MEDIÇÕES ==========")
        print("1 - Registrar medição")
        print("0 - Voltar")

        opcao = input("Escolha: ").strip()

        if opcao == "1":
            registrar_medicao()
            pausar()

        elif opcao == "0":
            break

        else:
            print("Opção inválida.")


# =========================================================
# MENU DO USUÁRIO
# =========================================================

def menu_usuario():
    while Sessao.autenticada():

        print("\n==========================================")
        print("          SISTEMA ESTUFA IoT02")
        print("==========================================")
        print(f"Usuário: {Sessao.usuario_atual()['nome']}")
        print("------------------------------------------")
        print("1 - Cadastrar sensores")
        print("2 - Consultar sensores")
        print("3 - Medições")
        print("4 - Meu perfil")
        print("5 - Encerrar sessão")
        print("0 - Sair do programa")

        opcao = input("Escolha: ").strip()

        if opcao == "1":
            cadastrar_sensor()
            pausar()

        elif opcao == "2":
            consultar_sensores()
            pausar()

        elif opcao == "3":
            menu_medicoes()

        elif opcao == "4":
            meu_perfil()
            pausar()

        elif opcao == "5":
            Sessao.encerrar()
            print("Sessão encerrada!")
            return

        elif opcao == "0":
            Sessao.encerrar()
            print("Programa encerrado.")
            raise SystemExit

        else:
            print("Opção inválida.")


# =========================================================
# MENU INICIAL
# =========================================================

def menu_inicial():
    while True:

        print("\n==========================================")
        print("          SISTEMA ESTUFA IoT02")
        print("==========================================")
        print("1 - Fazer login")
        print("2 - Cadastrar usuário")
        print("0 - Sair do programa")

        opcao = input("Escolha: ").strip()

        if opcao == "1":
            login()

            if Sessao.autenticada():
                menu_usuario()

        elif opcao == "2":
            cadastrar_usuario()

        elif opcao == "0":
            print("Programa encerrado.")
            break

        else:
            print("Opção inválida.")


# =========================================================
# EXECUÇÃO
# =========================================================

if __name__ == "__main__":
    try:
        menu_inicial()

    except KeyboardInterrupt:
        Sessao.encerrar()
        print("\nPrograma interrompido pelo usuário.")
