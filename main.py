
from database.bancodedados import conectar
from sessao import Sessao

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from mysql.connector import Error
from decimal import Decimal, InvalidOperation
from getpass import getpass


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def pausar():
    input("\nPressione ENTER para continuar...")


def usuario_atual():
    return Sessao.usuario_atual()


def usuario_e_ti():
    usuario = usuario_atual()

    if usuario and usuario.get("cargo", "").lower() == "ti":
        return True

    return False


def atualizar_dados_sessao():
    usuario = usuario_atual()

    if not usuario:
        return

    conexao = conectar()

    if conexao is None:
        return

    cursor = conexao.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT idusuario, nome, email, senha, cargo
            FROM usuario
            WHERE idusuario = %s
            """,
            (usuario["idusuario"],)
        )

        dados = cursor.fetchone()

        if dados:
            Sessao.iniciar(dados)

    except Error as erro:
        print(f"Erro ao atualizar sessão: {erro}")

    finally:
        cursor.close()
        conexao.close()


def validar_email(email):
    return "@" in email and "." in email.split("@")[-1]


def ler_valor_decimal():
    try:
        valor_texto = input("Valor da medição: ").strip().replace(",", ".")
        valor = Decimal(valor_texto)

        if not valor.is_finite():
            print("Digite um valor numérico válido.")
            return None

        if abs(valor) > Decimal("99999999.99"):
            print("Valor fora do limite permitido.")
            return None

        if valor.as_tuple().exponent < -2:
            print("Digite no máximo duas casas decimais.")
            return None

        return valor

    except InvalidOperation:
        print("Digite um valor numérico válido.")
        return None


# ============================================================
# CADASTRO PÚBLICO DE USUÁRIO
# ============================================================

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
        print("Não foi possível conectar ao banco.")
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

        # Cadastro público sempre cria usuário Técnico.
        cursor.execute(
            """
            INSERT INTO usuario (nome, email, senha, cargo)
            VALUES (%s, %s, %s, %s)
            """,
            (nome, email, senha_hash, "tecnico")
        )

        conexao.commit()

        print("\nUsuário cadastrado com sucesso!")
        print("Cargo: Técnico")

    except Error as erro:
        conexao.rollback()
        print(f"Erro ao cadastrar usuário: {erro}")

    finally:
        cursor.close()
        conexao.close()


# ============================================================
# LOGIN
# ============================================================

def login():
    print("\n========== LOGIN ==========")

    email = input("E-mail: ").strip()
    senha = getpass("Senha: ")

    conexao = conectar()

    if conexao is None:
        print("Não foi possível conectar ao banco.")
        return

    cursor = conexao.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT idusuario, nome, email, senha, cargo
            FROM usuario
            WHERE email = %s
            """,
            (email,)
        )

        usuario = cursor.fetchone()

        if usuario and check_password_hash(usuario["senha"], senha):
            Sessao.iniciar(usuario)

            print(f"\nBem-vindo(a), {usuario['nome']}!")
            print(f"Cargo: {usuario['cargo']}")

        else:
            print("\nE-mail ou senha incorretos.")

    except Error as erro:
        print(f"Erro ao realizar login: {erro}")

    finally:
        cursor.close()
        conexao.close()


# ============================================================
# CADASTRO DE USUÁRIO PELO TI
# ============================================================

