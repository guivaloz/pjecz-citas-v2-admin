"""
Cit Clientes Recuperaciones, tareas para ejecutar en el fondo
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
from citas_admin.extensions import database

from citas_admin.blueprints.cit_clientes_recuperaciones.models import CitClienteRecuperacion

locale.setlocale(locale.LC_TIME, "es_MX.utf8")

bitacora = logging.getLogger(__name__)
bitacora.setLevel(logging.INFO)
formato = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
empunadura = logging.FileHandler("cit_clientes_recuperaciones.log")
empunadura.setFormatter(formato)
bitacora.addHandler(empunadura)

app = create_app()
db.app = app

load_dotenv()  # Take environment variables from .env

EXPIRACION_HORAS = 48
RECOVER_ACCOUNT_CONFIRM_URL = os.getenv("RECOVER_ACCOUNT_CONFIRM_URL", "")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "")


def enviar(cit_cliente_recuperacion_id):
    """Enviar mensaje con URL para definir contrasena"""

    # Consultar
    cit_cliente_recuperacion = CitClienteRecuperacion.query.get(cit_cliente_recuperacion_id)
    if cit_cliente_recuperacion.estatus != "A":
        mensaje_error = f"El ID {cit_cliente_recuperacion.id} NO tiene estatus activo"
        set_task_error(mensaje_error)
        bitacora.warning(mensaje_error)
        return mensaje_error
    if cit_cliente_recuperacion.ya_recuperado is True:
        mensaje_error = f"El ID {cit_cliente_recuperacion.id} YA fue recuperado"
        set_task_error(mensaje_error)
        bitacora.warning(mensaje_error)
        return mensaje_error

    # Bandera para saber si se tienen todos los elementos necesarios
    bandera = True

    # Momento en que se elabora este mensaje
    momento = datetime.now()
    momento_str = momento.strftime("%d/%B/%Y %I:%M%p")

    # URL
    url = None
    if RECOVER_ACCOUNT_CONFIRM_URL != "":
        url = f"{RECOVER_ACCOUNT_CONFIRM_URL}?hashid={cit_cliente_recuperacion.encode_id()}&cadena_validar={cit_cliente_recuperacion.cadena_validar}</p>"
    else:
        bandera = False

    # Contenidos
    contenidos = [
        "<h1>Sistema de Citas</h1>",
        "<h2>PODER JUDICIAL DEL ESTADO DE COAHUILA DE ZARAGOZA</h2>",
        f"<p>Fecha de elaboración: {momento_str}.</p>",
        f"Antes de {EXPIRACION_HORAS} horas vaya a este URL para cambiar su contraseña:<br>",
        url,
        "<p>ESTE MENSAJE ES ELABORADO POR UN PROGRAMA. FAVOR DE NO RESPONDER.</p>",
    ]
    content = Content("text/html", "".join(contenidos))

    # Remitente
    from_email = None
    if SENDGRID_FROM_EMAIL != "":
        from_email = Email(SENDGRID_FROM_EMAIL)
    else:
        bandera = False

    # Destinatario
    to_email = To(cit_cliente_recuperacion.cit_cliente.email)

    # Asunto
    subject = "Recuperar su contraseña en el Sistema de Citas"

    # SendGrid
    sendgrid_client = None
    if SENDGRID_API_KEY != "":
        sendgrid_client = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
    else:
        bandera = False

    # Enviar mensaje
    mensaje_final = ""
    if bandera:
        mail = Mail(from_email, to_email, subject, content)
        sendgrid_client.client.mail.send.post(request_body=mail.get())
        mensaje_final = f"Se ha enviado el mensaje {cit_cliente_recuperacion.mensajes_cantidad} a {cit_cliente_recuperacion.cit_cliente.email}"
        bitacora.info(mensaje_final)
    else:
        mensaje_final = f"Se omite el envio a {cit_cliente_recuperacion.cit_cliente.email} por que faltan elementos"
        bitacora.warning(mensaje_final)

    # Incrementar contador
    if bandera:
        cit_cliente_recuperacion.mensajes_cantidad += 1
        cit_cliente_recuperacion.save()

    # Terminar tarea
    set_task_progress(100)
    return mensaje_final


def reenviar():
    """Reenviar mensajes a quienes no han terminado su recuperacion"""

    # Consultar las recuperaciones pendientes
    consulta = CitClienteRecuperacion.query.filter_by(ya_recuperado=False).filter_by(estatus="A").all()

    # Si la consulta no arrojo resultados, terminar
    if len(consulta) == 0:
        set_task_progress(100)
        mensaje_final = "No hay recuperaciones pendientes, no se reenviaron mensajes"
        bitacora.info(mensaje_final)
        return mensaje_final

    # Bucle para enviar los mensajes
    bajas_cantidad = 0
    envios_cantidad = 0
    for recuperacion in consulta:

        # Si ya expiró, no se envía y de da de baja
        if recuperacion.expiracion <= datetime.now():
            recuperacion.estatus = "B"
            recuperacion.save()
            bajas_cantidad += 1
            continue

        # Enviar el mensaje
        enviar(recuperacion.id)

        # Incrementar
        envios_cantidad += 1

    # Terminar tarea
    set_task_progress(100)
    mensaje_final = f"Se han reenviado {envios_cantidad} mensajes de recuperaciones y se dieron de baja {bajas_cantidad}"
    bitacora.info(mensaje_final)
    return mensaje_final
