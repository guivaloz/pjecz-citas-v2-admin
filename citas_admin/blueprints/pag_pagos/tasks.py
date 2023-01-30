"""
Pagos, tareas en el fondo
"""
from datetime import datetime
import locale
import logging
import os

from delta import html
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


def enviar(pag_pago_id, email=None):
    """Enviar mensajes vía correo electrónico"""

    # Consultar Pago
    pago = PagPago.query.get(pag_pago_id)
    if pago is None:
        mensaje_error = f"El ID del Pago '{pag_pago_id}' NO existe"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error
    if pago.estatus != "A":
        mensaje_error = f"El ID {pago.id} NO tiene estatus ACTIVO"
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

    # Si viene un e-mail de pruebas
    if email is None:
        email = pago.email

    # Momento en que se elabora este mensaje
    momento = datetime.now()
    momento_str = momento.strftime("%d/%b/%Y %I:%M %p")

    # Definir cliente de SendGrid
    sendgrid_client = None
    if SENDGRID_API_KEY != "":
        sendgrid_client = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
    else:
        bitacora.warning("La variable SENDGRID_API_KEY NO ha sido declarada.")

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
    url = PAGO_VERIFY_URL + cifrar_id(pago.id)

    # Elaborar contenido del mensaje
    contenidos = plantilla.render(
        mensaje_asunto="Comprobante de Pago",
        fecha_elaboracion=momento_str,
        destinatario_nombre=pago.cit_cliente.nombre,
        pago=pago,
        url=url,
    )

    # Si la variable SENDGRID_API_KEY NO ha sido declarada
    if SENDGRID_API_KEY == "":
        # Guardar mensaje en archivo
        archivo_html = f"pago_{pago.id}_{email}_{momento.strftime('%Y%m%d_%H%M%S')}.html"
        with open(archivo_html, "w", encoding="UTF-8") as puntero:
            puntero.write(contenidos)
        bitacora.info("Se guardó el mensaje en %s", archivo_html)

    # Definir destinatario para SendGrid
    to_email = To(email)

    # Definir contenido para SendGrid
    content = Content("text/html", contenidos)

    # Enviar mensaje via SendGrid
    mail = Mail(from_email, to_email, "Comprobante de Pago PJECZ", content)
    try:
        sendgrid_client.client.mail.send.post(request_body=mail.get())
        pago.ya_se_envio_comprobante = True
        pago.save()
    except Exception as error:
        mensaje_error = f"ERROR al enviar mensaje: {str(error)}"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error

    # Terminar tarea
    set_task_progress(100)
    mensaje_final = f"Comprobante de Pago enviado a {email}"
    bitacora.info(mensaje_final)
    return mensaje_final


def enviar_mensajes_comprobantes(tiempo, email=None):
    """Enviar mensajes vía correo electrónico"""

    # Consultar Pagos
    pagos = PagPago.query.filter_by(estatus="A").filter_by(estado="PAGADO").filter_by(ya_se_envio_comprobante=False).filter(PagPago.creado <= tiempo).all()

    count = 0
    for pago in pagos:
        enviar(pago.id, email)
        count += 1

    # Terminar tarea
    set_task_progress(100)
    mensaje_final = f"Se enviaron {count} comprobantes de pago"
    bitacora.info(mensaje_final)
    return mensaje_final


def cancelar_solicitados_expirados(tiempo_limite):
    """Pasa a estado de CANCELADO todos los pagos en estado previo de SOLICITADO"""

    # Seleccionar Pagos con estado SOLICITADO y menor al tiempo límite indicado
    pagos = PagPago.query.filter_by(estatus="A").filter_by(estado="SOLICITADO").filter(PagPago.creado <= tiempo_limite).all()

    # Contador de registros modificados
    count = 0
    for pago in pagos:
        pago.estado = "CANCELADO"
        pago.save()
        count += 1

    # Terminar tarea
    set_task_progress(100)
    mensaje_final = f"Se cancelaron {count} pagos"
    bitacora.info(mensaje_final)
    return mensaje_final
