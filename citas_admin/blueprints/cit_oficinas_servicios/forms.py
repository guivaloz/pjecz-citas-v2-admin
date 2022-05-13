"""
Cit Oficinas-Servicios, formularios
"""
from flask import Flask
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from wtforms.ext.sqlalchemy.fields import QuerySelectField

from citas_admin.blueprints.cit_servicios.models import CitServicio
from citas_admin.blueprints.oficinas.models import Oficina


def cit_servicios_opciones():
    """Cit Servicios: opciones para select"""
    return CitServicio.query.filter_by(estatus="A").order_by(CitServicio.clave).all()


def oficinas_opciones():
    """Oficinas: opciones para select"""
    return Oficina.query.filter_by(estatus="A").order_by(Oficina.clave).all()


class CitOficinaServicioFormWithOficina(FlaskForm):
    """Formulario Autoridad-Servicio"""

    oficina = StringField("Oficina")  # Solo lectura
    cit_servicio = QuerySelectField(label="Servicio", query_factory=cit_servicios_opciones, get_label="compuesto", validators=[DataRequired()])
    guardar = SubmitField("Guardar")


class CitOficinaServicioFormWithCitServicio(FlaskForm):
    """Formulario Autoridad-Servicio"""

    oficina = QuerySelectField(label="Oficina", query_factory=oficinas_opciones, get_label="compuesto", validators=[DataRequired()])
    cit_servicio = StringField("Cit Servicio")  # Solo lectura
    guardar = SubmitField("Guardar")


class CitCategoriaAndDistritoForm(FlaskForm):
    """Formulario asignar servicios de una categoria a todas las oficinas de un distrito"""
