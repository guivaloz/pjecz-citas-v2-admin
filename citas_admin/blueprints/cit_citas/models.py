"""
Cit Citas, modelos
"""
from collections import OrderedDict
from citas_admin.extensions import db
from lib.universal_mixin import UniversalMixin


class CitCita(db.Model, UniversalMixin):
    """CitCita"""

    ESTADOS = OrderedDict(
        [
            ("ASISTIO", "Asistió"),
            ("CANCELO", "Canceló"),
            ("CONFIRMO", "Confirmó"),
            ("PENDIENTE", "Pendiente"),
        ]
    )

    # Nombre de la tabla
    __tablename__ = "cit_citas"

    # Clave primaria
    id = db.Column(db.Integer, primary_key=True)

    # Claves foráneas
    cit_servicio_id = db.Column(db.Integer, db.ForeignKey("cit_servicios.id"), index=True, nullable=False)
    cit_servicio = db.relationship("CitServicio", back_populates="cit_citas")
    cit_cliente_id = db.Column(db.Integer, db.ForeignKey("cit_clientes.id"), index=True, nullable=False)
    cit_cliente = db.relationship("CitCliente", back_populates="cit_citas")
    oficina_id = db.Column(db.Integer, db.ForeignKey("oficinas.id"), index=True, nullable=False)
    oficina = db.relationship("Oficina", back_populates="cit_citas")

    # Columnas
    inicio = db.Column(db.DateTime(), nullable=False)
    termino = db.Column(db.DateTime(), nullable=False)
    notas = db.Column(db.Text(), nullable=False, default="", server_default="")
    estado = db.Column(db.Enum(*ESTADOS, name="tipos_estados", native_enum=False))
    asistencia = db.Column(db.Boolean, nullable=False, default=False)

    # Hijos
    cit_citas_documentos = db.relationship("CitCitaDocumento", back_populates="cit_cita", lazy="noload")

    def __repr__(self):
        """Representación"""
        return f"<CitCita {self.id}>"
