"""
Cit Citas, modelos
"""

from sqlalchemy import Column, Enum, Integer, String
from sqlalchemy.orm import relationship

from lib.universal_mixin import UniversalMixin
from citas_admin.extensions import database


class CitCitaStats(database.Model, UniversalMixin):
    """Registros de las estadísticas de Citas"""

    CAT_CITAS_TOTALES = "CITAS_TOTALES"
    CAT_CITAS_ESTADO = "CITAS_ESTADO"

    CATEGORIAS = [
        CAT_CITAS_TOTALES,
        CAT_CITAS_ESTADO,
    ]

    SUBCAT_CITAS_TOTALES_HOY = "HOY"
    SUBCAT_CITAS_TOTALES_SEMANA = "SEMANA"
    SUBCAT_CITAS_TOTALES_MES = "MES"
    SUBCAT_CITAS_TOTALES_CINCO_MESES = "CINCO_MESES"
    SUBCAT_CITAS_TOTALES_ANO = "ANO"

    SUBCAT_CITAS_ESTADO_PORCENTAJE = "PORCENTAJE"

    SUBCATEGORIAS = [
        # CITAS_TOTALES
        SUBCAT_CITAS_TOTALES_HOY,
        SUBCAT_CITAS_TOTALES_SEMANA,
        SUBCAT_CITAS_TOTALES_MES,
        SUBCAT_CITAS_TOTALES_CINCO_MESES,
        SUBCAT_CITAS_TOTALES_ANO,
        # CAT_CITAS_ESTADO
        SUBCAT_CITAS_ESTADO_PORCENTAJE,
    ]

    # Nombre de la tabla
    __tablename__ = "cit_citas_stats"

    # Clave primaria
    id = Column(Integer, primary_key=True)

    # Columnas
    etiqueta = Column(String(), nullable=False)
    dato = Column(Integer(), nullable=False)
    categoria = Column(Enum(*CATEGORIAS, name="subcategorias", native_enum=False), nullable=False)
    subcategoria = Column(Enum(*SUBCATEGORIAS, name="subcategorias", native_enum=False), nullable=False)

    def __repr__(self):
        """Representación"""
        return f"<CitCitaStat {self.id}>"
