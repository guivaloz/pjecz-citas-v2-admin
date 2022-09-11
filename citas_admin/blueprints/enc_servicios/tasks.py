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
from jinja2 import Environment, FileSystemLoader

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
        mensaje_error = f"El ID de la encuesta servicios '{enc_servicios_id}' NO existe"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error
    if encuesta.estatus != "A":
        mensaje_error = f"El ID {encuesta.id} NO tiene estatus ACTIVO"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error
    if encuesta.estado != "PENDIENTE":
        mensaje_error = f"La encuesta con ID {encuesta.id} tiene un estado diferente de PENDIENTE"
        set_task_error(mensaje_error)
        bitacora.warning(mensaje_error)
        return mensaje_error

    # Validar el Cliente
    cliente = CitCliente.query.get(encuesta.cit_cliente_id)
    if cliente is None:
        mensaje_error = f"El ID del cliente '{encuesta.cit_cliente_id}' NO existe"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error
    if cliente.estatus != "A":
        mensaje_error = f"El ID del cliente {cliente.id} NO tiene estatus ACTIVO"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error

    # Validar la Oficina
    oficina = Oficina.query.get(encuesta.oficina_id)
    if oficina is None:
        mensaje_error = f"El ID de la oficina '{encuesta.oficina_id}' NO existe"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error
    if oficina.estatus != "A":
        mensaje_error = f"El ID de la oficina {oficina.id} NO tiene estatus ACTIVO"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error

    # Momento en que se elabora este mensaje
    momento = datetime.now()
    momento_str = momento.strftime("%d/%b/%Y %I:%M %p")

    # Validar POLL_SERVICE_URL
    url = None
    if POLL_SERVICE_URL == "":
        mensaje_error = "La variable POLL_SYSTEM_URL NO ha sido declarada"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error
    url = f"{POLL_SERVICE_URL}?hashid={encuesta.encode_id()}"

    # Importar plantilla Jinja2
    entorno = Environment(
        loader=FileSystemLoader("citas_admin/blueprints/enc_servicios/templates/enc_servicios"),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    plantilla = entorno.get_template("email.jinja2")
    contenidos = plantilla.render(
        fecha_elaboracion=momento_str,
        cliente_nombre=cliente.nombre,
        url_encuesta=url,
    )
    content = Content("text/html", contenidos)

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
    subject = "Encuesta de Servicio otorgado por el PJECZ"

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
