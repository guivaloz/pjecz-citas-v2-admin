"""
Cit Tramites y Servicios, formularios
"""
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DecimalField
from wtforms.validators import DataRequired, Length, Optional


class CitTramiteServicioForm(FlaskForm):
    """Formulario CitTramiteServicio"""

    nombre = StringField("Nombre", validators=[DataRequired(), Length(max=256)])
    costo = DecimalField("Costo", validators=[DataRequired()])
    url = StringField("URL", validators=[Optional(), Length(max=512)])
    guardar = SubmitField("Guardar")
