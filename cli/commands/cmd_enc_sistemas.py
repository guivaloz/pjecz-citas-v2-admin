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

RECOVER_ACCOUNT_CONFIRM_URL = os.getenv("RECOVER_ACCOUNT_CONFIRM_URL", "")


@click.group()
def cli():
    """Enc Sistemas"""


@click.command()
@click.option("--id", default=None, help="El id de una encuesta en particular.", type=int)
@click.option("--cliente_id", default=None, help="El id del cliente que desea consultar.", type=int)
@click.option("--estado", show_choices=True, type=click.Choice(["pendiente", "cancelado", "contestado"], case_sensitive=False))
def consultar(id, cliente_id, estado):
    """Listado de respuestas de la encuesta"""
    if estado is not None and id is None and cliente_id is None:
        encuestas = EncSistema.query.filter_by(estatus="A").filter_by(estado=estado.upper()).order_by(EncSistema.id).all()
        if len(encuestas) == 0:
            click.echo("No hay registros")
            return
        datos = []
        for encuesta in encuestas:
            datos.append(
                [
                    encuesta.id,
                    encuesta.cit_cliente.id,
                    encuesta.cit_cliente.nombre,
                ]
            )
        click.echo(tabulate(datos, headers=["id", "cliente_id", "nombre del cliente"]))
        click.echo("------------------------------")
        click.echo(f"Cantidad de encuestas: {len(datos)}")
    # Imprime la respuesta a la encuesta indicada por su id
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
    if cliente_id is not None and cliente_id > 0:
        cliente = CitCliente.query.get(cliente_id)
        if cliente is None:
            click.echo(click.style(f"El cliente con el id '{cliente_id}' no existe.", fg="red"))
            return 0
        encuestas = EncSistema.query.filter_by(cit_cliente_id=cliente_id).filter_by(estatus="A")
        if estado is not None:
            encuestas = encuestas.filter_by(estado=estado.upper())
        encuestas = encuestas.order_by(EncSistema.id.desc()).all()
        click.echo(f"Cliente: {cliente_id} - {cliente.nombre}")
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
    """Enviar email con URL para abrir la encuesta"""
    encuesta = EncSistema.query.get(id)
    if encuesta is None:
        click.echo(click.style(f"La encuesta con el id '{id}' no existe.", fg="red"))
        return 0
    click.echo(f"Por enviar un email a: {encuesta.cit_cliente.email}")
    click.echo(f"Con este URL: {RECOVER_ACCOUNT_CONFIRM_URL}?cadena_validar={encuesta.encode_id()}")
    # app.task_queue.enqueue(
    #     "citas_admin.blueprints.enc_sistemas.tasks.enviar",
    #     cit_cliente_recuperacion_id=cit_cliente_recuperacion.id,
    # )
    click.echo("Enviar se está ejecutando en el fondo.")


@click.command()
@click.option("--cliente_id", help="El id del cliente.", type=int)
def crear(cliente_id):
    """Crea un nuevo registro de respuesta en la encuesta del sistema"""
    # Se revisa si existe el cliente
    cliente = CitCliente.query.get(cliente_id)
    if cliente is None:
        click.echo(click.style(f"El cliente con el id '{cliente_id}' no existe.", fg="red"))
        return 0
    encuesta = EncSistema(
        cit_cliente=cliente,
        estado="PENDIENTE",
    )
    encuesta.save()
    click.echo(f"Encuesta creada exitosamente con el id: {encuesta.id}")


cli.add_command(consultar)
cli.add_command(enviar)
cli.add_command(crear)
