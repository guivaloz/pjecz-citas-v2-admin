"""
Cit Servicios, formularios
"""
from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField, SubmitField, TimeField
from wtforms.validators import DataRequired, Length, Optional


class CitServicioForm(FlaskForm):
    """Formulario CITDíasInhabiles"""

    cit_categoria_nombre = StringField("Categoria")  # Read only
    clave = StringField("Clave", validators=[DataRequired(), Length(max=32)])
    descripcion = StringField("Descripcion", validators=[DataRequired(), Length(max=64)])
    duracion = TimeField("Duración (horas:minutos)", validators=[DataRequired()], format="%H:%M")
    documentos_limite = IntegerField("Documentos limite", validators=[Optional()])
    desde = TimeField("Horario de comienzo para agendar citas (horas:minutos)", validators=[Optional()])
    hasta = TimeField("Horario de termino para agendar citas (horas:minutos)", validators=[Optional()])
    dias_habilitados = StringField("Días Hábiles", validators=[Optional()])
    guardar = SubmitField("Guardar")
