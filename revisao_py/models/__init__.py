from flask_sqlalchemy import SQLAlchemy

# Um único objeto db para a aplicação; os Models escolhem o arquivo SQLite com __bind_key__.
db = SQLAlchemy()

from .base import ModeloBase
from .coleta_voo import ColetaVoo
from .voo_info import VooInfo

__all__ = ["db", "ModeloBase", "ColetaVoo", "VooInfo"]
