"""
Cit Clientes, formularios
"""

from flask_wtf import FlaskForm
from wtforms import BooleanField, IntegerField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, Regexp

from lib.safe_string import EMAIL_REGEXP


class CitClienteForm(FlaskForm):
    """Formulario CitCliente"""

    nombres = StringField("Nombres", validators=[DataRequired(), Length(max=256)])
    apellido_primero = StringField("Primer apellido", validators=[DataRequired(), Length(max=256)])
    apellido_segundo = StringField("Segundo apellido", validators=[Optional(), Length(max=256)])
    curp = StringField("CURP", validators=[DataRequired(), Length(max=18)])
    telefono = StringField("Teléfono", validators=[DataRequired(), Length(max=64)])
    email = StringField(
        "Correo electrónico (único en la BD)", validators=[DataRequired(), Length(max=256), Regexp(EMAIL_REGEXP)]
    )
    limite_citas_pendientes = IntegerField("Límite de citas pendientes", validators=[DataRequired()])
    autoriza_mensajes = BooleanField("Autoriza mensajes")
    enviar_boletin = BooleanField("Enviar boletín")
    es_adulto_mayor = BooleanField("Es adulto mayor")
    es_mujer = BooleanField("Es mujer")
    es_identidad = BooleanField("Es identidad")
    es_discapacidad = BooleanField("Es discapacidad")
    es_personal_interno = BooleanField("Es personal interno")
    guardar = SubmitField("Guardar")
