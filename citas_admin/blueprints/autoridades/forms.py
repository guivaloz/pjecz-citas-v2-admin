"""
Autoridades, formularios
"""

from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, Regexp

from lib.safe_string import CLAVE_REGEXP
from citas_admin.blueprints.distritos.models import Distrito


class AutoridadForm(FlaskForm):
    """Formulario Autoridad"""

    distrito = SelectField("Distrito", coerce=int, validators=[DataRequired()])
    descripcion = StringField("Descripción", validators=[DataRequired(), Length(max=256)])
    descripcion_corta = StringField("Descripción corta (máximo 64 caracteres)", validators=[DataRequired(), Length(max=64)])
    clave = StringField("Clave (hasta 16 caracteres)", validators=[DataRequired(), Regexp(CLAVE_REGEXP)])
    guardar = SubmitField("Guardar")

    def __init__(self, *args, **kwargs):
        """Inicializar y cargar opciones de distritos"""
        super().__init__(*args, **kwargs)
        self.distrito.choices = [
            (d.id, d.clave + " - " + d.nombre_corto)
            for d in Distrito.query.filter_by(estatus="A").order_by(Distrito.clave).all()
        ]
