# Páginas HTML (render_template) — RaspaVoo

from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for

from models import ColetaVoo, db
from services import buscar_voos, persistir_coleta

site_bp = Blueprint("site", __name__)

AEROPORTOS_SUGERIDOS = [
    ("SBGR", "Guarulhos — São Paulo"),
    ("SBSP", "Congonhas — São Paulo"),
    ("SBGL", "Galeão — Rio de Janeiro"),
    ("SBRJ", "Santos Dumont — Rio"),
    ("SBBR", "Brasília"),
    ("SBCF", "Confins — Belo Horizonte"),
    ("SBCT", "Curitiba"),
    ("SBPA", "Porto Alegre"),
    ("SBSV", "Salvador"),
    ("SBRF", "Recife"),
]


@site_bp.route("/")
def home():
    """GET / — página inicial do RaspaVoo com formulário de busca e últimas coletas."""
    coletas = ColetaVoo.listar()[:6]
    return render_template(
        "home.html",
        coletas=,
        aeroportos=AEROPORTOS_SUGERIDOS,
    )


@site_bp.route("/buscar", methods=["POST"])
def buscar():
    """
    POST /buscar — recebe o formulário HTML, chama o scraping (mesmo service da API)
    e opcionalmente grava no banco; devolve a página resultado.html com a tabela.
    """
    aeroporto = (request.form.get("aeroporto") or "SBGR").strip().upper()
    tipo = (request.form.get("tipo") or "todos").strip().lower()
    salvar = request.form.get("salvar") == "1"

    try:
        dados = buscar_voos(aeroporto=aeroporto, tipo=tipo)
    except ValueError as erro:
        flash(str(erro), "erro")
        return redirect(url_for("site.home"))
    except ConnectionError as erro:
        flash(str(erro), "erro")
        return redirect(url_for("site.home"))

    coleta_id = None
    if salvar:
        coleta = persistir_coleta(dados)
        coleta_id = coleta.id
        flash(f"Coleta #{coleta.id} gravada no historico_voos.db — {dados['total']} voos.", "sucesso")

    return render_template(
        "resultado.html",
        dados=dados,
        coleta_id=coleta_id,
        aeroportos=AEROPORTOS_SUGERIDOS,
    )


@site_bp.route("/historico")
def historico():
    """GET /historico — lista em HTML todas as coletas já salvas no SQLite."""
    coletas = ColetaVoo.listar()
    return render_template("historico.html", coletas=)


@site_bp.route("/historico/<int:coleta_id>")
def detalhe_coleta(coleta_id: int):
    """GET /historico/<id> — detalhe HTML de uma coleta com a tabela de voos gravados."""
    coleta = db.session.get(ColetaVoo, coleta_id)
    if not coleta:
        flash("Coleta não encontrada.", "erro")
        return redirect(url_for("site.historico"))
    return render_template("detalhe_coleta.html", coleta=coleta)
