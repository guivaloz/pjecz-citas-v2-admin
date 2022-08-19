"""
Cit Citas, tareas en el fondo
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

from citas_admin.blueprints.cit_citas.models import CitCita

locale.setlocale(locale.LC_TIME, "es_MX.utf8")

bitacora = logging.getLogger(__name__)
bitacora.setLevel(logging.INFO)
formato = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
empunadura = logging.FileHandler("cit_citas.log")
empunadura.setFormatter(formato)
bitacora.addHandler(empunadura)

app = create_app()
db.app = app

load_dotenv()  # Take environment variables from .env

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "")
HOST = os.getenv("HOST", "")


def enviar(cit_cita_id):
    """Enviar mensaje con datos de la cita agendada"""

    # Consultar
    cit_cita = CitCita.query.get(cit_cita_id)
    if cit_cita.estatus != "A":
        mensaje_error = f"El ID {cit_cita.id} NO tiene estatus activo"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error

    # Esta completo para enviar el mensaje por correo electronico
    esta_completo_para_enviar_mensaje = True

    # Si la oficina tiene palomeado Puede enviar codigos QR
    va_a_incluir_qr = False
    if cit_cita.oficina.puede_enviar_qr is True:  # Esta propuedad puede ser NULA
        va_a_incluir_qr = True

    # Momento en que se elabora este mensaje
    momento = datetime.now()

    # Si puede enviar codigos QR
    asistencia_url = None
    if va_a_incluir_qr:
        # Validar que este definido el HOST
        if HOST == "":
            va_a_incluir_qr = False
            bitacora.warning("No se incluye el codigo QR porque la variable HOST no esta definida.")
        else:
            # Definir el URL para marcar asistencia
            asistencia_url = HOST + "/cit_citas/asistencia/" + cit_cita.encode_id()

    # Contenidos
    contenidos = []
    contenidos.append("<h1>Sistema de Citas</h1>")
    contenidos.append("<h2>PODER JUDICIAL DEL ESTADO DE COAHUILA DE ZARAGOZA</h2>")
    contenidos.append(f"<p>Fecha de elaboración: {momento.strftime('%Y.%m.%d - %I:%M %p')}.</p>")
    contenidos.append("<p>Le proporcionamos la información detalla de la cita que agendó en este sistema:</p>")
    contenidos.append("<ul>")
    contenidos.append(f"<li><strong>Nombre</strong>: {cit_cita.cit_cliente.nombre}</li>")
    contenidos.append(f"<li><strong>Oficina</strong>: {cit_cita.oficina.descripcion}</li>")
    contenidos.append(f"<li><strong>Servicio</strong>: {cit_cita.cit_servicio.descripcion}</li>")
    contenidos.append(f"<li><strong>Fecha y hora</strong>: {cit_cita.inicio.strftime('%d de %B de %Y a las %I:%M %p')}</li>")
    contenidos.append(f"<li><strong>Notas</strong>: {cit_cita.notas}</li>")
    contenidos.append("</ul>")
    contenidos.append("<small>Por favor llegue diez minutos antes de la fecha y hora mencionados.</small>")
    if va_a_incluir_qr:
        contenidos.append("<h3>Código QR para marcar asistencia</h3>")
        contenidos.append(f'<img src="https://chart.googleapis.com/chart?chs=250x250&cht=qr&chl={asistencia_url}" alt="[ERROR_EN_QR]">')
        contenidos.append("<p>Si no no se ve el QR, active la opción para mostrar las imágenes.</p>")
        contenidos.append("<p>Por favor, al llegar exija que le escaneen este QR, para que se refleje en su historial de asistencia.</p>")
    contenidos.append("<p><strong>ESTE MENSAJE ES ELABORADO POR UN PROGRAMA. FAVOR DE NO RESPONDER.</strong></p>")
    content = Content("text/html", "\n".join(contenidos))

    # Validar remitente
    from_email = None
    if SENDGRID_FROM_EMAIL != "":
        from_email = Email(SENDGRID_FROM_EMAIL)
    else:
        esta_completo_para_enviar_mensaje = False

    # Destinatario
    to_email = To(cit_cita.cit_cliente.email)

    # Asunto
    subject = "Cita Agendada - PJECZ"

    # Validar SendGrid
    sendgrid_client = None
    if SENDGRID_API_KEY != "":
        sendgrid_client = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
    else:
        esta_completo_para_enviar_mensaje = False

    # Enviar mensaje
    if esta_completo_para_enviar_mensaje:
        mail = Mail(from_email, to_email, subject, content)
        sendgrid_client.client.mail.send.post(request_body=mail.get())
    else:
        mensaje_error = f"Se omite el envío a {cit_cita.cit_cliente.email} por que faltan elementos"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error

    # Terminar tarea
    set_task_progress(100)
    if va_a_incluir_qr:
        mensaje_final = f"Se ha enviado un mensaje con QR a {cit_cita.cit_cliente.email} de la cita {cit_cita.id}, URL: {asistencia_url}"
    else:
        mensaje_final = f"Se ha enviado un mensaje a {cit_cita.cit_cliente.email} de la cita {cit_cita.id}"
    bitacora.info(mensaje_final)
    return mensaje_final
