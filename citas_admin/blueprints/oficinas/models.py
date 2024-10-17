"""
Oficinas, modelos
"""

from datetime import time
from typing import List

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from citas_admin.extensions import database
from lib.universal_mixin import UniversalMixin


class Oficina(database.Model, UniversalMixin):
    """Oficina"""

    # Nombre de la tabla
    __tablename__ = "oficinas"

    # Clave primaria
    id: Mapped[int] = mapped_column(primary_key=True)

    # Claves foráneas
    distrito_id: Mapped[int] = mapped_column(ForeignKey("distritos.id"))
    distrito: Mapped["Distrito"] = relationship(back_populates="oficinas")
    domicilio_id: Mapped[int] = mapped_column(ForeignKey("domicilios.id"))
    domicilio: Mapped["Domicilio"] = relationship(back_populates="oficinas")

    # Columnas
    clave: Mapped[str] = mapped_column(String(32), unique=True)
    descripcion: Mapped[str] = mapped_column(String(512))
    descripcion_corta: Mapped[str] = mapped_column(String(64))
    es_jurisdiccional: Mapped[bool] = mapped_column(default=False)
    puede_agendar_citas: Mapped[bool] = mapped_column(default=False)
    apertura: Mapped[time]
    cierre: Mapped[time]
    limite_personas: Mapped[int]
    puede_enviar_qr: Mapped[bool] = mapped_column(default=False)

    # Hijos
    cit_citas: Mapped[List["CitCita"]] = relationship("CitCita", back_populates="oficina")
    cit_horas_bloqueadas: Mapped[List["CitHoraBloqueada"]] = relationship("CitHoraBloqueada", back_populates="oficina")
    cit_oficinas_servicios: Mapped[List["CitOficinaServicio"]] = relationship("CitOficinaServicio", back_populates="oficina")
    usuarios: Mapped[List["Usuario"]] = relationship("Usuario", back_populates="oficina")
    usuarios_oficinas: Mapped[List["UsuarioOficina"]] = relationship("UsuarioOficina", back_populates="oficina")

    def __repr__(self):
        """Representación"""
        return f"<Oficina {self.clave}>"