def cadastrar_usuario_ti():
    if not usuario_e_ti():
        print("Acesso permitido somente para usuários TI.")
        return

    print("\n========== CADASTRAR USUÁRIO ==========")

    nome = input("Nome: ").strip()
    email = input("E-mail: ").strip()
    senha = getpass("Senha: ")

    if not nome or not email or not senha:
        print("Todos os campos são obrigatórios.")
        return

    if not validar_email(email):
        print("E-mail inválido.")
        return

    print("\nSelecione o cargo do usuário:")
    print("1 - Técnico")
    print("2 - TI")

    opcao = input("Escolha: ").strip()

    if opcao == "1":
        cargo = "tecnico"
    elif opcao == "2":
        cargo = "TI"
    else:
        print("Opção inválida.")
        return

    conexao = conectar()

    if conexao is None:
        print("Não foi possível conectar ao banco.")
        return

    cursor = conexao.cursor()

    try:
        cursor.execute(
            "SELECT idusuario FROM usuario WHERE email = %s",
            (email,)
        )

        if cursor.fetchone():
            print("Já existe um usuário com este e-mail.")
            return

        senha_hash = generate_password_hash(senha)

        cursor.execute(
            """
            INSERT INTO usuario (nome, email, senha, cargo)
            VALUES (%s, %s, %s, %s)
            """,
            (nome, email, senha_hash, cargo)
        )

        conexao.commit()

        print("\nUsuário cadastrado com sucesso!")
        print(f"Nome: {nome}")
        print(f"E-mail: {email}")
        print(f"Cargo: {cargo}")

    except Error as erro:
        conexao.rollback()
        print(f"Erro ao cadastrar usuário: {erro}")

    finally:
        cursor.close()
        conexao.close()


# ============================================================
# GERENCIAR USUÁRIOS - SOMENTE TI
# ============================================================

def listar_usuarios():
    if not usuario_e_ti():
        print("Acesso permitido somente para TI.")
        return

    conexao = conectar()

    if conexao is None:
        return

    cursor = conexao.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT idusuario, nome, email, cargo
            FROM usuario
            ORDER BY idusuario
            """
        )

        usuarios = cursor.fetchall()

        print("\n========== USUÁRIOS CADASTRADOS ==========")

        if not usuarios:
            print("Nenhum usuário cadastrado.")
            return

        for usuario in usuarios:
            print("--------------------------------------")
            print(f"ID: {usuario['idusuario']}")
            print(f"Nome: {usuario['nome']}")
            print(f"E-mail: {usuario['email']}")
            print(f"Cargo: {usuario['cargo']}")

    except Error as erro:
        print(f"Erro ao listar usuários: {erro}")

    finally:
        cursor.close()
        conexao.close()


def alterar_usuario():
    if not usuario_e_ti():
        print("Acesso permitido somente para TI.")
        return

    listar_usuarios()

    try:
        idusuario = int(input("\nDigite o ID do usuário: "))
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
            SELECT idusuario, nome, email, cargo
            FROM usuario
            WHERE idusuario = %s
            """,
            (idusuario,)
        )

        usuario = cursor.fetchone()

        if not usuario:
            print("Usuário não encontrado.")
            return

        print("\nDeixe em branco para manter o valor atual.")

        nome = input(f"Nome ({usuario['nome']}): ").strip()
        email = input(f"E-mail ({usuario['email']}): ").strip()

        print("\nCargo:")
        print("1 - Técnico")
        print("2 - TI")

        opcao_cargo = input("Nova opção de cargo (ENTER mantém): ").strip()

        novo_nome = nome if nome else usuario["nome"]
        novo_email = email if email else usuario["email"]

        novo_cargo = usuario["cargo"]

        if opcao_cargo == "1":
            novo_cargo = "tecnico"
        elif opcao_cargo == "2":
            novo_cargo = "TI"
        elif opcao_cargo != "":
            print("Opção de cargo inválida.")
            return

        if not validar_email(novo_email):
            print("E-mail inválido.")
            return

        if novo_email != usuario["email"]:
            cursor.execute(
                """
                SELECT idusuario
                FROM usuario
                WHERE email = %s AND idusuario <> %s
                """,
                (novo_email, idusuario)
            )

            if cursor.fetchone():
                print("Este e-mail já pertence a outro usuário.")
                return

        # Impede rebaixar o último usuário TI.
        if usuario["cargo"].lower() == "ti" and novo_cargo.lower() != "ti":
            cursor.execute(
                "SELECT COUNT(*) AS total FROM usuario WHERE LOWER(cargo) = 'ti'"
            )

            total_ti = cursor.fetchone()["total"]

            if total_ti <= 1:
                print("Não é possível rebaixar o último usuário TI.")
                return

        cursor.execute(
            """
            UPDATE usuario
            SET nome = %s, email = %s, cargo = %s
            WHERE idusuario = %s
            """,
            (novo_nome, novo_email, novo_cargo, idusuario)
        )

        conexao.commit()

        print("\nUsuário atualizado com sucesso!")

        if Sessao.obter_id_usuario() == idusuario:
            atualizar_dados_sessao()

    except Error as erro:
        conexao.rollback()
        print(f"Erro ao alterar usuário: {erro}")

    finally:
        cursor.close()
        conexao.close()


