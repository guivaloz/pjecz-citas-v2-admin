"""
Clientes, formularios
"""
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import Length, Optional, Required


class ClienteEditForm(FlaskForm):
    """Formulario Edición de Clientes"""

    nombres = StringField("Nombres", validators=[Required()])
    apellido_primero = StringField("Apellido Primero", validators=[Required(), Length(max=256)])
    apellido_segundo = StringField("Apellido Segundo", validators=[Optional(), Length(max=256)])
    curp = StringField("CURP", validators=[Required(), Length(max=18)])
    email = StringField("Email", validators=[Required(), Length(max=256)])
    telefono = StringField("Teléfono", validators=[Optional(), Length(max=64)])
    guardar = SubmitField("Guardar")
