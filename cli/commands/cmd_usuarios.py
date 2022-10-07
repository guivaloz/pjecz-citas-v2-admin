"""
Usuarios

- nueva_api_key: Nueva API Key
- nueva_contrasena: Nueva contraseña
"""
from datetime import datetime, timedelta

import click

from lib.pwgen import generar_api_key

from citas_admin.app import create_app
from citas_admin.extensions import db

from citas_admin.blueprints.usuarios.models import Usuario
from citas_admin.extensions import pwd_context

app = create_app()
db.app = app


@click.group()
def cli():
    """Usuarios"""


@click.command()
@click.argument("email", type=str)
@click.option("--dias", default=90, help="Cantidad de días para expirar la API Key")
def nueva_api_key(email, dias):
    """Nueva API key"""
    usuario = Usuario.find_by_identity(email)
    if usuario is None:
        click.echo(f"No existe el e-mail {email} en usuarios")
        return
    usuario.api_key = generar_api_key(usuario.id, usuario.email)
    usuario.api_key_expiracion = datetime.now() + timedelta(days=dias)
    usuario.save()
    click.echo(f"Nueva api_key para el usuario {usuario.id} es {usuario.api_key} que expira el {usuario.api_key_expiracion.strftime('%Y-%m-%d')}")


@click.command()
@click.argument("email", type=str)
def nueva_contrasena(email):
    """Nueva contraseña"""
    usuario = Usuario.find_by_identity(email)
    if usuario is None:
        click.echo(f"No existe el e-mail {email} en usuarios")
        return
    contrasena_1 = input("Contraseña: ")
    contrasena_2 = input("De nuevo la misma contraseña: ")
    if contrasena_1 != contrasena_2:
        click.echo("No son iguales las contraseñas. Por favor intente de nuevo.")
        return
    usuario.contrasena = pwd_context.hash(contrasena_1.strip())
    usuario.save()
    click.echo(f"Nueva contraseña para el usuario {usuario.id}")


cli.add_command(nueva_api_key)
cli.add_command(nueva_contrasena)
