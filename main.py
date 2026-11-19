
from database.bancodedados import conectar
from sessao import Sessao

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from mysql.connector import Error
from decimal import Decimal, InvalidOperation
from getpass import getpass


# =====================================================
# FUNÇÕES AUXILIARES
# =====================================================

def obter_tabela_usuario(conexao):
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


def obter_tabela_medicao(conexao):
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT TABLE_NAME
        FROM information_schema.tables
        WHERE TABLE_SCHEMA = DATABASE()
          AND LOWER(TABLE_NAME) = 'medicao'
        LIMIT 1
    """)

    resultado = cursor.fetchone()
    cursor.close()

    return resultado[0] if resultado else None


def obter_status(valor):
    if valor in (1, True, "1", "ativo", "ATIVO"):
        return "ATIVO"

    return "INATIVO"


def listar_sensores(conexao, apenas_ativos=False):
    cursor = conexao.cursor(dictionary=True)

    sql = """
        SELECT
            idsensor,
            tipo,
            descricao,
            unidade_medida,
            status,
            id_usuario_cadastro
        FROM sensor
    """

    if apenas_ativos:
        sql += " WHERE status = 1"

    sql += " ORDER BY idsensor ASC"

    cursor.execute(sql)
    sensores = cursor.fetchall()
    cursor.close()

    return sensores


def buscar_sensor(conexao, id_sensor):
    cursor = conexao.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            idsensor,
            tipo,
            descricao,
            unidade_medida,
            status,
            id_usuario_cadastro
        FROM sensor
        WHERE idsensor = %s
    """, (id_sensor,))

    sensor = cursor.fetchone()
    cursor.close()

    return sensor


# =====================================================
# CADASTRO DE USUÁRIO
# =====================================================

def cadastrar_usuario():
    conexao = conectar()

    if conexao is None:
        return

    tabela = obter_tabela_usuario(conexao)

    if tabela is None:
        print("\nTabela de usuários não encontrada.")
        conexao.close()
        return

    print("\n========== CADASTRO DE USUÁRIO ==========")

    nome = input("Nome: ").strip()
    email = input("E-mail: ").strip().lower()
    senha = getpass("Senha: ")
    confirmar = getpass("Confirme a senha: ")

    if not nome or not email or not senha:
        print("\nPreencha todos os campos.")
        conexao.close()
        return

    if len(nome) > 50 or len(email) > 100:
        print("\nNome ou e-mail ultrapassa o limite permitido.")
        conexao.close()
        return

    if len(senha) < 8:
        print("\nA senha deve ter pelo menos 8 caracteres.")
        conexao.close()
        return

    if senha != confirmar:
        print("\nAs senhas não coincidem.")
        conexao.close()
        return

    cursor = conexao.cursor()

    try:
        cursor.execute(
            f"SELECT idusuario FROM `{tabela}` WHERE email = %s",
            (email,)
        )

        if cursor.fetchone():
            print("\nEste e-mail já está cadastrado.")
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

        print("\nUsuário cadastrado com sucesso!")

    except Error as erro:
        conexao.rollback()
        print(f"\nErro ao cadastrar usuário: {erro}")

    finally:
        cursor.close()
        conexao.close()


# =====================================================
# LOGIN
# =====================================================

def fazer_login():
    conexao = conectar()

    if conexao is None:
        return

    tabela = obter_tabela_usuario(conexao)

    if tabela is None:
        print("\nTabela de usuários não encontrada.")
        conexao.close()
        return

    print("\n========== LOGIN ==========")

    email = input("E-mail: ").strip().lower()
    senha = getpass("Senha: ")

    cursor = conexao.cursor(dictionary=True)

    try:
        cursor.execute(
            f"""
            SELECT idusuario, nome, email, senha
            FROM `{tabela}`
            WHERE email = %s
            """,
            (email,)
        )

        usuario = cursor.fetchone()

        if usuario and check_password_hash(usuario["senha"], senha):
            Sessao.iniciar(usuario)
            print(f"\nBem-vindo, {usuario['nome']}!")

        else:
            print("\nE-mail ou senha incorretos.")

    except Error as erro:
        print(f"\nErro ao realizar login: {erro}")

    finally:
        cursor.close()
        conexao.close()


# =====================================================
# CADASTRAR SENSOR
# =====================================================

