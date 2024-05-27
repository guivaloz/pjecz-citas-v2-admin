"""
Usuarios-Oficinas, formularios
"""

from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField
from wtforms.validators import DataRequired

from citas_admin.blueprints.oficinas.models import Oficina
from citas_admin.blueprints.usuarios.models import Usuario


class UsuarioOficinaWithUsuarioForm(FlaskForm):
    """Formulario para crear un Usuario-Oficina con un Usuario dado"""

    oficina = SelectField("Oficina", coerce=int, validators=[DataRequired()])
    usuario_email = StringField("Usuario e-mail")  # Read only
    usuario_nombre = StringField("Usuario nombre")  # Read only
    guardar = SubmitField("Guardar")

    def __init__(self, *args, **kwargs):
        """Inicializar y cargar opciones de oficina"""
        super().__init__(*args, **kwargs)
        self.oficina.choices = [
            (o.id, o.clave + " - " + o.descripcion_corta)
            for o in Oficina.query.filter_by(estatus="A").order_by(Oficina.clave).all()
        ]


class UsuarioOficinaWithOficinaForm(FlaskForm):
    """Formulario para crear un Usuario-Oficina con una Oficina dada"""

    oficina = StringField("Oficina")  # Read only
    usuario = SelectField("Usuario", coerce=int, validators=[DataRequired()])
    guardar = SubmitField("Guardar")

    def __init__(self, *args, **kwargs):
        """Inicializar y cargar opciones de usuario"""
        super().__init__(*args, **kwargs)
        self.usuario.choices = [(u.id, u.email) for u in Usuario.query.filter_by(estatus="A").order_by(Usuario.email).all()]
