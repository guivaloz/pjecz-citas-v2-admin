"""
Cit Horas Bloqueadas, modelos
"""

from datetime import date, time

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from citas_admin.extensions import database
from lib.universal_mixin import UniversalMixin


class CitHoraBloqueada(database.Model, UniversalMixin):
    """CitHoraBloqueada"""

    # Nombre de la tabla
    __tablename__ = "cit_horas_bloqueadas"

    # Clave primaria
    id: Mapped[int] = mapped_column(primary_key=True)

    # Clave foránea
    oficina_id: Mapped[int] = mapped_column(ForeignKey("oficinas.id"))
    oficina: Mapped["Oficina"] = relationship(back_populates="cit_horas_bloqueadas")

    # Columnas
    fecha: Mapped[date]
    inicio: Mapped[time]
    termino: Mapped[time]
    descripcion: Mapped[str] = mapped_column(String(256))

    def __repr__(self):
        """Representación"""
        return f"<CitHoraBloqueada {self.fecha} {self.inicio}-{self.termino}>"
