"""
Cit Clientes, modelos
"""

from sqlalchemy import Boolean, Column, Date, Integer, String
from sqlalchemy.orm import relationship

from lib.universal_mixin import UniversalMixin
from citas_admin.extensions import database


class CitCliente(database.Model, UniversalMixin):
    """CitCliente"""

    # Nombre de la tabla
    __tablename__ = "cit_clientes"

    # Clave primaria
    id = Column(Integer, primary_key=True)

    # Columnas
    nombres = Column(String(256), nullable=False)
    apellido_primero = Column(String(256), nullable=False)
    apellido_segundo = Column(String(256), nullable=False, default="", server_default="")
    curp = Column(String(18), unique=True, nullable=False)
    telefono = Column(String(64), nullable=False, default="", server_default="")
    email = Column(String(256), unique=True, nullable=False)
    contrasena_md5 = Column(String(256), nullable=False)
    contrasena_sha256 = Column(String(256), nullable=False)
    renovacion = Column(Date(), nullable=False)
    limite_citas_pendientes = Column(Integer(), nullable=False)

    # Columnas booleanas
    autoriza_mensajes = Column(Boolean(), nullable=False, default=True)
    enviar_boletin = Column(Boolean(), nullable=False, default=False)
    es_adulto_mayor = Column(Boolean(), nullable=False, default=False)
    es_mujer = Column(Boolean(), nullable=False, default=False)
    es_identidad = Column(Boolean(), nullable=False, default=False)
    es_discapacidad = Column(Boolean(), nullable=False, default=False)
    es_personal_interno = Column(Boolean(), nullable=False, default=False)

    # Hijos
    cit_citas = relationship("CitCita", back_populates="cit_cliente")
    cit_clientes_recuperaciones = relationship("CitClienteRecuperacion", back_populates="cit_cliente")
    enc_servicios = relationship("EncServicio", back_populates="cit_cliente")
    enc_sistemas = relationship("EncSistema", back_populates="cit_cliente")
    pag_pagos = relationship("PagPago", back_populates="cit_cliente")
    ppa_solicitudes = relationship("PpaSolicitud", back_populates="cit_cliente")
    tdt_solicitudes = relationship("TdtSolicitud", back_populates="cit_cliente")

    @property
    def nombre(self):
        """Junta nombres, apellido_primero y apellido segundo"""
        return self.nombres + " " + self.apellido_primero + " " + self.apellido_segundo

    @property
    def telefono_formato(self):
        """Teléfono con formato"""
        if len(self.telefono) != 10:
            return self.telefono
        return f"({self.telefono[:3]}) {self.telefono[3:6]}-{self.telefono[6:]}"

    def __repr__(self):
        """Representación"""
        return f"<CitCliente {self.email}>"
