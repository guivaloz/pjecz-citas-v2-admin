"""
Boletines

- consultar: Consultar boletines
- enviar: Enviar mensajes con boletines
"""
import click

from citas_admin.blueprints.boletines.models import Boletin
from citas_admin.blueprints.cit_clientes.models import CitCliente

from citas_admin.app import create_app
from citas_admin.extensions import db

app = create_app()
db.app = app


@click.group()
@click.pass_context
def cli(ctx):
    """Boletines"""


@click.command()
@click.option("--boletin_id", default=None, help="ID del boletin", type=int)
@click.option("--cit_cliente_id", default=None, help="ID del cliente", type=int)
@click.option("--email", default=None, help="email para probar", type=str)
@click.pass_context
def enviar(ctx, boletin_id=None, cit_cliente_id=None, email=None):
    """Enviar boletines"""
    click.echo("Enviar boletines")

    # Si no viene el boletin_id
    if boletin_id is None:
        click.echo("ERROR: Aun no puedo consultar los boletines con estado PROGRAMADO, necesito boletin_id")
        ctx.exit(1)

    # Validar boletin
    boletin = Boletin.query.get(boletin_id)
    if boletin is None:
        click.echo(f"ERROR: El ID del boletin '{boletin_id}' NO existe")
        ctx.exit(1)
    if boletin.estatus != "A":
        click.echo(f"ERROR: El ID {boletin.id} NO tiene estatus ACTIVO")
        ctx.exit(1)

    # Agregar tarea en el fondo para enviar boletines
    app.task_queue.enqueue(
        "citas_admin.blueprints.boletines.tasks.enviar",
        boletin_id=boletin_id,
        cit_cliente_id=cit_cliente_id,
        email=email,
    )

    # Mostrar mensaje de termino
    mensaje = "Se ha agregado una tarea en el fondo"
    if email is not None:
        mensaje += f" para enviar el boletin {boletin_id} al email {email}"
    elif cit_cliente_id is None:
        mensaje += f" para enviar el boletin {boletin_id} a todos los clientes activos"
    else:
        mensaje += f" para guardar el boletin {boletin_id} en un archivo"
    click.echo(mensaje)
    ctx.exit(0)


cli.add_command(enviar)
