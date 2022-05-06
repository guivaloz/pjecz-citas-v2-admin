"""
Usuarios

- nueva_contrasena: Cambiar contraseña de un usuario
- enviar_reporte: Enviar via correo electronico el reporte de usuarios
- sincronizar: Sincronizar usuarios con la API de RRHH Personal
"""
import click

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
def nueva_contrasena(email):
    """Cambiar contraseña de un usuario"""
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
    click.echo(f"Se ha cambiado la contraseña de {email} en usuarios")


cli.add_command(nueva_contrasena)
