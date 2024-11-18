"""
Cit Oficinas-Servicios, formularios
"""

from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField
from wtforms.validators import DataRequired

from citas_admin.blueprints.cit_servicios.models import CitServicio
from citas_admin.blueprints.oficinas.models import Oficina


class CitOficinaServicioWithCitServicioForm(FlaskForm):
    """Formulario para nuevo Cit Oficina-Servicio con un CitServicio"""

    cit_servicio = StringField("Servicio")  # Read only
    oficina = SelectField("Oficina", coerce=int, validators=[DataRequired()])
    guardar = SubmitField("Guardar")

    def __init__(self):
        """Inicializar y cargar opciones para oficina"""
        super().__init__()
        self.oficina.choices = [
            (o.id, o.clave + " - " + o.descripcion_corta)
            for o in Oficina.query.filter_by(estatus="A").order_by(Oficina.clave).all()
        ]


class CitOficinaServicioWithOficinaForm(FlaskForm):
    """Formulario para nuevo Cit Oficina-Servicio con una Oficina"""

    cit_servicio = SelectField("Servicio", coerce=int, validators=[DataRequired()])
    oficina = StringField("Oficina")  # Read only
    guardar = SubmitField("Guardar")

    def __init__(self):
        """Inicializar y cargar opciones para cit_servicio"""
        super().__init__()
        self.cit_servicio.choices = [
            (s.id, s.clave + " - " + s.descripcion)
            for s in CitServicio.query.filter_by(estatus="A").order_by(CitServicio.clave).all()
        ]
