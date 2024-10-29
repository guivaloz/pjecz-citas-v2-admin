"""
Pag Pagos, tareas en el fondo
"""

import logging
from datetime import date, datetime, timedelta
from pathlib import Path

import pytz
from openpyxl import Workbook
from sqlalchemy import or_

from citas_admin.app import create_app
from citas_admin.blueprints.autoridades.models import Autoridad
from citas_admin.blueprints.cit_clientes.models import CitCliente
from citas_admin.blueprints.distritos.models import Distrito
from citas_admin.blueprints.pag_pagos.models import PagPago
from citas_admin.extensions import database
from config.settings import get_settings
from lib.exceptions import (
    MyAnyError,
    MyBucketNotFoundError,
    MyEmptyError,
    MyFileNotAllowedError,
    MyFileNotFoundError,
    MyUploadError,
)
from lib.google_cloud_storage import upload_file_to_gcs
from lib.tasks import set_task_error, set_task_progress

# Constantes
GCS_BASE_DIRECTORY = "pag_pagos"
LOCAL_BASE_DIRECTORY = "exports/pag_pagos"
TIMEZONE = "America/Mexico_City"

# Bitácora logs/pag_pagos.log
bitacora = logging.getLogger(__name__)
bitacora.setLevel(logging.INFO)
formato = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
empunadura = logging.FileHandler("logs/pag_pagos.log")
empunadura.setFormatter(formato)
bitacora.addHandler(empunadura)

# Cargar la aplicación para tener acceso a la base de datos
app = create_app()
app.app_context().push()
database.app = app


