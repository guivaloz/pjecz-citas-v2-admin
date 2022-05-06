"""
Cit Horas Bloqueadas, modelos
"""
from citas_admin.extensions import db
from lib.universal_mixin import UniversalMixin


class CitHoraBloqueada(db.Model, UniversalMixin):
    """CitHoraBloqueada"""

    # Nombre de la tabla
    __tablename__ = "cit_horas_bloqueadas"

    # Clave primaria
    id = db.Column(db.Integer, primary_key=True)

    # Clave foránea
    oficina_id = db.Column(db.Integer, db.ForeignKey("oficinas.id"), index=True, nullable=False)
    oficina = db.relationship("Oficina", back_populates="cit_horas_bloqueadas")

    # Columnas
    fecha = db.Column(db.Date(), nullable=False)
    inicio_tiempo = db.Column(db.Time(), nullable=False)
    termino_tiempo = db.Column(db.Time(), nullable=False)
    descripcion = db.Column(db.String(512), nullable=True)

    def __repr__(self):
        """Representación"""
        return f"<CitHoraBloqueada {self.id}>"
