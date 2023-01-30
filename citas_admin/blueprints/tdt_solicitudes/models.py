"""
Tres de Tres - Solicitudes, modelos
"""
from collections import OrderedDict
from citas_admin.extensions import db
from lib.universal_mixin import UniversalMixin


class TDTSolicitud(db.Model, UniversalMixin):
    """TDTSolicitud"""

    CARGOS = OrderedDict(
        [
            ("PRESIDENCIA MUNICIPAL", "Presidencia Municipal"),
            ("REGIDURIA", "Regiduría"),
            ("SINDICATURA", "Sindicatura"),
        ]
    )

    PRINCIPIOS = OrderedDict(
        [
            ("MAYORIA RELATIVA", "Mayoría relativa"),
            ("REPRESENTACION PROPORCIONAL", "Representación proporcional"),
        ]
    )

    # Nombre de la tabla
    __tablename__ = "tdt_solicitudes"

    # Clave primaria
    id = db.Column(db.Integer, primary_key=True)

    # Claves foráneas
    cit_cliente_id = db.Column(db.Integer, db.ForeignKey("cit_clientes.id"), index=True, nullable=False)
    cit_cliente = db.relationship("CitCliente", back_populates="tdt_solicitudes")
    municipio_id = db.Column(db.Integer, db.ForeignKey("municipios.id"), index=True, nullable=False)
    municipio = db.relationship("Municipio", back_populates="tdt_solicitudes")
    tdt_partido_id = db.Column(db.Integer, db.ForeignKey("tdt_partidos.id"), index=True, nullable=False)
    tdt_partido = db.relationship("TDTPartido", back_populates="tdt_solicitudes")

    # Columnas
    autoriza = db.Column(db.Boolean, nullable=False, default=False, server_default="false")
    cargo = db.Column(db.Enum(*CARGOS, name="tdt_solicitudes_tipos_cargos", native_enum=False), index=True, nullable=False)
    domicilio_calle = db.Column(db.String(256))
    domicilio_numero = db.Column(db.String(24))
    domicilio_colonia = db.Column(db.String(256))
    domicilio_cp = db.Column(db.Integer())
    identificacion_oficial_archivo = db.Column(db.String(64))
    identificacion_oficial_url = db.Column(db.String(256))
    principio = db.Column(db.Enum(*PRINCIPIOS, name="tdt_solicitudes_tipos_principios", native_enum=False), index=True, nullable=False)
    token = db.Column(db.String(128), nullable=False)

    def __repr__(self):
        """Representación"""
        return "<TDTSolicitud>"
