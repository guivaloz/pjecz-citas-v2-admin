"""
Cit Clientes, reportes
"""
import re

from citas_admin.blueprints.cit_citas.models import CitCita
from citas_admin.blueprints.cit_clientes.models import CitCliente


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
