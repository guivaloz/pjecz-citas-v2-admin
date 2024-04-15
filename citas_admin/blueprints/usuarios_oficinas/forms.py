"""
Usuarios Oficinas, formularios
"""

from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField
from wtforms.validators import DataRequired

from citas_admin.blueprints.oficinas.models import Oficina


class UsuarioOficinaWithUsuarioForm(FlaskForm):
    """Formulario UsuarioOficina"""

    oficina = SelectField("Oficina", coerce=int, validators=[DataRequired()])
    usuario = StringField("Usuario")  # Read only
    guardar = SubmitField("Guardar")

    def __init__(self, *args, **kwargs):
        """Inicializar y cargar opciones de oficinas"""
        super().__init__(*args, **kwargs)
        self.oficina.choices = [
            (o.id, o.clave + " - " + o.descripcion_corta)
            for o in Oficina.query.filter_by(estatus="A").order_by(Oficina.clave).all()
        ]
