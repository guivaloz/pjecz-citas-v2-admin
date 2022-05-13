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

    # Juntar los servicios activos de la categoria
    cit_servicios = []
    for cit_servicio in cit_categoria.cit_servicios:
        if cit_servicio.estatus == "A":
            cit_servicios.append(cit_servicio)
    bitacora.info("Hay %d servicios activos en la categoria %s", len(cit_servicios), cit_categoria.nombre)

    # Juntar las oficinas activas del distrito
    oficinas = []
    for oficina in distrito.oficinas:
        if oficina.estatus == "A" and oficina.puede_agendar_citas:
            oficinas.append(oficina)
    bitacora.info("Hay %d oficinas activas en el distrito %s", len(oficinas), distrito.nombre)

    # Actualizar o insertar registros de Oficina-Servicio
    actualizaciones_contador = 0
    inserciones_contador = 0
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
