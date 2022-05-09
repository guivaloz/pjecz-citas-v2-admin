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

    # Clave foránea
    clave_foranea_id = db.Column(db.Integer, db.ForeignKey("tabla_clave_foranea.id"), index=True, nullable=False)
    clave_foranea = db.relationship("Clase_clave_foranea", back_populates="plural_esta_clase")

    # Columnas
    nombre = db.Column(db.String(256), unique=True, nullable=False)
    descripcion = db.Column(db.String(256), nullable=False)

    # Hijos
    cit_categorias_servicios = db.relationship("CitCategroiaServicio", back_populates="cit_categoria", lazy="noload")

    def __repr__(self):
        """Representación"""
        return "<CitCategoria>"
