"""
Cit Categorias, modelos
"""
from citas_admin.extensions import db
from lib.universal_mixin import UniversalMixin


class CitCategoria(db.Model, UniversalMixin):
    """CitCategoria"""

    # Nombre de la tabla
    __tablename__ = "cit_categorias"

    # Clave primaria
    id = db.Column(db.Integer, primary_key=True)

    # Columnas
    nombre = db.Column(db.String(64), unique=True, nullable=False)

    # Hijos
    cit_servicios = db.relationship("CitServicio", back_populates="cit_categoria", lazy="noload")

    def __repr__(self):
        """Representación"""
        return f"<CitCategoria {self.nombre}>"
