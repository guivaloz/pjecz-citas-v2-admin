"""
Cit Clientes, tareas para ejecutar en el fondo
"""
import json
import locale
import logging
import re
from datetime import datetime
from sqlalchemy import func, or_

from lib.tasks import set_task_progress, set_task_error

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

FILE_NAME = "tmp/clientes_errores_reporte.json"


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
    with open(FILE_NAME, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

    # Terminar tarea
    set_task_progress(100)
    mensaje_final = "Se ha actualizado el reporte de errores de cit_clientes"
    bitacora.info(mensaje_final)
    return mensaje_final


def recorrer_registros():
    """Recorre uno aun todos los registros de la tabla cit_clientes"""
    # Query de consulta
    registros = CitCliente.query.order_by(CitCliente.id).all()
    # Arreglo con todos lo reportes a consultar
    reportes = []
    reportes.append(Reporte_CURP_parecidos())
    reportes.append(Reporte_apellido_segundo_vacio())
    reportes.append(Reporte_nombre_apellidos_cortos())
    reportes.append(Reporte_nombre_apellido_repetidos())
    reportes.append(Reporte_telefono_repetido())
    reportes.append(Reporte_telefono_vacio())
    reportes.append(Reporte_telefono_formato())
    reportes.append(Reporte_clientes_sin_citas())
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


class Reporte_CURP_parecidos(Reporte):
    """Clase para reporte - CURPS parecidos"""

    def __init__(self):
        """Constructor"""
        Reporte.__init__(
            self,
            "CURP Parecidos",
            "Se revisaron los CURP y se compararon los primeros 16 caracteres para ver si alguien intento duplicar su registro",
        )

    def check(self, registro):
        """Valida si los primeros 16 caracteres son iguales a otro registro"""
        if len(registro.curp) < 18:
            self.cantidad += 1
            result = {
                "id": registro.id,
                "nombre": registro.nombre,
            }
            self.resultados.append(result)


class Reporte_apellido_segundo_vacio(Reporte):
    """Clase para reporte - sin apellido segundo"""

    def __init__(self):
        """Constructor"""
        Reporte.__init__(
            self,
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


class Reporte_nombre_apellidos_cortos(Reporte):
    """Clase para reporte - Nombres o Apellidos demasiado cortos"""

    def __init__(self):
        """Constructor"""
        Reporte.__init__(
            self,
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


class Reporte_nombre_apellido_repetidos(Reporte):
    """Clase para reporte - Nombres y Apellidos repetidos"""

    def __init__(self):
        """Constructor"""
        Reporte.__init__(
            self,
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


class Reporte_telefono_repetido(Reporte):
    """Clase para reporte - Teléfono repetido"""

    def __init__(self):
        """Constructor"""
        Reporte.__init__(
            self,
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


class Reporte_telefono_vacio(Reporte):
    """Clase para reporte - Teléfono repetido"""

    def __init__(self):
        """Constructor"""
        Reporte.__init__(
            self,
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


class Reporte_telefono_formato(Reporte):
    """Clase para reporte - Teléfono Formato incorrecto"""

    def __init__(self):
        """Constructor"""
        Reporte.__init__(
            self,
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


class Reporte_clientes_sin_citas(Reporte):
    """Clase para reporte - Clientes sin Citas"""

    def __init__(self):
        """Constructor"""
        Reporte.__init__(
            self,
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


if __name__ == "__main__":
    refresh_report()
