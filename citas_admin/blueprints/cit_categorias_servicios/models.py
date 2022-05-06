"""
Cit Categorias Servicios, modelos
"""
from citas_admin.extensions import db
from lib.universal_mixin import UniversalMixin


class CitCategoriaServicio(db.Model, UniversalMixin):
    """Cit Categoria Servicio"""

    # Nombre de la tabla
    __tablename__ = "cit_servicios"

    # Clave primaria
    id = db.Column(db.Integer, primary_key=True)

    # Clave foránea
    cit_categoria_id = db.Column(db.Integer, db.ForeignKey("cit_categorias.id"), index=True, nullable=False)
    cit_categoria = db.relationship("CitCategoria", back_populates="cit_categorias_servicios")

    # Columnas
    clave = db.Column(db.String(32), unique=True, nullable=False)
    duracion = db.Column(db.Time(), nullable=False)
    nombre = db.Column(db.String(128), nullable=False)
    solicitar_expedientes = db.Column(db.Boolean, nullable=False)

    # Hijos

    def __repr__(self):
        """Representación"""
        return f"<CitCategoriaServicio {self.id}>"
