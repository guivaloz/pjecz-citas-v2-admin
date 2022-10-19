"""
Clientes, formularios
"""
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, IntegerField, PasswordField
from wtforms.validators import Length, Optional, Required, NumberRange, Regexp, EqualTo

from lib.safe_string import CONTRASENA_REGEXP


CONTRASENA_MENSAJE = "De 8 a 48 caracteres con al menos una mayúscula, una minúscula y un número. No acentos, ni eñe."


class CitClienteEditForm(FlaskForm):
    """Formulario Edición de Clientes"""

    nombres = StringField("Nombres", validators=[Required()])
    apellido_primero = StringField("Apellido Primero", validators=[Required(), Length(max=256)])
    apellido_segundo = StringField("Apellido Segundo", validators=[Optional(), Length(max=256)])
    curp = StringField("CURP", validators=[Required(), Length(max=18)])
    email = StringField("Email", validators=[Required(), Length(max=256)])
    telefono = StringField("Teléfono", validators=[Optional(), Length(max=64)])
    limite_citas = IntegerField("Límite de Citas", validators=[Optional(), NumberRange(min=0, max=500)])
    recibir_boletin = BooleanField("Recibir Boletín")
    guardar = SubmitField("Guardar")


class CitClienteNewForm(FlaskForm):
    """Nuevo Cliente"""

    nombres = StringField("Nombres", validators=[Required()])
    apellido_primero = StringField("Apellido Primero", validators=[Required(), Length(max=256)])
    apellido_segundo = StringField("Apellido Segundo", validators=[Optional(), Length(max=256)])
    curp = StringField("CURP", validators=[Required(), Length(max=18)])
    email = StringField("Email", validators=[Required(), Length(max=256)])
    telefono = StringField("Teléfono", validators=[Optional(), Length(max=64)])
    contrasena = PasswordField(
        "Contraseña",
        validators=[
            Required(),
            Regexp(CONTRASENA_REGEXP, 0, CONTRASENA_MENSAJE),
            EqualTo("contrasena_repetir", message="Las contraseñas deben coincidir."),
        ],
    )
    contrasena_repetir = PasswordField("Repetir contraseña", validators=[Required()])
    guardar = SubmitField("Guardar")
