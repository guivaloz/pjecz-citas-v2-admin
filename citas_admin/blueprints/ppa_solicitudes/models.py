"""
Pago de Pensiones Alimenticias - Solicitudes, modelos
"""
from citas_admin.extensions import db
from lib.universal_mixin import UniversalMixin


class PpaSolicitud(db.Model, UniversalMixin):
    """PpaSolicitud"""

    # Nombre de la tabla
    __tablename__ = "ppa_solicitudes"

    # Clave primaria
    id = db.Column(db.Integer, primary_key=True)

    # Claves foráneas
    autoridad_id = db.Column(db.Integer, db.ForeignKey("autoridades.id"), index=True, nullable=False)
    autoridad = db.relationship("Autoridad", back_populates="ppa_solicitudes")
    cit_cliente_id = db.Column(db.Integer, db.ForeignKey("cit_clientes.id"), index=True, nullable=False)
    cit_cliente = db.relationship("CitCliente", back_populates="ppa_solicitudes")

    # Columnas domicilio particular
    domicilio_calle = db.Column(db.String(256))
    domicilio_numero = db.Column(db.String(24))
    domicilio_colonia = db.Column(db.String(256))
    domicilio_cp = db.Column(db.Integer())

    # Columnas compañía telefónica
    compania_telefonica = db.Column(db.String(64))

    # Columnas número de expediente donde se decretó la pensión
    numero_expediente = db.Column(db.String(24))

    # Columnas archivo PDF de la credencial de elector
    identificacion_oficial_archivo = db.Column(db.String(64))
    identificacion_oficial_url = db.Column(db.String(256))

    # Columnas archivo PDF del comprobante de domicilio
    comprobante_domicilio_archivo = db.Column(db.String(64))
    comprobante_domicilio_url = db.Column(db.String(256))

    # Columnas archivo PDF de la autorización de transferencia de datos personales
    autorizacion_archivo = db.Column(db.String(64))
    autorizacion_url = db.Column(db.String(256))

    # Columnas mensajes
    ya_se_envio_acuse = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self):
        """Representación"""
        return f"<PpaSolicitud {self.id}>"
