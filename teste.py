
import re
import math
import unicodedata
from getpass import getpass

from werkzeug.security import generate_password_hash, check_password_hash

from database.bancodedados import conectar
from sessao import Sessao


# ============================================================
# VALIDAÇÕES
# ============================================================

def contar_letras(texto):
    return sum(
        1 for caractere in texto
        if unicodedata.category(caractere).startswith("L")
    )


def validar_texto(mensagem, minimo_letras=3, permitir_vazio=False):
    while True:
        texto = input(mensagem).strip()

        if permitir_vazio and texto == "":
            return ""

        if not texto:
            print("Erro: este campo é obrigatório.")
            continue

        if contar_letras(texto) < minimo_letras:
            print(f"Erro: informe pelo menos {minimo_letras} letras.")
            continue

        return texto


def validar_unidade(mensagem, permitir_vazio=False):
    while True:
        unidade = input(mensagem).strip()

        if permitir_vazio and unidade == "":
            return ""

        if not unidade:
            print("Erro: informe a unidade de medida.")
            continue

        if not unidade.isalpha():
            print(
                "Erro: a unidade deve conter somente letras, "
                "sem números, espaços ou caracteres especiais."
            )
            continue

        if len(unidade) > 5:
            print("Erro: a unidade deve ter no máximo 5 letras.")
            continue

        return unidade


def validar_email(mensagem="E-mail: "):
    while True:
        email = input(mensagem).strip().lower()

        padrao = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"

        if not re.fullmatch(padrao, email):
            print("Erro: informe um e-mail válido.")
            continue

        return email


def validar_id(mensagem):
    while True:
        valor = input(mensagem).strip()

        if not valor.isdigit() or int(valor) <= 0:
            print("Erro: informe um ID numérico válido.")
            continue

        return int(valor)


def validar_valor_medicao(mensagem):
    while True:
        entrada = input(mensagem).strip().replace(",", ".")

        try:
            valor = float(entrada)

            if not math.isfinite(valor):
                print("Erro: informe um valor numérico válido.")
                continue

            return valor

        except ValueError:
            print("Erro: digite somente um valor numérico.")


def validar_senha(mensagem="Senha: "):
    while True:
        senha = getpass(mensagem)

        if len(senha) < 6:
            print("Erro: a senha deve ter pelo menos 6 caracteres.")
            continue

        return senha


# ============================================================
# CADASTRO DE USUÁRIO
# ============================================================

def cadastrar_usuario():
    conexao = conectar()

    if not conexao:
        return

    cursor = conexao.cursor(dictionary=True)

    try:
        print("\n========== CADASTRO DE USUÁRIO ==========")

        nome = validar_texto("Nome: ")
        email = validar_email()

        cursor.execute(
            "SELECT idusuario FROM usuario WHERE email = %s",
            (email,)
        )

        if cursor.fetchone():
            print("\nEste e-mail já está cadastrado.")
            return

        senha = validar_senha()
        confirmar_senha = getpass("Confirme a senha: ")

        if senha != confirmar_senha:
            print("\nAs senhas não correspondem.")
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

    except Exception as erro:
        conexao.rollback()
        print(f"\nErro ao cadastrar usuário: {erro}")

    finally:
        cursor.close()
        conexao.close()


# ============================================================
# LOGIN
# ============================================================

def login():
    conexao = conectar()

    if not conexao:
        return

    cursor = conexao.cursor(dictionary=True)

    try:
        print("\n========== LOGIN ==========")

        email = validar_email()
        senha = getpass("Senha: ")

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

    except Exception as erro:
        print(f"\nErro ao realizar login: {erro}")

    finally:
        cursor.close()
        conexao.close()


# ============================================================
# CADASTRO DE SENSOR
# ============================================================

