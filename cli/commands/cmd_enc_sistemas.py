"""
Enc Sistemas

- consultar: Consultar encuestas de sistemas
- enviar: Enviar mensaje con URL para contestar la encuesta
- crear: Crea una nueva encuesta
- crear_enviar: Crear y enviar mensajes para contestar las encuestas
- cancelar: Cancelar encuestas pendientes creadas hace 7 dias
"""
from datetime import datetime, timedelta
import os

import click
from dotenv import load_dotenv
from pytz import timezone
from tabulate import tabulate

from citas_admin.app import create_app
from citas_admin.extensions import db

from citas_admin.blueprints.cit_citas.models import CitCita
from citas_admin.blueprints.cit_clientes.models import CitCliente
from citas_admin.blueprints.enc_sistemas.models import EncSistema

app = create_app()
db.app = app

load_dotenv()  # Take environment variables from .env

HUSO_HORARIO = "America/Mexico_City"
POLL_SYSTEM_URL = os.getenv("POLL_SYSTEM_URL", "")
SAFE_LIMIT = 30


@click.group()
@click.pass_context
def cli(ctx):
    """Enc Sistemas"""

    # Validar que este defino POLL_SYSTEM_URL
    if POLL_SYSTEM_URL == "":
        click.echo(click.style("Falta la variable de entorno POLL_SYSTEM_URL", fg="red"))
        ctx.exit(1)


@click.command()
@click.option("--id", default=None, help="El id de una encuesta en particular.", type=int)
@click.option("--cit_cliente_id", default=None, help="El id del cliente que desea consultar.", type=int)
@click.option("--estado", show_choices=True, type=click.Choice(["pendiente", "cancelado", "contestado"], case_sensitive=False))
@click.option("--limit", default=None, help="límite de registros a mostrar.", type=int)
@click.pass_context
def consultar(ctx, id, cit_cliente_id, estado, limit):
    """Consultar encuestas de sistemas"""
    click.echo("Consultar encuestas de sistemas")

    # Si viene el ID, se muestran los datos de esa encuesta
    if id is not None and id > 0:
        encuesta = EncSistema.query.get(id)
        if encuesta is None:
            click.echo(click.style(f"No existe la encuesta de sistemas con ID {id}", fg="red"))
            ctx.exit(1)
        click.echo(f"Enviada: {encuesta.creado.strftime('%Y/%m/%d - %H:%M %p')}")
        click.echo(f"Contestada: {encuesta.modificado.strftime('%Y/%m/%d - %H:%M %p')}")
        click.echo(f"Cliente: {encuesta.cit_cliente_id} - {encuesta.cit_cliente.nombre}")
        click.echo(f"Respuesta_01: {encuesta.respuesta_01} - {_respuesta_int_to_string(encuesta.respuesta_01)}")
        click.echo(f"Respuesta_02: {encuesta.respuesta_02}")
        click.echo(f"Respuesta_03: {encuesta.respuesta_03}")
        click.echo(f"Estado: {encuesta.estado}")
        url = f"{POLL_SYSTEM_URL}?hashid={encuesta.encode_id()}"
        click.echo(f"URL: {url}")
        ctx.exit(0)

    # Si viene el cit_cliente_id, se muestran TODOS los datos de sus encuestas
    if cit_cliente_id is not None and cit_cliente_id > 0:
        cliente = CitCliente.query.get(cit_cliente_id)
        if cliente is None:
            click.echo(click.style(f"El cliente con el id '{cit_cliente_id}' no existe.", fg="red"))
            ctx.exit(1)
        encuestas = EncSistema.query.filter_by(cit_cliente_id=cit_cliente_id).filter_by(estatus="A")
        if estado is not None:
            encuestas = encuestas.filter_by(estado=estado.upper())
        limite = limit if limit is not None and limit > 0 else SAFE_LIMIT
        encuestas = encuestas.order_by(EncSistema.id.desc()).limit(limite).all()
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
            url = f"{POLL_SYSTEM_URL}?hashid={encuesta.encode_id()}"
            click.echo(f"URL: {url}")
        click.echo("------------------------------")
        click.echo(f"Cantidad de respuestas: {len(encuestas)}")
        ctx.exit(0)

    # De lo contrario, mostrar la tabla
    encuestas = EncSistema.query.filter_by(estatus="A")
    if estado is not None:
        encuestas = encuestas.filter_by(estado=estado.upper())
    limite = limit if limit is not None and limit > 0 else SAFE_LIMIT
    encuestas = encuestas.order_by(EncSistema.id.desc()).limit(limite).all()
    if len(encuestas) == 0:
        click.echo("No hay registros")
        ctx.exit(1)
    datos = []
    for encuesta in encuestas:
        datos.append(
            [
                encuesta.id,
                encuesta.creado.strftime("%Y/%m/%d - %H:%M %p"),
                encuesta.cit_cliente.id,
                encuesta.cit_cliente.nombre,
            ]
        )
    click.echo(tabulate(datos, headers=["ID", "Creado", "ID Cliente", "Nombre del Cliente"]))
    click.echo("------------------------------")
    click.echo(f"Cantidad de encuestas: {len(datos)}")
    ctx.exit(0)


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
@click.argument("cit_cliente_id", type=int)
@click.pass_context
def crear(ctx, cit_cliente_id):
    """Crear una nueva encuesta de sistemas"""
    click.echo(f"Crear una nueva encuesta de sistemas para el cliente con ID {cit_cliente_id}")

    # Validar el cliente
    cliente = CitCliente.query.get(cit_cliente_id)
    if cliente is None:
        click.echo(click.style(f"El cliente con el id '{cit_cliente_id}' no existe.", fg="red"))
        ctx.exit(1)

    # Agregar la encuesta
    encuesta = EncSistema(
        cit_cliente=cliente,
        estado="PENDIENTE",
    )
    encuesta.save()

    # Mostrar el mensaje de termino
    url = f"{POLL_SYSTEM_URL}?hashid={encuesta.encode_id()}"
    click.echo(f"Se ha creado la encuesta con ID {encuesta.id} y URL {url}")
    ctx.exit(0)


