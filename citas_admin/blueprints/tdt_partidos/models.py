"""
Tres de Tres - Partidos, modelos
"""

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from lib.universal_mixin import UniversalMixin
from citas_admin.extensions import database


class TdtPartido(database.Model, UniversalMixin):
    """TdtPartido"""

    # Nombre de la tabla
    __tablename__ = "tdt_partidos"

    # Clave primaria
    id = Column(Integer, primary_key=True)

    # Columnas
    nombre = Column(String(256), unique=True, nullable=False)
    siglas = Column(String(24), unique=True, nullable=False)

    # Hijos
    tdt_solicitudes = relationship("TdtSolicitud", back_populates="tdt_partido")

    def __repr__(self):
        """Representación"""
        return f"<TdtPartido {self.siglas}>"
