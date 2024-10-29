"""
Cit Clientes Recuperaciones, tareas para ejecutar en el fondo
"""

import logging
import os
from datetime import datetime

import sendgrid
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
from sendgrid.helpers.mail import Content, Email, Mail, To

from citas_admin.app import create_app
from citas_admin.blueprints.cit_clientes_recuperaciones.models import CitClienteRecuperacion
from citas_admin.extensions import database
from lib.exceptions import MyAnyError, MyIsDeletedError, MyNotExistsError, MyNotValidParamError
from lib.tasks import set_task_error, set_task_progress

# Constantes
JINJA2_TEMPLATES_DIR = "citas_admin/blueprints/cit_clientes_recuperaciones/templates/cit_clientes_recuperaciones"
TIMEZONE = "America/Mexico_City"

# Bitácora logs/cit_clientes_recuperaciones.log
bitacora = logging.getLogger(__name__)
bitacora.setLevel(logging.INFO)
formato = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
empunadura = logging.FileHandler("logs/cit_clientes_recuperaciones.log")
empunadura.setFormatter(formato)
bitacora.addHandler(empunadura)

# Cargar variables de entorno
load_dotenv()
HOST = os.getenv("HOST", "http://localhost:5000")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "citas@pjecz.gob.mx")

# Cargar la aplicación para tener acceso a la base de datos
app = create_app()
app.app_context().push()
database.app = app


def enviar(cit_cliente_recuperacion_id: int, to_email: str = None) -> str:
    """Enviar mensaje via email con un URL para cambiar su contraseña"""

    # Agregar mensaje de inicio
    mensaje = f"Inicia el envío de mensaje con un URL para cambiar la contraseña para {to_email}"
    bitacora.info(mensaje)

    # Validar que esté configurado el API Key de SendGrid
    if SENDGRID_API_KEY == "":
        mensaje = "No está configurado el API Key de SendGrid"
        bitacora.error(mensaje)
        raise MyNotExistsError(mensaje)

    # Consultar y validar la recuperación
    cit_cliente_recuperacion = CitClienteRecuperacion.query.get(cit_cliente_recuperacion_id)
    if cit_cliente_recuperacion is None:
        mensaje = f"No existe la recuperación {cit_cliente_recuperacion_id}"
        bitacora.error(mensaje)
        raise MyNotExistsError(mensaje)
    if cit_cliente_recuperacion.estatus != "A":
        mensaje = f"La recuperación {cit_cliente_recuperacion_id} está eliminada"
        bitacora.error(mensaje)
        raise MyIsDeletedError(mensaje)
    if cit_cliente_recuperacion.ya_recuperado is True:
        mensaje = f"La recuperación {cit_cliente_recuperacion_id} ya fue utilizada"
        bitacora.error(mensaje)
        raise MyNotValidParamError(mensaje)

    # Si ya expiró la recuperación, eliminarla y terminar
    if cit_cliente_recuperacion.expiracion <= datetime.now():
        cit_cliente_recuperacion.delete()
        mensaje = f"La recuperación {cit_cliente_recuperacion_id} expiró"
        bitacora.info(mensaje)
        return mensaje

    # Validar el cliente
    if cit_cliente_recuperacion.cit_cliente.estatus != "A":
        mensaje = f"El cliente {cit_cliente_recuperacion.cit_cliente_id} está eliminado"
        bitacora.error(mensaje)
        raise MyIsDeletedError(mensaje)

    # Cargar la plantilla
    entorno = Environment(loader=FileSystemLoader(JINJA2_TEMPLATES_DIR), trim_blocks=True, lstrip_blocks=True)
    plantilla = entorno.get_template("email_password.jinja2")

    # Elaborar el asunto del mensaje
    asunto_str = f"PJECZ Sistema de Citas: Cambiar contraseña"

    # Elaborar el contenido del mensaje
    contenidos = plantilla.render(
        cit_cliente_recuperacion=cit_cliente_recuperacion,
        fecha_elaboracion=datetime.now().strftime("%d/%b/%Y %I:%M %p"),
        expiracion_horas=24,
        recuperacion_url=f"{HOST}/cit_clientes_recuperaciones/recuperar/{cit_cliente_recuperacion.encode_id()}",
    )

    # Si to_email es None, se usará el email del cliente
    if to_email is None:
        to_email = cit_cliente_recuperacion.cit_cliente.email

    # Enviar el mensaje
    send_grid = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
    remitente_email = Email(SENDGRID_FROM_EMAIL)
    destinatario_email = To(to_email)
    contenido = Content("text/html", contenidos)
    mail = Mail(remitente_email, destinatario_email, asunto_str, contenido)
    send_grid.client.mail.send.post(request_body=mail.get())

    # Entregar mensaje de término
    mensaje = f"Se envió el mensaje con un URL para cambiar su contraseña a {to_email}"
    bitacora.info(mensaje)
    return mensaje


def reenviar() -> str:
    """Reenviar mensajes via email a quienes no han terminado su recuperación"""

    # Agregar mensaje de inicio
    mensaje = f"Inicia el reenvío de mensajes de recuperación de contraseña"
    bitacora.info(mensaje)

    # Consultar las recuperaciones pendientes
    cit_clientes_recuperaciones = CitClienteRecuperacion.query.filter_by(ya_recuperado=False).filter_by(estatus="A").all()

    # Si la consulta no arrojo resultados, terminar
    if cit_clientes_recuperaciones is None:
        mensaje = "No hay recuperaciones pendientes"
        bitacora.info(mensaje)
        return mensaje

    # Bucle entre las recuperaciones pendientes
    contador = 0
    for cit_cliente_recuperacion in cit_clientes_recuperaciones:
        try:
            enviar(cit_cliente_recuperacion.id)
            contador += 1
        except MyAnyError as error:
            bitacora.warning(str(error))

    # Entregar mensaje de término
    mensaje = f"Se enviaron {contador} mensajes de recuperación de contraseña"
    bitacora.info(mensaje)
    return mensaje


def lanzar_enviar(cit_cliente_recuperacion_id: int, to_email: str = None):
    """Lanzar tarea para enviar mensaje con un URL para cambiar su contraseña"""

    # Iniciar la tarea en el fondo
    set_task_progress(0, "Inicia tarea para enviar mensaje con un URL para cambiar su contraseña")

    # Ejecutar
    try:
        mensaje_termino = enviar(cit_cliente_recuperacion_id, to_email)
    except MyAnyError as error:
        mensaje_error = str(error)
        set_task_error(mensaje_error)
        return mensaje_error

    # Terminar la tarea en el fondo y entregar el mensaje de término
    set_task_progress(100, mensaje_termino)
    return mensaje_termino


def lanzar_reenviar():
    """Lanzar tarea para reenviar mensajes a quienes no han terminado su recuperación"""

    # Iniciar la tarea en el fondo
    set_task_progress(0, "Inicia tarea para reenviar mensajes a quienes no han terminado su recuperación")

    # Ejecutar
    try:
        mensaje_termino = reenviar()
    except MyAnyError as error:
        mensaje_error = str(error)
        set_task_error(mensaje_error)
        return mensaje_error

    # Terminar la tarea en el fondo y entregar el mensaje de termino
    set_task_progress(100, mensaje_termino)
    return mensaje_termino
