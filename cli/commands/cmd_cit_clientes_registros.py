"""
CLI Cit Clientes Registros

- eliminar: Eliminar los registros de clientes que YA terminaron su registro
- enviar: Enviar mensaje via email con un URL para confirmar su registro
- reenviar: Reenviar mensajes via email con un URL a quienes deben confirmar su registro
"""

import sys

import click

from citas_admin.app import create_app
from citas_admin.blueprints.cit_clientes_registros.models import CitClienteRegistro
from citas_admin.extensions import database

app = create_app()
app.app_context().push()
database.app = app


@click.group()
def cli():
    """Cit Clientes Registros"""


@click.command()
def eliminar():
    """Eliminar los registros de clientes que YA terminaron su registro"""
    click.echo("Eliminar los registros de clientes que YA terminaron su registro")

    # Consultar registros de clientes cuyo estatus sea "A' y con el booleano ya_registrado en False
    cit_clientes_registros = CitClienteRegistro.query.filter_by(estatus="A").filter_by(ya_registrado=False).all()

    # Si no hay registros que eliminar, mostrar mensaje y salir
    if not cit_clientes_registros:
        click.echo("No hay registros que eliminar")
        sys.exit(1)

    # Eliminar registros
    contador = 0
    click.echo("Eliminando: ", nl=False)
    for cit_cliente_registro in cit_clientes_registros:
        cit_cliente_registro.delete()
        contador += 1
        click.echo(".", nl=False)
    click.echo()

    # Mensaje final
    click.echo(f"Se eliminaron {contador} registros")


@click.command()
@click.argument("cit_cliente_registro_id", type=int)
@click.option("--to_email", default=None, help="Otro e-mail para probar", type=str)
def enviar(cit_cliente_registro_id: int, to_email: str):
    """Enviar mensaje via email con un URL para confirmar su registro"""
    click.echo("Enviar mensaje via email con un URL para confirmar su registro")

    # Consultar registro
    cit_cliente_registro = CitClienteRegistro.query.get(cit_cliente_registro_id)

    # Si no existe el registro
    if cit_cliente_registro is None:
        click.echo(f"No se encontró el registro con el id {cit_cliente_registro_id}")
        sys.exit(1)

    # Si el registro no tiene un estatus 'A'
    if cit_cliente_registro.estatus != "A":
        click.echo("El registro no tiene un estatus 'A'")
        sys.exit(1)

    # Si el registro ya fue registrado
    if cit_cliente_registro.ya_registrado:
        click.echo("El registro ya fue registrado")
        sys.exit(1)

    # Agregar tarea en el fondo para enviar el mensaje
    app.task_queue.enqueue(
        "citas_admin.blueprints.cit_clientes_registros.tasks.enviar",
        cit_cliente_registro_id=cit_cliente_registro_id,
        to_email=to_email,
    )

    # Si no se especifica to_email, sabemos que la tarea usará el del cliente
    if to_email is None:
        to_email = cit_cliente_registro.email

    # Mostrar mensaje de termino
    click.echo(f"Se ha agregado una tarea para enviar un mensaje a {to_email}")


@click.command()
def reenviar():
    """Reenviar mensajes via email con un URL a quienes deben confirmar su registro"""
    click.echo("Reenviar mensajes via email con un URL a quienes deben confirmar su registro")

    # Agregar tarea en el fondo para enviar el mensaje
    app.task_queue.enqueue("citas_admin.blueprints.cit_clientes_registros.tasks.reenviar")

    # Mensaje final
    click.echo("Se ha agregado una tarea para reenviar los mensajes.")


cli.add_command(eliminar)
cli.add_command(enviar)
cli.add_command(reenviar)
