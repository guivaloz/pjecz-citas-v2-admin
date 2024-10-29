"""
Cit Citas, tareas para ejecutar en el fondo
"""

import logging
import os
from datetime import datetime

import sendgrid
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
from sendgrid.helpers.mail import Content, Email, Mail, To

from citas_admin.app import create_app
from citas_admin.blueprints.cit_citas.models import CitCita
from citas_admin.extensions import database
from lib.exceptions import MyAnyError, MyIsDeletedError, MyNotExistsError, MyNotValidParamError
from lib.tasks import set_task_error, set_task_progress

# Constantes
JINJA2_TEMPLATES_DIR = "citas_admin/blueprints/cit_citas/templates/cit_citas"
TIMEZONE = "America/Mexico_City"

# Bitácora logs/cit_citas.log
bitacora = logging.getLogger(__name__)
bitacora.setLevel(logging.INFO)
formato = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
empunadura = logging.FileHandler("logs/cit_citas.log")
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


def enviar_pendiente(cit_cita_id: int, to_email: str = None) -> str:
    """Enviar mensaje vía email de una cita agendada"""

    # Agregar mensaje de inicio
    mensaje = f"Inicia el envío de mensaje de una cita agendada a {to_email}"
    bitacora.info(mensaje)

    # Validar que esté configurado el API Key de SendGrid
    if SENDGRID_API_KEY == "":
        mensaje = "No está configurado el API Key de SendGrid"
        bitacora.error(mensaje)
        raise MyNotExistsError(mensaje)

    # Consultar y validar la cita
    cit_cita = CitCita.query.get(cit_cita_id)
    if cit_cita is None:
        mensaje = f"La cita con ID {cit_cita_id} no existe"
        bitacora.error(mensaje)
        raise MyNotExistsError(mensaje)
    if cit_cita.estatus != "A":
        mensaje = f"La cita con ID {cit_cita_id} está eliminada"
        bitacora.error(mensaje)
        raise MyIsDeletedError(mensaje)
    if cit_cita.estado != "PENDIENTE":
        mensaje = f"La cita con ID {cit_cita_id} no está en estado PENDIENTE"
        bitacora.error(mensaje)
        raise MyNotValidParamError(mensaje)

    # Validar el cliente
    if cit_cita.cit_cliente.estatus != "A":
        mensaje = f"El cliente {cit_cita.cit_cliente_id} está eliminado"
        bitacora.error(mensaje)
        raise MyIsDeletedError(mensaje)

    # Cargar la plantilla
    entorno = Environment(loader=FileSystemLoader(JINJA2_TEMPLATES_DIR), trim_blocks=True, lstrip_blocks=True)
    plantilla = entorno.get_template("email_pending.jinja2")

    # Elaborar el asunto del mensaje
    asunto_str = f"PJECZ Sistema de Citas: Cita agendada"

    # Elaborar el contenido del mensaje
    contenidos = plantilla.render(cit_cita=cit_cita, fecha_elaboracion=datetime.now().strftime("%d/%b/%Y %I:%M %p"))

    # Si to_email es None, se usará el email del cliente
    if to_email is None:
        to_email = cit_cita.cit_cliente.email

    # Enviar el mensaje
    send_grid = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
    remitente_email = Email(SENDGRID_FROM_EMAIL)
    destinatario_email = To(to_email)
    contenido = Content("text/html", contenidos)
    mail = Mail(remitente_email, destinatario_email, asunto_str, contenido)
    send_grid.client.mail.send.post(request_body=mail.get())

    # Entregar mensaje de término
    mensaje = f"Mensaje enviado a {to_email} sobre una cita agendada"
    bitacora.info(mensaje)
    return mensaje


