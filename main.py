
from flask import (
    Flask,
    jsonify,
    request,
    render_template,
    redirect,
    url_for,
    session,
    flash
)

from database.bancodedados import conectar

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from functools import wraps
from decimal import Decimal
from datetime import datetime


app = Flask(__name__)

app.secret_key = "estufa_iot01_chave_secreta"


# ==========================================
# PROTEÇÃO DE ROTAS
# ==========================================

def login_obrigatorio(funcao):
    @wraps(funcao)
    def verificar_login(*args, **kwargs):

        if "usuario_id" not in session:
            return redirect(url_for("login"))

        return funcao(*args, **kwargs)

    return verificar_login


# ==========================================
# PÁGINA INICIAL / DASHBOARD
# ==========================================

@app.route("/")
@login_obrigatorio
def index():
    return render_template("index.html")


# ==========================================
# LOGIN
# ==========================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if "usuario_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":

        email = request.form.get("email")
        senha = request.form.get("senha")

        conexao = conectar()

        if conexao is None:
            flash("Erro ao conectar ao banco de dados.")
            return render_template("login.html")

        cursor = conexao.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT idusuario, nome, email, senha
                FROM usuario
                WHERE email = %s
            """, (email,))

            usuario = cursor.fetchone()

            if usuario and check_password_hash(usuario["senha"], senha):

                session["usuario_id"] = usuario["idusuario"]
                session["usuario_nome"] = usuario["nome"]

                return redirect(url_for("index"))

            flash("E-mail ou senha incorretos.")

        except Exception as erro:
            print("Erro no login:", erro)
            flash("Ocorreu um erro ao realizar o login.")

        finally:
            cursor.close()
            conexao.close()

    return render_template("login.html")


# ==========================================
# CADASTRO DE USUÁRIO
# ==========================================

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():

    if "usuario_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":

        nome = request.form.get("nome")
        email = request.form.get("email")
        senha = request.form.get("senha")

        if not nome or not email or not senha:
            flash("Preencha todos os campos.")
            return render_template("cadastro.html")

        if len(senha) < 8:
            flash("A senha precisa ter pelo menos 8 caracteres.")
            return render_template("cadastro.html")

        conexao = conectar()

        if conexao is None:
            flash("Erro ao conectar ao banco de dados.")
            return render_template("cadastro.html")

        cursor = conexao.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT idusuario
                FROM usuario
                WHERE email = %s
            """, (email,))

            usuario_existente = cursor.fetchone()

            if usuario_existente:
                flash("Este e-mail já está cadastrado.")

            else:
                senha_criptografada = generate_password_hash(senha)

                cursor.execute("""
                    INSERT INTO usuario (nome, email, senha)
                    VALUES (%s, %s, %s)
                """, (
                    nome,
                    email,
                    senha_criptografada
                ))

                conexao.commit()

                flash("Cadastro realizado com sucesso!")
                return redirect(url_for("login"))

        except Exception as erro:
            conexao.rollback()
            print("Erro no cadastro:", erro)
            flash("Erro ao realizar o cadastro.")

        finally:
            cursor.close()
            conexao.close()

    return render_template("cadastro.html")


# ==========================================
# API DE CADASTRO DE USUÁRIOS
# ==========================================

