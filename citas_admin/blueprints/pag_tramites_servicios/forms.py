"""
Pag Tramites Servicios, formularios
"""
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DecimalField
from wtforms.validators import DataRequired, Length, Optional


class PagTramiteServicioForm(FlaskForm):
    """Formulario PagTramiteServicio"""

    clave = StringField("Clave", validators=[DataRequired(), Length(max=256)])
    descripcion = StringField("Descripción", validators=[DataRequired(), Length(max=256)])
    costo = DecimalField("Costo", validators=[DataRequired()])
    url = StringField("Página pjecz.gob.mx", validators=[Optional(), Length(max=512)])
    guardar = SubmitField("Guardar")
