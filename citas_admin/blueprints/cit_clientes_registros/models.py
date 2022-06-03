"""
Cit Clientes Registros, modelos
"""
from citas_admin.extensions import db
from lib.universal_mixin import UniversalMixin


class CitClienteRegistro(db.Model, UniversalMixin):
    """CitClienteRegistro"""

    # Nombre de la tabla
    __tablename__ = "cit_clientes_registros"

    # Clave primaria
    id = db.Column(db.Integer, primary_key=True)

    # Columnas
    nombres = db.Column(db.String(256), nullable=False)
    apellido_primero = db.Column(db.String(256), nullable=False)
    apellido_segundo = db.Column(db.String(256), nullable=False, default="", server_default="")
    curp = db.Column(db.String(18), nullable=False, index=True)
    telefono = db.Column(db.String(64), nullable=False, default="", server_default="")
    email = db.Column(db.String(256), nullable=False, index=True)
    expiracion = db.Column(db.DateTime(), nullable=False)
    cadena_validar = db.Column(db.String(256), nullable=False)
    mensajes_cantidad = db.Column(db.Integer(), nullable=False, default=0)
    ya_registrado = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self):
        """Representación"""
        return "<CitClienteRegistro>"
