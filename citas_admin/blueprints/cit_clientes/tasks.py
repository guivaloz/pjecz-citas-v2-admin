"""
Cit Clientes, tareas para ejecutar en el fondo
"""
import json
import locale
import logging
import re
from datetime import datetime, timedelta

from sqlalchemy import text
from sqlalchemy.sql import func
from citas_admin.blueprints.cit_clientes_recuperaciones.models import CitClienteRecuperacion
from lib import database
from lib.database import SessionLocal
from lib.tasks import set_task_progress, set_task_error
from lib.storage import GoogleCloudStorage, NotAllowedExtesionError, UnknownExtesionError, NotConfiguredError
from google.cloud.storage import Blob

from citas_admin.app import create_app
from citas_admin.extensions import db

from citas_admin.blueprints.cit_clientes.models import CitCliente
from citas_admin.blueprints.cit_citas.models import CitCita

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


def refresh_report():
    """Actualiza el reporte de avisos de clientes"""

    empunadura = logging.FileHandler("cit_clientes_reportes.log")
    empunadura.setFormatter(formato)
    bitacora.addHandler(empunadura)

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


class Reporte:
    """Clase padre para Reportes"""

    def __init__(self, titulo, descripcion):
        """Constructor"""
        self.titulo = titulo
        self.descripcion = descripcion
        self.cantidad = 0
        self.resultados = []

    def check(self, registro):
        """Verifica la condición del reporte"""
        pass

    def entregar_reporte(self):
        """Entrega el resultado del reporte"""
        reporte = {
            "titulo": self.titulo,
            "descripcion": self.descripcion,
            "cantidad": self.cantidad,
            "resultados": self.resultados,
        }
        return reporte


class ReporteCurpParecidos(Reporte):
    """Clase para reporte - CURPS parecidos"""

    def __init__(self):
        """Constructor"""
        super().__init__("CURP Parecidos", "Se revisaron los CURP y se compararon los primeros 16 caracteres para ver si alguien intento duplicar su registro")

    def check(self, registro):
        """Valida si los primeros 16 caracteres son iguales a otro registro"""
        if len(registro.curp) < 18:
            self.cantidad += 1
            result = {
                "id": registro.id,
                "nombre": registro.nombre,
            }
            self.resultados.append(result)


class ReporteApellidoSegundoVacio(Reporte):
    """Clase para reporte - sin apellido segundo"""

    def __init__(self):
        """Constructor"""
        super().__init__(
            "Sin Apellido Segundo",
            "Clientes que no tienen apellido segundo",
        )

    def check(self, registro):
        """Valida si el apellido segundo en vacío o Nulo"""
        if registro.apellido_segundo == "" or registro.apellido_segundo is None:
            self.cantidad += 1
            result = {
                "id": registro.id,
                "nombre": registro.nombre,
            }
            self.resultados.append(result)


class ReporteNombreApellidosCortos(Reporte):
    """Clase para reporte - Nombres o Apellidos demasiado cortos"""

    def __init__(self):
        """Constructor"""
        super().__init__(
            "Nombre o Apellidos demasiado cortos",
            "Los nombres y apellidos demasiado cortos podrían representar un error de captura",
        )

    def check(self, registro):
        """Valida si el apellido segundo en vacío o Nulo"""
        if len(registro.nombres) < 3 or len(registro.apellido_primero) < 3 or len(registro.apellido_segundo) < 3:
            self.cantidad += 1
            result = {
                "id": registro.id,
                "nombre": registro.nombre,
            }
            self.resultados.append(result)


class ReporteNombreApellidoRepetidos(Reporte):
    """Clase para reporte - Nombres y Apellidos repetidos"""

    def __init__(self):
        """Constructor"""
        super().__init__(
            "Nombre y Apellido Primero Repetidos",
            "Clientes con el mismo nombre y apellido primero que otro. Posiblemente se registro más de una vez",
        )

    def check(self, registro):
        """Valida si el apellido segundo en vacío o Nulo"""
        # Query de consulta
        consulta = CitCliente.query
        consulta = consulta.filter(CitCliente.nombres == registro.nombres).filter(CitCliente.apellido_primero == registro.apellido_primero)
        consulta = consulta.filter(CitCliente.id > registro.id).first()
        if consulta:
            self.cantidad += 1
            result = {"id": registro.id, "nombre": registro.nombre, "id_copia": consulta.id, "nombre_parecido": consulta.nombre}
            self.resultados.append(result)


