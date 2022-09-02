"""
Enc Sistemas

- consultar: Ver listado de la encuesta filtrado por estado
- enviar: Enviar mensaje con URL para contestar la encuesta
- crear: Crea una nueva encuesta
"""
import os
import click
from dotenv import load_dotenv
from datetime import datetime
from tabulate import tabulate

from citas_admin.app import create_app
from citas_admin.extensions import db

from citas_admin.blueprints.enc_sistemas.models import EncSistema
from citas_admin.blueprints.cit_clientes.models import CitCliente

app = create_app()
db.app = app

load_dotenv()  # Take environment variables from .env

POLL_SYSTEM_URL = os.getenv("POLL_SYSTEM_URL", "")
SAFE_LIMIT = 30


@click.group()
def cli():
    """Enc Sistemas"""


@click.command()
@click.option("--id", default=None, help="El id de una encuesta en particular.", type=int)
@click.option("--cit_cliente_id", default=None, help="El id del cliente que desea consultar.", type=int)
@click.option("--estado", show_choices=True, type=click.Choice(["pendiente", "cancelado", "contestado"], case_sensitive=False))
@click.option("--limit", default=None, help="límite de registros a mostrar.", type=int)
def consultar(id, cit_cliente_id, estado, limit):
    """Consultar encuestas de sistemas"""
    click.echo("Listado de encuestas de sistemas")

    # Si solo viene el estado, mostrar una tabla
    if estado is not None and id is None and cit_cliente_id is None:
        encuestas = EncSistema.query.filter_by(estatus="A").filter_by(estado=estado.upper())
        # Se establece el limite de registros a mostrar
        limite = limit if limit is not None and limit > 0 else SAFE_LIMIT
        encuestas = encuestas.order_by(EncSistema.id.desc()).limit(limite).all()
        if len(encuestas) == 0:
            click.echo("No hay registros")
            return 1
        datos = []
        for encuesta in encuestas:
            datos.append(
                [
                    encuesta.id,
                    encuesta.cit_cliente.id,
                    encuesta.cit_cliente.nombre,
                ]
            )
        click.echo(tabulate(datos, headers=["ID", "ID del Cliente", "Nombre del Cliente"]))
        click.echo("------------------------------")
        click.echo(f"Cantidad de encuestas: {len(datos)}")

    # Si viene el ID, se muestran los datos de esa encuesta
    if id is not None and id > 0:
        encuesta = EncSistema.query.get(id)
        click.echo(f"Enviada: {encuesta.creado.strftime('%Y/%m/%d - %H:%M %p')}")
        click.echo(f"Contestada: {encuesta.modificado.strftime('%Y/%m/%d - %H:%M %p')}")
        click.echo(f"Cliente: {encuesta.cit_cliente_id} - {encuesta.cit_cliente.nombre}")
        click.echo(f"Respuesta_01: {encuesta.respuesta_01} - {_respuesta_int_to_string(encuesta.respuesta_01)}")
        click.echo(f"Respuesta_02: {encuesta.respuesta_02}")
        click.echo(f"Respuesta_03: {encuesta.respuesta_03}")
        click.echo(f"Estado: {encuesta.estado}")
        return 1

    # Imprime todas las respuestas a encuestas que a hecho el cliente indicado
    if cit_cliente_id is not None and cit_cliente_id > 0:
        cliente = CitCliente.query.get(cit_cliente_id)
        if cliente is None:
            click.echo(click.style(f"El cliente con el id '{cit_cliente_id}' no existe.", fg="red"))
            return 0
        encuestas = EncSistema.query.filter_by(cit_cliente_id=cit_cliente_id).filter_by(estatus="A")
        if estado is not None:
            encuestas = encuestas.filter_by(estado=estado.upper())
        encuestas = encuestas.order_by(EncSistema.id.desc()).all()
        click.echo(f"Cliente: {cit_cliente_id} - {cliente.nombre}")
        for encuesta in encuestas:
            click.echo("------------------------------")
            click.echo(f"id: {encuesta.id}")
            click.echo(f"Enviada: {encuesta.creado.strftime('%Y/%m/%d - %H:%M %p')}")
            click.echo(f"Contestada: {encuesta.modificado.strftime('%Y/%m/%d - %H:%M %p')}")
            click.echo(f"Respuesta_01: {encuesta.respuesta_01} - {_respuesta_int_to_string(encuesta.respuesta_01)}")
            click.echo(f"Respuesta_02: {encuesta.respuesta_02}")
            click.echo(f"Respuesta_03: {encuesta.respuesta_03}")
            click.echo(f"Estado: {encuesta.estado}")
        click.echo("------------------------------")
        click.echo(f"Cantidad de respuestas: {len(encuestas)}")
        return 1

    # Regresa 0 en caso de no tener ningún parámetro
    return 0


def _respuesta_int_to_string(respuesta: int):
    """Convierte el valor numérico de la respuesta_01 a un texto descriptivo"""
    if respuesta == 1:
        return "Muy Difícil"
    elif respuesta == 2:
        return "Difícil"
    elif respuesta == 3:
        return "Neutral"
    elif respuesta == 4:
        return "Fácil"
    elif respuesta == 5:
        return "Muy Fácil"
    elif respuesta is None:
        return ""
    else:
        return "ERROR: RESPUESTA DESCONOCIDA"


@click.command()
@click.argument("id", type=int)
def enviar(id):
    """Enviar mensaje por correo electrónico con el URL para abrir la encuesta"""
    click.echo(f"Por enviar mensaje al cliente con ID {id}")

    # Consultar la encuesta
    encuesta = EncSistema.query.get(id)
    if encuesta is None:
        click.echo(click.style(f"La encuesta con el id '{id}' no existe.", fg="red"))
        return 0

    # Validar que este defino POLL_SYSTEM_URL
    if POLL_SYSTEM_URL == "":
        click.echo(click.style("Falta la variable de entorno POLL_SYSTEM_URL", fg="red"))
        return 0

    # Agregar tarea en el fondo para enviar el mensaje
    # app.task_queue.enqueue(
    #     "citas_admin.blueprints.enc_sistemas.tasks.enviar",
    #     cit_cliente_recuperacion_id=cit_cliente_recuperacion.id,
    # )

    # Mostrar mensaje de termino
    url = f"{POLL_SYSTEM_URL}?hashid={encuesta.encode_id()}"
    click.echo(f"Se ha enviado un mensaje a {encuesta.cit_cliente.email} con el URL {url}")


@click.command()
@click.option("--cit_cliente_id", help="El id del cliente.", type=int)
def crear(cit_cliente_id):
    """Crear una nueva encuesta de sistemas"""
    click.echo(f"Crear una nueva encuesta de sistemas para el cliente con ID {cit_cliente_id}")

    # Validar el cliente
    cliente = CitCliente.query.get(cit_cliente_id)
    if cliente is None:
        click.echo(click.style(f"El cliente con el id '{cit_cliente_id}' no existe.", fg="red"))
        return 0

    # Agregar la encuesta
    encuesta = EncSistema(
        cit_cliente=cliente,
        estado="PENDIENTE",
    )
    encuesta.save()

    # Mostrar el mensaje de termino
    click.echo(f"Se ha creado la encuesta de sistemas con el id: {encuesta.id}")


# Añadir comandos al comando cli - citas enc_sistemas consultar | enviar | crear
cli.add_command(consultar)
cli.add_command(enviar)
cli.add_command(crear)
