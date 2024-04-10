"""
Tres de Tres - Solicitudes, modelos
"""

from sqlalchemy import Boolean, Column, Date, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from lib.universal_mixin import UniversalMixin
from citas_admin.extensions import database


class TdtSolicitud(database.Model, UniversalMixin):
    """TdtSolicitud"""

    CARGOS = {
        "GOBERNATURA": "Gobernatura",
        "DIPUTACION": "Diputación",
        "PRESIDENCIA MUNICIPAL": "Presidencia Municipal",
        "REGIDURIA": "Regiduría",
        "SINDICATURA": "Sindicatura",
    }

    PRINCIPIOS = {
        "MAYORIA RELATIVA": "Mayoría relativa",
        "REPRESENTACION PROPORCIONAL": "Representación proporcional",
    }

    # Nombre de la tabla
    __tablename__ = "tdt_solicitudes"

    # Clave primaria
    id = Column(Integer, primary_key=True)

    # Claves foráneas
    cit_cliente_id = Column(Integer, ForeignKey("cit_clientes.id"), index=True, nullable=False)
    cit_cliente = relationship("CitCliente", back_populates="tdt_solicitudes")
    municipio_id = Column(Integer, ForeignKey("municipios.id"), index=True, nullable=False)
    municipio = relationship("Municipio", back_populates="tdt_solicitudes")
    tdt_partido_id = Column(Integer, ForeignKey("tdt_partidos.id"), index=True, nullable=False)
    tdt_partido = relationship("TdtPartido", back_populates="tdt_solicitudes")

    # Columnas cargo y principio
    cargo = Column(Enum(*CARGOS, name="tdt_solicitudes_tipos_cargos", native_enum=False), index=True, nullable=False)
    principio = Column(
        Enum(*PRINCIPIOS, name="tdt_solicitudes_tipos_principios", native_enum=False), index=True, nullable=False
    )

    # Columnas domicilio particular
    domicilio_calle = Column(String(256))
    domicilio_numero = Column(String(24))
    domicilio_colonia = Column(String(256))
    domicilio_cp = Column(Integer())

    # Columnas archivo PDF de la credencial de elector
    identificacion_oficial_archivo = Column(String(64))
    identificacion_oficial_url = Column(String(256))

    # Columnas archivo PDF del comprobante de domicilio
    comprobante_domicilio_archivo = Column(String(64))
    comprobante_domicilio_url = Column(String(256))

    # Columnas archivo PDF de la autorización de transferencia de datos personales
    autorizacion_archivo = Column(String(64))
    autorizacion_url = Column(String(256))

    # Columnas mensajes
    ya_se_envio_acuse = Column(Boolean, nullable=False, default=False)

    # Columna caducidad
    caducidad = Column(Date, nullable=False)

    def __repr__(self):
        """Representación"""
        return "<TdtSolicitud>"
