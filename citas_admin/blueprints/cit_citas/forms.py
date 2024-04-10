"""
Citas, formularios
"""

from xmlrpc.client import DateTime
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DateField, SelectField, IntegerField, TimeField, RadioField
from wtforms.validators import Length, Optional, DataRequired
from wtforms.ext.sqlalchemy.fields import QuerySelectField

from citas_admin.blueprints.distritos.models import Distrito


def distritos_opciones():
    """Distritos: opciones para select"""
    return Distrito.query.filter_by(estatus="A").order_by(Distrito.nombre).all()


class CitCitaSearchForm(FlaskForm):
    """Buscar CitCita - Juzgados"""

    cliente = StringField("Cliente", validators=[Optional(), Length(max=64)])
    email = StringField("Email", validators=[Optional(), Length(max=64)])
    buscar = SubmitField("Buscar")


class CitCitaSearchAdminForm(FlaskForm):
    """Buscar CitCita - Administradores"""

    cliente = StringField("Cliente", validators=[Optional(), Length(max=64)])
    email = StringField("Email", validators=[Optional(), Length(max=64)])
    fecha = DateField("Fecha", validators=[Optional()])
    distrito = QuerySelectField(
        "Distrito",
        query_factory=distritos_opciones,
        get_label="nombre",
        allow_blank=True,
        blank_text="",
        validators=[Optional()],
    )
    oficina = SelectField(label="Oficina", coerce=int, validate_choice=False, validators=[Optional()])
    buscar = SubmitField("Buscar")


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
