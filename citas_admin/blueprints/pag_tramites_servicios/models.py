"""
Pag Tramites Servicios, modelos
"""

from typing import List

from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from citas_admin.extensions import database
from lib.universal_mixin import UniversalMixin


class PagTramiteServicio(database.Model, UniversalMixin):
    """PagTramiteServicio"""

    # Nombre de la tabla
    __tablename__ = "pag_tramites_servicios"

    # Clave primaria
    id: Mapped[int] = mapped_column(primary_key=True)

    # Columnas
    clave: Mapped[str] = mapped_column(String(16), unique=True)
    descripcion: Mapped[str] = mapped_column(String(256))
    costo: Mapped[float] = mapped_column(Numeric(precision=8, scale=2, decimal_return_scale=2))
    url: Mapped[str] = mapped_column(String(256))

    # Hijos
    pag_pagos: Mapped[List["PagPago"]] = relationship("PagPago", back_populates="pag_tramite_servicio")

    def __repr__(self):
        """Representación"""
        return f"<PagTramiteServicio {self.clave}>"
