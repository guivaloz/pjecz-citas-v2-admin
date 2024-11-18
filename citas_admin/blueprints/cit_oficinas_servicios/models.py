"""
Cit Oficinas-Servicios, modelos
"""

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from citas_admin.extensions import database
from lib.universal_mixin import UniversalMixin


class CitOficinaServicio(database.Model, UniversalMixin):
    """CitOficinaServicio"""

    # Nombre de la tabla
    __tablename__ = "cit_oficinas_servicios"

    # Clave primaria
    id: Mapped[int] = mapped_column(primary_key=True)

    # Claves foráneas
    cit_servicio_id: Mapped[int] = mapped_column(ForeignKey("cit_servicios.id"))
    cit_servicio: Mapped["CitServicio"] = relationship(back_populates="cit_oficinas_servicios")
    oficina_id: Mapped[int] = mapped_column(ForeignKey("oficinas.id"))
    oficina: Mapped["Oficina"] = relationship(back_populates="cit_oficinas_servicios")

    # Columnas
    descripcion: Mapped[str] = mapped_column(String(256))

    def __repr__(self):
        """Representación"""
        return f"<CitOficinaServicio {self.descripcion}>"
