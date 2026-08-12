# Lê coletas já gravadas no banco historico (não chama o FlightAware de novo).

from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify

from models import ColetaVoo, db

historico_api_bp = ("historico_api", __name__, url_prefix="/api/historico")


@historico_api_bp.route("/coletas", methods=["GET"])
def listar_coletas() -> Any:
    """GET /api/historico/coletas — lista todas as coletas salvas em JSON (sem os voos)."""
    coletas = ColetaVoo.listar()
    return jsonify([c.para_dict() for c in coletas])


@historico_api_bp.route("/coletas/<int:coleta_id>", methods=["GET"])
def detalhe_coleta(coleta_id: int) -> Any:
    """GET /api/historico/coletas/<id> — detalhe de uma coleta, incluindo a lista de voos."""
    coleta = db.session.get(ColetaVoo, coleta_id)
    if not coleta:
        return jsonify({"erro": "Coleta não encontrada"}), 404
    return jsonify(coleta.para_dict(incluir_voos=True))
