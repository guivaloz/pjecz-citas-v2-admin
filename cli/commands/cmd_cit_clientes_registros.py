"""
Cit Clientes Registros

- consultar: Ver registros
- eliminar: Eliminar registros
- enviar: Enviar mensaje con URL de confirmacion
- reenviar: Reenviar mensajes a quienes no han terminado su registro
"""

import os

import click
from dotenv import load_dotenv
from tabulate import tabulate

from citas_admin.app import create_app
from citas_admin.extensions import database
from citas_admin.blueprints.cit_clientes_registros.models import CitClienteRegistro

app = create_app()
app.app_context().push()
database.app = app

load_dotenv()  # Take environment variables from .env

NEW_ACCOUNT_CONFIRM_URL = os.getenv("NEW_ACCOUNT_CONFIRM_URL", "")


@click.group()
def cli():
    """Cit Clientes Registros"""


@click.command()
@click.option("--id", default=None, help="Number of greetings.")
def consultar(id):
    """Consultar registros"""
    if id is None:
        cit_clientes_registros = (
            CitClienteRegistro.query.filter_by(estatus="A").filter_by(ya_registrado=False).order_by(CitClienteRegistro.id).all()
        )
        if len(cit_clientes_registros) == 0:
            click.echo("No hay registros")
            return
        datos = []
        for cit_cliente_registro in cit_clientes_registros:
            datos.append(
                [
                    cit_cliente_registro.id,
                    cit_cliente_registro.nombres,
                    cit_cliente_registro.apellido_primero,
                    cit_cliente_registro.apellido_segundo,
                    cit_cliente_registro.curp,
                    cit_cliente_registro.email,
                    cit_cliente_registro.mensajes_cantidad,
                ]
            )
        click.echo(
            tabulate(datos, headers=["id", "nombres", "apellido_primero", "apellido_segundo", "curp", "email", "cantidad"])
        )
    else:
        cit_cliente_registro = CitClienteRegistro.query.get(id)
        url = f"{NEW_ACCOUNT_CONFIRM_URL}?hashid={cit_cliente_registro.encode_id()}&cadena_validar={cit_cliente_registro.cadena_validar}"
        click.echo(f"Nombres: {cit_cliente_registro.nombres}")
        click.echo(f"Apellido primero: {cit_cliente_registro.apellido_primero}")
        click.echo(f"Apellido segundo: {cit_cliente_registro.apellido_segundo}")
        click.echo(f"CURP: {cit_cliente_registro.curp}")
        click.echo(f"e-mail: {cit_cliente_registro.email}")
        click.echo(f"URL para confirmar: {url}")
        click.echo(f"Cantidad de mensajes: {cit_cliente_registro.mensajes_cantidad}")


@click.command()
def eliminar():
    """Eliminar registros"""
    cit_clientes_registros = CitClienteRegistro.query.filter_by(estatus="A").filter_by(ya_registrado=False).all()
    if len(cit_clientes_registros) == 0:
        click.echo("No hay registros")
        return
    contador = 0
    for cit_cliente_registro in cit_clientes_registros:
        cit_cliente_registro.estatus = "B"
        cit_cliente_registro.save()
        contador += 1
    click.echo(f"Se eliminaron {contador} registros")


@click.command()
@click.argument("id", type=int)
def enviar(id):
    """Enviar mensaje con URL de confirmacion"""
    cit_cliente_registro = CitClienteRegistro.query.get(id)
    if cit_cliente_registro is None:
        click.echo(f"No existe el registro {id}")
        return
    click.echo(f"Por enviar un mensaje a: {cit_cliente_registro.email}")
    click.echo(f"Con este URL para confirmar: {NEW_ACCOUNT_CONFIRM_URL}?cadena_validar={cit_cliente_registro.cadena_validar}")
    click.echo(f"El contador de mensajes sera: {cit_cliente_registro.mensajes_cantidad}")
    app.task_queue.enqueue(
        "citas_admin.blueprints.cit_clientes_registros.tasks.enviar",
        cit_cliente_registro_id=cit_cliente_registro.id,
    )
    click.echo("Enviar se está ejecutando en el fondo.")


@click.command()
def reenviar():
    """Reenviar mensajes a quienes no han terminado su registro"""
    app.task_queue.enqueue(
        "citas_admin.blueprints.cit_clientes_registros.tasks.reenviar",
    )
    click.echo("Reenviar se está ejecutando en el fondo.")


cli.add_command(consultar)
cli.add_command(eliminar)
cli.add_command(enviar)
cli.add_command(reenviar)
