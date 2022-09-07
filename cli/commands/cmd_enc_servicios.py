"""
Enc Servicios

- consultar: Ver listado de la encuesta filtrado por estado
- enviar: Enviar mensaje con URL para contestar la encuesta
- crear: Crea una nueva encuesta
"""
import os
import click
from dotenv import load_dotenv
from tabulate import tabulate

from citas_admin.app import create_app
from citas_admin.extensions import db

from citas_admin.blueprints.enc_servicios.models import EncServicio
from citas_admin.blueprints.cit_clientes.models import CitCliente
from citas_admin.blueprints.oficinas.models import Oficina
from citas_admin.blueprints.cit_citas.models import CitCita

app = create_app()
db.app = app

load_dotenv()  # Take environment variables from .env

POLL_SERVICE_URL = os.getenv("POLL_SERVICE_URL", "")
SAFE_LIMIT = 30


@click.group()
@click.pass_context
def cli(ctx):
    """Enc Servicios"""

    # Validar que este defino POLL_SYSTEM_URL
    if POLL_SERVICE_URL == "":
        click.echo(click.style("Falta la variable de entorno POLL_SERVICE_URL", fg="red"))
        ctx.exit(1)


@click.command()
@click.option("--id", default=None, help="El id de una encuesta en particular.", type=int)
@click.option("--cit_cliente_id", default=None, help="El id del cliente que desea consultar.", type=int)
@click.option("--oficina_id", default=None, help="El id de la oficina que desea consultar.", type=int)
@click.option("--estado", show_choices=True, type=click.Choice(["pendiente", "cancelado", "contestado"], case_sensitive=False))
@click.option("--limit", default=None, help="límite de registros a mostrar.", type=int)
@click.pass_context
def consultar(ctx, id, cit_cliente_id, oficina_id, estado, limit):
    """Consultar encuestas de servicios"""
    click.echo("Consultar encuestas de servicios")

    # Si viene el ID, se muestran los datos de esa encuesta
    if id is not None and id > 0:
        encuesta = EncServicio.query.get(id)
        if encuesta is None:
            click.echo(click.style(f"No existe la encuesta de servicios con ID {id}", fg="red"))
            ctx.exit(1)
        click.echo(f"Creada: {encuesta.creado.strftime('%Y/%m/%d - %H:%M %p')}")
        click.echo(f"Contestada: {encuesta.modificado.strftime('%Y/%m/%d - %H:%M %p')}")
        click.echo(f"Cliente: {encuesta.cit_cliente_id} - {encuesta.cit_cliente.nombre}")
        click.echo(f"Oficina: {encuesta.oficina.id} - {encuesta.oficina.clave} : {encuesta.oficina.descripcion_corta}")
        click.echo(f"Respuesta_01: {encuesta.respuesta_01} - {_respuesta_int_to_string(encuesta.respuesta_01)}")
        click.echo(f"Respuesta_02: {encuesta.respuesta_02} - {_respuesta_int_to_string(encuesta.respuesta_02)}")
        click.echo(f"Respuesta_03: {encuesta.respuesta_03} - {_respuesta_int_to_string(encuesta.respuesta_03)}")
        click.echo(f"Respuesta_04: {encuesta.respuesta_04}")
        click.echo(f"Estado: {encuesta.estado}")
        url = f"{POLL_SERVICE_URL}?hashid={encuesta.encode_id()}"
        click.echo(f"URL: {url}")
        ctx.exit(0)

    # Si viene el cit_cliente_id, se muestran TODOS los datos de sus encuestas
    if cit_cliente_id is not None and cit_cliente_id > 0:
        cliente = CitCliente.query.get(cit_cliente_id)
        if cliente is None:
            click.echo(click.style(f"El cliente con el id '{cit_cliente_id}' no existe.", fg="red"))
            ctx.exit(1)
        encuestas = EncServicio.query.filter_by(cit_cliente_id=cit_cliente_id).filter_by(estatus="A")
        if estado is not None:
            encuestas = encuestas.filter_by(estado=estado.upper())
        # Se establece el limite de registros a mostrar
        limite = limit if limit is not None and limit > 0 else SAFE_LIMIT
        encuestas = encuestas.order_by(EncServicio.id.desc()).limit(limite).all()
        click.echo(f"Cliente: {cit_cliente_id} - {cliente.nombre}")
        for encuesta in encuestas:
            click.echo("------------------------------")
            click.echo(f"id: {encuesta.id}")
            click.echo(f"Creada: {encuesta.creado.strftime('%Y/%m/%d - %H:%M %p')}")
            click.echo(f"Contestada: {encuesta.modificado.strftime('%Y/%m/%d - %H:%M %p')}")
            click.echo(f"Oficina: {encuesta.oficina.id} - {encuesta.oficina.clave} : {encuesta.oficina.descripcion_corta}")
            click.echo(f"Respuesta_01: {encuesta.respuesta_01} - {_respuesta_int_to_string(encuesta.respuesta_01)}")
            click.echo(f"Respuesta_02: {encuesta.respuesta_02} - {_respuesta_int_to_string(encuesta.respuesta_02)}")
            click.echo(f"Respuesta_03: {encuesta.respuesta_03} - {_respuesta_int_to_string(encuesta.respuesta_03)}")
            click.echo(f"Respuesta_04: {encuesta.respuesta_04}")
            click.echo(f"Estado: {encuesta.estado}")
        click.echo("------------------------------")
        click.echo(f"Cantidad de respuestas: {len(encuestas)}")
        ctx.exit(1)

    # Si viene el oficina_id, se muestran sus encuestas
    if oficina_id is not None and oficina_id > 0:
        # Validar Oficina
        oficina = Oficina.query.get(oficina_id)
        if oficina is None:
            click.echo(click.style(f"La Oficina con el ID '{oficina_id}' no existe.", fg="red"))
            return 0
        encuestas = EncServicio.query.filter_by(oficina_id=oficina_id).filter_by(estatus="A")
        if estado is not None:
            encuestas = encuestas.filter_by(estado=estado.upper())
        # Se establece el limite de registros a mostrar
        limite = limit if limit is not None and limit > 0 else SAFE_LIMIT
        # Se consultan las encuestas
        encuestas = encuestas.order_by(EncServicio.id.desc()).limit(limite).all()
        click.echo(f"Oficina: {oficina.id} - {oficina.clave} : {oficina.descripcion_corta}")
        if len(encuestas) == 0:
            click.echo("No hay registros")
            ctx.exit(1)
        datos = []
        for encuesta in encuestas:
            datos.append(
                [
                    encuesta.id,
                    encuesta.creado.strftime("%Y/%m/%d %H:%M"),
                    encuesta.respuesta_01,
                    encuesta.respuesta_03,
                    encuesta.respuesta_02,
                    encuesta.cit_cliente.id,
                    encuesta.cit_cliente.nombre,
                    encuesta.estado,
                ]
            )
        click.echo(tabulate(datos, headers=["ID", "Creado", "R01", "R02", "R03", "ID Cli", "Nombre del Cliente", "Estado"]))
        click.echo("------------------------------")
        click.echo(f"Cantidad de encuestas: {len(datos)}")
        ctx.exit(0)

    # De lo contrario, mostrar la tabla
    encuestas = EncServicio.query.filter_by(estatus="A")
    if estado is not None:
        encuestas = EncServicio.query.filter_by(estatus="A").filter_by(estado=estado.upper())
    limite = limit if limit is not None and limit > 0 else SAFE_LIMIT
    encuestas = encuestas.order_by(EncServicio.id.desc()).limit(limite).all()
    if len(encuestas) == 0:
        click.echo("No hay registros")
        ctx.exit(1)
    datos = []
    for encuesta in encuestas:
        datos.append(
            [
                encuesta.id,
                encuesta.creado.strftime("%Y/%m/%d %H:%M"),
                encuesta.oficina.id,
                encuesta.oficina.clave + " : " + encuesta.oficina.descripcion_corta,
                encuesta.cit_cliente.id,
                encuesta.cit_cliente.nombre,
            ]
        )
    click.echo(tabulate(datos, headers=["ID", "Creado", "ID Ofi", "Oficina Nombre (clave : nombre corto)", "ID Cli", "Nombre del Cliente"]))
    click.echo("------------------------------")
    click.echo(f"Cantidad de encuestas: {len(datos)}")
    ctx.exit(0)


