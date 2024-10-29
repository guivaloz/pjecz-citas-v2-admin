"""
CLI Cit Clientes

- nueva-contrasena: Nueva contraseña
"""

import sys

import click
from dotenv import load_dotenv

from citas_admin.app import create_app
from citas_admin.blueprints.cit_clientes.models import CitCliente
from citas_admin.extensions import database, pwd_context

load_dotenv()  # Take environment variables from .env

app = create_app()
app.app_context().push()
database.app = app


@click.group()
def cli():
    """Cit Clientes"""


@click.command()
@click.argument("cit_cliente_email", type=str)
def nueva_contrasena(cit_cliente_email):
    """Nueva contraseña"""
    click.echo("Nueva contraseña")

    # Consultar cliente
    cit_cliente = CitCliente.query.filter_by(email=cit_cliente_email).first()

    # Si no existe el cliente
    if cit_cliente is None:
        click.echo(f"No se encontró el cliente con el email {cit_cliente_email}")
        sys.exit(1)

    # Si el estatus del cliente es diferente a "A"
    if cit_cliente.estatus != "A":
        click.echo("El cliente no tiene un estatus 'A'")
        sys.exit(1)

    # Preguntar la nueva contraseña dos veces
    contrasena_1 = input("Contraseña: ").strip()
    contrasena_2 = input("De nuevo la misma contraseña: ").strip()

    # Validar que las contraseñas coincidan
    if contrasena_1 != contrasena_2:
        click.echo("No son iguales las contraseñas. Por favor intente de nuevo.")
        return

    # Actualizar la contraseña
    cit_cliente.contrasena_md5 = ""
    cit_cliente.contrasena_sha256 = pwd_context.hash(contrasena_1)
    cit_cliente.save()

    # Mensaje final
    click.echo(f"Se ha actualizado la contraseña del cliente {cit_cliente.email}")


cli.add_command(nueva_contrasena)
