"""
Cit Horas Bloqueadas, modelos
"""

from sqlalchemy import Column, Date, ForeignKey, Integer, String, Time
from sqlalchemy.orm import relationship

from lib.universal_mixin import UniversalMixin
from citas_admin.extensions import database


class CitHoraBloqueada(database.Model, UniversalMixin):
    """CitHoraBloqueada"""

    # Nombre de la tabla
    __tablename__ = "cit_horas_bloqueadas"

    # Clave primaria
    id = Column(Integer, primary_key=True)

    # Clave foránea
    oficina_id = Column(Integer, ForeignKey("oficinas.id"), index=True, nullable=False)
    oficina = relationship("Oficina", back_populates="cit_horas_bloqueadas")

    # Columnas
    fecha = Column(Date(), nullable=False, index=True)
    inicio = Column(Time(), nullable=False)
    termino = Column(Time(), nullable=False)
    descripcion = Column(String)

    def __repr__(self):
        """Representación"""
        return f"<CitHoraBloqueada {self.id}>"
