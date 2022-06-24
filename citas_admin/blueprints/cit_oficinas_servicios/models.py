"""
Cit Oficinas-Servicios, modelos
"""
from citas_admin.extensions import db
from lib.universal_mixin import UniversalMixin


class CitOficinaServicio(db.Model, UniversalMixin):
    """CitOficinaServicio"""

    # Nombre de la tabla
    __tablename__ = "cit_oficinas_servicios"

    # Clave primaria
    id = db.Column(db.Integer, primary_key=True)

    # Clave foránea
    cit_servicio_id = db.Column(db.Integer, db.ForeignKey("cit_servicios.id"), index=True, nullable=False)
    cit_servicio = db.relationship("CitServicio", back_populates="cit_oficinas_servicios")
    oficina_id = db.Column(db.Integer, db.ForeignKey("oficinas.id"), index=True, nullable=False)
    oficina = db.relationship("Oficina", back_populates="cit_oficinas_servicios")

    # Columnas
    descripcion = db.Column(db.String(256), nullable=False)

    def __repr__(self):
        """Representación"""
        return f"<CitOficinaServicio {self.descripcion}>"
