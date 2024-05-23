"""
Autoridad
"""

from sqlalchemy import Boolean, Column, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from lib.universal_mixin import UniversalMixin
from citas_admin.extensions import database


class Autoridad(database.Model, UniversalMixin):
    """Autoridad"""

    ORGANOS_JURISDICCIONALES = {
        "NO DEFINIDO": "No Definido",
        "JUZGADO DE PRIMERA INSTANCIA": "Juzgado de Primera Instancia",
        "PLENO O SALA DEL TSJ": "Pleno o Sala del TSJ",
        "TRIBUNAL DISTRITAL": "Tribunal Distrital",
        "TRIBUNAL DE CONCILIACION Y ARBITRAJE": "Tribunal de Conciliación y Arbitraje",
    }

    # Nombre de la tabla
    __tablename__ = "autoridades"

    # Clave primaria
    id = Column(Integer, primary_key=True)

    # Claves foráneas
    distrito_id = Column(Integer, ForeignKey("distritos.id"), index=True, nullable=False)
    distrito = relationship("Distrito", back_populates="autoridades")
    materia_id = Column(Integer, ForeignKey("materias.id"), index=True, nullable=False)
    materia = relationship("Materia", back_populates="autoridades")

    # Columnas
    clave = Column(String(16), nullable=False, unique=True)
    descripcion = Column(String(256), nullable=False)
    descripcion_corta = Column(String(64), nullable=False, default="", server_default="")
    es_jurisdiccional = Column(Boolean, nullable=False, default=False)
    es_notaria = Column(Boolean, nullable=False, default=False)
    es_organo_especializado = Column(Boolean, nullable=False, default=False)
    organo_jurisdiccional = Column(
        Enum(*ORGANOS_JURISDICCIONALES, name="tipos_organos_jurisdiccionales", native_enum=False),
        index=True,
        nullable=False,
    )

    # Hijos
    usuarios = relationship("Usuario", back_populates="autoridad")

    def __repr__(self):
        """Representación"""
        return f"<Autoridad {self.clave}>"
