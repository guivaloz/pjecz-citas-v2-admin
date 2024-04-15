"""
Cit Oficinas-Servicios, formularios
"""

from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField
from wtforms.validators import DataRequired

from citas_admin.blueprints.cit_categorias.models import CitCategoria
from citas_admin.blueprints.cit_servicios.models import CitServicio
from citas_admin.blueprints.distritos.models import Distrito
from citas_admin.blueprints.oficinas.models import Oficina


class CitOficinaServicioFormWithOficina(FlaskForm):
    """Formulario Autoridad-Servicio"""

    oficina = StringField("Oficina")  # Read only
    cit_servicio = SelectField("Servicio", coerce=int, validators=[DataRequired()])
    guardar = SubmitField("Guardar")

    def __init__(self, *args, **kwargs):
        """Inicializar y cargar opciones de servicios"""
        super().__init__(*args, **kwargs)
        self.cit_servicio.choices = [
            (s.id, s.clave + " - " + s.descripcion)
            for s in CitServicio.query.filter_by(estatus="A").order_by(CitServicio.clave).all()
        ]


class CitOficinaServicioFormWithCitServicio(FlaskForm):
    """Formulario Autoridad-Servicio"""

    oficina = SelectField("Oficina", coerce=int, validators=[DataRequired()])
    cit_servicio = StringField("Cit Servicio")  # Read only
    guardar = SubmitField("Guardar")

    def __init__(self, *args, **kwargs):
        """Inicializar y cargar opciones de oficinas"""
        super().__init__(*args, **kwargs)
        self.oficina.choices = [
            (o.id, o.clave + " - " + o.descripcion_corta)
            for o in Oficina.query.filter_by(estatus="A").order_by(Oficina.clave).all()
        ]


class CitOficinaServicioFormWithCitCategoria(FlaskForm):
    """Formulario asignar servicios de una categoria a todas las oficinas de un distrito"""

    cit_categoria = StringField("Categoría")  # Read only
    distrito = SelectField("Distrito", coerce=int, validators=[DataRequired()])
    guardar = SubmitField("Asignar los servicios a las oficinas")

    def __init__(self, *args, **kwargs):
        """Inicializar y cargar opciones de distritos"""
        super().__init__(*args, **kwargs)
        self.distrito.choices = [
            (d.id, d.clave + " - " + d.nombre_corto)
            for d in Distrito.query.filter_by(estatus="A").order_by(Distrito.clave).all()
        ]


class CitOficinaServicioFormWithDistrito(FlaskForm):
    """Formulario asignar servicios de una categoria a todas las oficinas de un distrito"""

    cit_categoria = SelectField("Categoría", coerce=int, validators=[DataRequired()])
    distrito = StringField("Distrito")  # Read only
    guardar = SubmitField("Asignar los servicios a las oficinas")

    def __init__(self, *args, **kwargs):
        """Inicializar y cargar opciones de categorias"""
        super().__init__(*args, **kwargs)
        self.cit_categoria.choices = [
            (c.id, c.clave + " - " + c.nombre)
            for c in CitCategoria.query.filter_by(estatus="A").order_by(CitCategoria.clave).all()
        ]
