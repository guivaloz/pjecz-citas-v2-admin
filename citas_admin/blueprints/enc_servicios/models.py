"""
Encuesta Servicios, modelos
"""
from collections import OrderedDict
from citas_admin.extensions import db
from lib.universal_mixin import UniversalMixin


class EncServicio(db.Model, UniversalMixin):
    """Encuesta del Servicio"""

    ESTADOS = OrderedDict(
        [
            ("PENDIENTE", "Pendiente"),
            ("CANCELADO", "Cancelado"),
            ("CONTESTADO", "Contestado"),
        ]
    )

    # Nombre de la tabla
    __tablename__ = "enc_servicios"

    # Clave primaria
    id = db.Column(db.Integer, primary_key=True)

    # Clave foránea
    cit_cliente_id = db.Column(db.Integer, db.ForeignKey("cit_clientes.id"), nullable=False)
    cit_cliente = db.relationship("CitCliente", back_populates="enc_servicios")
    oficina_id = db.Column(db.Integer, db.ForeignKey("oficinas.id"), nullable=False)
    oficina = db.relationship("Oficina", back_populates="enc_servicios")

    # Columnas
    respuesta_01 = db.Column(db.Integer(), nullable=True)
    respuesta_02 = db.Column(db.Integer(), nullable=True)
    respuesta_03 = db.Column(db.Integer(), nullable=True)
    respuesta_04 = db.Column(db.String(255), nullable=True)
    estado = db.Column(db.Enum(*ESTADOS, name="estados", native_enum=False))

    def __repr__(self):
        """Representación"""
        return f"<Encuesta_Servicio {self.id}>"
