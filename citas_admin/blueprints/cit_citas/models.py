"""
Cit Citas, modelos
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from lib.universal_mixin import UniversalMixin
from citas_admin.extensions import database

import pytz

from citas_admin.extensions import database
from lib.universal_mixin import UniversalMixin


class CitCita(database.Model, UniversalMixin):
    """CitCita"""

    ESTADOS = {
        "ASISTIO": "Asistió",
        "CANCELO": "Canceló",
        "INASISTENCIA": "Inasistencia",
        "PENDIENTE": "Pendiente",
    }

    # Nombre de la tabla
    __tablename__ = "cit_citas"

    # Clave primaria
    id = Column(Integer, primary_key=True)

    # Claves foráneas
    cit_cliente_id = Column(Integer, ForeignKey("cit_clientes.id"), index=True, nullable=False)
    cit_cliente = relationship("CitCliente", back_populates="cit_citas")
    cit_servicio_id = Column(Integer, ForeignKey("cit_servicios.id"), index=True, nullable=False)
    cit_servicio = relationship("CitServicio", back_populates="cit_citas")
    oficina_id = Column(Integer, ForeignKey("oficinas.id"), index=True, nullable=False)
    oficina = relationship("Oficina", back_populates="cit_citas")

    # Columnas
    inicio = Column(DateTime(), nullable=False)
    termino = Column(DateTime(), nullable=False)
    notas = Column(Text(), nullable=False, default="", server_default="")
    estado = Column(Enum(*ESTADOS, name="estados", native_enum=False))
    asistencia = Column(Boolean, nullable=False, default=False)
    codigo_asistencia = Column(String(4))
    cancelar_antes = Column(DateTime())

    # Hijos
    cit_citas_documentos = relationship("CitCitaDocumento", back_populates="cit_cita")

    @property
    def puede_cancelarse(self):
        """Puede cancelarse esta cita?"""
        if self.estado != "PENDIENTE":
            return False
        ahora = datetime.now(tz=pytz.timezone("America/Mexico_City"))
        ahora_sin_tz = ahora.replace(tzinfo=None)
        if self.cancelar_antes is None:
            return ahora_sin_tz < self.inicio
        return ahora_sin_tz < self.cancelar_antes

    def __repr__(self):
        """Representación"""
        return f"<CitCita {self.id}>"
