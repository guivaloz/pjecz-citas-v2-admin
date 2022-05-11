"""
Cit Autoridades-Servicios, formularios
"""
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from wtforms.ext.sqlalchemy.fields import QuerySelectField

from citas_admin.blueprints.autoridades.models import Autoridad
from citas_admin.blueprints.cit_servicios.models import CitServicio


def autoridades_opciones():
    """Autoridades: opciones para select"""
    return Autoridad.query.filter_by(estatus="A").order_by(Autoridad.clave).all()


def cit_servicios_opciones():
    """Cit Servicios: opciones para select"""
    return CitServicio.query.filter_by(estatus="A").order_by(CitServicio.clave).all()


class CitAutoridadServicioFormWithAutoridad(FlaskForm):
    """Formulario Autoridad-Servicio"""

    autoridad = StringField("Autoridad")  # Solo lectura
    cit_servicio = QuerySelectField(query_factory=cit_servicios_opciones, get_label="compuesto", validators=[DataRequired()])
    guardar = SubmitField("Guardar")


class CitAutoridadServicioFormWithCitServicio(FlaskForm):
    """Formulario Autoridad-Servicio"""

    autoridad = QuerySelectField(query_factory=autoridades_opciones, get_label="compuesto", validators=[DataRequired()])
    cit_servicio = StringField("Cit Servicio")  # Solo lectura
    guardar = SubmitField("Guardar")