@click.command()
@click.argument("id", type=int)
@click.pass_context
def enviar(ctx, id):
    """Enviar mensaje por correo electrónico con el URL para abrir la encuesta"""
    click.echo(f"Por enviar un mensaje al cliente con ID {id}")

    # Consultar la encuesta
    encuesta = EncSistema.query.get(id)
    if encuesta is None:
        click.echo(click.style(f"La encuesta con el id '{id}' no existe.", fg="red"))
        ctx.exit(1)

    # Agregar tarea en el fondo para enviar el mensaje
    app.task_queue.enqueue(
        "citas_admin.blueprints.enc_sistemas.tasks.enviar",
        enc_sistemas_id=encuesta.id,
    )

    # Mostrar mensaje de termino
    url = f"{POLL_SYSTEM_URL}?hashid={encuesta.encode_id()}"
    click.echo(f"Se ha enviado un mensaje a {encuesta.cit_cliente.email} con el URL {url}")
    ctx.exit(0)


@click.command()
@click.option("--test", default=True, help="Modo de pruebas")
@click.pass_context
def crear_enviar(ctx, test):
    """Crear y enviar mensajes para contestar las encuestas"""
    click.echo("Crear y enviar mensajes para contestar las encuestas")

    # Google App Engine usa tiempo universal, sin esta correccion las fechas de la noche cambian al dia siguiente
    ahora_utc = datetime.now(timezone("UTC"))
    ahora_mx_coah = ahora_utc.astimezone(timezone(HUSO_HORARIO))

    # Definir inicio_desde e inicio_hasta
    # En el cron debe ejecutarse esta rutina a las 12, 14, 16 y 18 horas
    # Para que tome las citas de entre 2 y 4 horas antes
    inicio_desde = ahora_mx_coah - timedelta(hours=4)  # Por ejemplo, si son las 12 horas el inicio desde seria las 8 horas
    inicio_hasta = ahora_mx_coah - timedelta(hours=2)  # Por ejemplo, si son las 12 horas el inicio hasta seria las 10 horas

    # Consultar citas con estado ASISTIO, asistencia verdadero y en el rango inicio_desde a inicio_hasta
    citas = CitCita.query
    citas = citas.filter_by(estado="ASISTIO").filter_by(asistencia=True).filter_by(estatus="A")
    citas = citas.filter(CitCita.inicio >= inicio_desde).filter(CitCita.inicio <= inicio_hasta)

    # Si la consulta no entrega nada, terminar
    if citas.count() == 0:
        click.echo("No hay citas para crear encuestas y enviar mensajes que inviten a contestarlas")
        ctx.exit(0)

    # Bucle en cada cita
    contador = 0
    for cita in citas.all():

        # Consultar la ultima encuesta del cliente con estado CONTESTADO
        enc_sistema = EncSistema.query.filter_by(cit_cliente_id=cita.cit_cliente_id).filter_by(estado="CONTESTADO").filter_by(estatus="A").order_by(EncSistema.id.desc()).first()

        # Si el cliente tiene una encuesta CONTESTADO de hace 2 meses o menos, no crear una nueva
        if enc_sistema is not None and enc_sistema.creado >= ahora_mx_coah - timedelta(days=60):
            continue

        # Consultar las encuestas del cliente con estado PENDIENTE
        enc_sistema = EncSistema.query.filter_by(cit_cliente_id=cita.cit_cliente_id).filter_by(estado="PENDIENTE").filter_by(estatus="A")

        # Si el cliente tiene una encuesta PENDIENTE, no crear una nueva
        # Recuerde que un cliente puede tener ninguna o solo una encuesta pendiente
        if enc_sistema.count() > 0:
            continue

        # Si NO esta en modo de pruebas, crear la encuesta
        if test is False:

            # Agregar la encuesta
            enc_sistema = EncSistema(
                cit_cliente=cita.cit_cliente,
                estado="PENDIENTE",
            )
            enc_sistema.save()

            # Agregar tarea en el fondo para enviar el mensaje
            app.task_queue.enqueue(
                "citas_admin.blueprints.enc_sistemas.tasks.enviar",
                enc_sistemas_id=enc_sistema.id,
            )

        # Incrementar el contador
        contador += 1

    # Si esta en modo de pruebas
    if test:
        click.echo(f"Modo de pruebas: Se pueden crear {contador} encuestas de sistemas")
    else:
        click.echo(f"Se han creado {contador} encuestas de sistemas y agregado las tareas para enviar los mensajes")

    # Terminar
    ctx.exit(0)


