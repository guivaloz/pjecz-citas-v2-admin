"""
Cit Citas

- consultar: Ver listado de citas
"""
import click
from tabulate import tabulate

from citas_admin.app import create_app
from citas_admin.extensions import db

from citas_admin.blueprints.cit_citas.models import CitCita

app = create_app()
db.app = app

OFFSET = 0
LIMIT = 40


@click.group()
@click.pass_context
def cli(ctx):
    """Cit Citas"""


@click.command()
@click.option("--estado", default="", help="ASISTIO, CANCELO, PENDIENTE", type=str)
@click.option("--limit", default=LIMIT, help="Limit", type=int)
@click.option("--offset", default=OFFSET, help="Offset", type=int)
@click.pass_context
def consultar(ctx, estado, limit, offset):
    """Consultar las citas"""
    click.echo("Consultar las citas")

    # Consultar
    cit_citas = CitCita.query.filter_by(estatus="A")
    if estado != "":
        cit_citas = cit_citas.filter_by(estado=estado.upper())
    cit_citas = cit_citas.order_by(CitCita.id.desc()).offset(offset).limit(limit)

    # Mostrar la tabla
    renglones = []
    for cit_cita in cit_citas.all():
        renglones.append(
            [
                cit_cita.id,
                cit_cita.cit_cliente.email,
                cit_cita.oficina.clave,
                cit_cita.cit_servicio.clave,
                cit_cita.inicio.strftime("%Y-%m-%d %H:%M"),
                cit_cita.notas[:24],
                cit_cita.estado,
                "SI" if cit_cita.asistencia else "",
            ]
        )
    encabezados = ["ID", "e-mail", "Oficina", "Servicio", "Inicio", "Notas", "Estado", "Asistencia"]
    click.echo(tabulate(renglones, encabezados))
    ctx.exit(0)


cli.add_command(consultar)
