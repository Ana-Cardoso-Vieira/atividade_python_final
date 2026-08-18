import os
import sqlite3
import requests
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "troque-esta-chave-em-producao-1234567890")
app.config["DEBUG"] = False

DATABASE = os.path.join(os.path.dirname(__file__), "database.db")


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS tarefas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            descricao TEXT,
            status TEXT NOT NULL DEFAULT 'pendente',
            usuario_id INTEGER NOT NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
        """
    )
    db.commit()
    db.close()


def query_db(query, args=(), one=False):
    db = get_db()
    cur = db.execute(query, args)
    rv = cur.fetchall()
    return (rv[0] if rv else None) if one else rv


def execute_db(query, args=()):
    db = get_db()
    cur = db.execute(query, args)
    db.commit()
    return cur.lastrowid


def login_requerido(view):
    from functools import wraps

    @wraps(view)
    def wrapped(*args, **kwargs):
        if "usuario_id" not in session:
            flash("Você precisa estar logado para acessar essa página.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


@app.context_processor
def inject_usuario():
    return {"usuario_logado": session.get("usuario_nome")}


@app.route("/")
def index():
    if "usuario_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")

        if not nome or not email or not senha:
            flash("Preencha todos os campos.", "danger")
            return render_template("registro.html")

        if len(senha) < 4:
            flash("A senha deve ter pelo menos 4 caracteres.", "danger")
            return render_template("registro.html")

        existente = query_db("SELECT id FROM usuarios WHERE email = ?", (email,), one=True)
        if existente:
            flash("Já existe uma conta com esse e-mail.", "danger")
            return render_template("registro.html")

        senha_hash = generate_password_hash(senha)
        execute_db(
            "INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
            (nome, email, senha_hash),
        )
        flash("Conta criada com sucesso! Faça login.", "success")
        return redirect(url_for("login"))

    return render_template("registro.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")

        usuario = query_db("SELECT * FROM usuarios WHERE email = ?", (email,), one=True)

        if usuario and check_password_hash(usuario["senha"], senha):
            session.clear()
            session["usuario_id"] = usuario["id"]
            session["usuario_nome"] = usuario["nome"]
            flash(f"Bem-vindo, {usuario['nome']}!", "success")
            return redirect(url_for("dashboard"))

        flash("E-mail ou senha inválidos.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Você saiu da sua conta.", "info")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_requerido
def dashboard():
    status_filtro = request.args.get("status", "todas")

    if status_filtro in ("pendente", "em_andamento", "concluida"):
        tarefas = query_db(
            "SELECT * FROM tarefas WHERE usuario_id = ? AND status = ? ORDER BY id DESC",
            (session["usuario_id"], status_filtro),
        )
    else:
        tarefas = query_db(
            "SELECT * FROM tarefas WHERE usuario_id = ? ORDER BY id DESC",
            (session["usuario_id"],),
        )

    frase = None
    try:
        resposta = requests.get("https://api.adviceslip.com/advice", timeout=3)
        if resposta.ok:
            frase = resposta.json().get("slip", {}).get("advice")
    except requests.RequestException:
        frase = None

    if not frase:
        frase = "Continue firme: cada tarefa concluída é um passo à frente."

    return render_template(
        "dashboard.html", tarefas=tarefas, frase=frase, status_filtro=status_filtro
    )


@app.route("/tarefas/status/<status>")
@login_requerido
def tarefas_por_status_json(status):
    if status == "todas":
        tarefas = query_db(
            "SELECT * FROM tarefas WHERE usuario_id = ? ORDER BY id DESC",
            (session["usuario_id"],),
        )
    else:
        tarefas = query_db(
            "SELECT * FROM tarefas WHERE usuario_id = ? AND status = ? ORDER BY id DESC",
            (session["usuario_id"], status),
        )

    return jsonify(
        [
            {
                "id": t["id"],
                "titulo": t["titulo"],
                "descricao": t["descricao"],
                "status": t["status"],
            }
            for t in tarefas
        ]
    )


@app.route("/nova_tarefa", methods=["GET", "POST"])
@login_requerido
def nova_tarefa():
    if request.method == "POST":
        titulo = request.form.get("titulo", "").strip()
        descricao = request.form.get("descricao", "").strip()
        status = request.form.get("status", "pendente")

        if not titulo:
            flash("O título da tarefa é obrigatório.", "danger")
            return render_template("form_tarefa.html", tarefa=None)

        if status not in ("pendente", "em_andamento", "concluida"):
            status = "pendente"

        execute_db(
            "INSERT INTO tarefas (titulo, descricao, status, usuario_id) VALUES (?, ?, ?, ?)",
            (titulo, descricao, status, session["usuario_id"]),
        )
        flash("Tarefa criada com sucesso!", "success")
        return redirect(url_for("dashboard"))

    return render_template("form_tarefa.html", tarefa=None)


@app.route("/editar/<int:id>", methods=["GET", "POST"])
@login_requerido
def editar_tarefa(id):
    tarefa = query_db(
        "SELECT * FROM tarefas WHERE id = ? AND usuario_id = ?",
        (id, session["usuario_id"]),
        one=True,
    )
    if tarefa is None:
        flash("Tarefa não encontrada.", "danger")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        titulo = request.form.get("titulo", "").strip()
        descricao = request.form.get("descricao", "").strip()
        status = request.form.get("status", "pendente")

        if not titulo:
            flash("O título da tarefa é obrigatório.", "danger")
            return render_template("form_tarefa.html", tarefa=tarefa)

        if status not in ("pendente", "em_andamento", "concluida"):
            status = "pendente"

        execute_db(
            "UPDATE tarefas SET titulo = ?, descricao = ?, status = ? WHERE id = ? AND usuario_id = ?",
            (titulo, descricao, status, id, session["usuario_id"]),
        )
        flash("Tarefa atualizada com sucesso!", "success")
        return redirect(url_for("dashboard"))

    return render_template("form_tarefa.html", tarefa=tarefa)


@app.route("/excluir/<int:id>", methods=["POST"])
@login_requerido
def excluir_tarefa(id):
    execute_db(
        "DELETE FROM tarefas WHERE id = ? AND usuario_id = ?",
        (id, session["usuario_id"]),
    )
    flash("Tarefa excluída.", "info")
    return redirect(url_for("dashboard"))


@app.route("/progresso")
@login_requerido
def progresso():
    return render_template("progresso.html")


@app.route("/api/progresso")
@login_requerido
def api_progresso():
    linhas = query_db(
        "SELECT status, COUNT(*) as total FROM tarefas WHERE usuario_id = ? GROUP BY status",
        (session["usuario_id"],),
    )
    dados = {"pendente": 0, "em_andamento": 0, "concluida": 0}
    for linha in linhas:
        dados[linha["status"]] = linha["total"]
    return jsonify(dados)


@app.route("/api/tarefas", methods=["GET"])
@login_requerido
def api_listar_tarefas():
    tarefas = query_db(
        "SELECT * FROM tarefas WHERE usuario_id = ? ORDER BY id DESC",
        (session["usuario_id"],),
    )
    return jsonify([dict(t) for t in tarefas])


@app.route("/api/tarefas", methods=["POST"])
@login_requerido
def api_criar_tarefa():
    dados = request.get_json(silent=True) or {}
    titulo = (dados.get("titulo") or "").strip()
    descricao = (dados.get("descricao") or "").strip()
    status = dados.get("status", "pendente")

    if not titulo:
        return jsonify({"erro": "O título é obrigatório."}), 400
    if status not in ("pendente", "em_andamento", "concluida"):
        status = "pendente"

    novo_id = execute_db(
        "INSERT INTO tarefas (titulo, descricao, status, usuario_id) VALUES (?, ?, ?, ?)",
        (titulo, descricao, status, session["usuario_id"]),
    )
    tarefa = query_db("SELECT * FROM tarefas WHERE id = ?", (novo_id,), one=True)
    return jsonify(dict(tarefa)), 201


@app.route("/api/tarefas/<int:id>", methods=["PUT"])
@login_requerido
def api_atualizar_tarefa(id):
    tarefa = query_db(
        "SELECT * FROM tarefas WHERE id = ? AND usuario_id = ?",
        (id, session["usuario_id"]),
        one=True,
    )
    if tarefa is None:
        return jsonify({"erro": "Tarefa não encontrada."}), 404

    dados = request.get_json(silent=True) or {}
    titulo = (dados.get("titulo") or tarefa["titulo"]).strip()
    descricao = dados.get("descricao", tarefa["descricao"])
    status = dados.get("status", tarefa["status"])
    if status not in ("pendente", "em_andamento", "concluida"):
        status = tarefa["status"]

    execute_db(
        "UPDATE tarefas SET titulo = ?, descricao = ?, status = ? WHERE id = ? AND usuario_id = ?",
        (titulo, descricao, status, id, session["usuario_id"]),
    )
    tarefa_atualizada = query_db("SELECT * FROM tarefas WHERE id = ?", (id,), one=True)
    return jsonify(dict(tarefa_atualizada))


@app.route("/api/tarefas/<int:id>", methods=["DELETE"])
@login_requerido
def api_excluir_tarefa(id):
    tarefa = query_db(
        "SELECT * FROM tarefas WHERE id = ? AND usuario_id = ?",
        (id, session["usuario_id"]),
        one=True,
    )
    if tarefa is None:
        return jsonify({"erro": "Tarefa não encontrada."}), 404

    execute_db("DELETE FROM tarefas WHERE id = ? AND usuario_id = ?", (id, session["usuario_id"]))
    return jsonify({"mensagem": "Tarefa excluída com sucesso."})


@app.route("/rest")
@login_requerido
def rest_demo():
    return render_template("rest.html")


if __name__ == "__main__":
    init_db()
    app.run(debug=False)
else:
    init_db()
