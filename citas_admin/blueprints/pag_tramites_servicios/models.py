"""
Pag Tramites Servicios, modelos
"""
from citas_admin.extensions import db
from lib.universal_mixin import UniversalMixin


class PagTramiteServicio(db.Model, UniversalMixin):
    """PagTramiteServicio"""

    # Nombre de la tabla
    __tablename__ = "pag_tramites_servicios"

    # Clave primaria
    id = db.Column(db.Integer, primary_key=True)

    # Columnas
    clave = db.Column(db.String(16), nullable=False, unique=True)
    descripcion = db.Column(db.String(256), nullable=False)
    costo = db.Column(db.Numeric(precision=8, scale=2, decimal_return_scale=2), nullable=False)
    url = db.Column(db.String(256), nullable=False)

    # Hijos
    pag_pagos = db.relationship("PagPago", back_populates="pag_tramite_servicio")

    def __repr__(self):
        """Representación"""
        return f"<PagTramiteServicio> {self.id}"
