# Cada linha = um voo (chegada/partida) gravado naquela coleta (snapshot do scraping).

from . import db
from .base import ModeloBase


class VooInfo():
    """Model de um voo individual pertencente a uma ColetaVoo."""

    __bind_key__ = "historico"
    __tablename__ = "voos_info"

    coleta_id = db.Column(
        db.Integer,
        db.ForeignKey("coletas_voo.id"),
        nullable=False,
    )
    categoria = db.Column(db.String(40), nullable=False)
    identificacao = db.Column(db.String(40), nullable=False)
    tipo_aeronave = db.Column(db.String(40))
    local = db.Column(db.String(200))
    partida = db.Column(db.String(80))
    chegada = db.Column(db.String(80))

    coleta = db.relationship("ColetaVoo", back_populates="voos")

    def para_dict(self) -> dict:
        """Serializa este voo para dict/JSON (usado pela API e pelo detalhe da coleta)."""
        return {
            "id": self.id,
            "coleta_id": self.coleta_id,
            "categoria": self.categoria,
            "identificacao": self.identificacao,
            "tipo_aeronave": self.tipo_aeronave,
            "local": self.local,
            "partida": self.partida,
            "chegada": self.chegada,
            "data_criacao": str(self.data_criacao),
            "data_atualizacao": str(self.data_atualizacao),
        }
