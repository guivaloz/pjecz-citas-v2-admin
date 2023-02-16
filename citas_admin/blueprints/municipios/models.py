"""
Municipios, modelos
"""
from citas_admin.extensions import db
from lib.universal_mixin import UniversalMixin


class Municipio(db.Model, UniversalMixin):
    """Municipio"""

    # Nombre de la tabla
    __tablename__ = "municipios"

    # Clave primaria
    id = db.Column(db.Integer, primary_key=True)

    # Columnas
    nombre = db.Column(db.String(256), unique=True, nullable=False)

    # Hijos
    tdt_candidatos = db.relationship("TdtCandidato", back_populates="municipio")

    def __repr__(self):
        """Representación"""
        return f"<Municipio {self.nombre}>"