def cadastrar_sensor():
    if not Sessao.autenticada():
        print("\nFaça login para cadastrar sensores.")
        return

    conexao = conectar()

    if conexao is None:
        return

    print("\n========== CADASTRAR SENSOR ==========")

    tipo = input("Tipo do sensor: ").strip()
    descricao = input("Descrição: ").strip()
    unidade = input("Unidade de medida: ").strip()

    if not tipo or not descricao or not unidade:
        print("\nPreencha todos os campos.")
        conexao.close()
        return

    if len(tipo) > 30 or len(descricao) > 255 or len(unidade) > 5:
        print("\nUm ou mais campos ultrapassam o limite permitido.")
        conexao.close()
        return

    id_usuario = Sessao.obter_id_usuario()
    cursor = conexao.cursor()

    try:
        cursor.execute("""
            INSERT INTO sensor
            (tipo, descricao, unidade_medida, status, id_usuario_cadastro)
            VALUES (%s, %s, %s, %s, %s)
        """, (tipo, descricao, unidade, 1, id_usuario))

        conexao.commit()

        print("\nSensor cadastrado com sucesso!")
        print(f"ID do sensor: {cursor.lastrowid}")

    except Error as erro:
        conexao.rollback()
        print(f"\nErro ao cadastrar sensor: {erro}")

    finally:
        cursor.close()
        conexao.close()


# =====================================================
# EXIBIR INFORMAÇÕES DO SENSOR
# =====================================================

def exibir_sensor(sensor):
    print("\n========== INFORMAÇÕES DO SENSOR ==========")
    print(f"ID: {sensor['idsensor']}")
    print(f"Tipo: {sensor['tipo']}")
    print(f"Descrição: {sensor['descricao']}")
    print(f"Unidade de medida: {sensor['unidade_medida']}")
    print(f"Status: {obter_status(sensor['status'])}")
    print(f"ID do usuário responsável: {sensor['id_usuario_cadastro']}")
    print("-------------------------------------------")


# =====================================================
# ALTERAR SENSOR
# =====================================================

def alterar_sensor(conexao, sensor):
    print("\n========== ALTERAR SENSOR ==========")
    print("Pressione ENTER para manter a informação atual.")

    novo_tipo = input(
        f"Tipo [{sensor['tipo']}]: "
    ).strip()

    nova_descricao = input(
        f"Descrição [{sensor['descricao']}]: "
    ).strip()

    nova_unidade = input(
        f"Unidade [{sensor['unidade_medida']}]: "
    ).strip()

    print("\nStatus atual:", obter_status(sensor["status"]))
    print("1 - ATIVO")
    print("0 - INATIVO")
    print("ENTER - Manter status")

    novo_status = input("Novo status: ").strip()

    tipo = novo_tipo if novo_tipo else sensor["tipo"]
    descricao = nova_descricao if nova_descricao else sensor["descricao"]
    unidade = nova_unidade if nova_unidade else sensor["unidade_medida"]

    if novo_status == "1":
        status = 1
    elif novo_status == "0":
        status = 0
    elif novo_status == "":
        status = sensor["status"]
    else:
        print("\nStatus inválido.")
        return

    if len(tipo) > 30 or len(descricao) > 255 or len(unidade) > 5:
        print("\nUm ou mais campos ultrapassam o limite permitido.")
        return

    cursor = conexao.cursor()

    try:
        cursor.execute("""
            UPDATE sensor
            SET tipo = %s,
                descricao = %s,
                unidade_medida = %s,
                status = %s
            WHERE idsensor = %s
        """, (
            tipo,
            descricao,
            unidade,
            status,
            sensor["idsensor"]
        ))

        conexao.commit()

        print("\nSensor atualizado com sucesso!")

    except Error as erro:
        conexao.rollback()
        print(f"\nErro ao alterar sensor: {erro}")

    finally:
        cursor.close()


# =====================================================
# EXCLUIR SENSOR
# =====================================================

def excluir_sensor(conexao, sensor):
    print("\n========== EXCLUIR SENSOR ==========")

    print(f"ID: {sensor['idsensor']}")
    print(f"Tipo: {sensor['tipo']}")
    print(f"Descrição: {sensor['descricao']}")

    confirmacao = input(
        "\nTem certeza que deseja excluir este sensor? (S/N): "
    ).strip().upper()

    if confirmacao != "S":
        print("\nExclusão cancelada.")
        return

    cursor = conexao.cursor()

    try:
        cursor.execute(
            "DELETE FROM sensor WHERE idsensor = %s",
            (sensor["idsensor"],)
        )

        conexao.commit()

        if cursor.rowcount > 0:
            print("\nSensor excluído com sucesso!")
        else:
            print("\nSensor não encontrado.")

    except Error as erro:
        conexao.rollback()
        print("\nNão foi possível excluir o sensor.")
        print("Verifique se existem medições vinculadas a ele.")
        print(f"Detalhes: {erro}")

    finally:
        cursor.close()


