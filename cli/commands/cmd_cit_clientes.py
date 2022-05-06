"""
Cit Clientes

- agregar: Agregar un nuevo cliente
- cambiar_contrasena: Cambiar contraseña de un cliente
"""
from datetime import datetime, timedelta
import click
from lib.pwgen import generar_contrasena

from citas_admin.app import create_app
from citas_admin.extensions import db, pwd_context

from citas_admin.blueprints.cit_clientes.models import CitCliente

app = create_app()
db.app = app


@click.group()
def cli():
    """Cit Clientes"""


@click.command()
@click.argument("email", type=str)
def agregar(email):
    """Agregar un nuevo cliente"""
    # Validar que el email no exista
    if CitCliente.query.filter_by(email=email).first():
        click.echo(f"El email {email} ya existe")
        return
    # Preguntar los datos del cliente
    nombres = input("Nombres: ")
    apellido_paterno = input("Apellido paterno: ")
    apellido_materno = input("Apellido materno: ")
    curp = input("CURP: ")
    telefono = input("Teléfono: ")
    # Crear una contraseña aleatoria
    contrasena = generar_contrasena()
    # Definir la fecha de renovación dos meses después
    renovacion_fecha = datetime.now() + timedelta(days=60)
    # Agregar el cliente
    cit_cliente = CitCliente(
        nombres=nombres,
        apellido_paterno=apellido_paterno,
        apellido_materno=apellido_materno,
        curp=curp,
        telefono=telefono,
        email=email,
        contrasena=pwd_context.hash(contrasena),
        hash=pwd_context.hash(generar_contrasena()),
        renovacion_fecha=renovacion_fecha.date(),
    )
    cit_cliente.save()
    click.echo(f"Se ha creado el cliente {email} con contraseña {contrasena}")


@click.command()
@click.argument("email", type=str)
def cambiar_contrasena(email):
    """Cambiar contraseña de un cliente"""
    cit_cliente = CitCliente.query.filter_by(email=email).first()
    if cit_cliente is None:
        click.echo(f"No existe el e-mail {email} en cit_clientes")
        return
    contrasena_1 = input("Contraseña: ").strip()
    contrasena_2 = input("De nuevo la misma contraseña: ").strip()
    if contrasena_1 != contrasena_2:
        click.echo("No son iguales las contraseñas. Por favor intente de nuevo.")
        return
    cit_cliente.contrasena = pwd_context.hash(contrasena_1)
    cit_cliente.save()
    click.echo(f"Se ha cambiado la contraseña de {email} en usuarios")


cli.add_command(agregar)
cli.add_command(cambiar_contrasena)
