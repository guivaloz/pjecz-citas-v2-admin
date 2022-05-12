"""
Cit Autoridades-Servicios, tareas para ejecutar en el fondo
"""
import logging

from lib.tasks import set_task_progress, set_task_error

from citas_admin.app import create_app
from citas_admin.extensions import db

bitacora = logging.getLogger(__name__)
bitacora.setLevel(logging.INFO)
formato = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
empunadura = logging.FileHandler("cit_autoridades_servicios.log")
empunadura.setFormatter(formato)
bitacora.addHandler(empunadura)

app = create_app()
app.app_context().push()
db.app = app


def asignar_a_cit_categoria_con_distrito(cit_categoria_id, distrito_id):
    """Asignar Autoridades-Servicios a todos los servicios de una categoria"""

    # Iniciar
    bitacora.info("Inicia asignar Autoridades-Servicios a todos los servicios de una categoria")

    # Terminar
    set_task_progress(100)
    mensaje_final = "Terminado"
    bitacora.info(mensaje_final)
    return mensaje_final