# =====================================================
# CONSULTAR SENSORES
# =====================================================

def consultar_sensores():
    if not Sessao.autenticada():
        print("\nFaça login para consultar sensores.")
        return

    conexao = conectar()

    if conexao is None:
        return

    try:
        while True:
            sensores = listar_sensores(conexao)

            if not sensores:
                print("\nNenhum sensor cadastrado.")
                break

            print("\n========== SENSORES CADASTRADOS ==========")

            for sensor in sensores:
                print(
                    f"ID: {sensor['idsensor']} | "
                    f"Tipo: {sensor['tipo']} | "
                    f"Status: {obter_status(sensor['status'])}"
                )

            print("-------------------------------------------")
            print("Digite o ID para visualizar o sensor.")
            print("0 - Voltar")

            try:
                id_sensor = int(input("\nID do sensor: "))
            except ValueError:
                print("\nDigite um ID válido.")
                continue

            if id_sensor == 0:
                break

            sensor = buscar_sensor(conexao, id_sensor)

            if sensor is None:
                print("\nSensor não encontrado.")
                continue

            while True:
                exibir_sensor(sensor)

                print("1 - Alterar informações")
                print("2 - Excluir sensor")
                print("0 - Voltar")
                print("-------------------------------------------")

                opcao = input("Escolha uma opção: ").strip()

                if opcao == "1":
                    alterar_sensor(conexao, sensor)
                    sensor = buscar_sensor(conexao, id_sensor)

                    if sensor is None:
                        break

                elif opcao == "2":
                    excluir_sensor(conexao, sensor)
                    break

                elif opcao == "0":
                    break

                else:
                    print("\nOpção inválida.")

    except Error as erro:
        print(f"\nErro ao consultar sensores: {erro}")

    finally:
        conexao.close()


# =====================================================
# ABA DE MEDIÇÕES
# =====================================================

def listar_sensores_medicao(conexao, apenas_ativos=False):
    return listar_sensores(conexao, apenas_ativos)


# =====================================================
# REGISTRAR NOVA MEDIÇÃO
# =====================================================

def registrar_medicao():
    if not Sessao.autenticada():
        print("\nFaça login para registrar medições.")
        return

    conexao = conectar()

    if conexao is None:
        return

    tabela = obter_tabela_medicao(conexao)

    if tabela is None:
        print("\nTabela MEDICAO não encontrada.")
        conexao.close()
        return

    try:
        sensores = listar_sensores_medicao(
            conexao,
            apenas_ativos=True
        )

        if not sensores:
            print("\nNão existem sensores ativos cadastrados.")
            return

        print("\n========== SENSORES DISPONÍVEIS ==========")

        for sensor in sensores:
            print(
                f"ID: {sensor['idsensor']} | "
                f"Tipo: {sensor['tipo']} | "
                f"Unidade: {sensor['unidade_medida']}"
            )

        try:
            id_sensor = int(input("\nSelecione o ID do sensor: "))
        except ValueError:
            print("\nID inválido.")
            return

        sensor_selecionado = None

        for sensor in sensores:
            if sensor["idsensor"] == id_sensor:
                sensor_selecionado = sensor
                break

        if sensor_selecionado is None:
            print("\nSensor não encontrado ou inativo.")
            return

        print("\n========== NOVA MEDIÇÃO ==========")
        print(f"Sensor: {sensor_selecionado['tipo']}")
        print(f"Descrição: {sensor_selecionado['descricao']}")
        print(f"Unidade: {sensor_selecionado['unidade_medida']}")

        valor_digitado = input(
            f"Valor medido ({sensor_selecionado['unidade_medida']}): "
        ).strip().replace(",", ".")

        try:
            valor = Decimal(valor_digitado)
        except InvalidOperation:
            print("\nDigite um valor numérico válido.")
            return

        if not valor.is_finite():
            print("\nValor inválido.")
            return

        if abs(valor) >= Decimal("1000000"):
            print("\nValor ultrapassa o limite de DECIMAL(8,2).")
            return

        if valor != valor.quantize(Decimal("0.01")):
            print("\nInforme no máximo duas casas decimais.")
            return

        cursor = conexao.cursor()

        cursor.execute(
            f"""
            INSERT INTO `{tabela}` (idsensor, data_hora, valor)
            VALUES (%s, NOW(), %s)
            """,
            (id_sensor, valor)
        )

        conexao.commit()

        print("\nMedição registrada com sucesso!")
        print(f"ID da medição: {cursor.lastrowid}")
        print(f"Sensor: {sensor_selecionado['tipo']}")
        print(
            f"Valor: {valor} "
            f"{sensor_selecionado['unidade_medida']}"
        )

        cursor.close()

    except Error as erro:
        conexao.rollback()
        print(f"\nErro ao registrar medição: {erro}")

    finally:
        conexao.close()


