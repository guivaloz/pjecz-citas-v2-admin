"""
Boletines, formularios
"""
from flask_wtf import FlaskForm
from wtforms import DateField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional

from lib.wtforms import JSONField

from .models import Boletin


class BoletinForm(FlaskForm):
    """Formulario Boletin"""

    envio_programado = DateField("Fecha de envío programado", validators=[DataRequired()])
    estado = SelectField("Estado", choices=Boletin.ESTADOS, validators=[DataRequired()])
    asunto = StringField("Asunto", validators=[DataRequired(), Length(max=256)])
    contenido = JSONField("Contenido", validators=[Optional()])
    guardar = SubmitField("Guardar")
