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


def evaluar_asistencia(test=True):
    """Penaliza o Premia al cliente conforme su asistencia"""

    # Calcular fecha de límite
    fecha_actual = datetime.now()
    fecha_limite = datetime(
        year=fecha_actual.year,
        month=fecha_actual.month,
        day=fecha_actual.day,
        hour=0,
        minute=0,
        second=0,
    )
    fecha_limite = fecha_limite - timedelta(days=DIAS_MARGEN)

    # Contadores de cambios realizados
    count_clientes_ajustados = 0
    count_clientes_premiados = 0
    count_clientes_penalizados = 0

    db = database.SessionLocal()

    # Revisar los clientes
    clientes = CitCliente.query.filter_by(estatus="A").order_by(CitCliente.id).all()

    for cliente in clientes:

        # Variables para contar las citas por cliente
        count_citas_asistio = 0
        count_citas_inasistencia = 0

        # Consultar el número de citas por estado
        citas_cantidades = (
            db.query(
                CitCita.estado.label("estado"),
                func.count("*").label("cantidad"),
            )
            .filter_by(cit_cliente_id=cliente.id)
            .filter_by(estatus="A")
            .filter(CitCita.inicio > fecha_limite)
            .group_by(CitCita.estado)
            .all()
        )

        # Establecemos las cantidades de citas ASISTIDAS y INASISTIDAS
        if citas_cantidades is not None:
            for estado, cantidad in citas_cantidades:
                if estado == "ASISTIO":
                    count_citas_asistio = cantidad
                elif estado == "INASISTENCIA":
                    count_citas_inasistencia = cantidad

        # Toma de acciones dependiendo del resultado de la asistencia del cliente
        total_citas = count_citas_asistio + count_citas_inasistencia
        if total_citas == 0:
            if cliente.limite_citas_pendientes == LIMITE_SIN_CITAS:
                if test is False:
                    cliente.limite_citas_pendientes = LIMITE_SIN_CITAS
                    cliente.save()
                mensaje = f"Cliente {cliente.id} sin citas en los últimos {DIAS_MARGEN} días. Se ajustó su límite de citas a {LIMITE_SIN_CITAS}."
                bitacora.info(mensaje)
                count_clientes_ajustados += 1
        elif (count_citas_asistio * 100) / total_citas >= PORCENTAJE_ASISTENCIA_ACEPTABLE:
            if cliente.limite_citas_pendientes == LIMITE_ASISTENCIA:
                if test is False:
                    cliente.limite_citas_pendientes = LIMITE_ASISTENCIA
                    cliente.save()
                mensaje = f"Cliente {cliente.id} con buena asistencia en los últimos {DIAS_MARGEN} días. Se ajustó su límite de citas a {LIMITE_ASISTENCIA}."
                bitacora.info(mensaje)
                count_clientes_premiados += 1
        else:
            if cliente.limite_citas_pendientes == LIMITE_INASISTENCIA:
                if test is False:
                    cliente.limite_citas_pendientes = LIMITE_INASISTENCIA
                    cliente.save()
                mensaje = f"Cliente {cliente.id} con mala asistencia en los últimos {DIAS_MARGEN} días. Se ajustó su límite de citas a {LIMITE_INASISTENCIA}."
                bitacora.info(mensaje)
                count_clientes_penalizados += 1

    # Mensaje de Totales
    mensaje_final = f"Se procesaron {len(clientes)} Clientes, Fecha límite {fecha_limite} : Premiaron {count_clientes_premiados}, Ajustaron {count_clientes_ajustados}, Penalizaron {count_clientes_penalizados}."
    bitacora.info(mensaje_final)

    # Se termina la tarea y se envía el mensaje final
    set_task_progress(100)
    return mensaje_final