def excluir_usuario():
    if not usuario_e_ti():
        print("Acesso permitido somente para TI.")
        return

    listar_usuarios()

    try:
        idusuario = int(input("\nDigite o ID do usuário que deseja excluir: "))
    except ValueError:
        print("ID inválido.")
        return

    if Sessao.obter_id_usuario() == idusuario:
        print("Você não pode excluir sua própria conta.")
        return

    conexao = conectar()

    if conexao is None:
        return

    cursor = conexao.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT idusuario, nome, cargo
            FROM usuario
            WHERE idusuario = %s
            """,
            (idusuario,)
        )

        usuario = cursor.fetchone()

        if not usuario:
            print("Usuário não encontrado.")
            return

        if usuario["cargo"].lower() == "ti":
            cursor.execute(
                "SELECT COUNT(*) AS total FROM usuario WHERE LOWER(cargo) = 'ti'"
            )

            total_ti = cursor.fetchone()["total"]

            if total_ti <= 1:
                print("Não é possível excluir o último usuário TI.")
                return

        confirmacao = input(
            f"Confirma a exclusão de {usuario['nome']}? (s/n): "
        ).strip().lower()

        if confirmacao != "s":
            print("Exclusão cancelada.")
            return

        cursor.execute(
            "DELETE FROM usuario WHERE idusuario = %s",
            (idusuario,)
        )

        conexao.commit()

        print("Usuário excluído com sucesso!")

    except Error as erro:
        conexao.rollback()
        print(
            "Não foi possível excluir o usuário. "
            "Verifique se ele está vinculado a algum sensor."
        )
        print(f"Detalhes: {erro}")

    finally:
        cursor.close()
        conexao.close()


def gerenciar_usuarios():
    if not usuario_e_ti():
        print("Acesso permitido somente para TI.")
        return

    while True:
        print("\n========== GERENCIAR USUÁRIOS ==========")
        print("1 - Cadastrar usuário")
        print("2 - Listar usuários")
        print("3 - Alterar usuário")
        print("4 - Excluir usuário")
        print("0 - Voltar")

        opcao = input("Escolha: ").strip()

        if opcao == "1":
            cadastrar_usuario_ti()
            pausar()

        elif opcao == "2":
            listar_usuarios()
            pausar()

        elif opcao == "3":
            alterar_usuario()
            pausar()

        elif opcao == "4":
            excluir_usuario()
            pausar()

        elif opcao == "0":
            break

        else:
            print("Opção inválida.")


# ============================================================
# CADASTRO DE SENSOR
# ============================================================

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
            (tipo, descricao, unidade_medida, status, id_usuario_cadastro)
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

        print("Sensor cadastrado com sucesso!")

    except Error as erro:
        conexao.rollback()
        print(f"Erro ao cadastrar sensor: {erro}")

    finally:
        cursor.close()
        conexao.close()


# ============================================================
# LISTAR SENSORES
# ============================================================

def listar_sensores():
    conexao = conectar()

    if conexao is None:
        return []

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
            return []

        for sensor in sensores:
            situacao = "Ativo" if sensor["status"] else "Inativo"

            print("--------------------------------------")
            print(f"ID: {sensor['idsensor']}")
            print(f"Tipo: {sensor['tipo']}")
            print(f"Descrição: {sensor['descricao']}")
            print(f"Unidade: {sensor['unidade_medida']}")
            print(f"Status: {situacao}")
            print(
                f"Cadastrado por: "
                f"{sensor['usuario_cadastro'] or 'Não identificado'}"
            )

        return sensores

    except Error as erro:
        print(f"Erro ao consultar sensores: {erro}")
        return []

    finally:
        cursor.close()
        conexao.close()


# ============================================================
# CONSULTAR SENSOR INDIVIDUAL
# ============================================================

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
        print(f"Unidade de medida: {sensor['unidade_medida']}")
        print(f"Status: {'Ativo' if sensor['status'] else 'Inativo'}")
        print(f"Usuário responsável: {sensor['usuario_cadastro'] or 'Não identificado'}")

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


# ============================================================
# ALTERAR SENSOR
# ============================================================

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

        print("\nDeixe em branco para manter os dados atuais.")

        tipo = input(f"Tipo ({sensor['tipo']}): ").strip()
        descricao = input(f"Descrição ({sensor['descricao']}): ").strip()
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


# ============================================================
# ALTERAR STATUS DO SENSOR
# ============================================================

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

        status_atual = bool(sensor["status"])
        novo_status = 0 if status_atual else 1

        cursor.execute(
            "UPDATE sensor SET status = %s WHERE idsensor = %s",
            (novo_status, idsensor)
        )

        conexao.commit()

        print(
            "Status atualizado: "
            + ("Ativo" if novo_status else "Inativo")
        )

    except Error as erro:
        conexao.rollback()
        print(f"Erro ao alterar status: {erro}")

    finally:
        cursor.close()
        conexao.close()


# ============================================================
# EXCLUIR SENSOR
# ============================================================

def excluir_sensor(idsensor):
    conexao = conectar()

    if conexao is None:
        return

    cursor = conexao.cursor()

    try:
        cursor.execute(
            "SELECT idmedicao FROM MEDICAO WHERE idsensor = %s LIMIT 1",
            (idsensor,)
        )

        if cursor.fetchone():
            print(
                "Este sensor possui medições cadastradas. "
                "Não é possível excluí-lo sem tratar primeiro "
                "o histórico de medições."
            )
            return

        confirmacao = input(
            "Tem certeza que deseja excluir este sensor? (s/n): "
        ).strip().lower()

        if confirmacao != "s":
            print("Exclusão cancelada.")
            return

        cursor.execute(
            "DELETE FROM sensor WHERE idsensor = %s",
            (idsensor,)
        )

        conexao.commit()

        if cursor.rowcount:
            print("Sensor excluído com sucesso!")
        else:
            print("Sensor não encontrado.")

    except Error as erro:
        conexao.rollback()
        print(f"Erro ao excluir sensor: {erro}")

    finally:
        cursor.close()
        conexao.close()


# ============================================================
# MENU DE SENSORES
# ============================================================

def menu_sensores():
    while True:
        print("\n========== SENSORES ==========")
        print("1 - Cadastrar sensor")
        print("2 - Listar sensores")
        print("3 - Consultar sensor individual")
        print("0 - Voltar")

        opcao = input("Escolha: ").strip()

        if opcao == "1":
            cadastrar_sensor()
            pausar()

        elif opcao == "2":
            listar_sensores()
            pausar()

        elif opcao == "3":
            consultar_sensor()
            pausar()

        elif opcao == "0":
            break

        else:
            print("Opção inválida.")


# ============================================================
# REGISTRAR MEDIÇÃO
# ============================================================

def registrar_medicao():
    conexao = conectar()

    if conexao is None:
        return

    cursor = conexao.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT idsensor, tipo, descricao, unidade_medida
            FROM sensor
            WHERE status = 1
            ORDER BY idsensor
            """
        )

        sensores = cursor.fetchall()

        if not sensores:
            print("Não existem sensores ativos.")
            return

        print("\n========== SENSORES ATIVOS ==========")

        for sensor in sensores:
            print(
                f"ID: {sensor['idsensor']} | "
                f"{sensor['tipo']} | "
                f"{sensor['descricao']} | "
                f"{sensor['unidade_medida']}"
            )

        try:
            idsensor = int(input("\nID do sensor: "))
        except ValueError:
            print("ID inválido.")
            return

        sensor_selecionado = next(
            (s for s in sensores if s["idsensor"] == idsensor),
            None
        )

        if not sensor_selecionado:
            print("Sensor não encontrado ou inativo.")
            return

        valor = ler_valor_decimal()

        if valor is None:
            return

        cursor.execute(
            """
            INSERT INTO MEDICAO (idsensor, data_hora, valor)
            VALUES (%s, NOW(), %s)
            """,
            (idsensor, valor)
        )

        conexao.commit()

        print("\nMedição registrada com sucesso!")

    except Error as erro:
        conexao.rollback()
        print(f"Erro ao registrar medição: {erro}")

    finally:
        cursor.close()
        conexao.close()


