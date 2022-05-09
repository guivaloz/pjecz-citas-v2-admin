"""
Cit Servicios, formularios
"""
from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField, SubmitField, TimeField
from wtforms.validators import DataRequired, Length, Optional
from wtforms.ext.sqlalchemy.fields import QuerySelectField

from citas_admin.blueprints.cit_categorias.models import CitCategoria


def cit_categorias_opciones():
    """Categorias: opciones para select"""
    return CitCategoria.query.filter_by(estatus="A").order_by(CitCategoria.nombre).all()


class CitServicioForm(FlaskForm):
    """Formulario CITDíasInhabiles"""

    categoria = QuerySelectField(query_factory=cit_categorias_opciones, get_label="nombre")
    clave = StringField("Clave", validators=[DataRequired(), Length(max=32)])
    descripcion = StringField("Descripcion", validators=[Optional(), Length(max=256)])
    duracion = TimeField("Duración (horas:minutos)", validators=[DataRequired()], format="%H:%M")
    documentos_limite = IntegerField("Documentos limite", validators=[DataRequired()])

    guardar = SubmitField("Guardar")
