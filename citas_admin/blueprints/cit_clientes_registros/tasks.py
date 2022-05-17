"""
Cit Clientes Registros, tareas para ejecutar en el fondo
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

from citas_admin.blueprints.cit_clientes_registros.models import CitClienteRegistro

locale.setlocale(locale.LC_TIME, "es_MX.utf8")

bitacora = logging.getLogger(__name__)
bitacora.setLevel(logging.INFO)
formato = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
empunadura = logging.FileHandler("cit_clientes_registros.log")
empunadura.setFormatter(formato)
bitacora.addHandler(empunadura)

app = create_app()
db.app = app

load_dotenv()  # Take environment variables from .env

EXPIRACION_HORAS = 48
NEW_ACCOUNT_CONFIRM_URL = os.getenv("NEW_ACCOUNT_CONFIRM_URL", "https://localhost:3000/new_account_confirm")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "")


def enviar(cit_cliente_registro_id):
    """Enviar mensaje con URL de confirmacion"""

    # Consultar
    cit_cliente_registro = CitClienteRegistro.query.get(cit_cliente_registro_id)
    if cit_cliente_registro.estatus != "A":
        mensaje_error = f"El ID {cit_cliente_registro.id} NO tiene estatus activo"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error
    if cit_cliente_registro.ya_registrado is True:
        mensaje_error = f"El ID {cit_cliente_registro.id} YA fue registrado"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error

    # Bandera para saber si se tienen todos los elementos necesarios
    bandera = True

    # Momento en que se elabora este mensaje
    momento = datetime.now()
    momento_str = momento.strftime("%d/%B/%Y %I:%M%p")

    # Contenidos
    contenidos = [
        "<h1>Sistema de Citas</h1>",
        "<h2>PODER JUDICIAL DEL ESTADO DE COAHUILA DE ZARAGOZA</h2>",
        f"<p>Fecha de elaboración: {momento_str}.</p>",
        f"<p>Antes de {EXPIRACION_HORAS} horas vaya a esta pagina para validar y definir su contrasena:<br>",
        "{NEW_ACCOUNT_CONFIRM_URL}?confirm={cit_cliente_registro.cadena_validar}</p>",
        "<p>ESTE MENSAJE ES ELABORADO POR UN PROGRAMA. FAVOR DE NO RESPONDER.</p>",
    ]
    content = Content("text/html", "<br>".join(contenidos))

    # Remitente
    from_email = None
    if SENDGRID_FROM_EMAIL != "":
        from_email = Email(SENDGRID_FROM_EMAIL)
    else:
        bandera = False

    # Destinatario
    to_email = To(cit_cliente_registro.email)

    # Asunto
    subject = "Verificar su cuenta en el Sistema de Citas"

    # SendGrid
    sendgrid_client = None
    if SENDGRID_API_KEY != "":
        sendgrid_client = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
    else:
        bandera = False

    # Enviar mensaje
    if bandera:
        mail = Mail(from_email, to_email, subject, content)
        sendgrid_client.client.mail.send.post(request_body=mail.get())
    else:
        bitacora.warning("Se omite el envio a XXXX por XXX")

    # Incrementar contador
    cit_cliente_registro.mensajes_cantidad += 1
    cit_cliente_registro.save()

    # Terminar tarea
    set_task_progress(100)
    mensaje_final = f"Se ha enviado el mensaje {cit_cliente_registro.mensajes_cantidad} a {cit_cliente_registro.email}"
    bitacora.info(mensaje_final)
    return mensaje_final
