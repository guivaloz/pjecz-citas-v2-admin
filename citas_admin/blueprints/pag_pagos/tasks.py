"""
Pagos, tareas en el fondo
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
from lib.hashids import cifrar_id

from citas_admin.blueprints.pag_pagos.models import PagPago

from citas_admin.app import create_app
from citas_admin.extensions import db

locale.setlocale(locale.LC_TIME, "es_MX.utf8")

bitacora = logging.getLogger(__name__)
bitacora.setLevel(logging.INFO)
formato = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
empunadura = logging.FileHandler("pag_pagos.log")
empunadura.setFormatter(formato)
bitacora.addHandler(empunadura)

app = create_app()
db.app = app

load_dotenv()  # Take environment variables from .env

CANTIDAD = 10
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "")
PAGO_VERIFY_URL = os.getenv("PAGO_VERIFY_URL", "")


def enviar_mensaje_pagado(pag_pago_id, to_email=None):
    """Enviar mensaje de comprobante de pago vía correo electrónico"""

    # Consultar Pago
    pag_pago = PagPago.query.get(pag_pago_id)
    if pag_pago is None:
        mensaje_error = f"El ID del Pago '{pag_pago_id}' NO existe"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error
    if pag_pago.estatus != "A":
        mensaje_error = f"El ID {pag_pago.id} NO tiene estatus ACTIVO"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error
    if pag_pago.estado != "PAGADO":
        mensaje_error = f"El ID {pag_pago.id} NO tiene estado PAGADO"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error

    # Definir remitente para SendGrid
    if SENDGRID_FROM_EMAIL == "":
        mensaje_error = "La variable SENDGRID_FROM_EMAIL NO ha sido declarada"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error
    from_email = Email(SENDGRID_FROM_EMAIL)

    # Definir cliente de SendGrid
    if SENDGRID_API_KEY == "":
        mensaje_error = "La variable SENDGRID_API_KEY NO ha sido declarada"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error
    sendgrid_client = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)

    # Momento en que se elabora este mensaje
    momento = datetime.now()
    momento_str = momento.strftime("%d/%b/%Y %I:%M %p")

    # Definir la plantilla
    entorno = Environment(
        loader=FileSystemLoader("citas_admin/blueprints/pag_pagos/templates/pag_pagos"),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    plantilla = entorno.get_template("email.jinja2")

    # Generación de la URL de confirmación
    if PAGO_VERIFY_URL == "":
        mensaje_error = "La variable PAGO_VERIFY_URL NO ha sido declarada"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error
    url = PAGO_VERIFY_URL + "/" + cifrar_id(pag_pago.id)

    # Elaborar contenido del mensaje
    contenidos = plantilla.render(
        mensaje_asunto="Comprobante de Pago",
        fecha_elaboracion=momento_str,
        destinatario_nombre=pag_pago.cit_cliente.nombre,
        pag_pago=pag_pago,
        url=url,
    )

    # Si no se indicó un email de prueba se utilizará el registrado en el pago
    actualizar_registro = False
    if to_email is None:
        to_email = pag_pago.email
        actualizar_registro = True

    # Definir destinatario para SendGrid
    to_email = To(to_email)

    # Definir contenido para SendGrid
    content = Content("text/html", contenidos)

    # Enviar mensaje via SendGrid
    mail = Mail(from_email, to_email, "Comprobante de Pago PJECZ", content)
    try:
        sendgrid_client.client.mail.send.post(request_body=mail.get())
    except Exception as error:
        mensaje_error = f"ERROR al enviar mensaje: {str(error)}"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error

    # Si se utilizó el correo indicado en el pago se hace la actualización del registro de pago
    if actualizar_registro:
        pag_pago.ya_se_envio_comprobante = True
        pag_pago.save()

    # Terminar tarea
    set_task_progress(100)
    mensaje_final = f"Comprobante de Pago {pag_pago_id} enviado a {to_email}"
    bitacora.info(mensaje_final)
    return mensaje_final


def enviar_mensajes_comprobantes(before_creado, to_email=None):
    """Enviar mensajes vía correo electrónico"""

    # Consultar Pagos
    pagos = PagPago.query.filter_by(estatus="A").filter_by(estado="PAGADO").filter_by(ya_se_envio_comprobante=False).filter(PagPago.creado <= before_creado).all()

    # Enviamos los mensajes pendientes
    count = 0
    for pago in pagos:
        enviar_mensaje_pagado(pago.id, to_email)
        count += 1

    # Terminar tarea
    set_task_progress(100)
    mensaje_final = f"Se enviaron {count} comprobantes de pago creados antes del {before_creado.strftime('%Y-%m-%d %H:%M:%S')}"
    bitacora.info(mensaje_final)
    return mensaje_final


def cancelar_solicitados_expirados(before_creado):
    """Cambia el estado a CANCELADO de los pagos SOLICITADOS creados antes de before_creado"""

    # Selecciona Pagos con estado SOLICITADO y menor a before_creado en su tiempo de creado
    pagos = PagPago.query.filter_by(estatus="A").filter_by(estado="SOLICITADO").filter(PagPago.creado <= before_creado).all()

    # Cambia su estado a CANCELADO
    count = 0
    for pago in pagos:
        pago.estado = "CANCELADO"
        pago.save()
        count += 1

    # Terminar tarea
    set_task_progress(100)
    mensaje_final = f"Se cancelaron {count} pagos creados antes del {before_creado.strftime('%Y-%m-%d %H:%M:%S')}"
    bitacora.info(mensaje_final)
    return mensaje_final
