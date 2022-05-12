"""
Cit Oficinas-Servicios, tareas para ejecutar en el fondo
"""
import logging

from lib.tasks import set_task_progress, set_task_error

from citas_admin.app import create_app
from citas_admin.extensions import db

from citas_admin.blueprints.cit_categorias.models import CitCategoria
from citas_admin.blueprints.distritos.models import Distrito

bitacora = logging.getLogger(__name__)
bitacora.setLevel(logging.INFO)
formato = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
empunadura = logging.FileHandler("cit_oficinas_servicios.log")
empunadura.setFormatter(formato)
bitacora.addHandler(empunadura)

app = create_app()
app.app_context().push()
db.app = app


def asignar_a_cit_categoria_con_distrito(cit_categoria_id, distrito_id):
    """Asignar servicios de una categoria a todas las oficinas de un distrito"""

    # Iniciar
    bitacora.info("Inicia asignar servicios de una categoria a todas las oficinas de un distrito")

    # Validar Categoria
    cit_categoria = CitCategoria.query.get(cit_categoria_id)
    if cit_categoria is None:
        mensaje_error = "No se encuentra la categoria"
        bitacora.error(mensaje_error)
        return mensaje_error
    if cit_categoria.estatus != "A":
        mensaje_error = "Esta eliminada la categoria"
        bitacora.error(mensaje_error)
        return mensaje_error

    # Validar Distrito
    distrito = Distrito.query.get(distrito_id)
    if distrito is None:
        mensaje_error = "No se encuentra el distrito"
        bitacora.error(mensaje_error)
        return mensaje_error
    if distrito.estatus != "A":
        mensaje_error = "Esta eliminado el distrito"
        bitacora.error(mensaje_error)
        return mensaje_error

    # Terminar
    set_task_progress(100)
    mensaje_final = "Terminado"
    bitacora.info(mensaje_final)
    return mensaje_final
