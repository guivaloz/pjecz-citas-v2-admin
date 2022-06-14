"""
Cit Pagos, formularios
"""
from flask_wtf import FlaskForm
from wtforms import DecimalField, StringField, SubmitField
from wtforms.validators import DataRequired, Length


class CitPagoForm(FlaskForm):
    """Formulario CitPago"""

    cit_cliente_nombre = StringField("Cliente")  # Read only
    descripcion = StringField("Descripción", validators=[DataRequired(), Length(max=256)])
    total = DecimalField("Total", validators=[DataRequired()])
    guardar = SubmitField("Guardar")
