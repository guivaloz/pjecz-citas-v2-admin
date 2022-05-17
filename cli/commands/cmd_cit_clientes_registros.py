"""
Cit Clientes Registros

- ver: Ver mensaje de registro
- enviar: Enviar mensaje de registro
- cancelar: Cancelar mensaje de registro
"""
import click
from tabulate import tabulate

from citas_admin.app import create_app
from citas_admin.extensions import db

from citas_admin.blueprints.cit_clientes_registros.models import CitClienteRegistro

app = create_app()
db.app = app


@click.group()
def cli():
    """Cit Clientes Registros"""


@click.command()
@click.option("--id", default=1, help="Number of greetings.")
def ver():
    """Ver mensaje de registro"""
    cit_clientes_registros = CitClienteRegistro.query.filter_by(estatus="A").filter_by(ya_registrado=False).all()
    if cit_clientes_registros is None:
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
                cit_cliente_registro.email,
                cit_cliente_registro.curp,
            ]
        )
    click.echo(tabulate(datos, headers=["id", "nombres", "apellido_primero", "apellido_segundo", "email", "curp"]))


@click.command()
def enviar():
    """Enviar mensaje de registro"""
    click.echo("Por programar")


@click.command()
def cancelar():
    """Cancelar mensaje de registro"""
    click.echo("Por programar")


cli.add_command(ver)
cli.add_command(enviar)
cli.add_command(cancelar)
