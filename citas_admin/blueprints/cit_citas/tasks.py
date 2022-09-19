"""
Cit Citas, tareas en el fondo
"""
from datetime import datetime
import locale
import logging
import os
import sendgrid

from dotenv import load_dotenv
from sendgrid.helpers.mail import Email, To, Content, Mail
from jinja2 import Environment, FileSystemLoader

from lib.tasks import set_task_progress, set_task_error

from citas_admin.app import create_app
from citas_admin.extensions import db

from citas_admin.blueprints.cit_citas.models import CitCita
from citas_admin.blueprints.cit_clientes.models import CitCliente

locale.setlocale(locale.LC_TIME, "es_MX.utf8")

bitacora = logging.getLogger(__name__)
bitacora.setLevel(logging.INFO)
formato = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
empunadura = logging.FileHandler("cit_citas.log")
empunadura.setFormatter(formato)
bitacora.addHandler(empunadura)

app = create_app()
db.app = app

load_dotenv()  # Take environment variables from .env

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "")
HOST = os.getenv("HOST", "")


def enviar(cit_cita_id):
    """Enviar mensaje con datos de la cita agendada"""

    # Consultar
    cit_cita = CitCita.query.get(cit_cita_id)
    if cit_cita.estatus != "A":
        mensaje_error = f"El ID {cit_cita.id} NO tiene estatus activo"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error

    # Validar el cliente
    cliente = CitCliente.query.get(cit_cita.cit_cliente_id)
    if cliente is None:
        mensaje_error = f"El ID del cliente '{cit_cita.cit_cliente_id}' NO existe dentro la tabla cit_clientes"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error
    if cliente.estatus != "A":
        mensaje_error = f"El ID del cliente {cliente.id} NO tiene estatus activo"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error

    # Esta completo para enviar el mensaje por correo electronico
    esta_completo_para_enviar_mensaje = True

    # Si la oficina tiene palomeado Puede enviar codigos QR
    va_a_incluir_qr = False
    if cit_cita.oficina.puede_enviar_qr is True:  # Esta propuedad puede ser NULA
        va_a_incluir_qr = True

    # Momento en que se elabora este mensaje
    momento = datetime.now()
    momento_str = momento.strftime("%d/%b/%Y %I:%M %p")

    # Si puede enviar codigos QR
    asistencia_url = None
    if va_a_incluir_qr:
        # Validar que este definido el HOST
        if HOST == "":
            va_a_incluir_qr = False
            bitacora.warning("No se incluye el codigo QR porque la variable HOST no esta definida.")
        else:
            # Definir el URL para marcar asistencia
            asistencia_url = HOST + "/cit_citas/asistencia/" + cit_cita.encode_id()

    # Importar plantilla Jinja2
    entorno = Environment(
        loader=FileSystemLoader("citas_admin/blueprints/cit_citas/templates/cit_citas"),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    plantilla = entorno.get_template("email.jinja2")
    contenidos = plantilla.render(
        fecha_elaboracion=momento_str,
        cliente_nombre=cliente.nombre,
        cit_cita=cit_cita,
        va_a_incluir_qr=va_a_incluir_qr,
        asistencia_url=asistencia_url,
    )
    content = Content("text/html", contenidos)

    # Validar remitente
    from_email = None
    if SENDGRID_FROM_EMAIL != "":
        from_email = Email(SENDGRID_FROM_EMAIL)
    else:
        esta_completo_para_enviar_mensaje = False

    # Destinatario
    # to_email = To(cit_cita.cit_cliente.email)
    to_email = To("mayra.camacho@pjecz.gob.mx")

    # Asunto
    subject = "Cita Agendada - PJECZ"

    # Validar SendGrid
    sendgrid_client = None
    if SENDGRID_API_KEY != "":
        sendgrid_client = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
    else:
        esta_completo_para_enviar_mensaje = False

    # Enviar mensaje
    if esta_completo_para_enviar_mensaje:
        mail = Mail(from_email, to_email, subject, content)
        sendgrid_client.client.mail.send.post(request_body=mail.get())
    else:
        mensaje_error = f"Se omite el envío a {cit_cita.cit_cliente.email} por que faltan elementos"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error

    # Terminar tarea
    set_task_progress(100)
    if va_a_incluir_qr:
        mensaje_final = f"Se ha enviado un mensaje con QR a {cit_cita.cit_cliente.email} de la cita {cit_cita.id}, URL: {asistencia_url}"
    else:
        mensaje_final = f"Se ha enviado un mensaje a {cit_cita.cit_cliente.email} de la cita {cit_cita.id}"
    bitacora.info(mensaje_final)
    return mensaje_final


def enviar_msg_cancelacion(cit_cita_id):
    """Enviar mensaje de cita cancelada"""
    cit_cita = _validacion_cita(cit_cita_id)
    if cit_cita is None:
        return None

    cit_cliente = _validacion_cliente(cit_cita.cliente_id)
    if cit_cliente is None:
        return None

    # Importar plantilla Jinja2
    plantilla = _cargar_plantilla("email_cancel.jinja2")
    contenidos = plantilla.render(
        fecha_elaboracion=datetime.now().strftime("%d/%b/%Y %I:%M %p"),
        cit_cliente=cit_cliente,
        cit_cita=cit_cita,
    )
    content = Content("text/html", contenidos)

    envio_correcto = _enviar_email(
        to_email=To(cit_cita.cit_cliente.email),
        subject="Citas - Cancelación",
        content=content,
    )

    if envio_correcto:
        mensaje_final = f"Se ha enviado un mensaje a {cit_cita.cit_cliente.email} de cancelación de la cita {cit_cita.id}"
        bitacora.info(mensaje_final)
    else:
        mensaje_error = f"Se omite el envío a {cit_cita.cit_cliente.email} por que faltan elementos"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        mensaje_final = mensaje_error

    # Se termina la tarea y se envía el mensaje final
    set_task_progress(100)
    return mensaje_final


def enviar_msg_asistencia(cit_cita_id):
    """enviar mensaje de cita cancelada"""
    cit_cita = _validacion_cita(cit_cita_id)
    if cit_cita is None:
        return None

    cit_cliente = _validacion_cliente(cit_cita.cliente_id)
    if cit_cliente is None:
        return None
    
    # Importar plantilla Jinja2
    plantilla = _cargar_plantilla("email_assistance.jinja2")
    contenidos = plantilla.render(
        fecha_elaboracion=datetime.now().strftime("%d/%b/%Y %I:%M %p"),
        cit_cliente=cit_cliente,
        cit_cita=cit_cita,
    )
    content = Content("text/html", contenidos)

    envio_correcto = _enviar_email(
        to_email=To(cit_cita.cit_cliente.email),
        subject="Citas - Asistencia",
        content=content,
    )

    if envio_correcto:
        mensaje_final = f"Se ha enviado un mensaje a {cit_cita.cit_cliente.email} de asistencia a la cita {cit_cita.id}"
        bitacora.info(mensaje_final)
    else:
        mensaje_error = f"Se omite el envío a {cit_cita.cit_cliente.email} por que faltan elementos"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        mensaje_final = mensaje_error

    # Se termina la tarea y se envía el mensaje final
    set_task_progress(100)
    return mensaje_final


########################
### Métodos Privados ###
########################


def _validacion_cita(cit_cita_id):
    """Valida si la cita existe"""

    cit_cita = CitCita.query.get(cit_cita_id)
    if cit_cita.estatus != "A":
        mensaje_error = f"El ID {cit_cita.id} NO tiene estatus activo"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return None
    # Regresa la cita
    return cit_cita


def _validacion_cliente(cit_cliente_id):
    """Valida si el cliente existe"""

    cit_cliente = CitCliente.query.get(cit_cliente_id)
    if cit_cliente is None:
        mensaje_error = f"El ID del cliente '{cit_cliente_id}' NO existe"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return None
    if cit_cliente.estatus != "A":
        mensaje_error = f"El ID del cliente {cit_cliente.id} NO tiene estatus activo"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return None
    # Regresa la cita
    return cit_cliente


def _cargar_plantilla(nombre_plantilla):
    """Carga el archivo para ser utilizado como plantilla Jinja2"""
    # Importar plantilla Jinja2
    entorno = Environment(
        loader=FileSystemLoader("citas_admin/blueprints/cit_citas/templates/cit_citas"),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    plantilla = entorno.get_template(nombre_plantilla)

    return plantilla


def _enviar_email(to_email, subject, content):
    """Envía el mensaje vía SendGrid"""

    # Validar remitente
    from_email = None
    if SENDGRID_FROM_EMAIL != "":
        from_email = Email(SENDGRID_FROM_EMAIL)
    else:
        return False

    # Validar SendGrid
    sendgrid_client = None
    if SENDGRID_API_KEY != "":
        sendgrid_client = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
    else:
        return False

    # Enviar mensaje
    to_email = "ricardo.valdes@pjecz.gob.mx" # DEBUG: Para probar, utilizo mi correo
    mail = Mail(from_email, to_email, subject, content)
    sendgrid_client.client.mail.send.post(request_body=mail.get())

    return True


if __name__ == "__main__":
    # enviar(22663)
    enviar_msg_cancelacion(22663)
