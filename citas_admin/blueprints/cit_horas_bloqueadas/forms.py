"""
Cit Horas Bloqueadas, formularios
"""
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DateField, TimeField, SelectField
from wtforms.validators import DataRequired, Optional


class CitHoraBloqueadaAdminForm(FlaskForm):
    """Formulario CitHoraBloqueda"""

    oficina = SelectField(label="Oficina", coerce=int, validate_choice=False)
    fecha = DateField("Fecha", validators=[DataRequired()])
    inicio_tiempo = TimeField("Tiempo de inicio", validators=[DataRequired()])
    termino_tiempo = TimeField("Tiempo de termino", validators=[DataRequired()])
    descripcion = StringField("Descripción", validators=[Optional()])
    guardar = SubmitField("Guardar")


class CitHoraBloqueadaForm(FlaskForm):
    """Formulario CitHoraBloqueda"""

    oficina = StringField(label="Oficina")  # Read Only
    fecha = DateField("Fecha", validators=[DataRequired()])
    inicio_tiempo = TimeField("Tiempo de inicio", validators=[DataRequired()])
    termino_tiempo = TimeField("Tiempo de termino", validators=[DataRequired()])
    descripcion = StringField("Descripción", validators=[Optional()])
    guardar = SubmitField("Guardar")
