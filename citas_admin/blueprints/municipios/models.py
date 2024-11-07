"""
Municipios, modelos
"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from citas_admin.extensions import database
from lib.universal_mixin import UniversalMixin


class Municipio(database.Model, UniversalMixin):
    """Municipio"""

    # Nombre de la tabla
    __tablename__ = "municipios"

    # Clave primaria
    id: Mapped[int] = mapped_column(primary_key=True)

    # Columnas
    nombre: Mapped[str] = mapped_column(String(256), unique=True)

    def __repr__(self):
        """Representación"""
        return f"<Municipio {self.nombre}>"
