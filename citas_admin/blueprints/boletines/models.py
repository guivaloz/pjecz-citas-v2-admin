"""
Boletines, modelos
"""
from collections import OrderedDict
from citas_admin.extensions import db
from lib.universal_mixin import UniversalMixin


class Boletin(db.Model, UniversalMixin):
    """Boletin"""

    ESTADOS = OrderedDict(
        [
            ("BORRADOR", "Borrador"),
            ("PROGRAMADO", "Programado"),
            ("ENVIADO", "Enviado"),
            ("CANCELADO", "Cancelado"),
        ]
    )

    # Nombre de la tabla
    __tablename__ = "boletines"

    # Clave primaria
    id = db.Column(db.Integer, primary_key=True)

    # Columnas
    envio_programado = db.Column(db.DateTime(), nullable=False)
    estado = db.Column(
        db.Enum(*ESTADOS, name="boletines_estados", native_enum=False),
        index=True,
        nullable=False,
    )
    asunto = db.Column(db.String(256), nullable=False)
    contenido = db.Column(db.JSON())
    puntero = db.Column(db.Integer, nullable=False, default=0)

    def __repr__(self):
        """Representación"""
        return "<Boletin>"
