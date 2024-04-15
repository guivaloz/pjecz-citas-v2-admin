"""
Cit Oficinas-Servicios

- asignar: Asignar servicios de una categoria a todas las oficinas de un distrito
"""

import click

from citas_admin.app import create_app
from citas_admin.extensions import database
from citas_admin.blueprints.cit_categorias.models import CitCategoria
from citas_admin.blueprints.distritos.models import Distrito

app = create_app()
app.app_context().push()
database.app = app


@click.group()
def cli():
    """Cit Oficinas-Servicios"""


@click.command()
@click.argument("categoria_nombre", type=str)
@click.argument("distrito_nombre", type=str)
def asignar(categoria_nombre, distrito_nombre):
    """Asignar servicios de una categoria a todas las oficinas de un distrito"""
    cit_categoria = CitCategoria.query.filter_by(nombre=categoria_nombre).first()
    if cit_categoria is None:
        click.echo("ERROR: No se encuentra la categoria")
        return
    distrito = Distrito.query.filter_by(nombre=distrito_nombre).first()
    if distrito is None:
        click.echo("ERROR: No se encuentra al distrito")
        return
    app.task_queue.enqueue(
        "citas_admin.blueprints.cit_oficinas_servicios.tasks.asignar_a_cit_categoria_con_distrito",
        cit_categoria_id=cit_categoria.id,
        distrito_id=distrito.id,
    )
    click.echo("Asignar se está ejecutando en el fondo.")


@click.command()
@click.argument("categoria_nombre", type=str)
def asignar_todos_distritos(categoria_nombre):
    """Asignar servicios de una categoria a todas las oficinas de todos los distritos"""
    cit_categoria = CitCategoria.query.filter_by(nombre=categoria_nombre).first()
    if cit_categoria is None:
        click.echo("ERROR: No se encuentra la categoria")
        return
    app.task_queue.enqueue(
        "citas_admin.blueprints.cit_oficinas_servicios.tasks.asignar_a_cit_categoria_todos_distritos",
        cit_categoria_id=cit_categoria.id,
    )
    click.echo("Asignar se está ejecutando en el fondo.")


cli.add_command(asignar)
cli.add_command(asignar_todos_distritos)
