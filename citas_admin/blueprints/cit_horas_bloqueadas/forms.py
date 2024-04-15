"""
Cit Horas Bloqueadas, formularios
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DateField, TimeField, SelectField
from wtforms.validators import DataRequired, Optional

from citas_admin.blueprints.oficinas.models import Oficina


class CitHoraBloqueadaAdminForm(FlaskForm):
    """Formulario CitHoraBloqueda"""

    oficina = SelectField("Oficina", coerce=int, validate_choice=False)
    fecha = DateField("Fecha", validators=[DataRequired()])
    inicio_tiempo = TimeField("Tiempo de inicio", validators=[DataRequired()])
    termino_tiempo = TimeField("Tiempo de termino", validators=[DataRequired()])
    descripcion = StringField("Descripción", validators=[Optional()])
    guardar = SubmitField("Guardar")

    def __init__(self, *args, **kwargs):
        """Inicializar y cargar opciones de oficinas"""
        super().__init__(*args, **kwargs)
        self.oficina.choices = [
            (o.id, o.clave + " - " + o.descripcion_corta)
            for o in Oficina.query.filter_by(estatus="A").order_by(Oficina.clave).all()
        ]


class CitHoraBloqueadaForm(FlaskForm):
    """Formulario CitHoraBloqueda"""

    oficina = StringField(label="Oficina")  # Read Only
    fecha = DateField("Fecha", validators=[DataRequired()])
    inicio_tiempo = TimeField("Tiempo de inicio", validators=[DataRequired()])
    termino_tiempo = TimeField("Tiempo de termino", validators=[DataRequired()])
    descripcion = StringField("Descripción", validators=[Optional()])
    guardar = SubmitField("Guardar")