def exportar_xlsx(desde: date = None, hasta: date = None) -> tuple[str, str, str]:
    """Exportar Pagos PAGADOS y ENTREGADOS a un archivo XLSX"""

    # Iniciar listado con los mensajes
    mensajes = []

    # Definir la fecha y hora actual
    hoy = datetime.now(pytz.timezone(TIMEZONE))

    # Si no se especifica el rango de fechas...
    if desde is None or hasta is None:
        # Calcular el primer día del mes anterior a las 00:00:00
        desde = datetime(year=hoy.year, month=hoy.month, day=1, tzinfo=pytz.timezone(TIMEZONE)) - timedelta(days=1)
        desde = desde.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        # Definir hasta con el último día del mes anterior a las 23:59:59
        hasta = datetime(
            year=hoy.year, month=hoy.month, day=1, hour=23, minute=59, second=59, tzinfo=pytz.timezone(TIMEZONE)
        ) - timedelta(seconds=1)
    else:
        # Convertir desde a timestamp con hora 00:00:00
        desde = datetime(year=desde.year, month=desde.month, day=desde.day, hour=0, minute=0, second=0)
        # Convertir hasta a timestamp con hora 23:59:59
        hasta = datetime(year=hasta.year, month=hasta.month, day=hasta.day, hour=23, minute=59, second=59)

    # Agregar a mensajes el rango de fechas
    desde_str = desde.strftime("%Y-%m-%d %H:%M:%S")
    hasta_str = hasta.strftime("%Y-%m-%d %H:%M:%S")
    mensaje = f"Inica exportar Pagos PAGADOS y ENTREGADOS desde {desde_str} hasta {hasta_str}"
    bitacora.info(mensaje)
    mensajes.append(mensaje)

    # Consultar los pagos
    pag_pagos = (
        PagPago.query.join(Autoridad, Autoridad.id == PagPago.autoridad_id)
        .join(Distrito, Distrito.id == Autoridad.distrito_id)
        .join(CitCliente, CitCliente.id == PagPago.cit_cliente_id)
        .filter(PagPago.estatus == "A")
        .filter(or_(PagPago.estado == "PAGADO", PagPago.estado == "ENTREGADO"))
        .filter(PagPago.creado >= desde)
        .filter(PagPago.creado <= hasta)
        .order_by(PagPago.creado)
    )

    # Iniciar el archivo XLSX
    libro = Workbook()

    # Tomar la hoja del libro XLSX
    hoja = libro.active

    # Agregar la fila con las cabeceras de las columnas
    hoja.append(
        [
            "CREADO",
            "DISTRITO",
            "AUTORIDAD",
            "NOMBRES",
            "APELLIDO PRIMERO",
            "APELLIDO SEGUNDO",
            "CURP",
            "EMAIL",
            "TELEFONO",
            "ESTADO",
            "FOLIO",
            "TOTAL",
        ]
    )

    # Bucle por los pagos para agregar las filas
    contador = 0
    for pago in pag_pagos:
        hoja.append(
            [
                pago.creado,
                pago.autoridad.distrito.nombre_corto,
                pago.autoridad.descripcion_corta,
                pago.cit_cliente.nombres,
                pago.cit_cliente.apellido_primero,
                pago.cit_cliente.apellido_segundo,
                pago.cit_cliente.curp,
                pago.cit_cliente.email,
                pago.cit_cliente.telefono,
                pago.estado,
                pago.folio,
                pago.total,
            ]
        )
        contador += 1

    # Agregar a mensajes la cantidad de pagos exportados
    mensaje = f"Se exportaron {contador} Pagos PAGADOS y ENTREGADOS"
    bitacora.info(mensaje)
    mensajes.append(mensaje)

    # Determinar el nombre del archivo XLSX
    desde_str = desde.strftime("%Y-%m-%d")
    hasta_str = hasta.strftime("%Y-%m-%d")
    momento_str = hoy.strftime("%Y-%m-%d_%H%M%S")
    ahora = datetime.now(tz=pytz.timezone(TIMEZONE))
    nombre_archivo_xlsx = f"pagos_{desde_str}_{hasta_str}_{momento_str}.xlsx"

    # Determinar las rutas con directorios con el año y el número de mes en dos digitos
    ruta_local = Path(LOCAL_BASE_DIRECTORY, ahora.strftime("%Y"), ahora.strftime("%m"))
    ruta_gcs = Path(GCS_BASE_DIRECTORY, ahora.strftime("%Y"), ahora.strftime("%m"))

    # Si no existe el directorio local, crearlo
    Path(ruta_local).mkdir(parents=True, exist_ok=True)

    # Guardar el archivo XLSX
    ruta_local_archivo_xlsx = str(Path(ruta_local, nombre_archivo_xlsx))
    libro.save(ruta_local_archivo_xlsx)

    # Si esta configurado Google Cloud Storage
    public_url = ""
    settings = get_settings()
    if settings.CLOUD_STORAGE_DEPOSITO != "":
        # Leer el contenido del archivo XLSX
        with open(ruta_local_archivo_xlsx, "rb") as archivo:
            # Subir el archivo XLSX a Google Cloud Storage
            try:
                public_url = upload_file_to_gcs(
                    bucket_name=settings.CLOUD_STORAGE_DEPOSITO,
                    blob_name=f"{ruta_gcs}/{nombre_archivo_xlsx}",
                    content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    data=archivo.read(),
                )
                mensaje = f"Se subió el archivo {nombre_archivo_xlsx} a GCS"
                bitacora.info(mensaje)
                mensajes.append(mensaje)
            except (MyEmptyError, MyBucketNotFoundError, MyFileNotAllowedError, MyFileNotFoundError, MyUploadError) as error:
                mensaje = f"Falló el subir el archivo XLSX a GCS: {str(error)}"
                bitacora.warning(mensaje)
                mensajes.append(mensaje)

    # Entregar mensaje de termino, el nombre del archivo XLSX y la URL publica
    mensaje_termino = "\n".join(mensajes)
    return mensaje_termino, nombre_archivo_xlsx, public_url


def lanzar_exportar_xlsx():
    """Exportar Personas a un archivo XLSX"""

    # Iniciar la tarea en el fondo
    set_task_progress(0, "Inicia exportar Pagos a un archivo XLSX")

    # Ejecutar el creador
    try:
        mensaje_termino, nombre_archivo_xlsx, public_url = exportar_xlsx()
    except MyAnyError as error:
        mensaje_error = str(error)
        set_task_error(mensaje_error)
        return mensaje_error

    # Terminar la tarea en el fondo y entregar el mensaje de termino
    set_task_progress(100, mensaje_termino, nombre_archivo_xlsx, public_url)
    return mensaje_termino
