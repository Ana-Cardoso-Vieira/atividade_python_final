# Service de webscraping — painel ao vivo de voos no FlightAware (HTML + BeautifulSoup).
# Espelha a Aula 17 (ge_globo.py): requests → BeautifulSoup → lista estruturada.

from __future__ import annotations

import re
from typing import TypedDict

import requests
from bs4 import BeautifulSoup

URL_BASE: str = "https://www.flightaware.com/live/airport/"
TIMEOUT: int = 20
USER_AGENT: str = "Mozilla/5.0 (compatible; TecTI-Aula19/1.0; +aula-educacional)"

# ICAO: 4 letras (ex.: SBGR, SBSP, SBBR).
REGEX_ICAO: re.Pattern[str] = re.compile(r"^[A-Z]{4}$")

TIPOS_VALIDOS: frozenset[str] = frozenset({"chegadas", "partidas", "todos"})

# Mapeia título da tabela do FlightAware → categoria + filtro de tipo.
MAPA_CATEGORIA: dict[str, tuple[str, str]] = {
    "arrivals": ("chegadas", "chegadas"),
    "departures": ("partidas", "partidas"),
    "en route": ("em_rota", "chegadas"),
    "scheduled to": ("em_rota", "chegadas"),
    "scheduled departures": ("partidas_programadas", "partidas"),
}


class Voo(TypedDict):
    """Estrutura de um voo extraído do HTML (um item da lista)."""

    categoria: str
    identificacao: str
    tipo_aeronave: str | None
    local: str | None
    partida: str | None
    chegada: str | None


class ResultadoBusca(TypedDict):
    """Pacote completo devolvido pelo scraping (metadados + lista de voos)."""

    fonte: str
    aeroporto: str
    tipo_busca: str
    total: int
    voos: list[Voo]


def _normalizar_aeroporto(codigo: str) -> str:
    """Remove espaços e deixa o código ICAO em maiúsculas (ex.: 'sbgr' → 'SBGR')."""
    return codigo.strip().upper()


def _categoria_da_tabela(titulo: str) -> tuple[str, str] | None:
    """
    Lê o título da tabela do FlightAware e devolve:
    - categoria em português (ex.: 'chegadas')
    - filtro usado na query (?tipo=chegadas|partidas)
    Retorna None se o título não for reconhecido.
    """
    titulo_l = titulo.lower()
    for chave, valor in MAPA_CATEGORIA.items():
        if chave in titulo_l:
            return valor
    return None


def _celulas_uteis(row) -> list[str]:
    """Extrai o texto de todas as células (th/td) de uma linha da tabela HTML."""
    return [c.get_text(" ", strip=True) for c in row.find_all(["th", "td"])]


def _linha_para_voo(cols: list[str], categoria: str) -> Voo | None:
    """
    Converte uma linha da tabela (lista de textos) em um dicionário Voo.
    Ignora cabeçalhos e linhas inválidas; retorna None nesses casos.
    Colunas típicas: Ident | Type | From/To | Depart | (vazio) | Arrive
    """
    if len(cols) < 4:
        return None
    identificacao = cols[0].strip()
    if not identificacao or identificacao.lower() in ("ident", "arrivals", "departures"):
        return None
    if identificacao.lower().startswith("arrivals") or identificacao.lower().startswith(
        "departures"
    ):
        return None
    if identificacao.lower().startswith("en route") or identificacao.lower().startswith(
        "scheduled"
    ):
        return None

    tipo_aeronave = cols[1].strip() or None
    local = cols[2].strip() or None
    partida = cols[3].strip() or None
    chegada = cols[5].strip() if len(cols) > 5 else (cols[4].strip() if len(cols) > 4 else None)
    if chegada == "":
        chegada = None

    return Voo(
        categoria=categoria,
        identificacao=identificacao,
        tipo_aeronave=tipo_aeronave,
        local=local,
        partida=partida,
        chegada=chegada,
    )


def buscar_voos(aeroporto: str = "SBGR", tipo: str = "todos") -> ResultadoBusca:
    """
    Função principal do scraping:
    1) baixa a página do aeroporto no FlightAware
    2) percorre as tabelas airportBoard com BeautifulSoup
    3) devolve um ResultadoBusca com a lista de voos (sem gravar no banco)
    """
    codigo = _normalizar_aeroporto(aeroporto)
    if not REGEX_ICAO.match(codigo):
        raise ValueError("Aeroporto deve ser um código ICAO de 4 letras (ex.: SBGR).")

    tipo_n = tipo.strip().lower()
    if tipo_n not in TIPOS_VALIDOS:
        raise ValueError("Parâmetro tipo deve ser 'chegadas', 'partidas' ou 'todos'.")

    url = URL_BASE + codigo
    try:
        resposta: requests.Response = requests.get(
            url,
            timeout=TIMEOUT,
            headers={"User-Agent": USER_AGENT},
        )
        resposta.raise_for_status()
    except requests.RequestException as erro:
        raise ConnectionError(f"Não foi possível acessar o FlightAware: {erro}") from erro

    resposta.encoding = resposta.apparent_encoding or "utf-8"
    soup = BeautifulSoup(resposta.text, "html.parser")

    vistos: set[tuple[str, str, str | None]] = set()
    voos: list[Voo] = []

    for tabela in soup.find_all("table", class_="airportBoard"):
        titulo = ""
        primeira = tabela.find("tr")
        if primeira:
            titulo = primeira.get_text(" ", strip=True)

        mapeado = _categoria_da_tabela(titulo)
        if not mapeado:
            continue
        categoria, filtro = mapeado
        if tipo_n != "todos" and filtro != tipo_n:
            continue

        for row in tabela.find_all("tr"):
            cols = _celulas_uteis(row)
            voo = _linha_para_voo(cols, categoria)
            if not voo:
                continue
            chave = (voo["categoria"], voo["identificacao"], voo["local"])
            if chave in vistos:
                continue
            vistos.add(chave)
            voos.append(voo)

    return ResultadoBusca(
        fonte=url,
        aeroporto=codigo,
        tipo_busca=tipo_n,
        total=len(voos),
        voos=voos,
    )
