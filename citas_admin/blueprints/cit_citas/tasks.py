"""
Cit Citas, tareas en el fondo
"""
from datetime import datetime, timedelta
import locale
import logging
import os
import sendgrid

from dotenv import load_dotenv
from sendgrid.helpers.mail import Email, To, Content, Mail
from jinja2 import Environment, FileSystemLoader
from sqlalchemy import text

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


def enviar_msg_agendada(cit_cita_id, to_email=None):
    """Enviar mensaje con datos de la cita agendada"""

    cit_cita = _validacion_cita(cit_cita_id)
    if cit_cita is None:
        return None

    cit_cliente = _validacion_cliente(cit_cita.cit_cliente_id)
    if cit_cliente is None:
        return None

    # Si la oficina tiene palomeado Puede enviar códigos QR
    va_a_incluir_qr = False
    if cit_cita.oficina.puede_enviar_qr is True:  # Esta propiedad puede ser NULA
        va_a_incluir_qr = True

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
    plantilla = _cargar_plantilla("email.jinja2")
    contenidos = plantilla.render(
        fecha_elaboracion=datetime.now().strftime("%d/%b/%Y %I:%M %p"),
        cit_cliente=cit_cliente,
        cit_cita=cit_cita,
        va_a_incluir_qr=va_a_incluir_qr,
        asistencia_url=asistencia_url,
    )
    content = Content("text/html", contenidos)

    # Destinatario
    to_email = cit_cliente.email if to_email is None else to_email

    envio_correcto = _enviar_email(
        to_email=to_email,
        subject="Citas - Agendada",
        content=content,
    )

    if envio_correcto:
        if va_a_incluir_qr:
            mensaje_final = f"Se ha enviado un mensaje con QR a {to_email} de la cita agendada {cit_cita.id}, URL: {asistencia_url}"
        else:
            mensaje_final = f"Se ha enviado un mensaje a {to_email} de la cita agendada {cit_cita.id}"
        bitacora.info(mensaje_final)
    else:
        mensaje_error = f"Se omite el envío a {to_email} por que faltan elementos"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        mensaje_final = mensaje_error

    # Se termina la tarea y se envía el mensaje final
    set_task_progress(100)
    return mensaje_final


def enviar_msg_cancelacion(cit_cita_id, to_email=None):
    """Enviar mensaje de cita cancelada"""

    cit_cita = _validacion_cita(cit_cita_id)
    if cit_cita is None:
        return None

    cit_cliente = _validacion_cliente(cit_cita.cit_cliente_id)
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

    # Destinatario
    to_email = cit_cliente.email if to_email is None else to_email

    envio_correcto = _enviar_email(
        to_email=to_email,
        subject="Citas - Cancelación",
        content=content,
    )

    if envio_correcto:
        mensaje_final = f"Se ha enviado un mensaje a {to_email} de cancelación de la cita {cit_cita.id}"
        bitacora.info(mensaje_final)
    else:
        mensaje_error = f"Se omite el envío a {to_email} por que faltan elementos"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        mensaje_final = mensaje_error

    # Se termina la tarea y se envía el mensaje final
    set_task_progress(100)
    return mensaje_final


def enviar_msg_asistencia(cit_cita_id, to_email=None):
    """enviar mensaje de cita cancelada"""

    cit_cita = _validacion_cita(cit_cita_id)
    if cit_cita is None:
        return None

    cit_cliente = _validacion_cliente(cit_cita.cit_cliente_id)
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

    # Destinatario
    to_email = cit_cliente.email if to_email is None else to_email

    envio_correcto = _enviar_email(
        to_email=to_email,
        subject="Citas - Asistencia",
        content=content,
    )

    if envio_correcto:
        mensaje_final = f"Se ha enviado un mensaje a {to_email} de asistencia a la cita {cit_cita.id}"
        bitacora.info(mensaje_final)
    else:
        mensaje_error = f"Se omite el envío a {to_email} por que faltan elementos"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        mensaje_final = mensaje_error

    # Se termina la tarea y se envía el mensaje final
    set_task_progress(100)
    return mensaje_final


def enviar_msg_no_asistencia(cit_cita_id, to_email=None):
    """enviar mensaje de falta a la cita, no asistió"""

    cit_cita = _validacion_cita(cit_cita_id)
    if cit_cita is None:
        return None

    cit_cliente = _validacion_cliente(cit_cita.cit_cliente_id)
    if cit_cliente is None:
        return None

    # Importar plantilla Jinja2
    plantilla = _cargar_plantilla("email_no_assistance.jinja2")
    contenidos = plantilla.render(
        fecha_elaboracion=datetime.now().strftime("%d/%b/%Y %I:%M %p"),
        cit_cliente=cit_cliente,
        cit_cita=cit_cita,
    )
    content = Content("text/html", contenidos)

    # Destinatario
    to_email = cit_cliente.email if to_email is None else to_email

    envio_correcto = _enviar_email(
        to_email=to_email,
        subject="Citas - Inasistencia",
        content=content,
    )

    if envio_correcto:
        mensaje_final = f"Se ha enviado un mensaje a {to_email} de NO asistencia a la cita {cit_cita.id}"
        bitacora.info(mensaje_final)
    else:
        mensaje_error = f"Se omite el envío a {to_email} por que faltan elementos"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        mensaje_final = mensaje_error

    # Se termina la tarea y se envía el mensaje final
    set_task_progress(100)
    return mensaje_final


def marcar_vencidas(test=True):
    """Actualiza el estado de las citas a INASISTENCIA"""

    # Calcular fecha de vencimiento
    fecha_actual = datetime.now()
    fecha_limite = datetime(
        year=fecha_actual.year,
        month=fecha_actual.month,
        day=fecha_actual.day,
        hour=23,
        minute=59,
        second=59,
    )
    fecha_limite = fecha_limite - timedelta(days=1)

    # Si no esta en modo prueba, se ejecuta el Query
    if test is False:
        engine = db.engine
        actualizacion = text(
            f"UPDATE cit_citas \
                SET estado = 'INASISTENCIA' \
                WHERE estado = 'PENDIENTE' AND inicio <= '{fecha_limite.strftime('%y%m%d %H:%M')}' \
                AND estatus = 'A'"
        )
        res = engine.execute(actualizacion)
        mensaje_final = f"¡Se pasaron {res.rowcount} citas al estado de INASISTENCIA"
        bitacora.info(mensaje_final)

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
    mail = Mail(from_email, To(to_email), subject, content)
    sendgrid_client.client.mail.send.post(request_body=mail.get())

    return True
