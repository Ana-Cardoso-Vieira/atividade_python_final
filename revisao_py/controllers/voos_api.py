# Rotas da API ao vivo (FlightAware) + sincronização que grava no historico_voos.db

from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify, request

from services import buscar_voos, persistir_coleta

voos_api_bp = Blueprint ("voos_api", __name__, url_prefix="/api")


def _validar_params() -> tuple[str, str] | tuple[Any, int]:
    """
    Lê e valida query params aeroporto e tipo da requisição.
    Sucesso → retorna (aeroporto, tipo).
    Erro → retorna (jsonify(...), status_http) para a rota devolver direto.
    """
    aeroporto: str = request.args.get("aeroporto", "SBGR").strip().upper()
    tipo: str = request.args.get("tipo", "todos").strip().lower()

    if len(aeroporto) != 4 or not aeroporto.isalpha():
        return jsonify(
            {"erro": "Parâmetro aeroporto deve ser ICAO de 4 letras (ex.: SBGR, SBSP)"}
        ), 400
    if tipo not in ("chegadas", "partidas", "todos"):
        return jsonify(
            {"erro": "Parâmetro tipo deve ser 'chegadas', 'partidas' ou 'todos'"}
        ), 400
    return aeroporto, tipo


@voos_api_bp.route("/voos", methods=[""])
def listar_voos() -> Any:
    """GET /api/voos — scraping ao vivo no FlightAware e responde JSON (não grava no banco)."""
    params = _validar_params()
    if isinstance(params[0], str) is False:
        return params

    aeroporto, tipo = params  # type: ignore[misc]
    try:
        dados = buscar_voos(aeroporto=aeroporto, tipo=tipo)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    except ConnectionError as erro:
        return jsonify({"erro": str(erro)}), 502

    return jsonify(dados)


@voos_api_bp.route("/voos/sincronizar", methods=[""])
def sincronizar_voos() -> Any:
    """
    POST /api/voos/sincronizar — faz o scraping e grava ColetaVoo + VooInfo
    no historico_voos.db. Cada POST = uma nova "foto" persistida.
    """
    params = _validar_params()
    if isinstance(params[0], str) is False:
        return params

    aeroporto, tipo = params  # type: ignore[misc]
    try:
        dados = buscar_voos(aeroporto=aeroporto, tipo=tipo)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    except ConnectionError as erro:
        return jsonify({"erro": str(erro)}), 502

    coleta = persistir_coleta(dados)

    return jsonify(
        {
            "mensagem": "Coleta gravada no historico_voos.db",
            "coleta_id": coleta.id,
            "dados_api": dados,
        }
    ), 201
