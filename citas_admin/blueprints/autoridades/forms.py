"""
Autoridades, formularios
"""

from flask_wtf import FlaskForm
from wtforms import BooleanField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, Regexp

from citas_admin.blueprints.autoridades.models import Autoridad
from citas_admin.blueprints.distritos.models import Distrito
from citas_admin.blueprints.materias.models import Materia
from lib.safe_string import CLAVE_REGEXP


class AutoridadForm(FlaskForm):
    """Formulario Autoridad"""

    distrito = SelectField("Distrito", coerce=int, validators=[DataRequired()])
    materia = SelectField("Materia", coerce=int, validators=[DataRequired()])
    clave = StringField("Clave (única de hasta 16 caracteres)", validators=[DataRequired(), Regexp(CLAVE_REGEXP)])
    descripcion = StringField("Descripción", validators=[DataRequired(), Length(max=256)])
    descripcion_corta = StringField("Descripción corta (máximo 64 caracteres)", validators=[DataRequired(), Length(max=64)])
    es_jurisdiccional = BooleanField("Es Jurisdiccional", validators=[Optional()])
    es_notaria = BooleanField("Es Notaría", validators=[Optional()])
    es_organo_especializado = BooleanField("Es Órgano Especializado", validators=[Optional()])
    organo_jurisdiccional = SelectField(
        "Órgano Jurisdiccional", choices=Autoridad.ORGANOS_JURISDICCIONALES.items(), validators=[DataRequired()]
    )
    guardar = SubmitField("Guardar")

    def __init__(self, *args, **kwargs):
        """Inicializar y cargar opciones en distrito y materia"""
        super().__init__(*args, **kwargs)
        self.distrito.choices = [
            (d.id, d.nombre_corto) for d in Distrito.query.filter_by(estatus="A").order_by(Distrito.nombre_corto).all()
        ]
        self.materia.choices = [(m.id, m.nombre) for m in Materia.query.filter_by(estatus="A").order_by(Materia.nombre).all()]
