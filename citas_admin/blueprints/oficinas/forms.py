"""
Oficinas, formularios
"""

from flask_wtf import FlaskForm
from wtforms import BooleanField, IntegerField, SelectField, StringField, SubmitField, TimeField
from wtforms.validators import DataRequired, Length, Optional

from citas_admin.blueprints.distritos.models import Distrito
from citas_admin.blueprints.domicilios.models import Domicilio


class OficinaForm(FlaskForm):
    """Formulario Oficina"""

    clave = StringField("Clave", validators=[DataRequired(), Length(max=32)])
    descripcion = StringField("Descripción", validators=[DataRequired(), Length(max=512)])
    descripcion_corta = StringField("Descripción Corta", validators=[DataRequired(), Length(max=64)])
    distrito = SelectField("Distrito", coerce=int, validators=[DataRequired()])
    domicilio = SelectField("Domicilio", coerce=int, validators=[DataRequired()])
    apertura = TimeField("Horario de apertura", validators=[DataRequired()], format="%H:%M")
    cierre = TimeField("Horario de cierre", validators=[DataRequired()], format="%H:%M")
    limite_personas = IntegerField("Límite de personas", validators=[DataRequired()])
    es_jurisdiccional = BooleanField("Es Jurisdiccional", validators=[Optional()])
    puede_agendar_citas = BooleanField("Puede agendar citas", validators=[Optional()])
    puede_enviar_qr = BooleanField("Puede enviar códigos QR", validators=[Optional()])
    guardar = SubmitField("Guardar")

    def __init__(self, *args, **kwargs):
        """Inicializar y cargar opciones en distrito y domicilio"""
        super().__init__(*args, **kwargs)
        self.distrito.choices = [
            (d.id, d.nombre_corto) for d in Distrito.query.filter_by(estatus="A").order_by(Distrito.nombre_corto).all()
        ]
        self.domicilio.choices = [
            (d.id, d.edificio) for d in Domicilio.query.filter_by(estatus="A").order_by(Domicilio.edificio).all()
        ]
