"""
Citas, formularios
"""
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DateField
from wtforms.validators import Length, Optional


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
    # distrito =
    # oficina =
    buscar = SubmitField("Buscar")
