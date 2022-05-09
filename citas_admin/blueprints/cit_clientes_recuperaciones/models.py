"""
Cit Clientes Recuperaciones, modelos
"""
from citas_admin.extensions import db
from lib.universal_mixin import UniversalMixin


class CitClienteRecuperacion(db.Model, UniversalMixin):
    """CitClienteRecuperacion"""

    # Nombre de la tabla
    __tablename__ = "cit_clientes_recuperaciones"

    # Clave primaria
    id = db.Column(db.Integer, primary_key=True)

    # Clave foránea
    cit_cliente_id = db.Column(db.Integer, db.ForeignKey("cit_clientes.id"), index=True, nullable=False)
    cit_cliente = db.relationship("CitCliente", back_populates="cit_clientes_recuperaciones")

    # Columnas
    nombre = db.Column(db.String(256), unique=True, nullable=False)
    descripcion = db.Column(db.String(256), nullable=False)

    def __repr__(self):
        """Representación"""
        return "<CitClienteRecuperacion>"