def enviar_cancelado(cit_cita_id: int, to_email: str = None) -> str:
    """Enviar mensaje vía email de una cita cancelada"""

    # Agregar mensaje de inicio
    mensaje = f"Inicia enviar vía email de una cita cancelada a {to_email}"
    bitacora.info(mensaje)

    # Validar que esté configurado el API Key de SendGrid
    if SENDGRID_API_KEY == "":
        mensaje = "No está configurado el API Key de SendGrid"
        bitacora.error(mensaje)
        raise MyNotExistsError(mensaje)

    # Consultar y validar la cita
    cit_cita = CitCita.query.get(cit_cita_id)
    if cit_cita is None:
        mensaje = f"La cita con ID {cit_cita_id} no existe"
        bitacora.error(mensaje)
        raise MyNotExistsError(mensaje)
    if cit_cita.estatus != "A":
        mensaje = f"La cita con ID {cit_cita_id} está eliminada"
        bitacora.error(mensaje)
        raise MyIsDeletedError(mensaje)
    if cit_cita.estado != "CANCELO":
        mensaje = f"La cita con ID {cit_cita_id} no está en estado CANCELO"
        bitacora.error(mensaje)
        raise MyNotValidParamError(mensaje)

    # Validar el cliente
    if cit_cita.cit_cliente.estatus != "A":
        mensaje = f"El cliente con ID {cit_cita.cit_cliente_id} está eliminado"
        bitacora.error(mensaje)
        raise MyIsDeletedError(mensaje)

    # Cargar la plantilla
    entorno = Environment(loader=FileSystemLoader(JINJA2_TEMPLATES_DIR), trim_blocks=True, lstrip_blocks=True)
    plantilla = entorno.get_template("email_cancelled.jinja2")

    # Elaborar el asunto del mensaje
    asunto_str = f"PJECZ Sistema de Citas: Cita cancelada"

    # Elaborar el contenido del mensaje
    contenidos = plantilla.render(cit_cita=cit_cita, fecha_elaboracion=datetime.now().strftime("%d/%b/%Y %I:%M %p"))

    # Si to_email es None, se usará el email del cliente
    if to_email is None:
        to_email = cit_cita.cit_cliente.email

    # Enviar el mensaje
    send_grid = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
    remitente_email = Email(SENDGRID_FROM_EMAIL)
    destinatario_email = To(to_email)
    contenido = Content("text/html", contenidos)
    mail = Mail(remitente_email, destinatario_email, asunto_str, contenido)
    send_grid.client.mail.send.post(request_body=mail.get())

    # Entregar mensaje de término
    mensaje = f"Mensaje enviado a {to_email} sobre una cita cancelada"
    bitacora.info(mensaje)
    return mensaje


def enviar_asistio(cit_cita_id: int, to_email: str = None) -> str:
    """Enviar mensaje vía email de su cita a la que asistió"""

    # Agregar mensaje de inicio
    mensaje = f"Inicia enviar vía email de una cita a la que asistió a {to_email}"
    bitacora.info(mensaje)

    # Validar que esté configurado el API Key de SendGrid
    if SENDGRID_API_KEY == "":
        mensaje = "No está configurado el API Key de SendGrid"
        bitacora.error(mensaje)
        raise MyNotExistsError(mensaje)

    # Consultar y validar la cita
    cit_cita = CitCita.query.get(cit_cita_id)
    if cit_cita is None:
        mensaje = f"La cita con ID {cit_cita_id} no existe"
        bitacora.error(mensaje)
        raise MyNotExistsError(mensaje)
    if cit_cita.estatus != "A":
        mensaje = f"La cita con ID {cit_cita_id} está eliminada"
        bitacora.error(mensaje)
        raise MyIsDeletedError(mensaje)
    if cit_cita.estado != "ASISTIO":
        mensaje = f"La cita con ID {cit_cita_id} no está en estado ASISTIO"
        bitacora.error(mensaje)
        raise MyNotValidParamError(mensaje)

    # Validar el cliente
    if cit_cita.cit_cliente.estatus != "A":
        mensaje = f"El cliente con ID {cit_cita.cit_cliente_id} está eliminado"
        bitacora.error(mensaje)
        raise MyIsDeletedError(mensaje)

    # Cargar la plantilla
    entorno = Environment(loader=FileSystemLoader(JINJA2_TEMPLATES_DIR), trim_blocks=True, lstrip_blocks=True)
    plantilla = entorno.get_template("email_assistance.jinja2")

    # Elaborar el asunto del mensaje
    asunto_str = f"PJECZ Sistema de Citas: Confirmación de asistencia"

    # Elaborar el contenido del mensaje
    contenidos = plantilla.render(cit_cita=cit_cita, fecha_elaboracion=datetime.now().strftime("%d/%b/%Y %I:%M %p"))

    # Si to_email es None, se usará el email del cliente
    if to_email is None:
        to_email = cit_cita.cit_cliente.email

    # Enviar el mensaje
    send_grid = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
    remitente_email = Email(SENDGRID_FROM_EMAIL)
    destinatario_email = To(to_email)
    contenido = Content("text/html", contenidos)
    mail = Mail(remitente_email, destinatario_email, asunto_str, contenido)
    send_grid.client.mail.send.post(request_body=mail.get())

    # Entregar mensaje de término
    mensaje = f"Mensaje enviado a {to_email} sobre una cita a la que asistió"
    bitacora.info(mensaje)
    return mensaje


