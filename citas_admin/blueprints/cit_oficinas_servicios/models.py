"""
Cit Oficinas-Servicios, modelos
"""

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from lib.universal_mixin import UniversalMixin
from citas_admin.extensions import database


class CitOficinaServicio(database.Model, UniversalMixin):
    """CitOficinaServicio"""

    # Nombre de la tabla
    __tablename__ = "cit_oficinas_servicios"

    # Clave primaria
    id = Column(Integer, primary_key=True)

    # Clave foránea
    cit_servicio_id = Column(Integer, ForeignKey("cit_servicios.id"), index=True, nullable=False)
    cit_servicio = relationship("CitServicio", back_populates="cit_oficinas_servicios")
    oficina_id = Column(Integer, ForeignKey("oficinas.id"), index=True, nullable=False)
    oficina = relationship("Oficina", back_populates="cit_oficinas_servicios")

    # Columnas
    descripcion = Column(String(256), nullable=False)

    def __repr__(self):
        """Representación"""
        return f"<CitOficinaServicio {self.descripcion}>"
