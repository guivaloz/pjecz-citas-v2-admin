"""
Cit Citas, modelos
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

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
    id: Mapped[int] = mapped_column(primary_key=True)

    # Claves foráneas
    cit_cliente_id: Mapped[int] = mapped_column(ForeignKey("cit_clientes.id"))
    cit_cliente: Mapped["CitCliente"] = relationship(back_populates="cit_citas")
    cit_servicio_id: Mapped[int] = mapped_column(ForeignKey("cit_servicios.id"))
    cit_servicio: Mapped["CitServicio"] = relationship(back_populates="cit_citas")
    oficina_id: Mapped[int] = mapped_column(ForeignKey("oficinas.id"))
    oficina: Mapped["Oficina"] = relationship(back_populates="cit_citas")

    # Columnas
    inicio: Mapped[datetime]
    termino: Mapped[datetime]
    notas: Mapped[str] = mapped_column(Text)
    estado: Mapped[str] = mapped_column(Enum(*ESTADOS, name="cit_citas_estados", native_enum=False), index=True)
    asistencia: Mapped[bool] = mapped_column(default=False)
    codigo_asistencia: Mapped[Optional[str]] = mapped_column(String(4))
    cancelar_antes: Mapped[Optional[datetime]]

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
