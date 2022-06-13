"""
Cit Horas Bloqueadas, formularios
"""
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DateField, TimeField, SelectField
from wtforms.validators import DataRequired, Optional


class CitHoraBloqueadaForm(FlaskForm):
    """Formulario CitDíasInhabiles"""

    oficina = SelectField(label="Oficina", coerce=int, validate_choice=False)
    fecha = DateField("Fecha", validators=[DataRequired()])
    inicio_tiempo = TimeField("Tiempo de inicio", validators=[DataRequired()])
    termino_tiempo = TimeField("Tiempo de termino", validators=[DataRequired()])
    descripcion = StringField("Descripción", validators=[Optional()])
    guardar = SubmitField("Guardar")
