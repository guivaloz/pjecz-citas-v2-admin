"""
Citas, formularios
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DateField, SelectField, IntegerField, TimeField
from wtforms.validators import Length, Optional, DataRequired

from citas_admin.blueprints.distritos.models import Distrito


class CitCitaAssistance(FlaskForm):
    """Marcar asistencia con el código de verificación"""

    cita_id = IntegerField("Cita ID", validators=[DataRequired()])
    cliente = StringField("Cliente", validators=[Optional()])
    codigo = StringField("Código de Verificación", validators=[DataRequired(), Length(min=4, max=4)])
    guardar = SubmitField("Marcar Asistencia")


class CitCitaNew(FlaskForm):
    """Nueva cita inmediata"""

    # cliente_id = IntegerField("Cliente ID", validators=[DataRequired()])
    oficina_id = IntegerField("Oficina ID", validators=[DataRequired()])
    servicio_id = IntegerField("Servicio ID", validators=[DataRequired()])
    horario = TimeField("Horario", validators=[DataRequired()])
    btnEnviar = SubmitField("Crear")
