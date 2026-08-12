# Uma "foto" de cada vez que o painel de voos foi consultado e salvo no histórico.
# Vive no segundo banco SQLite (bind historico) — ver app.py.

from . import db
from .base import ModeloBase


class ColetaVoo():
    """Model de uma sincronização/scraping salvo (cabeçalho da coleta)."""

    __bind_key__ = "historico"
    __tablename__ = "coletas_voo"

    fonte = db.Column(db.String(255), nullable=False)
    aeroporto = db.Column(db.String(10), nullable=False)
    tipo_busca = db.Column(db.String(20), nullable=False)
    total = db.Column(db.Integer, nullable=False, default=0)

    # relationship: uma coleta → vários voos (Aula 11, FK na filha).
    voos = db.relationship(
        "VooInfo",
        back_populates="coleta",
        cascade="all, delete-orphan",
    )

    @classmethod
    def listar(cls):
        """Devolve todas as coletas ordenadas da mais recente para a mais antiga."""
        return cls.query.order_by(cls.data_criacao.desc()).all()

    def para_dict(self, incluir_voos: bool = False) -> dict:
        """
        Serializa a coleta para dict/JSON.
        Se incluir_voos=True, também embute a lista de VooInfo dessa coleta.
        """
        dados = {
            "id": self.id,
            "fonte": self.fonte,
            "aeroporto": self.aeroporto,
            "tipo_busca": self.tipo_busca,
            "total": self.total,
            "data_criacao": str(self.data_criacao),
            "data_atualizacao": str(self.data_atualizacao),
        }
        if incluir_voos:
            dados["voos"] = [v.para_dict() for v in self.voos]
        return dados
