"""
Domicilios, modelos
"""

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from lib.universal_mixin import UniversalMixin

from citas_admin.extensions import database


class Domicilio(database.Model, UniversalMixin):
    """Domicilio"""

    # Nombre de la tabla
    __tablename__ = "domicilios"

    # Clave primaria
    id = Column(Integer, primary_key=True)

    # Clave foránea
    distrito_id = Column(Integer, ForeignKey("distritos.id"), index=True, nullable=False)
    distrito = relationship("Distrito", back_populates="domicilios")

    # Columnas
    edificio = Column(String(64), nullable=False, unique=True)
    estado = Column(String(64), nullable=False)
    municipio = Column(String(64), nullable=False)
    calle = Column(String(256), nullable=False)
    num_ext = Column(String(24), nullable=False)
    num_int = Column(String(24), nullable=False)
    colonia = Column(String(256), nullable=False)
    cp = Column(Integer(), nullable=False)
    completo = Column(String(1024), nullable=False)

    # Hijos
    # oficinas = relationship("Oficina", back_populates="domicilio")

    def __repr__(self):
        """Representación"""
        return f"<Domicilio {self.id}>"
