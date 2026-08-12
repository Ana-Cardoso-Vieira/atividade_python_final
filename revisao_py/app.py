# Aula 19 — Webscraping de voos (padrão da Aula 17 GE + histórico SQLite).
#
# Banco 1 (principal.db): reservado / bind padrão do Flask-SQLAlchemy (vazio nesta aula).
# Banco 2 (historico_voos.db): ColetaVoo + VooInfo — histórico de cada sincronização.
#
# Front: RaspaVoo (render_template) + API JSON em /api/*

import os

from flask import Flask, jsonify

from controllers import historico_api_bp, site_bp, voos_api_bp
from models import db

ENDPOINTS: list[dict[str, str]] = [
    {
        "metodo": "GET",
        "rota": "/api/voos",
        "descricao": "Webscraping ao vivo no FlightAware (não grava)",
        "query": "?aeroporto=SBGR&tipo=chegadas|partidas|todos",
    },
    {
        "metodo": "POST",
        "rota": "/api/voos/sincronizar",
        "descricao": "Scraping + grava coleta no historico_voos.db",
        "query": "?aeroporto=SBGR&tipo=chegadas|partidas|todos",
    },
    {
        "metodo": "GET",
        "rota": "/api/historico/coletas",
        "descricao": "Lista coletas gravadas",
    },
    {
        "metodo": "GET",
        "rota": "/api/historico/coletas/<id>",
        "descricao": "Detalhe de uma coleta com voos",
    },
]


def criar_app() -> Flask:
    """
    Monta a aplicação Flask: pastas de template/static, dois bancos SQLite,
    registra blueprints do site e da API, cria tabelas e devolve o app pronto.
    """
    app = Flask(
        __name__,
        template_folder="views/templates",
        static_folder="views/static",
    )
    pasta = os.path.abspath(os.path.dirname(__file__))

    # Dois bancos SQLite na pasta do projeto (ver models: __bind_key__ = "historico").
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
        pasta, "principal.db"
    )
    app.config["SQLALCHEMY_BINDS"] = {
        "historico": "sqlite:///" + os.path.join(pasta, "historico_voos.db"),
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "aula19-webscraping-voos-dev"

    db.init_app(app)
    app.register_blueprint(site_bp)
    app.register_blueprint(voos_api_bp)
    app.register_blueprint(historico_api_bp)

    with app.app_context():
        db.create_all()

    @app.route("/api")
    def api_index():
        """GET /api — índice JSON com a lista de endpoints da API (documentação rápida)."""
        return jsonify(
            {
                "aula": "19 — RaspaVoo · webscraping de voos + histórico",
                "site": "/",
                "fonte": "https://www.flightaware.com/live/airport/{ICAO}",
                "bancos": {
                    "principal": "principal.db (bind padrão)",
                    "historico": "historico_voos.db (coletas do scraping)",
                },
                "endpoints": ENDPOINTS,
            }
        )

    return app


app = criar_app()

if __name__ == "__main__":
    # Sobe o servidor de desenvolvimento (debug=True recarrega ao salvar arquivos).
    app.run(debug=True)
