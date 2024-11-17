"""
Cit Clientes, modelos
"""

from datetime import date
from typing import List

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from citas_admin.extensions import database
from lib.universal_mixin import UniversalMixin


class CitCliente(database.Model, UniversalMixin):
    """CitCliente"""

    # Nombre de la tabla
    __tablename__ = "cit_clientes"

    # Clave primaria
    id: Mapped[int] = mapped_column(primary_key=True)

    # Columnas
    nombres: Mapped[str] = mapped_column(String(256))
    apellido_primero: Mapped[str] = mapped_column(String(256))
    apellido_segundo: Mapped[str] = mapped_column(String(256))
    curp: Mapped[str] = mapped_column(String(18))
    telefono: Mapped[str] = mapped_column(String(64))
    email: Mapped[str] = mapped_column(String(256), unique=True)
    contrasena_md5: Mapped[str] = mapped_column(String(256))
    contrasena_sha256: Mapped[str] = mapped_column(String(256))
    renovacion: Mapped[date]
    limite_citas_pendientes: Mapped[int]
    autoriza_mensajes: Mapped[bool] = mapped_column(default=True)
    enviar_boletin: Mapped[bool] = mapped_column(default=False)
    es_adulto_mayor: Mapped[bool] = mapped_column(default=False)
    es_mujer: Mapped[bool] = mapped_column(default=False)
    es_identidad: Mapped[bool] = mapped_column(default=False)
    es_discapacidad: Mapped[bool] = mapped_column(default=False)
    es_personal_interno: Mapped[bool] = mapped_column(default=False)

    # Hijos
    cit_citas: Mapped[List["CitCita"]] = relationship(back_populates="cit_cliente")
    cit_clientes_recuperaciones: Mapped[List["CitClienteRecuperacion"]] = relationship(back_populates="cit_cliente")
    pag_pagos: Mapped[List["PagPago"]] = relationship(back_populates="cit_cliente")

    @property
    def nombre(self):
        """Junta nombres, apellido_primero y apellido segundo"""
        return self.nombres + " " + self.apellido_primero + " " + self.apellido_segundo

    def __repr__(self):
        """Representación"""
        return f"<CitCliente {self.email}>"
