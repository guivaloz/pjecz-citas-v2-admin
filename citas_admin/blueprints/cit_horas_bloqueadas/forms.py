"""
Cit Horas Bloqueadas, formularios
"""
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DateField, TimeField, SelectField
from wtforms.validators import DataRequired, Length, Optional


class CitHoraBloqueadaForm(FlaskForm):
    """Formulario CitDíasInhabiles"""

    oficina_id = SelectField(label="Oficina", coerce=int, validate_choice=False, validators=[DataRequired()])
    fecha = DateField("Fecha", validators=[DataRequired()])
    inicio_tiempo = TimeField("Tiempo de Inicio", validators=[DataRequired()])
    termino_tiempo = TimeField("Teimpo de Termino", validators=[DataRequired()])
    descripcion = StringField("Descripción", validators=[Optional(), Length(max=512)])
    guardar = SubmitField("Guardar")
