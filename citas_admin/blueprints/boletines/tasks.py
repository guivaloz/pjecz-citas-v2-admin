"""
Boletines, tareas en el fondo
"""
from datetime import datetime
import locale
import logging
import os

from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
import sendgrid
from sendgrid.helpers.mail import Email, To, Content, Mail

from lib.tasks import set_task_progress, set_task_error

from citas_admin.blueprints.boletines.models import Boletin
from citas_admin.blueprints.cit_clientes.models import CitCliente

from citas_admin.app import create_app
from citas_admin.extensions import db

locale.setlocale(locale.LC_TIME, "es_MX.utf8")

bitacora = logging.getLogger(__name__)
bitacora.setLevel(logging.INFO)
formato = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
empunadura = logging.FileHandler("boletines.log")
empunadura.setFormatter(formato)
bitacora.addHandler(empunadura)

app = create_app()
db.app = app

load_dotenv()  # Take environment variables from .env

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "")


def enviar(boletin_id, cit_cliente_id=None, email=None):
    """Enviar boletin"""

    # Definir valores por defecto del destinatario
    destinatario_nombre = "Destinatario para Pruebas"
    destinatario_email = ""
    if email is not None:
        destinatario_email = email

    # Consultar boletin
    boletin = Boletin.query.get(boletin_id)
    if boletin is None:
        mensaje_error = f"El ID del boletin '{boletin_id}' NO existe"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error
    if boletin.estatus != "A":
        mensaje_error = f"El ID {boletin.id} NO tiene estatus ACTIVO"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error

    # Consultar cliente
    if cit_cliente_id is not None:
        cit_cliente = CitCliente.query.get(cit_cliente_id)
        if cit_cliente is None:
            mensaje_error = f"El ID del cliente '{cit_cliente_id}' NO existe"
            set_task_error(mensaje_error)
            bitacora.error(mensaje_error)
            return mensaje_error
        if cit_cliente.estatus != "A":
            mensaje_error = f"El ID {cit_cliente.id} NO tiene estatus ACTIVO"
            set_task_error(mensaje_error)
            bitacora.error(mensaje_error)
            return mensaje_error
        if email is None:
            destinatario_email = cit_cliente.email

    # Momento en que se elabora este mensaje
    momento = datetime.now()
    momento_str = momento.strftime("%d/%b/%Y %I:%M %p")

    # Elaborar contenido del mensaje
    entorno = Environment(
        loader=FileSystemLoader("citas_admin/blueprints/boletines/templates/boletines"),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    plantilla = entorno.get_template("email.jinja2")
    contenidos = plantilla.render(
        mensaje_asunto=boletin.asunto,
        fecha_elaboracion=momento_str,
        destinatario_nombre=destinatario_nombre,
        mensaje_contenido=boletin.contenido,
    )

    # Si no hay e-mail de destinatario, se guarda el mensaje en un archivo
    if destinatario_email == "":
        # Guardar mensaje en archivo
        archivo = f"boletin_{boletin.id}_{momento.strftime('%Y%m%d_%H%M%S')}.html"
        with open(archivo, "w", encoding="UTF-8") as archivo:
            archivo.write(contenidos)
        # Terminar tarea
        set_task_progress(100)
        mensaje_final = "No hay e-mail de destinatario, no se envía"
        bitacora.info(mensaje_final)
        return mensaje_final

    # Definir remitente para SendGrid
    if SENDGRID_FROM_EMAIL == "":
        mensaje_error = "La variable SENDGRID_FROM_EMAIL NO ha sido declarada"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error
    from_email = Email(SENDGRID_FROM_EMAIL)

    # Definir destinatario para SendGrid
    to_email = To(destinatario_email)

    # Definir contenido para SendGrid
    content = Content("text/html", contenidos)

    # Definir cliente para SendGrid
    sendgrid_client = None
    if SENDGRID_API_KEY == "":
        mensaje_error = "La variable SENDGRID_API_KEY NO ha sido declarada"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error
    sendgrid_client = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)

    # Enviar mensaje via SendGrid
    mail = Mail(from_email, to_email, boletin.asunto, content)
    try:
        sendgrid_client.client.mail.send.post(request_body=mail.get())
    except Exception as error:
        mensaje_error = f"Error al enviar mensaje: {str(error)}"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error

    # Terminar tarea
    set_task_progress(100)
    mensaje_final = f"Boletin enviado a {destinatario_email}"
    bitacora.info(mensaje_final)
    return mensaje_final
