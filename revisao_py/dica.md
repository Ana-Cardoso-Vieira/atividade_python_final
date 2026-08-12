A ponte principal é o site_controller.py — o HTML não chama a API JSON; o formulário cai no controller, que usa o mesmo service do back.

1. App registra o front e o back juntos

app.py
Lines 42-62
def criar_app() -> Flask:
    app = Flask(
        __name__,
        template_folder="views/templates",
        static_folder="views/static",
    )
    # ...
    app.register_blueprint(site_bp)          # ← front (HTML)
    app.register_blueprint(voos_api_bp)      # ← API JSON
    app.register_blueprint(historico_api_bp)
2. Form do HTML aponta para a rota do controller

home.html
Lines 35-35
<form method="post" action="{{ url_for('site.buscar') }}" class="form-busca">
3. Controller liga front ↔ service (back)

site_controller.py
Lines 36-62
@site_bp.route("/buscar", methods=["POST"])
def buscar():
    aeroporto = (request.form.get("aeroporto") or "SBGR").strip().upper()
    # ...
    dados = buscar_voos(aeroporto=aeroporto, tipo=tipo)   # ← mesmo service da API
    if salvar:
        coleta = persistir_coleta(dados)                  # ← grava no SQLite
    return render_template("resultado.html", dados=dados, ...)  # ← devolve HTML
Fluxo resumido:

HTML form → POST /buscar → buscar_voos() / persistir_coleta() → render_template(...)

A API (/api/voos) usa os mesmos services, só que devolve jsonify em vez de template. O front e a API não se falam entre si; os dois consomem o back (services + models).