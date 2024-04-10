"""
Encuesta Servicios, modelos
"""

from sqlalchemy import Column, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from lib.universal_mixin import UniversalMixin
from citas_admin.extensions import database


class EncServicio(database.Model, UniversalMixin):
    """Encuesta del Servicio"""

    ESTADOS = {
        "PENDIENTE": "Pendiente",
        "CANCELADO": "Cancelado",
        "CONTESTADO": "Contestado",
    }

    # Nombre de la tabla
    __tablename__ = "enc_servicios"

    # Clave primaria
    id = Column(Integer, primary_key=True)

    # Clave foránea
    cit_cliente_id = Column(Integer, ForeignKey("cit_clientes.id"), nullable=False)
    cit_cliente = relationship("CitCliente", back_populates="enc_servicios")
    oficina_id = Column(Integer, ForeignKey("oficinas.id"), nullable=False)
    oficina = relationship("Oficina", back_populates="enc_servicios")

    # Columnas
    respuesta_01 = Column(Integer(), nullable=True)
    respuesta_02 = Column(Integer(), nullable=True)
    respuesta_03 = Column(Integer(), nullable=True)
    respuesta_04 = Column(String(512), nullable=True)
    estado = Column(Enum(*ESTADOS, name="estados", native_enum=False))

    def __repr__(self):
        """Representación"""
        return f"<Encuesta_Servicio {self.id}>"
