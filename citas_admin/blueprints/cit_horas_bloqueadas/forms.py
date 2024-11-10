"""
Cit Horas Bloqueadas, formularios
"""

from flask_wtf import FlaskForm
from wtforms import DateField, SelectField, StringField, SubmitField, TimeField
from wtforms.validators import DataRequired, Length


class CitHoraBloqueadaForm(FlaskForm):
    """Formulario CitHoraBloqueada"""

    oficina = StringField("Oficina")  # Read Only
    fecha = DateField("Fecha", validators=[DataRequired()])
    inicio_tiempo = TimeField("Inicio", validators=[DataRequired()])
    termino_tiempo = TimeField("Término", validators=[DataRequired()])
    descripcion = StringField("Descripción", validators=[DataRequired(), Length(max=256)])
    guardar = SubmitField("Guardar")


class CitHoraBloqueadaAdminForm(FlaskForm):
    """Formulario CitHoraBloqueada"""

    oficina = SelectField("Oficina", coerce=int, validate_choice=False, validators=[DataRequired()])  # Select2
    fecha = DateField("Fecha", validators=[DataRequired()])
    inicio_tiempo = TimeField("Inicio", validators=[DataRequired()])
    termino_tiempo = TimeField("Término", validators=[DataRequired()])
    descripcion = StringField("Descripción", validators=[DataRequired(), Length(max=256)])
    guardar = SubmitField("Guardar")
