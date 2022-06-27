"""
Cit Oficinas-Servicios, tareas para ejecutar en el fondo
"""
import logging

from lib.tasks import set_task_progress, set_task_error

from citas_admin.app import create_app
from citas_admin.extensions import db

from citas_admin.blueprints.cit_categorias.models import CitCategoria
from citas_admin.blueprints.cit_oficinas_servicios.models import CitOficinaServicio
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

    # Iniciar la tarea y los contadores
    bitacora.info("Inicia asignar servicios de una categoria a todas las oficinas de un distrito")
    set_task_progress(0)
    actualizaciones_contador = 0
    inserciones_contador = 0

    # Validar Categoria
    cit_categoria = CitCategoria.query.get(cit_categoria_id)
    if cit_categoria is None:
        mensaje_error = "No se encuentra la categoria"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error
    if cit_categoria.estatus != "A":
        mensaje_error = "Esta eliminada la categoria"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error

    # Validar Distrito
    distrito = Distrito.query.get(distrito_id)
    if distrito is None:
        mensaje_error = "No se encuentra el distrito"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error
    if distrito.estatus != "A":
        mensaje_error = "Esta eliminado el distrito"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error

    # Juntar los servicios activos de la categoria
    cit_servicios = []
    for cit_servicio in cit_categoria.cit_servicios:
        if cit_servicio.estatus == "A":
            cit_servicios.append(cit_servicio)
    if len(cit_servicios) == 0:
        mensaje_error = f"No hay servicios activos para la categoria {cit_categoria.nombre}"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error
    bitacora.info("Hay %d servicios activos en la categoria %s", len(cit_servicios), cit_categoria.nombre)

    # Juntar las oficinas activas del distrito
    oficinas = []
    for oficina in distrito.oficinas:
        if oficina.estatus == "A" and oficina.puede_agendar_citas:
            oficinas.append(oficina)
    if len(oficinas) == 0:
        mensaje_error = f"No hay oficinas activas o que puedan agendar citas para el distrito {distrito.nombre}"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error
    bitacora.info("Hay %d oficinas activas en el distrito %s", len(oficinas), distrito.nombre)

    # Actualizar o insertar registros de Oficina-Servicio
    for oficina in oficinas:
        for cit_servicio in cit_servicios:
            posible_cit_oficina_servicio = CitOficinaServicio.query.filter_by(cit_servicio_id=cit_servicio.id).filter_by(oficina_id=oficina.id).first()
            if posible_cit_oficina_servicio:
                # Actualizar Oficina-Servicio si esta eliminado
                if posible_cit_oficina_servicio.estatus != "A":
                    posible_cit_oficina_servicio.estatus = "A"
                    posible_cit_oficina_servicio.save()
                    actualizaciones_contador += 1
            else:
                # Insertar Oficina-Servicio
                CitOficinaServicio(
                    cit_servicio=cit_servicio,
                    oficina=oficina,
                    descripcion=f"{cit_servicio.clave} CON {oficina.clave}",
                ).save()
                inserciones_contador += 1

    # Terminar
    set_task_progress(100)
    mensaje_final = f"Terminado con {actualizaciones_contador} actualizaciones y {inserciones_contador} inserciones en Oficinas-Servicios."
    bitacora.info(mensaje_final)
    return mensaje_final


def asignar_a_cit_categoria_todos_distritos(cit_categoria_id):
    """Asignar servicios de una categoria a todas las oficinas de todos los distritos"""

    # Bucle para asignar los servicios de la categoria en todos los distritos
    for distrito in Distrito.query.filter_by(estatus="A").all():
        asignar_a_cit_categoria_con_distrito(cit_categoria_id, distrito.id)
