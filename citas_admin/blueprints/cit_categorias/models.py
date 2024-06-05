"""
Cit Categorias, modelos
"""

from typing import List

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from citas_admin.extensions import database
from lib.universal_mixin import UniversalMixin


class CitCategoria(database.Model, UniversalMixin):
    """CitCategoria"""

    # Nombre de la tabla
    __tablename__ = "cit_categorias"

    # Clave primaria
    id: Mapped[int] = mapped_column(primary_key=True)

    # Columnas
    nombre: Mapped[str] = mapped_column(String(64), unique=True)

    # Hijos
    cit_servicios: Mapped[List["CitServicio"]] = relationship(back_populates="cit_categoria")

    def __repr__(self):
        """Representación"""
        return f"<CitCategoria {self.nombre}>"
