"""
Cit Dias Inhabiles, modelos
"""

from sqlalchemy import Column, Date, Integer, String

from lib.universal_mixin import UniversalMixin

from citas_admin.extensions import database


class CitDiaInhabil(database.Model, UniversalMixin):
    """CitDiaInhabil"""

    # Nombre de la tabla
    __tablename__ = "cit_dias_inhabiles"

    # Clave primaria
    id = Column(Integer, primary_key=True)

    # Columnas
    fecha = Column(Date, unique=True, nullable=False)
    descripcion = Column(String(256), nullable=False)

    def __repr__(self):
        """Representación"""
        return f"<CitDiaInhabil {self.fecha}>"
