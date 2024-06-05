"""
Cit Servicios, modelos
"""

from datetime import time
from typing import List

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from citas_admin.extensions import database
from lib.universal_mixin import UniversalMixin


class CitServicio(database.Model, UniversalMixin):
    """CitServicio"""

    # Nombre de la tabla
    __tablename__ = "cit_servicios"

    # Clave primaria
    id: Mapped[int] = mapped_column(primary_key=True)

    # Clave foránea
    cit_categoria_id: Mapped[int] = mapped_column(ForeignKey("cit_categorias.id"))
    cit_categoria: Mapped["CitCategoria"] = relationship("CitCategoria", back_populates="cit_servicios")

    # Columnas
    clave: Mapped[str] = mapped_column(String(32), unique=True)
    descripcion: Mapped[str] = mapped_column(String(64))
    duracion: Mapped[time]
    documentos_limite: Mapped[int]
    desde: Mapped[time]
    hasta: Mapped[time]
    dias_habilitados: Mapped[str] = mapped_column(String(7))

    # Hijos
    cit_citas: Mapped[List["CitCita"]] = relationship(back_populates="cit_servicio")
    cit_oficinas_servicios: Mapped[List["CitOficinaServicio"]] = relationship(back_populates="cit_servicio")

    def __repr__(self):
        """Representación"""
        return f"<CitServicio {self.clave}>"
