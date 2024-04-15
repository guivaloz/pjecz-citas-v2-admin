"""
Citas, formularios
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DateField, SelectField, IntegerField, TimeField
from wtforms.validators import Length, Optional, DataRequired

from citas_admin.blueprints.distritos.models import Distrito


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
    distrito = SelectField("Distrito", coerce=int, validators=[DataRequired()])
    oficina = SelectField("Oficina", coerce=int, validate_choice=False, validators=[Optional()])
    buscar = SubmitField("Buscar")

    def __init__(self, *args, **kwargs):
        """Inicializar y cargar opciones de distritos"""
        super().__init__(*args, **kwargs)
        self.distrito.choices = [
            (d.id, d.clave + " - " + d.nombre_corto)
            for d in Distrito.query.filter_by(estatus="A").order_by(Distrito.clave).all()
        ]


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