@click.command()
@click.option("--test", default=True, help="Modo de pruebas")
@click.pass_context
def cancelar(ctx, test):
    """Cancelar encuestas pendientes creadas hace 7 dias o mas"""
    click.echo("Cancelar encuestas pendientes creadas hace 7 dias o mas")

    # Google App Engine usa tiempo universal, sin esta correccion las fechas de la noche cambian al dia siguiente
    ahora_utc = datetime.now(timezone("UTC"))
    ahora_mx_coah = ahora_utc.astimezone(timezone(HUSO_HORARIO))

    # Definir el creado_hasta a 7 dias antes
    creado_hasta = ahora_mx_coah - timedelta(days=7)

    # Consultar las encuestas PENDIENTE creadas antes de creado_hasta
    encuestas = EncSistema.query.filter(EncSistema.creado <= creado_hasta).filter_by(estado="PENDIENTE").filter_by(estatus="A")

    # Si la consulta no entrega nada, terminar
    if encuestas.count() == 0:
        click.echo("No hay citas para cancelar")
        ctx.exit(0)

    # Bucle en cada encuesta
    contador = 0
    for encuesta in encuestas.all():

        # Si NO esta en modo de pruebas, cancelar la encuesta
        if test is False:
            encuesta.estado = "CANCELADO"
            encuesta.estatus = "B"
            encuesta.save()

        # Incrementar el contador
        contador += 1

    # Si esta en modo de pruebas
    if test:
        click.echo(f"Modo de pruebas: Se pueden cancelar {contador} encuestas de servicios")
    else:
        click.echo(f"Se han cancelado {contador} encuestas de servicios")

    # Terminar
    ctx.exit(0)


# Añadir comandos al comando cli - citas enc_sistemas consultar | enviar | crear
cli.add_command(consultar)
cli.add_command(enviar)
cli.add_command(crear)
cli.add_command(crear_enviar)
cli.add_command(cancelar)
