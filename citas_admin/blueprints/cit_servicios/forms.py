"""
Cit Servicios, formularios
"""

from datetime import time

from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, StringField, SubmitField, TimeField
from wtforms.validators import DataRequired, Length, Optional

from citas_admin.blueprints.cit_categorias.models import CitCategoria


class CitServicioForm(FlaskForm):
    """Formulario Cit Servicio"""

    cit_categoria = SelectField("Categoría", coerce=int, validators=[DataRequired()])
    clave = StringField("Clave", validators=[DataRequired(), Length(max=32)])
    descripcion = StringField("Descripción", validators=[DataRequired(), Length(max=64)])
    duracion = TimeField("Duración (horas:minutos)", validators=[DataRequired()], format="%H:%M", default=time(0, 30))
    documentos_limite = IntegerField("Cantidad límite de documentos (0 es ilimitado)", validators=[Optional()], default=0)
    desde = TimeField("Horario de comienzo (horas:minutos)", validators=[Optional()])
    hasta = TimeField("Horario de término (horas:minutos)", validators=[Optional()])
    dias_habilitados = StringField("Días habilitados", validators=[Optional()])
    guardar = SubmitField("Guardar")

    def __init__(self, *args, **kwargs):
        """Inicializar y cargar opciones para cit_categoria"""
        super().__init__(*args, **kwargs)
        self.cit_categoria.choices = [
            (c.id, c.nombre) for c in CitCategoria.query.filter_by(estatus="A").order_by(CitCategoria.nombre).all()
        ]
