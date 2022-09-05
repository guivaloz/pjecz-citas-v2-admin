"""
Enc Servicios, tareas para ejecutar en el fondo
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

from citas_admin.blueprints.enc_servicios.models import EncServicio
from citas_admin.blueprints.cit_clientes.models import CitCliente
from citas_admin.blueprints.oficinas.models import Oficina

locale.setlocale(locale.LC_TIME, "es_MX.utf8")

bitacora = logging.getLogger(__name__)
bitacora.setLevel(logging.INFO)
formato = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
empunadura = logging.FileHandler("enc_servicios.log")
empunadura.setFormatter(formato)
bitacora.addHandler(empunadura)

app = create_app()
db.app = app

load_dotenv()  # Take environment variables from .env

POLL_SERVICE_URL = os.getenv("POLL_SERVICE_URL", "")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "")


def enviar(enc_servicios_id):
    """Enviar mensaje con URL para ver la encuesta de sistemas"""

    # Consultar encuesta
    encuesta = EncServicio.query.get(enc_servicios_id)
    if encuesta is None:
        mensaje_error = f"El ID de la encuesta servicios '{enc_servicios_id}' NO existe dentro la tabla enc_servicios"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error
    if encuesta.estatus != "A":
        mensaje_error = f"El ID {encuesta.id} NO tiene estatus activo"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error
    if encuesta.estado != "PENDIENTE":
        mensaje_error = "La encuesta tiene un estado diferente de PENDIENTE"
        set_task_error(mensaje_error)
        bitacora.warning(mensaje_error)
        return mensaje_error

    # Validar el Cliente
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

    # Validar la Oficina
    oficina = Oficina.query.get(encuesta.oficina_id)
    if oficina is None:
        mensaje_error = f"El ID del oficina '{encuesta.oficina_id}' NO existe dentro la tabla oficinas"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error
    if oficina.estatus != "A":
        mensaje_error = f"El ID del oficina {oficina.id} NO tiene estatus activo"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error

    # Momento en que se elabora este mensaje
    momento = datetime.now()
    momento_str = momento.strftime("%d/%B/%Y %I:%M %p")

    # Validar POLL_SERVICE_URL
    url = None
    if POLL_SERVICE_URL == "":
        mensaje_error = "La variable POLL_SYSTEM_URL NO ha sido declarada"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error
    url = f"{POLL_SERVICE_URL}?hashid={encuesta.encode_id()}"

    # Contenidos
    contenidos = [
        "<h1>Sistema de Citas - Encuesta de Servicio</h1>",
        "<h2>PODER JUDICIAL DEL ESTADO DE COAHUILA DE ZARAGOZA</h2>",
        f"<small>Fecha de elaboración: {momento_str}.</small>",
        f"<h3>Buen día {cliente.nombre}.</h3>",
        f"<p>Hemos detectado con nuestro sistema de citas que hizo un trámite en la oficina {oficina.descripcion}.<br>",
        "Le gustaría contestar una encuesta corta de servicio para conocer su experiencia en esta oficina.<br>",
        "Sus comentarios nos ayudarían a mejorar nuestros servicios.</p>",
        "<p>Si desea contestar la encuesta, le invitamos vaya al siguiente enlace:<br>",
        f"<a href='{url}'>Contestar Encuesta de Servicio</a></p>",
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
    subject = "Encuesta de satisfacción del servicio otorgado por el PJECZ"

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
