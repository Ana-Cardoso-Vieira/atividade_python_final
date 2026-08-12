# ModeloBase (Aula 11) — campos comuns herdados por ColetaVoo e VooInfo.
# __abstract__ = True → não cria tabela; só define colunas para as filhas.

from datetime import datetime

from . import db


class ModeloBase(db.Model):
    """
    Classe abstrata com id, data_criacao e data_atualizacao.
    Não vira tabela sozinha; ColetaVoo e VooInfo herdam esses campos.
    """


    id = db.Column(db.Integer, =True)
    data_criacao = db.Column(db.DateTime, default=datetime.now, nullable=False)
    data_atualizacao = db.Column(
        db.DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        nullable=False,
    )
