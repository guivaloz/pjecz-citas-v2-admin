"""
Pago de Pensiones Alimenticias - Solicitudes, modelos
"""

from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from lib.universal_mixin import UniversalMixin
from citas_admin.extensions import database


class PpaSolicitud(database.Model, UniversalMixin):
    """PpaSolicitud"""

    # Nombre de la tabla
    __tablename__ = "ppa_solicitudes"

    # Clave primaria
    id = Column(Integer, primary_key=True)

    # Claves foráneas
    autoridad_id = Column(Integer, ForeignKey("autoridades.id"), index=True, nullable=False)
    autoridad = relationship("Autoridad", back_populates="ppa_solicitudes")
    cit_cliente_id = Column(Integer, ForeignKey("cit_clientes.id"), index=True, nullable=False)
    cit_cliente = relationship("CitCliente", back_populates="ppa_solicitudes")

    # Columnas domicilio particular
    domicilio_calle = Column(String(256))
    domicilio_numero = Column(String(24))
    domicilio_colonia = Column(String(256))
    domicilio_cp = Column(Integer())

    # Columnas compañía telefónica
    compania_telefonica = Column(String(64))

    # Columnas número de expediente donde se decretó la pensión
    numero_expediente = Column(String(24))

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
        return f"<PpaSolicitud {self.id}>"
