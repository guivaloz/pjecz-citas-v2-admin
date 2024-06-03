"""
Cit Clientes Recuperaciones, modelos
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from lib.universal_mixin import UniversalMixin

from citas_admin.extensions import database


class CitClienteRecuperacion(database.Model, UniversalMixin):
    """CitClienteRecuperacion"""

    # Nombre de la tabla
    __tablename__ = "cit_clientes_recuperaciones"

    # Clave primaria
    id = Column(Integer, primary_key=True)

    # Clave foránea
    cit_cliente_id = Column(Integer, ForeignKey("cit_clientes.id"), index=True, nullable=False)
    cit_cliente = relationship("CitCliente", back_populates="cit_clientes_recuperaciones")

    # Columnas
    expiracion = Column(DateTime, nullable=False)
    cadena_validar = Column(String(256), nullable=False)
    mensajes_cantidad = Column(Integer, nullable=False, default=0)
    ya_recuperado = Column(Boolean, nullable=False, default=False)

    def __repr__(self):
        """Representación"""
        return f"<CitClienteRecuperacion {self.id}>"
