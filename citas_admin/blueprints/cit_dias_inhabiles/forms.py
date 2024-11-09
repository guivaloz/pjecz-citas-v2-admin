"""
Cit Dias Inhábiles, formularios
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length


class CitDiaInhabilForm(FlaskForm):
    """Formulario CitDiaInhabil"""

    fecha = StringField("Fecha", validators=[DataRequired()])
    descripcion = StringField("Descripción", validators=[DataRequired(), Length(max=256)])
    guardar = SubmitField("Guardar")
