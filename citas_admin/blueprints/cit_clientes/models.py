"""
Cit Clientes, modelos
"""
from citas_admin.extensions import db
from lib.universal_mixin import UniversalMixin


class CitCliente(db.Model, UniversalMixin):
    """CitCliente"""

    # Nombre de la tabla
    __tablename__ = "cit_clientes"

    # Clave primaria
    id = db.Column(db.Integer, primary_key=True)

    # Columnas
    nombres = db.Column(db.String(256), nullable=False)
    apellido_primero = db.Column(db.String(256), nullable=False)
    apellido_segundo = db.Column(db.String(256), nullable=False, default="", server_default="")
    curp = db.Column(db.String(18), unique=True, nullable=False)
    telefono = db.Column(db.String(64), nullable=False, default="", server_default="")
    email = db.Column(db.String(256), unique=True, nullable=False)
    contrasena_md5 = db.Column(db.String(256), nullable=False)
    contrasena_sha256 = db.Column(db.String(256), nullable=False)
    renovacion = db.Column(db.Date(), nullable=False)
    limite_citas_pendientes = db.Column(db.Integer(), nullable=True)

    # Columnas booleanas
    enviar_boletin = db.Column(db.Boolean(), nullable=False, default=True)
    es_adulto_mayor = db.Column(db.Boolean(), nullable=False, default=True)
    es_mujer = db.Column(db.Boolean(), nullable=False, default=True)
    es_identidad = db.Column(db.Boolean(), nullable=False, default=True)
    es_discapacidad = db.Column(db.Boolean(), nullable=False, default=True)

    # Hijos
    cit_citas = db.relationship("CitCita", back_populates="cit_cliente")
    cit_clientes_recuperaciones = db.relationship("CitClienteRecuperacion", back_populates="cit_cliente")
    cit_pagos = db.relationship("CitPago", back_populates="cit_cliente")
    enc_servicios = db.relationship("EncServicio", back_populates="cit_cliente")
    enc_sistemas = db.relationship("EncSistema", back_populates="cit_cliente")

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
