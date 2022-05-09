"""
Cit Citas Documentos, modelos
"""
from citas_admin.extensions import db
from lib.universal_mixin import UniversalMixin


class CitCitaDocumento(db.Model, UniversalMixin):
    """CitCitaDocumento"""

    # Nombre de la tabla
    __tablename__ = "cit_citas_documentos"

    # Clave primaria
    id = db.Column(db.Integer, primary_key=True)

    # Clave foránea
    cit_cita_id = db.Column(db.Integer, db.ForeignKey("cit_citas.id"), index=True, nullable=False)
    cit_cita = db.relationship("CitCita", back_populates="cit_citas_documentos")

    # Columnas
    descripcion = db.Column(db.String(256), nullable=False)

    def __repr__(self):
        """Representación"""
        return f"<CitCitaDocumento {self.id}>"
