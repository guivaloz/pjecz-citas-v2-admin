"""
Cit Días Inhabiles, modelos
"""
from citas_admin.extensions import db
from lib.universal_mixin import UniversalMixin


class CitDiaInhabil(db.Model, UniversalMixin):
    """CitDiaInhabil"""

    # Nombre de la tabla
    __tablename__ = "cit_dias_inhabiles"

    # Clave primaria
    id = db.Column(db.Integer, primary_key=True)

    # Columnas
    fecha = db.Column(db.Date(), unique=True, nullable=False)
    descripcion = db.Column(db.String(512), nullable=True)

    def __repr__(self):
        """Representación"""
        return f"<CitDiaInhabil {self.fecha}>"
