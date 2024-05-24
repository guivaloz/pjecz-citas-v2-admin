"""
Municipios, modelos
"""

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from lib.universal_mixin import UniversalMixin

from citas_admin.extensions import database


class Municipio(database.Model, UniversalMixin):
    """Municipio"""

    # Nombre de la tabla
    __tablename__ = "municipios"

    # Clave primaria
    id = Column(Integer, primary_key=True)

    # Columnas
    nombre = Column(String(256), unique=True, nullable=False)

    # Hijos
    tdt_solicitudes = relationship("TdtSolicitud", back_populates="municipio")

    def __repr__(self):
        """Representación"""
        return f"<Municipio {self.id}>"
