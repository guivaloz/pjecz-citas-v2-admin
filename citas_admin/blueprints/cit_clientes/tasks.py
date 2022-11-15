"""
Cit Clientes, tareas para ejecutar en el fondo
"""
from datetime import datetime, timedelta
import json
import locale
import logging

from sqlalchemy.sql import func

from lib import database
from lib.tasks import set_task_progress
from lib.storage import GoogleCloudStorage, NotConfiguredError

from citas_admin.blueprints.cit_clientes.models import CitCliente
from citas_admin.blueprints.cit_citas.models import CitCita

from citas_admin.app import create_app
from citas_admin.extensions import db

from .reports import (
    ReporteCurpParecidos,
    ReporteApellidoSegundoVacio,
    ReporteNombreApellidosCortos,
    ReporteNombreApellidoRepetidos,
    ReporteTelefonoRepetido,
    ReporteTelefonoVacio,
    ReporteTelefonoFormato,
    ReporteClientesSinCitas,
)

locale.setlocale(locale.LC_TIME, "es_MX.utf8")

bitacora = logging.getLogger(__name__)
bitacora.setLevel(logging.INFO)
formato = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
empunadura = logging.FileHandler("cit_clientes_reportes.log")
empunadura.setFormatter(formato)
bitacora.addHandler(empunadura)

app = create_app()
db.app = app

LIMITE_VERIFICACION = 30

FILE_NAME = "cit_clientes_reporte.json"

DIAS_MARGEN = 30
LIMITE_SIN_CITAS = 15
LIMITE_INASISTENCIA = 2
LIMITE_ASISTENCIA = 30
PORCENTAJE_ASISTENCIA_ACEPTABLE = 0.8


def refresh_report():
    """Actualiza el reporte de avisos de clientes"""

    # Creación del contenido del reporte JSON general
    data = {
        "fecha_creacion": "2022.08.01 13:00",
        "consultado": False,
        "total_errores": 0,
        "reportes": [],
    }

    # Momento en que se elabora este mensaje
    momento = datetime.now()
    data["fecha_creacion"] = momento.strftime("%Y/%m/%d %H:%M")

    # Llamar a los reportes por recorrido
    data["total_errores"], data["reportes"] = recorrer_registros()

    # Abrimos el archivo de reporte JSON
    with open("/tmp/" + FILE_NAME, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

    # Preparar Google Storage
    storage = GoogleCloudStorage("/")
    url = None

    # Subir el archivo a la nube (Google Storage)
    try:
        url = storage.upload_from_filename("pjecz-informatica", "json/" + FILE_NAME, "/tmp/" + FILE_NAME, "application/json")
    except NotConfiguredError:
        bitacora.warning("No se ha configurado el almacenamiento en la nube.")
    except Exception:
        bitacora.warning("Error al subir el archivo.")

    # Terminar tarea
    set_task_progress(100)
    mensaje_final = f"Se ha actualizado el reporte de errores de cit_clientes en: {url}"
    bitacora.info(mensaje_final)
    return mensaje_final


def recorrer_registros():
    """Recorre uno aun todos los registros de la tabla cit_clientes"""

    # Query de consulta
    registros = CitCliente.query.order_by(CitCliente.id).all()

    # Arreglo con todos lo reportes a consultar
    reportes = []
    reportes.append(ReporteCurpParecidos())
    reportes.append(ReporteApellidoSegundoVacio())
    reportes.append(ReporteNombreApellidosCortos())
    reportes.append(ReporteNombreApellidoRepetidos())
    reportes.append(ReporteTelefonoRepetido())
    reportes.append(ReporteTelefonoVacio())
    reportes.append(ReporteTelefonoFormato())
    reportes.append(ReporteClientesSinCitas())

    # Revisamos registro por registro todos lo posibles errores
    for registro in registros:
        for reporte in reportes:
            if reporte.cantidad < LIMITE_VERIFICACION:
                reporte.check(registro)

    # Regresamos la cantidad total de errores
    data_reportes = []
    count_errores_totales = 0
    for reporte in reportes:
        data_reportes.append(reporte.entregar_reporte())
        count_errores_totales += reporte.cantidad
    return count_errores_totales, data_reportes
