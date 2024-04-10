"""
Pagos Tramites Servicios, modelos
"""

from sqlalchemy import Column, Integer, Numeric, String
from sqlalchemy.orm import relationship

from lib.universal_mixin import UniversalMixin
from citas_admin.extensions import database


class PagTramiteServicio(database.Model, UniversalMixin):
    """PagTramiteServicio"""

    # Nombre de la tabla
    __tablename__ = "pag_tramites_servicios"

    # Clave primaria
    id = Column(Integer, primary_key=True)

    # Columnas
    clave = Column(String(16), nullable=False, unique=True)
    descripcion = Column(String(256), nullable=False)
    costo = Column(Numeric(precision=8, scale=2, decimal_return_scale=2), nullable=False)
    url = Column(String(256), nullable=False)

    # Hijos
    pag_pagos = relationship("PagPago", back_populates="pag_tramite_servicio")

    def __repr__(self):
        """Representación"""
        return f"<PagTramiteServicio> {self.id}"
