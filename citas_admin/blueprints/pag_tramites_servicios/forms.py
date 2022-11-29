"""
Pag Tramites Servicios, formularios
"""
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DecimalField
from wtforms.validators import DataRequired, Length, Optional


class PagTramiteServicioForm(FlaskForm):
    """Formulario PagTramiteServicio"""

    nombre = StringField("Nombre", validators=[DataRequired(), Length(max=256)])
    costo = DecimalField("Costo", validators=[DataRequired()])
    url = StringField("Página pjecz.gob.mx", validators=[Optional(), Length(max=512)])
    guardar = SubmitField("Guardar")
