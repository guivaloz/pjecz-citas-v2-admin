"""
Citas, formularios
"""
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import Length, Optional


class CitCitaSearchForm(FlaskForm):
    """Buscar CitCita"""

    cliente = StringField("Cliente", validators=[Optional(), Length(max=64)])
    email = StringField("email", validators=[Optional(), Length(max=64)])
    buscar = SubmitField("Buscar")
