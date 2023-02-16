"""
Tres de Tres - Partidos, modelos
"""
from citas_admin.extensions import db
from lib.universal_mixin import UniversalMixin


class TdtPartido(db.Model, UniversalMixin):
    """TdtPartido"""

    # Nombre de la tabla
    __tablename__ = "tdt_partidos"

    # Clave primaria
    id = db.Column(db.Integer, primary_key=True)

    # Columnas
    nombre = db.Column(db.String(256), unique=True, nullable=False)
    siglas = db.Column(db.String(24), unique=True, nullable=False)

    # Hijos
    tdt_solicitudes = db.relationship("TdtSolicitud", back_populates="tdt_partido")

    def __repr__(self):
        """Representación"""
        return f"<TdtPartido {self.siglas}>"
