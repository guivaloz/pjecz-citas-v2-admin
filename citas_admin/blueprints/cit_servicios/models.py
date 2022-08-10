"""
Cit Servicios, modelos
"""
from citas_admin.extensions import db
from lib.universal_mixin import UniversalMixin


class CitServicio(db.Model, UniversalMixin):
    """Cit Servicio"""

    # Nombre de la tabla
    __tablename__ = "cit_servicios"

    # Clave primaria
    id = db.Column(db.Integer, primary_key=True)

    # Clave foránea
    cit_categoria_id = db.Column(db.Integer, db.ForeignKey("cit_categorias.id"), index=True, nullable=False)
    cit_categoria = db.relationship("CitCategoria", back_populates="cit_servicios")

    # Columnas
    clave = db.Column(db.String(32), unique=True, nullable=False)
    descripcion = db.Column(db.String(64), nullable=False)
    duracion = db.Column(db.Time(), nullable=False)
    documentos_limite = db.Column(db.Integer, nullable=False)
    desde = db.Column(db.Time(), nullable=True)
    hasta = db.Column(db.Time(), nullable=True)
    dias_habiles = db.Column(db.String(7), nullable=True)

    # Hijos
    cit_citas = db.relationship("CitCita", back_populates="cit_servicio")
    cit_oficinas_servicios = db.relationship("CitOficinaServicio", back_populates="cit_servicio")

    @property
    def compuesto(self):
        """Entregar clave - descripcion para selects"""
        return f"{self.clave} - {self.descripcion}"

    def __repr__(self):
        """Representación"""
        return f"<CitServicio {self.clave}>"