def cadastrar_sensor():
    if not Sessao.autenticada():
        print("\nFaça login para cadastrar sensores.")
        return

    conexao = conectar()

    if not conexao:
        return

    cursor = conexao.cursor()

    try:
        print("\n========== CADASTRAR SENSOR ==========")

        tipo = validar_texto("Tipo do sensor: ")
        descricao = validar_texto("Descrição: ")
        unidade = validar_unidade("Unidade de medida: ")

        id_usuario = Sessao.obter_id_usuario()

        cursor.execute(
            """
            INSERT INTO sensor
                (tipo, descricao, unidade_medida, status, id_usuario_cadastro)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (tipo, descricao, unidade, True, id_usuario)
        )

        conexao.commit()

        print("\nSensor cadastrado com sucesso!")
        print(f"ID do sensor: {cursor.lastrowid}")
        print("Status: ATIVO")

    except Exception as erro:
        conexao.rollback()
        print(f"\nErro ao cadastrar sensor: {erro}")

    finally:
        cursor.close()
        conexao.close()


# ============================================================
# CONSULTAR SENSORES
# ============================================================

def consultar_sensores():
    if not Sessao.autenticada():
        print("\nFaça login para consultar sensores.")
        return

    conexao = conectar()

    if not conexao:
        return

    cursor = conexao.cursor(dictionary=True)

    try:
        while True:
            # Consulta novamente os dados a cada retorno à lista.
            print("\n========== SENSORES CADASTRADOS ==========")

            cursor.execute(
                """
                SELECT idsensor, tipo, status
                FROM sensor
                ORDER BY idsensor
                """
            )

            sensores = cursor.fetchall()

            if not sensores:
                print("\nNenhum sensor cadastrado.")
                return

            for sensor in sensores:
                status = (
                    "ATIVO"
                    if bool(sensor["status"])
                    else "INATIVO"
                )

                print(
                    f"\nID: {sensor['idsensor']} | "
                    f"Tipo: {sensor['tipo']} | "
                    f"Status: {status}"
                )

            print("\n0 - Voltar")

            id_sensor = input(
                "\nDigite o ID do sensor para consultar: "
            ).strip()

            if id_sensor == "0":
                break

            if not id_sensor.isdigit() or int(id_sensor) <= 0:
                print("\nDigite um ID válido.")
                continue

            cursor.execute(
                """
                SELECT
                    s.idsensor,
                    s.tipo,
                    s.descricao,
                    s.unidade_medida,
                    s.status,
                    s.id_usuario_cadastro,
                    u.nome AS usuario_cadastro
                FROM sensor s
                LEFT JOIN usuario u
                    ON s.id_usuario_cadastro = u.idusuario
                WHERE s.idsensor = %s
                """,
                (int(id_sensor),)
            )

            sensor = cursor.fetchone()

            if not sensor:
                print("\nSensor não encontrado.")
                continue

            exibir_detalhes_sensor(sensor)

            while True:
                print("\n========== OPÇÕES DO SENSOR ==========")
                print("1 - Alterar dados do sensor")
                print("2 - Alterar status do sensor")
                print("3 - Excluir sensor")
                print("4 - Consultar medições deste sensor")
                print("0 - Voltar à lista de sensores")

                opcao = input("\nEscolha: ").strip()

                if opcao == "1":
                    alterar_sensor(sensor["idsensor"])
                    break

                elif opcao == "2":
                    alterar_status_sensor(sensor["idsensor"])
                    break

                elif opcao == "3":
                    excluir_sensor(sensor["idsensor"])
                    break

                elif opcao == "4":
                    historico_medicoes(sensor["idsensor"])
                    break

                elif opcao == "0":
                    break

                else:
                    print("\nOpção inválida.")

            # O while recomeça e atualiza a lista automaticamente.

    except Exception as erro:
        print(f"\nErro ao consultar sensores: {erro}")

    finally:
        cursor.close()
        conexao.close()


def exibir_detalhes_sensor(sensor):
    status = "ATIVO" if bool(sensor["status"]) else "INATIVO"

    print("\n========== INFORMAÇÕES DO SENSOR ==========")
    print(f"ID: {sensor['idsensor']}")
    print(f"Tipo: {sensor['tipo']}")
    print(f"Descrição: {sensor['descricao']}")
    print(f"Unidade de medida: {sensor['unidade_medida']}")
    print(f"Status: {status}")
    print(f"ID do usuário que cadastrou: {sensor['id_usuario_cadastro']}")
    print(f"Usuário que cadastrou: {sensor['usuario_cadastro']}")


# ============================================================
# ALTERAR SENSOR
# ============================================================

def alterar_sensor(id_sensor):
    conexao = conectar()

    if not conexao:
        return

    cursor = conexao.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT tipo, descricao, unidade_medida
            FROM sensor
            WHERE idsensor = %s
            """,
            (id_sensor,)
        )

        sensor = cursor.fetchone()

        if not sensor:
            print("\nSensor não encontrado.")
            return

        print("\n========== ALTERAR SENSOR ==========")
        print("Deixe o campo vazio para manter o valor atual.")

        print(f"Tipo atual: {sensor['tipo']}")
        tipo = validar_texto(
            "Novo tipo: ",
            permitir_vazio=True
        )

        print(f"Descrição atual: {sensor['descricao']}")
        descricao = validar_texto(
            "Nova descrição: ",
            permitir_vazio=True
        )

        print(f"Unidade atual: {sensor['unidade_medida']}")
        unidade = validar_unidade(
            "Nova unidade: ",
            permitir_vazio=True
        )

        tipo = tipo if tipo else sensor["tipo"]
        descricao = descricao if descricao else sensor["descricao"]
        unidade = unidade if unidade else sensor["unidade_medida"]

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

        print("\nSensor atualizado com sucesso!")

    except Exception as erro:
        conexao.rollback()
        print(f"\nErro ao alterar sensor: {erro}")

    finally:
        cursor.close()
        conexao.close()


