"""
Usuarios Oficinas, formularios
"""
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from wtforms.ext.sqlalchemy.fields import QuerySelectField

from citas_admin.blueprints.oficinas.models import Oficina


def oficinas_opciones():
    """Oficinas: opciones para select"""
    return Oficina.query.filter_by(estatus="A").order_by(Oficina.clave).all()


class UsuarioOficinaWithUsuarioForm(FlaskForm):
    """Formulario UsuarioOficina"""

    oficina = QuerySelectField(query_factory=oficinas_opciones, get_label="compuesto", validators=[DataRequired()])
    usuario = StringField("Usuario")  # Read only
    guardar = SubmitField("Guardar")