def enviar_inasistencia(cit_cita_id: int, to_email: str = None) -> str:
    """Enviar un mensaje vía email de una cita por Inasistencia"""

    # Agregar mensaje de inicio
    mensaje = f"Inicia enviar vía email de una inasistencia a {to_email}"
    bitacora.info(mensaje)

    # Validar que esté configurado el API Key de SendGrid
    if SENDGRID_API_KEY == "":
        mensaje = "No está configurado el API Key de SendGrid"
        bitacora.error(mensaje)
        raise MyNotExistsError(mensaje)

    # Consultar y validar la cita
    cit_cita = CitCita.query.get(cit_cita_id)
    if cit_cita is None:
        mensaje = f"La cita con ID {cit_cita_id} no existe"
        bitacora.error(mensaje)
        raise MyNotExistsError(mensaje)
    if cit_cita.estatus != "A":
        mensaje = f"La cita con ID {cit_cita_id} está eliminada"
        bitacora.error(mensaje)
        raise MyIsDeletedError(mensaje)
    if cit_cita.estado != "INASISTENCIA":
        mensaje = f"La cita con ID {cit_cita_id} no está en estado INASISTENCIA"
        bitacora.error(mensaje)
        raise MyNotValidParamError(mensaje)

    # Validar el cliente
    if cit_cita.cit_cliente.estatus != "A":
        mensaje = f"El cliente con ID {cit_cita.cit_cliente_id} está eliminado"
        bitacora.error(mensaje)
        raise MyIsDeletedError(mensaje)

    # Cargar la plantilla
    entorno = Environment(loader=FileSystemLoader(JINJA2_TEMPLATES_DIR), trim_blocks=True, lstrip_blocks=True)
    plantilla = entorno.get_template("email_no_assistance.jinja2")

    # Elaborar el asunto del mensaje
    asunto_str = f"PJECZ Sistema de Citas: Aviso de inasistencia"

    # Elaborar el contenido del mensaje
    contenidos = plantilla.render(cit_cita=cit_cita, fecha_elaboracion=datetime.now().strftime("%d/%b/%Y %I:%M %p"))

    # Si to_email es None, se usará el email del cliente
    if to_email is None:
        to_email = cit_cita.cit_cliente.email

    # Enviar el mensaje
    send_grid = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
    remitente_email = Email(SENDGRID_FROM_EMAIL)
    destinatario_email = To(to_email)
    contenido = Content("text/html", contenidos)
    mail = Mail(remitente_email, destinatario_email, asunto_str, contenido)
    send_grid.client.mail.send.post(request_body=mail.get())

    # Entregar mensaje de término
    mensaje = f"Mensaje enviado a {to_email} sobre aviso de inasistencia"
    bitacora.info(mensaje)
    return mensaje


def lanzar_enviar_pendiente(cit_cita_id: int, to_email: str = None) -> str:
    """Lanzar tarea para enviar mensaje vía email de una cita agendada"""

    # Iniciar la tarea en el fondo
    set_task_progress(0, "Inicia tarea para enviar mensaje vía email de una cita agendada")

    # Ejecutar
    try:
        mensaje_termino = enviar_pendiente(cit_cita_id, to_email)
    except MyAnyError as error:
        mensaje_error = str(error)
        set_task_error(mensaje_error)
        return mensaje_error

    # Terminar la tarea en el fondo y entregar el mensaje de termino
    set_task_progress(100, mensaje_termino)
    return mensaje_termino


def lanzar_enviar_cancelado(cit_cita_id: int, to_email: str = None):
    """Lanzar tarea para enviar mensaje vía email de una cita cancelada"""

    # Iniciar la tarea en el fondo
    set_task_progress(0, "Inicia tarea para enviar mensaje vía email de una cita cancelada")

    # Ejecutar
    try:
        mensaje_termino = enviar_cancelado(cit_cita_id, to_email)
    except MyAnyError as error:
        mensaje_error = str(error)
        set_task_error(mensaje_error)
        return mensaje_error

    # Terminar la tarea en el fondo y entregar el mensaje de termino
    set_task_progress(100, mensaje_termino)
    return mensaje_termino


def lanzar_enviar_asistio(cit_cita_id: int, to_email: str = None):
    """Lanzar tarea para enviar mensaje vía email de su cita a la que asistió"""

    # Iniciar la tarea en el fondo
    set_task_progress(0, "Inicia tarea para enviar mensaje vía email de su cita a la que asistió")

    # Ejecutar
    try:
        mensaje_termino = enviar_asistio(cit_cita_id, to_email)
    except MyAnyError as error:
        mensaje_error = str(error)
        set_task_error(mensaje_error)
        return mensaje_error

    # Terminar la tarea en el fondo y entregar el mensaje de termino
    set_task_progress(100, mensaje_termino)
    return mensaje_termino


def lanzar_enviar_inasistencia(cit_cita_id: int, to_email: str = None):
    """Lanzar tarea para enviar un mensaje vía email de una cita por Inasistencia"""

    # Iniciar la tarea en el fondo
    set_task_progress(0, "Inicia tarea para enviar un mensaje vía email de una cita por Inasistencia")

    # Ejecutar
    try:
        mensaje_termino = enviar_inasistencia(cit_cita_id, to_email)
    except MyAnyError as error:
        mensaje_error = str(error)
        set_task_error(mensaje_error)
        return mensaje_error

    # Terminar la tarea en el fondo y entregar el mensaje de termino
    set_task_progress(100, mensaje_termino)
    return mensaje_termino