# ============================================================
# HISTÓRICO DE MEDIÇÕES POR SENSOR
# ============================================================

def historico_medicoes():
    conexao = conectar()

    if conexao is None:
        return

    cursor = conexao.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT idsensor, tipo, descricao, unidade_medida
            FROM sensor
            ORDER BY idsensor
            """
        )

        sensores = cursor.fetchall()

        if not sensores:
            print("Nenhum sensor cadastrado.")
            return

        print("\n========== SELECIONE O SENSOR ==========")

        for sensor in sensores:
            print(
                f"ID: {sensor['idsensor']} | "
                f"{sensor['tipo']} | "
                f"{sensor['descricao']}"
            )

        try:
            idsensor = int(input("\nDigite o ID do sensor: "))
        except ValueError:
            print("ID inválido.")
            return

        sensor_selecionado = next(
            (s for s in sensores if s["idsensor"] == idsensor),
            None
        )

        if not sensor_selecionado:
            print("Sensor não encontrado.")
            return

        cursor.execute(
            """
            SELECT idmedicao, data_hora, valor
            FROM MEDICAO
            WHERE idsensor = %s
            ORDER BY data_hora DESC, idmedicao DESC
            LIMIT 100
            """,
            (idsensor,)
        )

        medicoes = cursor.fetchall()

        print("\n========== HISTÓRICO DE MEDIÇÕES ==========")
        print(f"Sensor: {sensor_selecionado['tipo']}")
        print(f"Descrição: {sensor_selecionado['descricao']}")
        print(f"Unidade: {sensor_selecionado['unidade_medida']}")

        if not medicoes:
            print("\nEste sensor ainda não possui medições.")
            return

        for medicao in medicoes:
            print("--------------------------------------")
            print(f"ID da medição: {medicao['idmedicao']}")
            print(f"Data e hora: {medicao['data_hora']}")
            print(
                f"Valor: {medicao['valor']} "
                f"{sensor_selecionado['unidade_medida']}"
            )

    except Error as erro:
        print(f"Erro ao consultar medições: {erro}")

    finally:
        cursor.close()
        conexao.close()


# ============================================================
# MENU DE MEDIÇÕES
# ============================================================

def menu_medicoes():
    while True:
        print("\n========== MEDIÇÕES ==========")
        print("1 - Registrar medição")
        print("2 - Histórico de medições por sensor")
        print("0 - Voltar")

        opcao = input("Escolha: ").strip()

        if opcao == "1":
            registrar_medicao()
            pausar()

        elif opcao == "2":
            historico_medicoes()
            pausar()

        elif opcao == "0":
            break

        else:
            print("Opção inválida.")


# ============================================================
# MEU PERFIL
# ============================================================

def meu_perfil():
    usuario = usuario_atual()

    if not usuario:
        print("Nenhum usuário autenticado.")
        return

    print("\n========== MEU PERFIL ==========")
    print(f"ID: {usuario['idusuario']}")
    print(f"Nome: {usuario['nome']}")
    print(f"E-mail: {usuario['email']}")
    print(f"Cargo: {usuario['cargo']}")
    print("Senha: ********")

    print("\n1 - Alterar senha")
    print("0 - Voltar")

    opcao = input("Escolha: ").strip()

    if opcao == "1":
        alterar_senha()


def alterar_senha():
    usuario = usuario_atual()

    if not usuario:
        print("Faça login para continuar.")
        return

    senha_atual = getpass("Senha atual: ")
    nova_senha = getpass("Nova senha: ")
    confirmar_senha = getpass("Confirme a nova senha: ")

    if not nova_senha:
        print("A nova senha não pode ficar vazia.")
        return

    if nova_senha != confirmar_senha:
        print("As senhas não coincidem.")
        return

    conexao = conectar()

    if conexao is None:
        return

    cursor = conexao.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT senha FROM usuario WHERE idusuario = %s",
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

        atualizar_dados_sessao()

        print("Senha alterada com sucesso!")

    except Error as erro:
        conexao.rollback()
        print(f"Erro ao alterar senha: {erro}")

    finally:
        cursor.close()
        conexao.close()


# ============================================================
# ENCERRAR SESSÃO
# ============================================================

def encerrar_sessao():
    Sessao.encerrar()
    print("\nSessão encerrada com sucesso!")


# ============================================================
# MENU PRINCIPAL
# ============================================================

def menu_principal():
    while True:
        print("\n========================================")
        print("             ESTUFA IOT 02")
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


# ============================================================
# MENU DO USUÁRIO AUTENTICADO
# ============================================================

def menu_usuario():
    while Sessao.autenticada():

        usuario = usuario_atual()

        if not usuario:
            break

        print("\n========================================")
        print("             ESTUFA IOT 02")
        print("========================================")
        print(f"Usuário: {usuario['nome']}")
        print(f"Cargo: {usuario['cargo']}")
        print("========================================")

        print("1 - Cadastrar sensor")
        print("2 - Consultar sensores")
        print("3 - Medições")
        print("4 - Meu perfil")

        if usuario_e_ti():
            print("5 - Gerenciar usuários")
            print("6 - Encerrar sessão")
        else:
            print("5 - Encerrar sessão")

        print("0 - Sair do programa")
        print("========================================")

        opcao = input("Escolha: ").strip()

        if opcao == "1":
            cadastrar_sensor()
            pausar()

        elif opcao == "2":
            menu_sensores()

        elif opcao == "3":
            menu_medicoes()

        elif opcao == "4":
            meu_perfil()
            pausar()

        elif opcao == "5" and usuario_e_ti():
            gerenciar_usuarios()

        elif opcao == "5" and not usuario_e_ti():
            encerrar_sessao()
            break

        elif opcao == "6" and usuario_e_ti():
            encerrar_sessao()
            break

        elif opcao == "0":
            print("Encerrando o programa...")
            raise SystemExit

        else:
            print("Opção inválida.")


# ============================================================
# EXECUÇÃO DO SISTEMA
# ============================================================

if __name__ == "__main__":
    try:
        menu_principal()

    except KeyboardInterrupt:
        print("\n\nSistema interrompido pelo usuário.")

    except SystemExit:
        pass

    except Exception as erro:
        print(f"\nErro inesperado: {erro}")

    finally:
        if Sessao.autenticada():
            Sessao.encerrar()

        print("\nSistema finalizado.")
