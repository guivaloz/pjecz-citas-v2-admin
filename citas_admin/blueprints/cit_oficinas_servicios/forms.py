"""
Cit Oficinas-Servicios, formularios
"""
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from wtforms.ext.sqlalchemy.fields import QuerySelectField

from citas_admin.blueprints.cit_categorias.models import CitCategoria
from citas_admin.blueprints.cit_servicios.models import CitServicio
from citas_admin.blueprints.distritos.models import Distrito
from citas_admin.blueprints.oficinas.models import Oficina


def cit_categorias_opciones():
    """Cit Categorias: opciones para select"""
    return CitCategoria.query.filter_by(estatus="A").order_by(CitCategoria.nombre).all()


def cit_servicios_opciones():
    """Cit Servicios: opciones para select"""
    return CitServicio.query.filter_by(estatus="A").order_by(CitServicio.clave).all()


def distritos_opciones():
    """Distritos: opciones para select"""
    return Distrito.query.filter_by(estatus="A").order_by(Distrito.nombre).all()


def oficinas_opciones():
    """Oficinas: opciones para select"""
    return Oficina.query.filter_by(estatus="A").order_by(Oficina.clave).all()


class CitOficinaServicioFormWithOficina(FlaskForm):
    """Formulario Autoridad-Servicio"""

    oficina = StringField("Oficina")  # Read only
    cit_servicio = QuerySelectField(label="Servicio", query_factory=cit_servicios_opciones, get_label="compuesto", validators=[DataRequired()])
    guardar = SubmitField("Guardar")


class CitOficinaServicioFormWithCitServicio(FlaskForm):
    """Formulario Autoridad-Servicio"""

    oficina = QuerySelectField(label="Oficina", query_factory=oficinas_opciones, get_label="compuesto", validators=[DataRequired()])
    cit_servicio = StringField("Cit Servicio")  # Read only
    guardar = SubmitField("Guardar")


class CitOficinaServicioFormWithCitCategoria(FlaskForm):
    """Formulario asignar servicios de una categoria a todas las oficinas de un distrito"""

    cit_categoria = StringField("Categoría")  # Read only
    distrito = QuerySelectField(query_factory=distritos_opciones, get_label="nombre")
    guardar = SubmitField("Asignar los servicios a las oficinas")


class CitOficinaServicioFormWithDistrito(FlaskForm):
    """Formulario asignar servicios de una categoria a todas las oficinas de un distrito"""

    cit_categoria = QuerySelectField(query_factory=cit_categorias_opciones, get_label="nombre")
    distrito = StringField("Distrito")  # Read only
    guardar = SubmitField("Asignar los servicios a las oficinas")
