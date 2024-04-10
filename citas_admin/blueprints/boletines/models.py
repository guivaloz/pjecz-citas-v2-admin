"""
Boletines, modelos
"""

from sqlalchemy import Column, DateTime, Enum, Integer, String, JSON
from sqlalchemy.orm import relationship

from lib.universal_mixin import UniversalMixin
from citas_admin.extensions import database


class Boletin(database.Model, UniversalMixin):
    """Boletin"""

    ESTADOS = {
        "BORRADOR": "Borrador",
        "PROGRAMADO": "Programado",
        "ENVIADO": "Enviado",
    }

    # Nombre de la tabla
    __tablename__ = "boletines"

    # Clave primaria
    id = Column(Integer, primary_key=True)

    # Columnas
    envio_programado = Column(DateTime(), nullable=False)
    estado = Column(
        Enum(*ESTADOS, name="boletines_estados", native_enum=False),
        index=True,
        nullable=False,
    )
    asunto = Column(String(256), nullable=False)
    contenido = Column(JSON())
    puntero = Column(Integer, nullable=False, default=0)

    def __repr__(self):
        """Representación"""
        return "<Boletin>"
