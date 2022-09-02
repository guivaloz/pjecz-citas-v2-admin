"""
Enc Sistemas, tareas para ejecutar en el fondo
"""
from datetime import datetime
import locale
import logging
import os

import sendgrid
from dotenv import load_dotenv
from sendgrid.helpers.mail import Email, To, Content, Mail

from lib.tasks import set_task_progress, set_task_error

from citas_admin.app import create_app
from citas_admin.extensions import db

from citas_admin.blueprints.enc_sistemas.models import EncSistema
from citas_admin.blueprints.cit_clientes.models import CitCliente

locale.setlocale(locale.LC_TIME, "es_MX.utf8")

bitacora = logging.getLogger(__name__)
bitacora.setLevel(logging.INFO)
formato = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
empunadura = logging.FileHandler("enc_sistemas.log")
empunadura.setFormatter(formato)
bitacora.addHandler(empunadura)

app = create_app()
db.app = app

load_dotenv()  # Take environment variables from .env

EXPIRACION_HORAS = 48
POLL_SYSTEM_URL = os.getenv("POLL_SYSTEM_URL", "")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "")


def enviar(enc_sistemas_id):
    """Enviar mensaje con URL para ver la encuesta de sistemas"""

    # Consultar encuesta
    encuesta = EncSistema.query.get(enc_sistemas_id)
    if encuesta is None:
        mensaje_error = f"El ID de la encuesta sistemas '{enc_sistemas_id}' NO existe dentro la tabla enc_sistemas"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error
    if encuesta.estatus != "A":
        mensaje_error = f"El ID {encuesta.id} NO tiene estatus activo"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error

    # Validar el cliente
    cliente = CitCliente.query.get(encuesta.cit_cliente_id)
    if cliente is None:
        mensaje_error = f"El ID del cliente '{encuesta.cit_cliente_id}' NO existe dentro la tabla cit_clientes"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error
    if cliente.estatus != "A":
        mensaje_error = f"El ID del cliente {cliente.id} NO tiene estatus activo"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error

    # Momento en que se elabora este mensaje
    momento = datetime.now()
    momento_str = momento.strftime("%d/%B/%Y %I:%M %p")

    # Validar POLL_SYSTEM_URL
    url = None
    if POLL_SYSTEM_URL == "":
        mensaje_error = "La variable POLL_SYSTEM_URL NO ha sido declarada"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error
    url = f"{POLL_SYSTEM_URL}?hashid={encuesta.encode_id()}"

    # Contenidos
    contenidos = [
        "<h1>Sistema de Citas - Encuesta de Satisfacción</h1>",
        "<h2>PODER JUDICIAL DEL ESTADO DE COAHUILA DE ZARAGOZA</h2>",
        f"<small>Fecha de elaboración: {momento_str}.</small>",
        f"<h3>Buen día {cliente.nombre}.</h3>",
        "<p>Hemos detectado que agendó una cita en nuestro sistema recientemente.<br>",
        "Le gustaría contestar una encuesta corta de satisfacción para conocer su experiencia con este sistema.<br>",
        "Sus comentarios nos ayudarían a mejorar nuestro sistema.</p>",
        "<p>Si desea contestar la encuesta, le invitamos vaya al siguiente enlace:<br>",
        f"<a href='{url}'>Contestar Encuesta de Satisfacción</a></p>",
        "<p>De antemano le agradecemos prestar atención a este mensaje.</p>",
        "<p>Que tenga un excelente día.</p>",
        "<small><strong>ESTE MENSAJE ES ELABORADO POR UN PROGRAMA. FAVOR DE NO RESPONDER.</strong></small>",
    ]
    content = Content("text/html", "\n".join(contenidos))

    # Remitente
    if SENDGRID_FROM_EMAIL == "":
        mensaje_error = "La variable SENDGRID_FROM_EMAIL NO ha sido declarada"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error
    from_email = Email(SENDGRID_FROM_EMAIL)

    # Destinatario
    to_email = To(cliente.email)

    # Asunto
    subject = "Encuesta de satisfacción del Sistema de Citas"

    # SendGrid
    sendgrid_client = None
    if SENDGRID_API_KEY == "":
        mensaje_error = "La variable SENDGRID_API_KEY NO ha sido declarada"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error
    sendgrid_client = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)

    # Enviar mensaje
    mail = Mail(from_email, to_email, subject, content)
    sendgrid_client.client.mail.send.post(request_body=mail.get())

    # Terminar tarea
    set_task_progress(100)
    mensaje_final = f"Se ha enviado un mensaje a {cliente.email} con la URL: {url}"
    bitacora.info(mensaje_final)
    return mensaje_final
