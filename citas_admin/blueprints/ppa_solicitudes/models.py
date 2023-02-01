"""
Pago de Pensiones Alimenticias - Solicitudes, modelos
"""
from citas_admin.extensions import db
from lib.universal_mixin import UniversalMixin


class PPASolicitud(db.Model, UniversalMixin):
    """PPASolicitud"""

    # Nombre de la tabla
    __tablename__ = "ppa_solicitudes"

    # Clave primaria
    id = db.Column(db.Integer, primary_key=True)

    # Claves foráneas
    autoridad_id = db.Column(db.Integer, db.ForeignKey("autoridades.id"), index=True, nullable=False)
    autoridad = db.relationship("Autoridad", back_populates="ppa_solicitudes")
    cit_cliente_id = db.Column(db.Integer, db.ForeignKey("cit_clientes.id"), index=True, nullable=False)
    cit_cliente = db.relationship("CitCliente", back_populates="ppa_solicitudes")
    municipio_id = db.Column(db.Integer, db.ForeignKey("municipios.id"), index=True, nullable=False)
    municipio = db.relationship("Municipio", back_populates="ppa_solicitudes")

    # Columnas
    autorizacion_archivo = db.Column(db.String(64))
    autorizacion_url = db.Column(db.String(256))
    comprobante_domicilio_archivo = db.Column(db.String(64))
    comprobante_domicilio_url = db.Column(db.String(256))
    compania_telefonica = db.Column(db.String(64))
    domicilio_calle = db.Column(db.String(256))
    domicilio_numero = db.Column(db.String(24))
    domicilio_colonia = db.Column(db.String(256))
    domicilio_cp = db.Column(db.Integer())
    identificacion_oficial_archivo = db.Column(db.String(64))
    identificacion_oficial_url = db.Column(db.String(256))
    numero_expediente = db.Column(db.String(24))
    token = db.Column(db.String(128), nullable=False)

    def __repr__(self):
        """Representación"""
        return "<PPASolicitud>"
