"""
Base de datos

- inicializar
- alimentar
- reiniciar
- respaldar
"""
import os
import click

from citas_admin.app import create_app
from citas_admin.extensions import db

from cli.commands.alimentar_autoridades import alimentar_autoridades
from cli.commands.alimentar_distritos import alimentar_distritos
from cli.commands.alimentar_domicilios import alimentar_domicilios
from cli.commands.alimentar_cit_servicios import alimentar_cit_servicios
from cli.commands.alimentar_materias import alimentar_materias
from cli.commands.alimentar_modulos import alimentar_modulos
from cli.commands.alimentar_oficinas import alimentar_oficinas
from cli.commands.alimentar_permisos import alimentar_permisos
from cli.commands.alimentar_roles import alimentar_roles
from cli.commands.alimentar_usuarios import alimentar_usuarios
from cli.commands.alimentar_usuarios_roles import alimentar_usuarios_roles

from cli.commands.respaldar_autoridades import respaldar_autoridades
from cli.commands.respaldar_distritos import respaldar_distritos
from cli.commands.respaldar_domicilios import respaldar_domicilios
from cli.commands.respaldar_cit_servicios import respaldar_cit_servicios
from cli.commands.respaldar_materias import respaldar_materias
from cli.commands.respaldar_modulos import respaldar_modulos
from cli.commands.respaldar_oficinas import respaldar_oficinas
from cli.commands.respaldar_roles_permisos import respaldar_roles_permisos
from cli.commands.respaldar_usuarios_roles import respaldar_usuarios_roles

app = create_app()
db.app = app

entorno_implementacion = os.environ.get("DEPLOYMENT_ENVIRONMENT", "develop").upper()


@click.group()
def cli():
    """Base de Datos"""


@click.command()
def inicializar():
    """Inicializar"""
    if entorno_implementacion == "PRODUCTION":
        click.echo("PROHIBIDO: No se inicializa porque este es el servidor de producción.")
        return
    db.drop_all()
    db.create_all()
    click.echo("Termina inicializar.")


@click.command()
def alimentar():
    """Alimentar"""
    if entorno_implementacion == "PRODUCTION":
        click.echo("PROHIBIDO: No se alimenta porque este es el servidor de producción.")
        return
    alimentar_materias()
    alimentar_modulos()
    alimentar_roles()
    alimentar_permisos()
    alimentar_distritos()
    alimentar_autoridades()
    alimentar_domicilios()
    alimentar_cit_servicios()
    alimentar_oficinas()
    alimentar_usuarios()
    alimentar_usuarios_roles()
    click.echo("Termina alimentar.")


@click.command()
@click.pass_context
def reiniciar(ctx):
    """Reiniciar ejecuta inicializar y alimentar"""
    ctx.invoke(inicializar)
    ctx.invoke(alimentar)


@click.command()
def respaldar():
    """Respaldar"""
    respaldar_autoridades()
    respaldar_distritos()
    respaldar_domicilios()
    respaldar_cit_servicios()
    respaldar_materias()
    respaldar_modulos()
    respaldar_roles_permisos()
    respaldar_usuarios_roles()
    respaldar_oficinas()
    click.echo("Termina respaldar.")


cli.add_command(inicializar)
cli.add_command(alimentar)
cli.add_command(reiniciar)
cli.add_command(respaldar)
