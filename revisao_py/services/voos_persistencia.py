# Grava no banco o resultado de buscar_voos (cada sincronização = nova coleta).

from models import ColetaVoo, VooInfo, db
from services.flightaware import ResultadoBusca


def persistir_coleta(dados: ResultadoBusca) -> ColetaVoo:
    """
    Transforma o ResultadoBusca do scraping em registros no SQLite:
    cria uma ColetaVoo (cabeçalho) e vários VooInfo (voos daquela foto),
    faz commit e devolve a coleta salva.
    """
    coleta = ColetaVoo(
        fonte=dados["fonte"],
        aeroporto=dados["aeroporto"],
        tipo_busca=dados["tipo_busca"],
        total=dados["total"],
    )

    for item in dados["voos"]:
        coleta.voos.append(
            VooInfo(
                categoria=item["categoria"],
                identificacao=item["identificacao"],
                tipo_aeronave=item["tipo_aeronave"],
                local=item["local"],
                partida=item["partida"],
                chegada=item["chegada"],
            )
        )

    db.session.add(coleta)
    db.session.commit()
    return coleta
