"""
Boletines, tareas en el fondo
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

CANTIDAD = 10
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "")


def enviar(boletin_id, cit_cliente_id=None, email=None):
    """Enviar mensajes via correo electrónico"""

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

    # Definir remitente para SendGrid
    if SENDGRID_FROM_EMAIL == "":
        mensaje_error = "La variable SENDGRID_FROM_EMAIL NO ha sido declarada"
        set_task_error(mensaje_error)
        bitacora.error(mensaje_error)
        return mensaje_error
    from_email = Email(SENDGRID_FROM_EMAIL)

    # Inicilizar listado de destinatarios
    destinatarios = []
    puntero = 0

    # Si viene un e-mail de pruebas
    if email is not None:
        destinatarios.append(
            {
                "nombre": "Fulano de Tal",
                "email": email,
            }
        )
    elif cit_cliente_id is not None:
        # Viene un ID de cliente, entonces se le enviara solo a esta persona
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
            destinatarios.append(
                {
                    "nombre": cit_cliente.nombre,
                    "email": cit_cliente.email,
                }
            )
    else:
        # Consultar los clientes activos que quieren recibir el boletin
        cit_clientes = CitCliente.query.filter_by(estatus="A").filter_by(enviar_boletin=True).filter(CitCliente.id > boletin.puntero).order_by(CitCliente.id).limit(CANTIDAD).all()
        # Si hay resultados, agregarlos al listado de destinatarios
        if cit_clientes:
            puntero = 0
            for cit_cliente in cit_clientes:
                destinatarios.append(
                    {
                        "nombre": cit_cliente.nombre,
                        "email": cit_cliente.email,
                    }
                )
                puntero = cit_cliente.id
            # Actualizar el boletin con el id del ultimo cliente consultado
            boletin.puntero = puntero
            boletin.save()
        else:
            # No hubo clientes
            mensaje_final = f"No hay clientes en el salto {boletin.puntero}"
            # Si se acabaron los clientes
            if CitCliente.query.filter(CitCliente.id > boletin.puntero + CANTIDAD).count() == 0:
                # Actualizar el boletin con el estado ENVIADO
                boletin.puntero = 0
                boletin.estado = "ENVIADO"
                boletin.save()
            # Terminar
            set_task_progress(100)
            bitacora.info(mensaje_final)
            return mensaje_final

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
        loader=FileSystemLoader("citas_admin/blueprints/boletines/templates/boletines"),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    plantilla = entorno.get_template("email.jinja2")

    # Bucle destinatarios
    for destinatario in destinatarios:

        # Elaborar contenido del mensaje
        contenidos = plantilla.render(
            mensaje_asunto=boletin.asunto,
            fecha_elaboracion=momento_str,
            destinatario_nombre=destinatario["nombre"],
            mensaje_contenido=html.render(boletin.contenido["ops"]),
        )

        # Si la variable SENDGRID_API_KEY NO ha sido declarada
        if SENDGRID_API_KEY == "":
            # Guardar mensaje en archivo
            archivo_html = f"boletin_{boletin.id}_{destinatario['email']}_{momento.strftime('%Y%m%d_%H%M%S')}.html"
            with open(archivo_html, "w", encoding="UTF-8") as puntero:
                puntero.write(contenidos)
            bitacora.info("Se guardó el mensaje en %s", archivo_html)
            continue

        # Definir destinatario para SendGrid
        to_email = To(destinatario["email"])

        # Definir contenido para SendGrid
        content = Content("text/html", contenidos)

        # Enviar mensaje via SendGrid
        mail = Mail(from_email, to_email, boletin.asunto, content)
        try:
            sendgrid_client.client.mail.send.post(request_body=mail.get())
        except Exception as error:
            mensaje_error = f"ERROR al enviar mensaje: {str(error)}"
            set_task_error(mensaje_error)
            bitacora.error(mensaje_error)
            return mensaje_error

    # Terminar tarea
    set_task_progress(100)
    mensaje_final = "Boletines enviados a " + ", ".join([destinatario["email"] for destinatario in destinatarios])
    bitacora.info(mensaje_final)
    return mensaje_final
