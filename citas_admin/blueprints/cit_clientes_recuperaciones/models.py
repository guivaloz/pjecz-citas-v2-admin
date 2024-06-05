"""
Cit Clientes Recuperaciones, modelos
"""

from datetime import datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from citas_admin.extensions import database
from lib.universal_mixin import UniversalMixin


class CitClienteRecuperacion(database.Model, UniversalMixin):
    """CitClienteRecuperacion"""

    # Nombre de la tabla
    __tablename__ = "cit_clientes_recuperaciones"

    # Clave primaria
    id: Mapped[int] = mapped_column(primary_key=True)

    # Clave foránea
    cit_cliente_id: Mapped[int] = mapped_column(ForeignKey("cit_clientes.id"))
    cit_cliente: Mapped["CitCliente"] = relationship(back_populates="cit_clientes_recuperaciones")

    # Columnas
    expiracion: Mapped[datetime]
    cadena_validar: Mapped[str] = mapped_column(String(256))
    mensajes_cantidad: Mapped[int] = mapped_column(default=0)
    ya_recuperado: Mapped[bool] = mapped_column(default=False)

    def __repr__(self):
        """Representación"""
        return f"<CitClienteRecuperacion {self.id}>"
