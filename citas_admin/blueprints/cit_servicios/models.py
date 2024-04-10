"""
Cit Servicios, modelos
"""

from sqlalchemy import Column, ForeignKey, Integer, String, Time
from sqlalchemy.orm import relationship

from lib.universal_mixin import UniversalMixin
from citas_admin.extensions import database


class CitServicio(database.Model, UniversalMixin):
    """Cit Servicio"""

    # Nombre de la tabla
    __tablename__ = "cit_servicios"

    # Clave primaria
    id = Column(Integer, primary_key=True)

    # Clave foránea
    cit_categoria_id = Column(Integer, ForeignKey("cit_categorias.id"), index=True, nullable=False)
    cit_categoria = relationship("CitCategoria", back_populates="cit_servicios")

    # Columnas
    clave = Column(String(32), unique=True, nullable=False)
    descripcion = Column(String(64), nullable=False)
    duracion = Column(Time(), nullable=False)
    documentos_limite = Column(Integer, nullable=False)
    desde = Column(Time(), nullable=True)
    hasta = Column(Time(), nullable=True)
    dias_habilitados = Column(String(7), nullable=False)

    # Hijos
    cit_citas = relationship("CitCita", back_populates="cit_servicio")
    cit_oficinas_servicios = relationship("CitOficinaServicio", back_populates="cit_servicio")

    @property
    def compuesto(self):
        """Entregar clave - descripcion para selects"""
        return f"{self.clave} - {self.descripcion}"

    def __repr__(self):
        """Representación"""
        return f"<CitServicio {self.clave}>"
