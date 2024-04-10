"""
Cit Citas Documentos, modelos
"""

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from lib.universal_mixin import UniversalMixin
from citas_admin.extensions import database


class CitCitaDocumento(database.Model, UniversalMixin):
    """CitCitaDocumento"""

    # Nombre de la tabla
    __tablename__ = "cit_citas_documentos"

    # Clave primaria
    id = Column(Integer, primary_key=True)

    # Clave foránea
    cit_cita_id = Column(Integer, ForeignKey("cit_citas.id"), index=True, nullable=False)
    cit_cita = relationship("CitCita", back_populates="cit_citas_documentos")

    # Columnas
    descripcion = Column(String(256), nullable=False)

    def __repr__(self):
        """Representación"""
        return f"<CitCitaDocumento {self.id}>"
