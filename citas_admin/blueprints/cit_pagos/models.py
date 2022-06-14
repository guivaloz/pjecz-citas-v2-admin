"""
Cit Pagos, modelos
"""
from citas_admin.extensions import db
from lib.universal_mixin import UniversalMixin


class CitPago(db.Model, UniversalMixin):
    """CitPago"""

    # Nombre de la tabla
    __tablename__ = "cit_pagos"

    # Clave primaria
    id = db.Column(db.Integer, primary_key=True)

    # Clave foránea
    cit_cliente_id = db.Column(db.Integer, db.ForeignKey("cit_clientes.id"), index=True, nullable=False)
    cit_cliente = db.relationship("CitCliente", back_populates="cit_pagos")

    # Columnas
    descripcion = db.Column(db.String(256), nullable=False)
    total = db.Column(db.Numeric(12, 2), nullable=False)

    def __repr__(self):
        """Representación"""
        return f"<CitPago {self.descripcion} ${self.total}>"