# =====================================================
# CONSULTAR HISTÓRICO DE MEDIÇÕES
# =====================================================

def consultar_historico():
    if not Sessao.autenticada():
        print("\nFaça login para consultar medições.")
        return

    conexao = conectar()

    if conexao is None:
        return

    tabela = obter_tabela_medicao(conexao)

    if tabela is None:
        print("\nTabela MEDICAO não encontrada.")
        conexao.close()
        return

    try:
        sensores = listar_sensores_medicao(conexao)

        if not sensores:
            print("\nNenhum sensor cadastrado.")
            return

        print("\n========== SENSORES CADASTRADOS ==========")

        for sensor in sensores:
            print(
                f"ID: {sensor['idsensor']} | "
                f"Tipo: {sensor['tipo']} | "
                f"Status: {obter_status(sensor['status'])}"
            )

        try:
            id_sensor = int(input("\nDigite o ID do sensor: "))
        except ValueError:
            print("\nID inválido.")
            return

        sensor_selecionado = None

        for sensor in sensores:
            if sensor["idsensor"] == id_sensor:
                sensor_selecionado = sensor
                break

        if sensor_selecionado is None:
            print("\nSensor não encontrado.")
            return

        cursor = conexao.cursor(dictionary=True)

        cursor.execute(
            f"""
            SELECT
                idmedicao,
                idsensor,
                data_hora,
                valor
            FROM `{tabela}`
            WHERE idsensor = %s
            ORDER BY data_hora DESC, idmedicao DESC
            LIMIT 100
            """,
            (id_sensor,)
        )

        medicoes = cursor.fetchall()
        cursor.close()

        print("\n==========================================")
        print("          HISTÓRICO DE MEDIÇÕES")
        print("==========================================")
        print(f"Sensor: {sensor_selecionado['tipo']}")
        print(f"Descrição: {sensor_selecionado['descricao']}")
        print(f"Unidade: {sensor_selecionado['unidade_medida']}")
        print("------------------------------------------")

        if not medicoes:
            print("\nNenhuma medição registrada para este sensor.")
            return

        for medicao in medicoes:
            data_hora = medicao["data_hora"]

            if hasattr(data_hora, "strftime"):
                data_hora = data_hora.strftime("%d/%m/%Y %H:%M:%S")

            print(f"\nID da medição: {medicao['idmedicao']}")
            print(f"Data e hora: {data_hora}")
            print(
                f"Valor: {medicao['valor']} "
                f"{sensor_selecionado['unidade_medida']}"
            )
            print("------------------------------------------")

        print("\nExibindo as últimas 100 medições.")

    except Error as erro:
        print(f"\nErro ao consultar histórico: {erro}")

    finally:
        conexao.close()


# =====================================================
# MENU DE MEDIÇÕES
# =====================================================

def menu_medicoes():
    while True:
        print("\n======================================")
        print("              MEDIÇÕES")
        print("======================================")
        print("1 - Registrar nova medição")
        print("2 - Consultar histórico")
        print("0 - Voltar")
        print("--------------------------------------")

        opcao = input("Escolha uma opção: ").strip()

        if opcao == "1":
            registrar_medicao()

        elif opcao == "2":
            consultar_historico()

        elif opcao == "0":
            break

        else:
            print("\nOpção inválida.")


# =====================================================
# MEU PERFIL
# =====================================================

