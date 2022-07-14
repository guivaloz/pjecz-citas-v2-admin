"""
Cit Citas, modelos
"""
from collections import OrderedDict
from citas_admin.extensions import db
from lib.universal_mixin import UniversalMixin


class CitCitaStats(db.Model, UniversalMixin):
    """Registros de las estadísticas de Citas"""

    CAT_CITAS_TOTALES = "CITAS_TOTALES"
    CAT_SERVICIOS_TOP = "SERVICIOS_TOP"

    CATEGORIAS = [
        CAT_CITAS_TOTALES,
        CAT_SERVICIOS_TOP,
    ]

    SUBCAT_CITAS_TOTALES_HOY = "HOY"
    SUBCAT_CITAS_TOTALES_SEMANA = "SEMANA"
    SUBCAT_CITAS_TOTALES_MES = "MES"
    SUBCAT_CITAS_TOTALES_CINCO_MESES = "CINCO_MESES"
    SUBCAT_CITAS_TOTALES_ANO = "ANO"

    SUBCAT_SERVICIOS_TOP_CINCO_MAS = "5 MAS USADOS"

    SUBCATEGORIAS = [
        # CITAS_TOTALES
        SUBCAT_CITAS_TOTALES_HOY,
        SUBCAT_CITAS_TOTALES_SEMANA,
        SUBCAT_CITAS_TOTALES_MES,
        SUBCAT_CITAS_TOTALES_CINCO_MESES,
        SUBCAT_CITAS_TOTALES_ANO,
        # SERVICIOS_TOP
        SUBCAT_SERVICIOS_TOP_CINCO_MAS,
    ]

    # Nombre de la tabla
    __tablename__ = "cit_citas_stats"

    # Clave primaria
    id = db.Column(db.Integer, primary_key=True)

    # Columnas
    etiqueta = db.Column(db.String(), nullable=False)
    dato = db.Column(db.Integer(), nullable=False)
    categoria = db.Column(db.Enum(*CATEGORIAS, name="subcategorias", native_enum=False), nullable=False)
    subcategoria = db.Column(db.Enum(*SUBCATEGORIAS, name="subcategorias", native_enum=False), nullable=False)

    def __repr__(self):
        """Representación"""
        return f"<CitCitaStat {self.id}>"
