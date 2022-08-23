"""
Encuestas, modelos
"""
from citas_admin.extensions import db
from lib.universal_mixin import UniversalMixin


class Encuesta_Sistema(db.Model, UniversalMixin):
    """Encuesta del Sistema"""

    # Nombre de la tabla
    __tablename__ = "encuesta_sistema"

    # Clave primaria
    id = db.Column(db.Integer, primary_key=True)

    # Clave foránea
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), index=True, nullable=False)
    cliente = db.relationship("Cliente", back_populates="encuesta_sistema")

    # Columnas
    respuesta_01 = db.Column(db.Integer(), nullable=False)
    respuesta_02 = db.Column(db.String(255), nullable=False, default="", server_default="")
    respuesta_03 = db.Column(db.String(255), nullable=False, default="", server_default="")

    def __repr__(self):
        """Representación"""
        return f"<Encuesta_Sistema {self.id}>"