def _respuesta_int_to_string(respuesta: int):
    """Convierte el valor numérico de la respuesta_01 a un texto descriptivo"""
    if respuesta == 1:
        return "Muy Insatisfecho"
    elif respuesta == 2:
        return "Insatisfecho"
    elif respuesta == 3:
        return "Neutral"
    elif respuesta == 4:
        return "Satisfecho"
    elif respuesta == 5:
        return "Muy Satisfecho"
    elif respuesta is None:
        return ""
    else:
        return "ERROR: RESPUESTA DESCONOCIDA"


@click.command()
@click.argument("id", type=int)
@click.pass_context
def enviar(ctx, id):
    """Enviar mensaje por correo electrónico con el URL para abrir la encuesta"""
    click.echo(f"Por enviar mensaje al cliente con ID {id}")

    # Consultar la encuesta
    encuesta = EncServicio.query.get(id)
    if encuesta is None:
        click.echo(click.style(f"La encuesta con el id '{id}' no existe.", fg="red"))
        ctx.exit(1)

    # Agregar tarea en el fondo para enviar el mensaje
    app.task_queue.enqueue(
        "citas_admin.blueprints.enc_servicios.tasks.enviar",
        enc_servicios_id=encuesta.id,
    )

    # Mostrar mensaje de termino
    url = f"{POLL_SERVICE_URL}?hashid={encuesta.encode_id()}"
    click.echo(f"Se ha enviado un mensaje a {encuesta.cit_cliente.email} con el URL {url}")
    ctx.exit(0)


@click.command()
@click.argument("cit_cita_id", type=int)
@click.pass_context
def crear(ctx, cit_cita_id):
    """Crear una nueva encuesta de sistemas"""
    click.echo(f"Crear una nueva encuesta de servios para la cita con ID {cit_cita_id}")

    # Validar la cita
    cita = CitCita.query.get(cit_cita_id)
    if cita is None:
        click.echo(click.style(f"La Cita con el ID '{cit_cita_id}' no existe.", fg="red"))
        ctx.exit(1)

    # Agregar la encuesta
    encuesta = EncServicio(
        cit_cliente=cita.cit_cliente,
        oficina=cita.oficina,
        estado="PENDIENTE",
    )
    encuesta.save()

    # Mostrar el mensaje de termino
    url = f"{POLL_SERVICE_URL}?hashid={encuesta.encode_id()}"
    click.echo(f"Se ha creado la encuesta con ID {encuesta.id} y URL {url}")
    ctx.exit(0)


# Añadir comandos al comando cli - citas enc_servicios consultar | enviar | crear
cli.add_command(consultar)
cli.add_command(enviar)
cli.add_command(crear)
