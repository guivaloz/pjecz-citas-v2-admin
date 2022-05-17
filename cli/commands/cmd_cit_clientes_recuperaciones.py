"""
Cit Clientes Recuperaciones

- ver: Ver recuperaciones
- enviar: Enviar mensaje con URL para definir contrasena
- eliminar: Eliminar recuperaciones
"""
import os
import click
from dotenv import load_dotenv
from tabulate import tabulate

from citas_admin.app import create_app
from citas_admin.extensions import db

from citas_admin.blueprints.cit_clientes_recuperaciones.models import CitClienteRecuperacion

app = create_app()
db.app = app

load_dotenv()  # Take environment variables from .env

RECOVER_ACCOUNT_CONFIRM_URL = os.getenv("RECOVER_ACCOUNT_CONFIRM_URL", "https://localhost:3000/recover_account_confirm")


@click.group()
def cli():
    """Cit Clientes Recuperaciones"""


@click.command()
@click.option("--id", default=None, help="Number of greetings.")
def ver(id):
    """Ver recuperaciones"""
    if id is None:
        cit_clientes_recuperaciones = CitClienteRecuperacion.query.filter_by(estatus="A").filter_by(ya_recuperado=False).order_by(CitClienteRecuperacion.id).all()
        if len(cit_clientes_recuperaciones) == 0:
            click.echo("No hay registros")
            return
        datos = []
        for cit_cliente_recuperacion in cit_clientes_recuperaciones:
            datos.append(
                [
                    cit_cliente_recuperacion.id,
                    cit_cliente_recuperacion.cit_cliente.nombres,
                    cit_cliente_recuperacion.cit_cliente.apellido_primero,
                    cit_cliente_recuperacion.cit_cliente.apellido_segundo,
                    cit_cliente_recuperacion.cit_cliente.curp,
                    cit_cliente_recuperacion.cit_cliente.email,
                    cit_cliente_recuperacion.cit_cliente.mensajes_cantidad,
                ]
            )
        click.echo(tabulate(datos, headers=["id", "nombres", "apellido_primero", "apellido_segundo", "curp", "email", "cantidad"]))
    else:
        cit_cliente_recuperacion = CitClienteRecuperacion.query.get(id)
        click.echo(f"Nombres: {cit_cliente_recuperacion.cit_cliente.nombres}")
        click.echo(f"Apellido primero: {cit_cliente_recuperacion.cit_cliente.apellido_primero}")
        click.echo(f"Apellido segundo: {cit_cliente_recuperacion.cit_cliente.apellido_segundo}")
        click.echo(f"CURP: {cit_cliente_recuperacion.cit_cliente.curp}")
        click.echo(f"e-mail: {cit_cliente_recuperacion.cit_cliente.email}")
        click.echo(f"URL para confirmar: {RECOVER_ACCOUNT_CONFIRM_URL}?confirm={cit_cliente_recuperacion.cadena_validar}")
        click.echo(f"Cantidad de mensajes: {cit_cliente_recuperacion.mensajes_cantidad}")


@click.command()
@click.argument("id", type=int)
def enviar(id):
    """Enviar mensaje con URL para definir contrasena"""
    cit_cliente_recuperacion = CitClienteRecuperacion.query.get(id)
    click.echo(f"Por enviar un mensaje a: {cit_cliente_recuperacion.email}")
    click.echo(f"Con este URL para confirmar: {RECOVER_ACCOUNT_CONFIRM_URL}?confirm={cit_cliente_recuperacion.cadena_validar}")
    click.echo(f"El contador de mensajes sera: {cit_cliente_recuperacion.mensajes_cantidad}")
    app.task_queue.enqueue(
        "citas_admin.blueprints.cit_clientes_registros.tasks.enviar",
        cit_cliente_recuperacion_id=cit_cliente_recuperacion.id,
    )
    click.echo("Enviar se está ejecutando en el fondo.")


@click.command()
def eliminar():
    """Eliminar recuperaciones"""
    cit_clientes_recuperaciones = CitClienteRecuperacion.query.filter_by(estatus="A").filter_by(ya_recuperado=False).all()
    if len(cit_clientes_recuperaciones) == 0:
        click.echo("No hay registros")
        return
    contador = 0
    for cit_cliente_recuperacion in cit_clientes_recuperaciones:
        cit_cliente_recuperacion.estatus = "B"
        cit_cliente_recuperacion.save()
        contador += 1
    click.echo(f"Se eliminaron {contador} registros")


cli.add_command(ver)
cli.add_command(enviar)
cli.add_command(eliminar)
