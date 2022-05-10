"""
Cit Autoridades Servicios, modelos
"""
from citas_admin.extensions import db
from lib.universal_mixin import UniversalMixin


class CitAutoridadServicio(db.Model, UniversalMixin):
    """CitAutoridadServicio"""

    # Nombre de la tabla
    __tablename__ = "cit_autoridades_servicios"

    # Clave primaria
    id = db.Column(db.Integer, primary_key=True)

    # Clave foránea
    autoridad_id = db.Column(db.Integer, db.ForeignKey("autoridades.id"), index=True, nullable=False)
    autoridad = db.relationship("Autoridad", back_populates="cit_autoridades_servicios")
    cit_servicio_id = db.Column(db.Integer, db.ForeignKey("cit_servicios.id"), index=True, nullable=False)
    cit_servicio = db.relationship("CitServicio", back_populates="cit_autoridades_servicios")

    def __repr__(self):
        """Representación"""
        return f"<CitAutoridadServicio {self.id}>"
