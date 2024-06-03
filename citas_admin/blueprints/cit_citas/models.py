"""
Cit Citas, modelos
"""

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from lib.universal_mixin import UniversalMixin

from citas_admin.extensions import database


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

    # Clave foránea
    cit_cliente_id = Column(Integer, ForeignKey("cit_clientes.id"), index=True, nullable=False)
    cit_cliente = relationship("CitCliente", back_populates="cit_citas")
    cit_servicio_id = Column(Integer, ForeignKey("cit_servicios.id"), index=True, nullable=False)
    cit_servicio = relationship("CitServicio", back_populates="cit_citas")
    oficina_id = Column(Integer, ForeignKey("oficinas.id"), index=True, nullable=False)
    oficina = relationship("Oficina", back_populates="cit_citas")

    # Columnas
    inicio = Column(DateTime, nullable=False)
    termino = Column(DateTime, nullable=False)
    notas = Column(Text, nullable=False)
    estado = Column(Enum(*ESTADOS, name="estados", native_enum=False))
    asistencia = Column(Boolean, nullable=False, default=False)
    codigo_asistencia = Column(String(4))
    cancelar_antes = Column(DateTime)

    def __repr__(self):
        """Representación"""
        return f"<CitCita {self.id}>"
