"""
Cit_Tramites_Servicios, modelos
"""
from citas_admin.extensions import db
from lib.universal_mixin import UniversalMixin


class CitTramiteServicio(db.Model, UniversalMixin):
    """CitTramiteServicio"""

    # Nombre de la tabla
    __tablename__ = 'cit_tramites_servicios'

    # Clave primaria
    id = db.Column(db.Integer, primary_key=True)

    # Columnas
    nombre = db.Column(db.String(256), nullable=False)
    costo = db.Column(db.Numeric(12, 2), nullable=False)
    url = db.Column(db.String(512))

    def __repr__(self):
        """ Representación """
        return f'<CitTramiteServicio> {self.id}'
