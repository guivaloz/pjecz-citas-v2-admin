"""
Cit Clientes, tareas para ejecutar en el fondo
"""
import json
import locale
import logging
from datetime import datetime
from sqlalchemy import func, or_

from lib.tasks import set_task_progress, set_task_error

from citas_admin.app import create_app
from citas_admin.extensions import db

from citas_admin.blueprints.cit_clientes.models import CitCliente

locale.setlocale(locale.LC_TIME, "es_MX.utf8")

bitacora = logging.getLogger(__name__)
bitacora.setLevel(logging.INFO)
formato = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
empunadura = logging.FileHandler("cit_clientes_reportes.log")
empunadura.setFormatter(formato)
bitacora.addHandler(empunadura)

app = create_app()
db.app = app


FILE_NAME = "citas_admin/blueprints/cit_clientes/data/reporte.json"


def refresh_report():
    """Actualiza el reporte de avisos de clientes"""
    
    # Creación del contenido del reporte JSON general
    data = {
        "fecha_creacion": "2022.08.01 13:00",
        "reportes": []
    }

    # Momento en que se elabora este mensaje
    momento = datetime.now()
    data["fecha_creacion"] = momento.strftime("%Y/%m/%d %H:%M")

    # --- Llamadas a los reportes ---
    data["reportes"].append(reporte_curp_parecidos())
    data["reportes"].append(reporte_sin_apellido_segundo())
    data["reportes"].append(reporte_nombre_apellidos_cortos())
    data["reportes"].append(reporte_nombre_apellido_repetidos())
    data["reportes"].append(reporte_telefono_repetido())
    data["reportes"].append(reporte_sin_telefono())
    data["reportes"].append(reporte_formato_telefono())
    data["reportes"].append(reporte_clientes_sin_citas())
    # --- Fin de llamadas a los reportes ---

    # Abrimos el archivo de reporte JSON
    with open(FILE_NAME, "w", encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    # Terminar tarea
    set_task_progress(100)
    mensaje_final = "Se ha actualizado el reporte de errores de cit_clientes"
    bitacora.info(mensaje_final)
    return mensaje_final


def reporte_curp_parecidos():
    """Revisa si los primeros 16 dígitos son iguales"""
    # Estructura de reporte
    reporte = {
        "titulo": "CURP Parecidos",
        "descripcion": "Se revisaron los CURP y se compararon los primeros 16 caracteres para ver si alguien intento duplicar su registro",
        "cantidad": 0,
        "resultados": []
    }

    reporte["cantidad"] = 1
    reporte["resultados"] = ["AAA"]

    # regresa una sección JSON del reporte generado
    return reporte


def reporte_sin_apellido_segundo():
    """Revisa si esta vacío el apellido segundos de los clientes"""
    # Estructura de reporte
    reporte = {
        "titulo": "Sin Apellido Segundo",
        "descripcion": "Clientes que no tienen apellido segundo",
        "cantidad": 0,
        "resultados": []
    }

    # Query de consulta
    registros = CitCliente.query.filter_by(apellido_segundo="").all()

    count = 0
    for registro in registros:
        reporte["resultados"].append(registro.nombre)
        count += 1
    reporte["cantidad"] = count

    # regresa una sección JSON del reporte generado
    return reporte


def reporte_nombre_apellidos_cortos():
    """Revisa si el Nombre o Apellidos son demasiado cortos"""
    # Estructura de reporte
    reporte = {
        "titulo": "Nombre o Apellidos demasiado cortos",
        "descripcion": "Los nombres y apellidos demasiado cortos podrían representar un error de captura",
        "cantidad": 0,
        "resultados": []
    }

    # Query de consulta
    registros = CitCliente.query.filter(or_(
            func.length(CitCliente.nombres) < 3,
            func.length(CitCliente.apellido_primero) < 3,
            func.length(CitCliente.apellido_segundo) < 3,
        )).all()

    count = 0
    for registro in registros:
        reporte["resultados"].append(registro.nombre)
        count += 1
    reporte["cantidad"] = count

    # regresa una sección JSON del reporte generado
    return reporte



def reporte_nombre_apellido_repetidos():
    """Revisa si el nombre y apellido primero esta repetido"""
    # Estructura de reporte
    reporte = {
        "titulo": "Nombre y Apellido Primero Repetidos",
        "descripcion": "Clientes con el mismo nombre y apellido primero que otro. Posiblemente se registro más de una vez",
        "cantidad": 0,
        "resultados": []
    }

    reporte["cantidad"] = 0
    reporte["resultados"] = []

    # regresa una sección JSON del reporte generado
    return reporte


def reporte_telefono_repetido():
    """Revisa si el teléfono esta repetido"""
    # Estructura de reporte
    reporte = {
        "titulo": "Teléfono Repetido",
        "descripcion": "Clientes con el mismo número telefónico",
        "cantidad": 0,
        "resultados": []
    }

    reporte["cantidad"] = 0
    reporte["resultados"] = []

    # regresa una sección JSON del reporte generado
    return reporte


def reporte_sin_telefono():
    """Revisa si el nombre y apellido primero esta repetido"""
    # Estructura de reporte
    reporte = {
        "titulo": "Sin Teléfono",
        "descripcion": "El teléfono es un campo opcional, por lo tanto puede estar vacío",
        "cantidad": 0,
        "resultados": []
    }

    reporte["cantidad"] = 0
    reporte["resultados"] = []

    # regresa una sección JSON del reporte generado
    return reporte


def reporte_formato_telefono():
    """Revisa el formato del teléfono"""
    # Estructura de reporte
    reporte = {
        "titulo": "Formato de Teléfono",
        "descripcion": "Se incluyó un formato de teléfono en el campo de teléfono. Se recomienda solo almacenar el número de teléfono como 10 dígitos",
        "cantidad": 0,
        "resultados": []
    }

    reporte["cantidad"] = 0
    reporte["resultados"] = []

    # regresa una sección JSON del reporte generado
    return reporte


def reporte_clientes_sin_citas():
    """Revisa si hay clientes sin citas"""
    # Estructura de reporte
    reporte = {
        "titulo": "Clientes sin Agendar Citas",
        "descripcion": "Clientes que no han agendado ninguna cita",
        "cantidad": 0,
        "resultados": []
    }

    reporte["cantidad"] = 0
    reporte["resultados"] = []

    # regresa una sección JSON del reporte generado
    return reporte


if __name__ == "__main__":
    refresh_report()