# ============================================================
# ALTERAR STATUS DO SENSOR
# ============================================================

def alterar_status_sensor(id_sensor):
    conexao = conectar()

    if not conexao:
        return

    cursor = conexao.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT idsensor, tipo, status
            FROM sensor
            WHERE idsensor = %s
            FOR UPDATE
            """,
            (id_sensor,)
        )

        sensor = cursor.fetchone()

        if not sensor:
            conexao.rollback()
            print("\nSensor não encontrado.")
            return

        status_atual = bool(sensor["status"])

        print("\n========== ALTERAR STATUS ==========")
        print(f"Sensor: {sensor['tipo']}")

        if status_atual:
            print("Status atual: ATIVO")
            print("\n1 - Desativar sensor")
            print("0 - Voltar")
        else:
            print("Status atual: INATIVO")
            print("\n1 - Ativar sensor")
            print("0 - Voltar")

        opcao = input("\nEscolha uma opção: ").strip()

        if opcao == "0":
            conexao.rollback()
            print("\nOperação cancelada.")
            return

        elif opcao == "1":
            novo_status = not status_atual

        else:
            conexao.rollback()
            print("\nOpção inválida.")
            return

        cursor.execute(
            """
            UPDATE sensor
            SET status = %s
            WHERE idsensor = %s
            """,
            (novo_status, id_sensor)
        )

        conexao.commit()

        print("\nStatus atualizado com sucesso!")

        if novo_status:
            print("Novo status: ATIVO")
        else:
            print("Novo status: INATIVO")
            print("O registro de novas medições está bloqueado.")

    except Exception as erro:
        conexao.rollback()
        print(f"\nErro ao alterar status: {erro}")

    finally:
        cursor.close()
        conexao.close()


# ============================================================
# EXCLUIR SENSOR
# ============================================================

def excluir_sensor(id_sensor):
    conexao = conectar()

    if not conexao:
        return

    cursor = conexao.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT idsensor
            FROM sensor
            WHERE idsensor = %s
            """,
            (id_sensor,)
        )

        if not cursor.fetchone():
            print("\nSensor não encontrado.")
            return

        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM MEDICAO
            WHERE idsensor = %s
            """,
            (id_sensor,)
        )

        resultado = cursor.fetchone()

        if resultado["total"] > 0:
            print("\nNão é possível excluir este sensor.")
            print("Existem medições vinculadas a ele.")
            return

        confirmacao = input(
            "\nDeseja realmente excluir este sensor? (s/n): "
        ).strip().lower()

        if confirmacao != "s":
            print("\nExclusão cancelada.")
            return

        cursor.execute(
            "DELETE FROM sensor WHERE idsensor = %s",
            (id_sensor,)
        )

        conexao.commit()

        print("\nSensor excluído com sucesso!")

    except Exception as erro:
        conexao.rollback()
        print(f"\nErro ao excluir sensor: {erro}")

    finally:
        cursor.close()
        conexao.close()


# ============================================================
# REGISTRAR MEDIÇÃO
# ============================================================

def registrar_medicao():
    if not Sessao.autenticada():
        print("\nFaça login para registrar medições.")
        return

    conexao = conectar()

    if not conexao:
        return

    cursor = conexao.cursor(dictionary=True)

    try:
        print("\n========== SENSORES ATIVOS ==========")

        cursor.execute(
            """
            SELECT idsensor, tipo, unidade_medida
            FROM sensor
            WHERE status = 1
            ORDER BY idsensor
            """
        )

        sensores = cursor.fetchall()

        if not sensores:
            print("\nNão existem sensores ativos para registrar medições.")
            return

        for sensor in sensores:
            print(
                f"ID: {sensor['idsensor']} | "
                f"Tipo: {sensor['tipo']} | "
                f"Unidade: {sensor['unidade_medida']}"
            )

        id_sensor = validar_id("\nDigite o ID do sensor: ")

        cursor.execute(
            """
            SELECT idsensor, tipo, unidade_medida, status
            FROM sensor
            WHERE idsensor = %s
            FOR UPDATE
            """,
            (id_sensor,)
        )

        sensor = cursor.fetchone()

        if not sensor:
            conexao.rollback()
            print("\nSensor não encontrado.")
            return

        if not sensor["status"]:
            conexao.rollback()
            print("\nNão é possível registrar medições!")
            print("Este sensor está INATIVO.")
            return

        print(f"\nSensor selecionado: {sensor['tipo']}")
        print(f"Unidade: {sensor['unidade_medida']}")

        valor = validar_valor_medicao(
            "Digite o valor da medição: "
        )

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

        cursor.execute(
            """
            INSERT INTO MEDICAO
                (idsensor, numero_medicao, valor)
            VALUES (%s, %s, %s)
            """,
            (id_sensor, numero_medicao, valor)
        )

        id_medicao = cursor.lastrowid

        cursor.execute(
            """
            SELECT data_hora
            FROM MEDICAO
            WHERE idmedicao = %s
            """,
            (id_medicao,)
        )

        medicao = cursor.fetchone()

        conexao.commit()

        print("\nMedição registrada com sucesso!")
        print(f"Identificação: {id_sensor}-{numero_medicao}")
        print(f"ID interno: {id_medicao}")
        print(f"Sensor: {sensor['tipo']}")
        print(f"Valor: {valor} {sensor['unidade_medida']}")
        print(f"Data e hora: {medicao['data_hora']}")

    except Exception as erro:
        conexao.rollback()
        print(f"\nErro ao registrar medição: {erro}")

    finally:
        cursor.close()
        conexao.close()


# ============================================================
# HISTÓRICO DE MEDIÇÕES
# ============================================================

def historico_medicoes(id_sensor):
    conexao = conectar()

    if not conexao:
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
            print("\nEste sensor ainda não possui medições.")
            return

        for medicao in medicoes:
            identificador = (
                f"{medicao['idsensor']}-{medicao['numero_medicao']}"
            )

            print("\n----------------------------------------")
            print(f"ID da medição: {identificador}")
            print(f"ID interno: {medicao['idmedicao']}")
            print(f"Sensor: {medicao['tipo']}")
            print(
                f"Valor: {medicao['valor']} "
                f"{medicao['unidade_medida']}"
            )
            print(f"Data e hora: {medicao['data_hora']}")

    except Exception as erro:
        print(f"\nErro ao consultar medições: {erro}")

    finally:
        cursor.close()
        conexao.close()


# ============================================================
# MENU DE MEDIÇÕES
# ============================================================

def menu_medicoes():
    if not Sessao.autenticada():
        print("\nFaça login para acessar as medições.")
        return

    while True:
        print("\n========== MEDIÇÕES ==========")
        print("1 - Registrar medição")
        print("0 - Voltar")

        opcao = input("\nEscolha uma opção: ").strip()

        if opcao == "1":
            registrar_medicao()

        elif opcao == "0":
            break

        else:
            print("\nOpção inválida.")


# ============================================================
# PERFIL DO USUÁRIO
# ============================================================

def meu_perfil():
    if not Sessao.autenticada():
        print("\nFaça login para acessar seu perfil.")
        return

    conexao = conectar()

    if not conexao:
        return

    cursor = conexao.cursor(dictionary=True)

    try:
        id_usuario = Sessao.obter_id_usuario()

        cursor.execute(
            """
            SELECT idusuario, nome, email
            FROM usuario
            WHERE idusuario = %s
            """,
            (id_usuario,)
        )

        usuario = cursor.fetchone()

        if not usuario:
            print("\nUsuário não encontrado.")
            return

        print("\n========== MEU PERFIL ==========")
        print(f"ID: {usuario['idusuario']}")
        print(f"Nome: {usuario['nome']}")
        print(f"E-mail: {usuario['email']}")
        print("Senha: ********")

        print("\n1 - Alterar senha")
        print("0 - Voltar")

        opcao = input("\nEscolha: ").strip()

        if opcao == "1":
            alterar_senha()

    except Exception as erro:
        print(f"\nErro ao consultar perfil: {erro}")

    finally:
        cursor.close()
        conexao.close()


# ============================================================
# ALTERAR SENHA
# ============================================================

def alterar_senha():
    if not Sessao.autenticada():
        print("\nFaça login para alterar sua senha.")
        return

    conexao = conectar()

    if not conexao:
        return

    cursor = conexao.cursor(dictionary=True)

    try:
        id_usuario = Sessao.obter_id_usuario()

        cursor.execute(
            """
            SELECT senha
            FROM usuario
            WHERE idusuario = %s
            """,
            (id_usuario,)
        )

        usuario = cursor.fetchone()

        if not usuario:
            print("\nUsuário não encontrado.")
            return

        senha_atual = getpass("Digite sua senha atual: ")

        if not check_password_hash(usuario["senha"], senha_atual):
            print("\nSenha atual incorreta.")
            return

        nova_senha = validar_senha("Digite a nova senha: ")
        confirmar = getpass("Confirme a nova senha: ")

        if nova_senha != confirmar:
            print("\nAs senhas não correspondem.")
            return

        senha_hash = generate_password_hash(nova_senha)

        cursor.execute(
            """
            UPDATE usuario
            SET senha = %s
            WHERE idusuario = %s
            """,
            (senha_hash, id_usuario)
        )

        conexao.commit()

        print("\nSenha alterada com sucesso!")

    except Exception as erro:
        conexao.rollback()
        print(f"\nErro ao alterar senha: {erro}")

    finally:
        cursor.close()
        conexao.close()


# ============================================================
# ENCERRAR SESSÃO
# ============================================================

def encerrar_sessao():
    if Sessao.autenticada():
        Sessao.encerrar()
        print("\nSessão encerrada com sucesso.")
    else:
        print("\nNenhum usuário está conectado.")


# ============================================================
# MENU PRINCIPAL
# ============================================================

def menu_principal():
    while True:
        print("\n========================================")
        print("             ESTUFA IoT02")
        print("========================================")

        if Sessao.autenticada():
            usuario = Sessao.usuario_atual()
            print(f"Usuário conectado: {usuario['nome']}")

            print("\n1 - Cadastrar sensores")
            print("2 - Consultar sensores")
            print("3 - Medições")
            print("4 - Meu perfil")
            print("5 - Encerrar sessão")
            print("0 - Sair do programa")

            opcao = input("\nEscolha uma opção: ").strip()

            if opcao == "1":
                cadastrar_sensor()

            elif opcao == "2":
                consultar_sensores()

            elif opcao == "3":
                menu_medicoes()

            elif opcao == "4":
                meu_perfil()

            elif opcao == "5":
                encerrar_sessao()

            elif opcao == "0":
                print("\nPrograma encerrado.")
                break

            else:
                print("\nOpção inválida.")

        else:
            print("\n1 - Fazer login")
            print("2 - Cadastrar usuário")
            print("0 - Sair do programa")

            opcao = input("\nEscolha uma opção: ").strip()

            if opcao == "1":
                login()

            elif opcao == "2":
                cadastrar_usuario()

            elif opcao == "0":
                print("\nPrograma encerrado.")
                break

            else:
                print("\nOpção inválida.")


# ============================================================
# INICIALIZAÇÃO
# ============================================================

if __name__ == "__main__":
    menu_principal()
