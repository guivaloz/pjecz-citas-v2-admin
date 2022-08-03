"""
Citas, formularios
"""
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DateField
from wtforms.validators import Length, Optional
from wtforms.ext.sqlalchemy.fields import QuerySelectField

from citas_admin.blueprints.distritos.models import Distrito
from citas_admin.blueprints.oficinas.models import Oficina


def distritos_opciones():
    """Distritos: opciones para select"""
    return Distrito.query.filter_by(estatus="A").order_by(Distrito.nombre).all()


class CitCitaSearchForm(FlaskForm):
    """Buscar CitCita - Juzgados"""

    cliente = StringField("Cliente", validators=[Optional(), Length(max=64)])
    email = StringField("Email", validators=[Optional(), Length(max=64)])
    buscar = SubmitField("Buscar")


class CitCitaSearchAdminForm(FlaskForm):
    """Buscar CitCita - Administradores"""

    cliente = StringField("Cliente", validators=[Optional(), Length(max=64)])
    email = StringField("Email", validators=[Optional(), Length(max=64)])
    fecha = DateField("Fecha", validators=[Optional()])
    distrito = QuerySelectField("Distrito", query_factory=distritos_opciones, get_label="nombre", allow_blank=True, blank_text="", validators=[Optional()])
    # oficina =
    buscar = SubmitField("Buscar")