@app.route("/api/usuarios", methods=["POST"])
def api_cadastrar_usuario():

    dados = request.get_json(silent=True)

    if not dados:
        return jsonify({
            "erro": "Envie os dados em formato JSON."
        }), 400

    nome = dados.get("nome")
    email = dados.get("email")
    senha = dados.get("senha")

    if not nome or not email or not senha:
        return jsonify({
            "erro": "Nome, e-mail e senha são obrigatórios."
        }), 400

    if len(senha) < 8:
        return jsonify({
            "erro": "A senha precisa ter pelo menos 8 caracteres."
        }), 400

    conexao = conectar()

    if conexao is None:
        return jsonify({
            "erro": "Erro ao conectar ao banco de dados."
        }), 500

    cursor = conexao.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT idusuario
            FROM usuario
            WHERE email = %s
        """, (email,))

        if cursor.fetchone():
            return jsonify({
                "erro": "E-mail já cadastrado."
            }), 409

        senha_criptografada = generate_password_hash(senha)

        cursor.execute("""
            INSERT INTO usuario (nome, email, senha)
            VALUES (%s, %s, %s)
        """, (
            nome,
            email,
            senha_criptografada
        ))

        conexao.commit()

        return jsonify({
            "mensagem": "Usuário cadastrado com sucesso!",
            "idusuario": cursor.lastrowid
        }), 201

    except Exception as erro:
        conexao.rollback()
        print("Erro na API de usuários:", erro)

        return jsonify({
            "erro": "Erro ao cadastrar usuário."
        }), 500

    finally:
        cursor.close()
        conexao.close()


# ==========================================
# CADASTRO E LISTAGEM DE SENSORES
# ==========================================

@app.route("/sensores", methods=["GET", "POST"])
@login_obrigatorio
def sensores():

    conexao = conectar()

    if conexao is None:
        return "Erro ao conectar ao banco de dados."

    cursor = conexao.cursor(dictionary=True)
    erro = None

    try:

        if request.method == "POST":

            tipo = request.form.get("tipo")
            descricao = request.form.get("descricao")
            unidade_medida = request.form.get("unidade_medida")

            if not tipo or not descricao or not unidade_medida:

                erro = "Preencha todos os campos."

            else:

                cursor.execute("""
                    INSERT INTO sensor (
                        tipo,
                        descricao,
                        unidade_medida,
                        status,
                        id_usuario_cadastro
                    )
                    VALUES (%s, %s, %s, TRUE, %s)
                """, (
                    tipo,
                    descricao,
                    unidade_medida,
                    session["usuario_id"]
                ))

                conexao.commit()

                return redirect(url_for("sensores"))

        cursor.execute("""
            SELECT
                idsensor,
                tipo,
                descricao,
                unidade_medida,
                status
            FROM sensor
            WHERE id_usuario_cadastro = %s
            ORDER BY idsensor DESC
        """, (session["usuario_id"],))

        lista_sensores = cursor.fetchall()

        return render_template(
            "sensores.html",
            sensores=lista_sensores,
            erro=erro
        )

    except Exception as erro:
        conexao.rollback()
        print("Erro na página de sensores:", erro)

        return "Erro ao carregar os sensores."

    finally:
        cursor.close()
        conexao.close()


# ==========================================
# ATIVAR / DESATIVAR SENSOR
# ==========================================

@app.route("/sensores/status/<int:idsensor>", methods=["POST"])
@login_obrigatorio
def alterar_status_sensor(idsensor):

    conexao = conectar()

    if conexao is None:
        return "Erro ao conectar ao banco de dados."

    cursor = conexao.cursor(dictionary=True)

    try:

        cursor.execute("""
            SELECT status
            FROM sensor
            WHERE idsensor = %s
              AND id_usuario_cadastro = %s
        """, (
            idsensor,
            session["usuario_id"]
        ))

        sensor = cursor.fetchone()

        if sensor:

            novo_status = not bool(sensor["status"])

            cursor.execute("""
                UPDATE sensor
                SET status = %s
                WHERE idsensor = %s
                  AND id_usuario_cadastro = %s
            """, (
                novo_status,
                idsensor,
                session["usuario_id"]
            ))

            conexao.commit()

        return redirect(url_for("sensores"))

    except Exception as erro:
        conexao.rollback()
        print("Erro ao alterar status do sensor:", erro)

        return "Erro ao atualizar o sensor."

    finally:
        cursor.close()
        conexao.close()


# ==========================================
# REGISTRO E HISTÓRICO DE MEDIÇÕES
# ==========================================

@app.route("/medicoes", methods=["GET", "POST"])
@login_obrigatorio
def medicoes():

    conexao = conectar()

    if conexao is None:
        return "Erro ao conectar ao banco de dados."

    cursor = conexao.cursor(dictionary=True)
    erro = None

    try:

        # REGISTRAR NOVA MEDIÇÃO

        if request.method == "POST":

            idsensor = request.form.get("idsensor")
            valor = request.form.get("valor")

            if not idsensor or valor is None or valor == "":

                erro = "Selecione um sensor e informe o valor."

            else:

                try:
                    valor_decimal = Decimal(valor)

                    cursor.execute("""
                        SELECT idsensor
                        FROM sensor
                        WHERE idsensor = %s
                          AND id_usuario_cadastro = %s
                          AND status = TRUE
                    """, (
                        idsensor,
                        session["usuario_id"]
                    ))

                    sensor_valido = cursor.fetchone()

                    if not sensor_valido:

                        erro = "Sensor não encontrado ou está inativo."

                    else:

                        cursor.execute("""
                            INSERT INTO medicao (
                                idsensor,
                                data_hora,
                                valor
                            )
                            VALUES (%s, NOW(), %s)
                        """, (
                            idsensor,
                            valor_decimal
                        ))

                        conexao.commit()

                        return redirect(url_for("medicoes"))

                except Exception:
                    erro = "Informe um valor numérico válido."

        # SENSORES ATIVOS PARA NOVAS MEDIÇÕES

        cursor.execute("""
            SELECT
                idsensor,
                tipo,
                descricao,
                unidade_medida
            FROM sensor
            WHERE id_usuario_cadastro = %s
              AND status = TRUE
            ORDER BY tipo
        """, (session["usuario_id"],))

        sensores_ativos = cursor.fetchall()

        # TODOS OS SENSORES PARA O FILTRO

        cursor.execute("""
            SELECT
                idsensor,
                tipo,
                descricao
            FROM sensor
            WHERE id_usuario_cadastro = %s
            ORDER BY tipo
        """, (session["usuario_id"],))

        todos_sensores = cursor.fetchall()

        # FILTRO POR SENSOR

        filtro_sensor = request.args.get("sensor", "").strip()

        consulta = """
            SELECT
                m.idmedicao,
                s.idsensor,
                s.tipo,
                s.descricao,
                m.valor,
                s.unidade_medida,
                m.data_hora
            FROM medicao m
            INNER JOIN sensor s
                ON m.idsensor = s.idsensor
            WHERE s.id_usuario_cadastro = %s
        """

        parametros = [session["usuario_id"]]

        if filtro_sensor:

            try:
                filtro_id = int(filtro_sensor)

                consulta += " AND s.idsensor = %s"
                parametros.append(filtro_id)

            except ValueError:
                filtro_sensor = ""

        consulta += """
            ORDER BY m.data_hora DESC
            LIMIT 100
        """

        cursor.execute(consulta, tuple(parametros))

        historico = cursor.fetchall()

        return render_template(
            "medicoes.html",
            sensores=sensores_ativos,
            todos_sensores=todos_sensores,
            medicoes=historico,
            filtro_sensor=filtro_sensor,
            erro=erro
        )

    except Exception as erro:
        conexao.rollback()
        print("Erro na página de medições:", erro)

        return "Erro ao carregar as medições."

    finally:
        cursor.close()
        conexao.close()


# ==========================================
# API DO DASHBOARD
# ==========================================

@app.route("/api/dashboard")
@login_obrigatorio
def api_dashboard():

    conexao = conectar()

    if conexao is None:
        return jsonify({
            "erro": "Erro ao conectar ao banco de dados."
        }), 500

    cursor = conexao.cursor(dictionary=True)

    try:

        # QUANTIDADE DE SENSORES ATIVOS

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM sensor
            WHERE id_usuario_cadastro = %s
              AND status = TRUE
        """, (session["usuario_id"],))

        resultado_sensores = cursor.fetchone()

        sensores_ativos = resultado_sensores["total"]

        # ÚLTIMA TEMPERATURA

        cursor.execute("""
            SELECT m.valor
            FROM medicao m
            INNER JOIN sensor s
                ON m.idsensor = s.idsensor
            WHERE s.id_usuario_cadastro = %s
              AND s.status = TRUE
              AND LOWER(s.tipo) LIKE %s
            ORDER BY m.data_hora DESC
            LIMIT 1
        """, (
            session["usuario_id"],
            "%temperatura%"
        ))

        resultado_temperatura = cursor.fetchone()

        temperatura = (
            float(resultado_temperatura["valor"])
            if resultado_temperatura else None
        )

        # ÚLTIMA UMIDADE

        cursor.execute("""
            SELECT m.valor
            FROM medicao m
            INNER JOIN sensor s
                ON m.idsensor = s.idsensor
            WHERE s.id_usuario_cadastro = %s
              AND s.status = TRUE
              AND LOWER(s.tipo) LIKE %s
            ORDER BY m.data_hora DESC
            LIMIT 1
        """, (
            session["usuario_id"],
            "%umidade%"
        ))

        resultado_umidade = cursor.fetchone()

        umidade = (
            float(resultado_umidade["valor"])
            if resultado_umidade else None
        )

        # HISTÓRICO DAS ÚLTIMAS 20 MEDIÇÕES

        cursor.execute("""
            SELECT
                s.tipo,
                m.valor,
                s.unidade_medida,
                DATE_FORMAT(
                    m.data_hora,
                    '%d/%m/%Y %H:%i:%s'
                ) AS data_hora
            FROM medicao m
            INNER JOIN sensor s
                ON m.idsensor = s.idsensor
            WHERE s.id_usuario_cadastro = %s
            ORDER BY m.data_hora DESC
            LIMIT 20
        """, (session["usuario_id"],))

        historico = cursor.fetchall()

        for item in historico:
            item["valor"] = float(item["valor"])

        return jsonify({
            "temperatura": temperatura,
            "umidade": umidade,
            "sensores_ativos": sensores_ativos,
            "historico": historico
        })

    except Exception as erro:
        print("Erro na API do dashboard:", erro)

        return jsonify({
            "erro": "Erro ao buscar dados do dashboard."
        }), 500

    finally:
        cursor.close()
        conexao.close()


# ==========================================
# STATUS DA CONEXÃO COM O BANCO
# ==========================================

@app.route("/api/status-banco")
def status_banco():

    conexao = conectar()

    if conexao is None:
        return jsonify({
            "status": "erro",
            "mensagem": "Não foi possível conectar ao MySQL."
        }), 500

    cursor = conexao.cursor()

    try:

        cursor.execute("SELECT DATABASE()")
        banco = cursor.fetchone()

        return jsonify({
            "status": "conectado",
            "banco": banco[0],
            "mensagem": "Conexão realizada com sucesso!"
        })

    except Exception as erro:
        print("Erro ao verificar banco:", erro)

        return jsonify({
            "status": "erro",
            "mensagem": "Erro ao verificar o banco de dados."
        }), 500

    finally:
        cursor.close()
        conexao.close()


# ==========================================
# LOGOUT
# ==========================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# ==========================================
# EXECUTAR APLICAÇÃO
# ==========================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
