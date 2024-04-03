"""
Distritos
"""

from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

from lib.universal_mixin import UniversalMixin
from citas_admin.extensions import database


class Distrito(database.Model, UniversalMixin):
    """Distrito"""

    # Nombre de la tabla
    __tablename__ = "distritos"

    # Clave primaria
    id = Column(Integer, primary_key=True)

    # Columnas
    clave = Column(String(16), nullable=False, unique=True)
    nombre = Column(String(256), unique=True, nullable=False)
    nombre_corto = Column(String(64), nullable=False, default="", server_default="")
    es_distrito_judicial = Column(Boolean, nullable=False, default=False)
    es_distrito = Column(Boolean, nullable=False, default=False)
    es_jurisdiccional = Column(Boolean, nullable=False, default=False)

    # Hijos
    autoridades = relationship("Autoridad", back_populates="distrito")
    # oficinas = relationship("Oficina", back_populates="distrito")
    # pag_pagos = relationship("PagPago", back_populates="distrito")

    def __repr__(self):
        """Representación"""
        return f"<Distrito {self.clave}>"
