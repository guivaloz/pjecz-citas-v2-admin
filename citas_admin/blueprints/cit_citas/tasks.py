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
ASISTENCIA_URL = os.getenv("HOST", "http://citas-admin.justiciadigital.gob.mx")


def enviar(cit_cita_id):
    """Enviar mensaje con datos de la cita agendada"""

    # Consultar
    cit_cita = CitCita.query.get(cit_cita_id)
    if cit_cita.estatus != "A":
        mensaje_error = f"El ID {cit_cita.id} NO tiene estatus activo"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error

    # Bandera para saber si se tienen todos los elementos necesarios
    bandera = True

    # Momento en que se elabora este mensaje
    momento = datetime.now()

    # Data para codificar en el QR
    data = ASISTENCIA_URL + "/cit_citas/asistencia/" + cit_cita.encode_id()

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
    contenidos.append("</ul>")
    contenidos.append("<small>Por favor llegue cinco minutos antes de la fecha y hora mencionados.</small>")
    contenidos.append("<h3>Código QR para asistencia de la cita</h3>")
    contenidos.append("<p>Por favor, muestre este código QR en la recepción para marcar su asistencia a la cita.</p>")
    contenidos.append(f'<img src="https://chart.googleapis.com/chart?chs=250x250&cht=qr&chl={data}" alt="[ERROR_EN_QR]">')
    contenidos.append("<p><strong>ESTE MENSAJE ES ELABORADO POR UN PROGRAMA. FAVOR DE NO RESPONDER.</strong></p>")
    content = Content("text/html", "\n".join(contenidos))

    # Remitente
    from_email = None
    if SENDGRID_FROM_EMAIL != "":
        from_email = Email(SENDGRID_FROM_EMAIL)
    else:
        bandera = False

    # Destinatario
    to_email = To(cit_cita.cit_cliente.email)

    # Asunto
    subject = "Información de la cita"

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
        bitacora.warning("Se omite el envio a %s por que faltan elementos", cit_cita.cit_cliente.email)

    # Terminar tarea
    set_task_progress(100)
    mensaje_final = f"Se ha enviado un mensaje a {cit_cita.cit_cliente.email} de la cita {cit_cita.id}, a la URL: {data}"
    bitacora.info(mensaje_final)
    return mensaje_final
