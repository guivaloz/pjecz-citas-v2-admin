"""
Boletines

- consultar: Consultar boletines
- enviar: Enviar mensajes con boletines
"""
from datetime import datetime

import click
from tabulate import tabulate

from citas_admin.blueprints.boletines.models import Boletin

from citas_admin.app import create_app
from citas_admin.extensions import db

app = create_app()
db.app = app


@click.group()
@click.pass_context
def cli(ctx):
    """Boletines"""


@click.command()
@click.option("--boletin_id", default=None, help="ID del boletin", type=int)
@click.option("--cit_cliente_id", default=None, help="ID del cliente", type=int)
@click.option("--email", default=None, help="email para probar", type=str)
@click.pass_context
def enviar(ctx, boletin_id=None, cit_cliente_id=None, email=None):
    """Enviar boletines"""
    hoy = datetime.now().date()
    click.echo(f"Enviar boletines para hoy {hoy.strftime('%Y-%m-%d')}")

    # Si no viene el boletin_id
    if boletin_id is None:
        # Consultar el boletin mas viejo con estado PROGRAMADO
        boletin = Boletin.query.filter_by(estado="PROGRAMADO").filter(Boletin.envio_programado < hoy).filter_by(estatus="A").order_by(Boletin.id).first()
        if boletin is None:
            click.echo("No hay boletines programados para enviar hoy")
            ctx.exit(0)
    else:
        # Validar boletin
        boletin = Boletin.query.get(boletin_id)
        if boletin is None:
            click.echo(f"ERROR: El ID del boletin '{boletin_id}' NO existe")
            ctx.exit(1)
        if boletin.estatus != "A":
            click.echo(f"ERROR: El ID {boletin.id} NO tiene estatus ACTIVO")
            ctx.exit(1)

    # Agregar tarea en el fondo para enviar boletines
    app.task_queue.enqueue(
        "citas_admin.blueprints.boletines.tasks.enviar",
        boletin_id=boletin_id,
        cit_cliente_id=cit_cliente_id,
        email=email,
    )

    # Mostrar mensaje de termino
    mensaje = "Se ha agregado una tarea en el fondo"
    if email is not None:
        mensaje += f" para enviar el boletin {boletin_id} al email {email}"
    elif cit_cliente_id is None:
        mensaje += f" para enviar el boletin {boletin_id} a todos los clientes activos"
    else:
        mensaje += f" para guardar el boletin {boletin_id} en un archivo"
    click.echo(mensaje)
    ctx.exit(0)


@click.command()
@click.pass_context
def programados(ctx):
    """Mostrar los boletines programados"""
    hoy = datetime.now().date()

    # Consultar boletines que debo de enviar ahora
    boletines = Boletin.query.filter_by(estado="PROGRAMADO").filter(Boletin.envio_programado <= hoy).filter_by(estatus="A").order_by(Boletin.envio_programado.asc()).all()
    if boletines:
        click.echo(f"Boletines programados para enviar hoy {hoy.strftime('%Y-%m-%d')}")
        renglones = []
        for boletin in boletines:
            renglones.append([boletin.id, boletin.envio_programado.strftime("%Y-%m-%d"), boletin.asunto[:48], boletin.estado, boletin.puntero])
        encabezados = ["ID", "Envio P.", "Asunto", "Estado", "Puntero"]
        click.echo(tabulate(renglones, headers=encabezados))
    else:
        click.echo("NO HAY boletines para enviar hoy")
    click.echo()

    # Consultar boletines que se van a enviar en el futuro
    boletines = Boletin.query.filter_by(estado="PROGRAMADO").filter(Boletin.envio_programado > hoy).filter_by(estatus="A").order_by(Boletin.envio_programado.asc()).all()
    if boletines:
        click.echo("Boletines para enviar en el FUTURO")
        renglones = []
        for boletin in boletines:
            renglones.append([boletin.id, boletin.envio_programado.strftime("%Y-%m-%d"), boletin.asunto[:48], boletin.estado, boletin.puntero])
        encabezados = ["ID", "Envio P.", "Asunto", "Estado", "Puntero"]
        click.echo(tabulate(renglones, headers=encabezados))
    else:
        click.echo("NO HAY boletines para enviar en el FUTURO")
    click.echo()

    # Terminar
    ctx.exit(0)


cli.add_command(enviar)
cli.add_command(programados)