class ReporteTelefonoRepetido(Reporte):
    """Clase para reporte - Teléfono repetido"""

    def __init__(self):
        """Constructor"""
        super().__init__(
            "Teléfono Repetido",
            "Clientes con el mismo número telefónico",
        )

    def check(self, registro):
        """Valida si el apellido segundo en vacío o Nulo"""
        # Query de consulta
        consulta = CitCliente.query
        consulta = consulta.filter(CitCliente.telefono == registro.telefono)
        consulta = consulta.filter(CitCliente.id > registro.id).first()
        if consulta:
            self.cantidad += 1
            result = {
                "id": registro.id,
                "nombre": registro.nombre,
                "telefono": registro.telefono,
                "id_copia": consulta.id,
                "nombre_copia": consulta.nombre,
                "telefono_copia": consulta.telefono,
            }
            self.resultados.append(result)


class ReporteTelefonoVacio(Reporte):
    """Clase para reporte - Teléfono repetido"""

    def __init__(self):
        """Constructor"""
        super().__init__(
            "Sin Teléfono",
            "El teléfono es un campo opcional, por lo tanto puede estar vacío",
        )

    def check(self, registro):
        """Valida si el apellido segundo en vacío o Nulo"""
        if registro.telefono == "" or registro.telefono is None:
            self.cantidad += 1
            result = {
                "id": registro.id,
                "nombre": registro.nombre,
                "telefono": registro.telefono,
            }
            self.resultados.append(result)


class ReporteTelefonoFormato(Reporte):
    """Clase para reporte - Teléfono Formato incorrecto"""

    def __init__(self):
        """Constructor"""
        super().__init__(
            "Formato de Teléfono",
            "Se incluyó un formato de teléfono en el campo de teléfono. Se recomienda solo almacenar el número de teléfono como 10 dígitos",
        )

    def check(self, registro):
        """Valida si el apellido segundo en vacío o Nulo"""
        if re.sub(r"\([0-9]{3}\) [0-9]{3}\-[0-9]{4}", "", registro.telefono) == "":
            return
        if not registro.telefono.isnumeric():
            self.cantidad += 1
            result = {
                "id": registro.id,
                "nombre": registro.nombre,
                "telefono": registro.telefono,
            }
            self.resultados.append(result)


class ReporteClientesSinCitas(Reporte):
    """Clase para reporte - Clientes sin Citas"""

    def __init__(self):
        """Constructor"""
        super().__init__(
            "Clientes sin Agendar Citas",
            "Clientes que no han agendado ninguna cita",
        )

    def check(self, registro):
        """Valida si el apellido segundo en vacío o Nulo"""
        # Query de consulta
        consulta = CitCita.query
        consulta = consulta.filter(CitCita.cit_cliente_id == registro.id).first()
        if consulta is None:
            self.cantidad += 1
            result = {
                "id": registro.id,
                "nombre": registro.nombre,
            }
            self.resultados.append(result)


def evaluar_asistencia(test=True):
    """Penaliza o Premia al cliente conforme su asistencia"""

    # Constantes para parámetros
    DIAS_MARGEN = 30
    LIMITE_SIN_CITAS = 15
    LIMITE_INASISTENCIA = 2
    LIMITE_ASISTENCIA = 30
    PORCENTAJE_ASISTENCIA_ACEPTABLE = 0.8

    # Configuración del LOG
    empunadura = logging.FileHandler("cit_clientes.log")
    empunadura.setFormatter(formato)
    bitacora.addHandler(empunadura)

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

    db = SessionLocal()

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


# TODO: Función para eliminar clientes sin ninguna cita agendada.
def eliminar_sin_citas(dias=30):
    """Elimina los cit_clientes sin citas agendadas"""

    # Configuración del LOG
    empunadura = logging.FileHandler("cit_clientes.log")
    empunadura.setFormatter(formato)
    bitacora.addHandler(empunadura)

    # Establecer al fecha
    fecha_creado = datetime.now() - timedelta(days=dias)

    # Revisar los clientes
    db = SessionLocal()
    results = db.query(CitCliente, CitCita).outerjoin(CitCita).filter(CitCita.cit_cliente_id == None).filter(CitCliente.creado <= fecha_creado).all()

    # Inicializar el engine para ejecutar comandos SQL
    engine = database.engine

    for cliente, _ in results:
        # Borrado de recuperaciones
        borrado = text(
            f"DELETE \
                FROM cit_clientes_recuperaciones \
                WHERE cit_cliente_id = {cliente.id}"
        )
        engine.execute(borrado)
        # Borrado del cit_cliente
        cliente_borrar = CitCliente.query.get(cliente.id)
        mensaje = f"Se eliminó PERMANENTEMENTE el Cliente: {cliente.id} por no tener citas."
        cliente_borrar.delete(permanently=True)
        bitacora.info(mensaje)

    # Mensaje de Totales
    mensaje_final = f"Se eliminaron {len(results)} clientes por no tener citas."
    bitacora.info(mensaje_final)

    # Se termina la tarea y se envía el mensaje final
    set_task_progress(100)
    return mensaje_final
