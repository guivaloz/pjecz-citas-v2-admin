"""
Cit Citas, modelos
"""
from collections import OrderedDict
from citas_admin.extensions import db
from lib.universal_mixin import UniversalMixin


class CitCitaStats(db.Model, UniversalMixin):
    """Registros de las estadísticas de Citas"""

    TIPOS = OrderedDict(
        [
            ("HOY", "Hoy"),
            ("SEMANA", "Semana"),
            ("MES", "Mes"),
            ("CINCO_MESES", "Cinco Meses"),
            ("ANO", "Año"),
        ]
    )

    # Nombre de la tabla
    __tablename__ = "cit_citas_stats"

    # Clave primaria
    id = db.Column(db.Integer, primary_key=True)

    # Columnas
    etiqueta = db.Column(db.String(), nullable=False)
    dato = db.Column(db.Integer(), nullable=False)
    tipo = db.Column(db.Enum(*TIPOS, name="tipos", native_enum=False), nullable=False)

    def __repr__(self):
        """Representación"""
        return f"<CitCitaStat {self.id}>"