def meu_perfil():
    if not Sessao.autenticada():
        print("\nFaça login para acessar seu perfil.")
        return

    conexao = conectar()

    if conexao is None:
        return

    tabela = obter_tabela_usuario(conexao)

    if tabela is None:
        print("\nTabela de usuários não encontrada.")
        conexao.close()
        return

    usuario = Sessao.usuario_atual()

    try:
        while True:
            cursor = conexao.cursor(dictionary=True)

            cursor.execute(
                f"""
                SELECT idusuario, nome, email, senha
                FROM `{tabela}`
                WHERE idusuario = %s
                """,
                (usuario["idusuario"],)
            )

            dados = cursor.fetchone()
            cursor.close()

            if dados is None:
                print("\nUsuário não encontrado.")
                break

            print("\n======================================")
            print("              MEU PERFIL")
            print("======================================")
            print(f"Nome: {dados['nome']}")
            print(f"E-mail de login: {dados['email']}")
            print("Senha: ******** (protegida)")
            print("--------------------------------------")
            print("1 - Alterar senha")
            print("0 - Voltar")
            print("--------------------------------------")

            opcao = input("Escolha uma opção: ").strip()

            if opcao == "1":
                trocar_senha(conexao, tabela, dados)

            elif opcao == "0":
                break

            else:
                print("\nOpção inválida.")

    except Error as erro:
        print(f"\nErro ao consultar perfil: {erro}")

    finally:
        conexao.close()


# =====================================================
# TROCAR SENHA
# =====================================================

def trocar_senha(conexao, tabela, usuario):
    print("\n========== ALTERAR SENHA ==========")

    senha_atual = getpass("Digite sua senha atual: ")
    nova_senha = getpass("Digite sua nova senha: ")
    confirmar_senha = getpass("Confirme sua nova senha: ")

    if not check_password_hash(usuario["senha"], senha_atual):
        print("\nSenha atual incorreta.")
        return

    if len(nova_senha) < 8:
        print("\nA nova senha deve ter pelo menos 8 caracteres.")
        return

    if nova_senha != confirmar_senha:
        print("\nAs novas senhas não coincidem.")
        return

    senha_hash = generate_password_hash(nova_senha)

    cursor = conexao.cursor()

    try:
        cursor.execute(
            f"""
            UPDATE `{tabela}`
            SET senha = %s
            WHERE idusuario = %s
            """,
            (senha_hash, usuario["idusuario"])
        )

        conexao.commit()

        usuario["senha"] = senha_hash

        print("\nSenha alterada com sucesso!")

    except Error as erro:
        conexao.rollback()
        print(f"\nErro ao alterar senha: {erro}")

    finally:
        cursor.close()


# =====================================================
# MENU DO USUÁRIO
# =====================================================

def menu_usuario():
    while Sessao.autenticada():

        usuario = Sessao.usuario_atual()

        print("\n======================================")
        print("          SISTEMA DE ESTUFA IOT")
        print("======================================")
        print(f"Usuário: {usuario['nome']}")
        print("--------------------------------------")
        print("1 - Cadastrar sensor")
        print("2 - Consultar sensores")
        print("3 - Medições")
        print("4 - Meu perfil")
        print("5 - Encerrar sessão")
        print("0 - Sair do programa")
        print("--------------------------------------")

        opcao = input("Escolha uma opção: ").strip()

        if opcao == "1":
            cadastrar_sensor()

        elif opcao == "2":
            consultar_sensores()

        elif opcao == "3":
            menu_medicoes()

        elif opcao == "4":
            meu_perfil()

        elif opcao == "5":
            Sessao.encerrar()
            print("\nSessão encerrada.")

        elif opcao == "0":
            print("\nSistema encerrado.")
            raise SystemExit

        else:
            print("\nOpção inválida.")


# =====================================================
# MENU PRINCIPAL
# =====================================================

def menu_principal():
    while True:
        print("\n======================================")
        print("          SISTEMA DE ESTUFA IOT")
        print("======================================")
        print("1 - Cadastrar usuário")
        print("2 - Fazer login")
        print("0 - Sair")
        print("--------------------------------------")

        opcao = input("Escolha uma opção: ").strip()

        if opcao == "1":
            cadastrar_usuario()

        elif opcao == "2":
            fazer_login()

            if Sessao.autenticada():
                menu_usuario()

        elif opcao == "0":
            print("\nSistema encerrado.")
            break

        else:
            print("\nOpção inválida.")


# =====================================================
# EXECUÇÃO DO SISTEMA
# =====================================================

if __name__ == "__main__":
    menu_principal()
