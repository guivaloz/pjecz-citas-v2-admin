"""
Cit Horas Bloqueadas, formularios
"""
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DateField, TimeField
from wtforms.validators import DataRequired


class CitHoraBloqueadaForm(FlaskForm):
    """Formulario CitDíasInhabiles"""

    oficina = StringField("Oficina")  # Read only
    fecha = DateField("Fecha", validators=[DataRequired()])
    inicio = TimeField("Tiempo de inicio", validators=[DataRequired()])
    termino = TimeField("Tiempo de termino", validators=[DataRequired()])
    guardar = SubmitField("Guardar")
