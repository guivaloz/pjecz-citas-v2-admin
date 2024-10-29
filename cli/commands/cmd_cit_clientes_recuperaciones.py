"""
CLI Cit Clientes Recuperaciones

- eliminar: Eliminar recuperaciones que NO fueron realizadas
- enviar: Enviar mensaje via email con un URL en el contenido para cambiar su contraseña
- reenviar: Reenviar mensajes via email a quienes no han terminado su recuperación
"""

import os
import sys

import click
from dotenv import load_dotenv

from citas_admin.app import create_app
from citas_admin.blueprints.cit_clientes_recuperaciones.models import CitClienteRecuperacion
from citas_admin.extensions import database

load_dotenv()  # Take environment variables from .env
RECOVER_ACCOUNT_CONFIRM_URL = os.environ.get("RECOVER_ACCOUNT_CONFIRM_URL", "")

app = create_app()
app.app_context().push()
database.app = app


@click.group()
def cli():
    """Cit Clientes Recuperaciones"""


@click.command()
def eliminar():
    """Eliminar recuperaciones"""
    click.echo("Eliminar recuperaciones que NO fueron realizadas")

    # Consultar recuperaciones cuyo estatus sea "A' y con el booleano ya_recuperado en False
    cit_clientes_recuperaciones = CitClienteRecuperacion.query.filter_by(estatus="A").filter_by(ya_recuperado=False).all()

    # Si no hay recuperaciones que eliminar, mostrar mensaje y salir
    if not cit_clientes_recuperaciones:
        click.echo("No hay recuperaciones que eliminar")
        sys.exit(1)

    # Eliminar recuperaciones
    contador = 0
    click.echo("Eliminando: ", nl=False)
    for cit_cliente_recuperacion in cit_clientes_recuperaciones:
        cit_cliente_recuperacion.delete()
        contador += 1
        click.echo(".", nl=False)
    click.echo()

    # Mensaje final
    click.echo(f"Se eliminaron {contador} recuperaciones")


@click.command()
@click.argument("cit_cliente_recuperacion_id", type=int)
@click.option("--to_email", default=None, help="Otro e-mail para probar", type=str)
def enviar(cit_cliente_recuperacion_id: int, to_email: str):
    """Enviar mensaje via email con un URL en el contenido para cambiar su contraseña"""
    click.echo("Enviar mensaje via email con un URL en el contenido para cambiar su contraseña")

    # Si NO está definido RECOVER_ACCOUNT_CONFIRM_URL, mostrar mensaje y salir
    if RECOVER_ACCOUNT_CONFIRM_URL == "":
        click.echo("No está definida la variable de entorno RECOVER_ACCOUNT_CONFIRM_URL")
        sys.exit(1)

    # Consultar la recuperación
    cit_cliente_recuperacion = CitClienteRecuperacion.query.get(cit_cliente_recuperacion_id)

    # Si no existe la recuperación, mostrar mensaje y salir
    if cit_cliente_recuperacion is None:
        click.echo(f"No se encontró la recuperación con el id {cit_cliente_recuperacion_id}")
        sys.exit(1)

    # Si la recuperación tiene estatus "B", mostrar mensaje y salir
    if cit_cliente_recuperacion.estatus == "B":
        click.echo(f"No se puede enviar porque la recuperación {cit_cliente_recuperacion_id} está eliminada")
        sys.exit(1)

    # Agregar tarea en el fondo para enviar el mensaje
    app.task_queue.enqueue(
        "citas_admin.blueprints.cit_clientes_recuperaciones.tasks.enviar",
        cit_cliente_recuperacion_id=cit_cliente_recuperacion.id,
        to_email=to_email,
    )

    # Si no se especifica to_email, sabemos que la tarea usará el del cliente
    if to_email is None:
        to_email = cit_cliente_recuperacion.cit_cliente.email

    # Mensaje final
    click.echo(f"Se ha agregado una tarea para enviar un mensaje a {to_email}")


@click.command()
def reenviar():
    """Reenviar mensajes via email a quienes no han terminado su recuperación"""
    click.echo("Reenviar mensajes via email a quienes no han terminado su recuperación")

    # Agregar tarea en el fondo para enviar el mensaje
    app.task_queue.enqueue("citas_admin.blueprints.cit_clientes_recuperaciones.tasks.reenviar")

    # Mensaje final
    click.echo("Se ha agregado una tarea para reenviar los mensajes.")


cli.add_command(eliminar)
cli.add_command(enviar)
cli.add_command(reenviar)
