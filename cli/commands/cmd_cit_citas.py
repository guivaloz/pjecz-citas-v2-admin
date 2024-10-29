"""
CLI Cit Citas

- enviar_pendiente: Enviar mensaje vía email de una cita agendada
- enviar_cancelado: Enviar mensaje vía email de una cita cancelada
- enviar_asistio: Enviar mensaje vía email de su cita a la que asistió
- enviar_inasistencia: Enviar un mensaje vía email de una cita por Inasistencia
"""

import sys

import click

from citas_admin.app import create_app
from citas_admin.blueprints.cit_citas.models import CitCita
from citas_admin.extensions import database

app = create_app()
app.app_context().push()
database.app = app


@click.group()
def cli():
    """Cit Citas"""


@click.command()
@click.argument("cit_cita_id", type=int)
@click.option("--to_email", default=None, help="Otro e-mail para probar", type=str)
def enviar_pendiente(cit_cita_id: int, to_email: str):
    """Enviar mensaje vía email de una cita agendada"""
    click.echo("Enviar mensaje vía email de una cita agendada")

    # Consultar cita
    cit_cita = CitCita.query.get(cit_cita_id)

    # Si no existe la cita
    if cit_cita is None:
        click.echo(f"No se encontró la cita con el id {cit_cita_id}")
        sys.exit(1)

    # Si la cita no tiene un estatus 'A'
    if cit_cita.estatus != "A":
        click.echo("La cita no tiene un estatus 'A'")
        sys.exit(1)

    # Si la cita tiene un estado diferente a PENDIENTE
    if cit_cita.estado != "PENDIENTE":
        click.echo("La cita tiene un estado diferente a PENDIENTE")
        sys.exit(1)

    # Agregar tarea en el fondo para enviar el mensaje
    app.task_queue.enqueue(
        "citas_admin.blueprints.cit_citas.tasks.enviar_pendiente",
        cit_cita_id=cit_cita_id,
        to_email=to_email,
    )

    # Si no se especifica to_email, sabemos que la tarea usará el del cliente
    if to_email is None:
        to_email = cit_cita.cit_cliente.email

    # Mostrar mensaje de termino
    click.echo(f"Se ha agregado una tarea para enviar un mensaje a {to_email}")


@click.command()
@click.argument("cit_cita_id", type=int)
@click.option("--to_email", default=None, help="Otro e-mail para probar", type=str)
def enviar_cancelado(cit_cita_id: int, to_email: str):
    """Enviar mensaje vía email de una cita cancelada"""
    click.echo("Enviar mensaje vía email de una cita cancelada")

    # Consultar cita
    cit_cita = CitCita.query.get(cit_cita_id)

    # Si no existe la cita
    if cit_cita is None:
        click.echo(f"ERROR: No se encontró la cita con el id {cit_cita_id}")
        sys.exit(1)

    # Si la cita no tiene un estatus 'A'
    if cit_cita.estatus != "A":
        click.echo("La cita no tiene un estatus 'A'")
        sys.exit(1)

    # Si la cita tiene un estado diferente a CANCELO
    if cit_cita.estado != "CANCELO":
        click.echo("La cita tiene un estado diferente a CANCELO")
        sys.exit(1)

    # Agregar tarea en el fondo para enviar el mensaje
    app.task_queue.enqueue(
        "citas_admin.blueprints.cit_citas.tasks.enviar_cancelado",
        cit_cita_id=cit_cita_id,
        to_email=to_email,
    )

    # Si no se especifica to_email, sabemos que la tarea usará el del cliente
    if to_email is None:
        to_email = cit_cita.cit_cliente.email

    # Mostrar mensaje de termino
    click.echo(f"Se ha agregado una tarea para enviar un mensaje a {to_email}")


@click.command()
@click.argument("cit_cita_id", type=int)
@click.option("--to_email", default=None, help="Otro e-mail para probar", type=str)
def enviar_asistio(cit_cita_id: int, to_email: str):
    """Enviar mensaje vía email de su cita a la que asistió"""
    click.echo("Enviar mensaje vía email de su cita a la que asistió")

    # Validar cita
    cit_cita = CitCita.query.get(cit_cita_id)

    # Si no existe la cita
    if cit_cita is None:
        click.echo(f"ERROR: No se encontró la cita con el id {cit_cita_id}")
        sys.exit(1)

    # Si la cita no tiene un estatus 'A'
    if cit_cita.estatus != "A":
        click.echo("La cita no tiene un estatus 'A'")
        sys.exit(1)

    # Si la cita tiene un estado diferente a ASISTIO
    if cit_cita.estado != "ASISTIO":
        click.echo("La cita tiene un estado diferente a ASISTIO")
        sys.exit(1)

    # Agregar tarea en el fondo para enviar el mensaje
    app.task_queue.enqueue(
        "citas_admin.blueprints.cit_citas.tasks.enviar_asistio",
        cit_cita_id=cit_cita_id,
        to_email=to_email,
    )

    # Si no se especifica to_email, sabemos que la tarea usará el del cliente
    if to_email is None:
        to_email = cit_cita.cit_cliente.email

    # Mostrar mensaje de termino
    click.echo(f"Se ha agregado una tarea para enviar un mensaje a {to_email}")


@click.command()
@click.argument("cit_cita_id", type=int)
@click.option("--to_email", default=None, help="Otro e-mail para probar", type=str)
def enviar_inasistencia(cit_cita_id: int, to_email: str):
    """Enviar un mensaje vía email de una cita por Inasistencia"""
    click.echo("Envío de mensaje de cita NO asistida")

    # Validar cita
    cit_cita = CitCita.query.get(cit_cita_id)

    # Si no existe la cita
    if cit_cita is None:
        click.echo(f"ERROR: No se encontró la cita con el id {cit_cita_id}")
        sys.exit(1)

    # Si la cita no tiene un estatus 'A'
    if cit_cita.estatus != "A":
        click.echo("La cita no tiene un estatus 'A'")
        sys.exit(1)

    # Si la cita tiene un estado diferente a INASISTENCIA
    if cit_cita.estado != "INASISTENCIA":
        click.echo("La cita tiene un estado diferente a INASISTENCIA")
        sys.exit(1)

    # Agregar tarea en el fondo para enviar el mensaje
    app.task_queue.enqueue(
        "citas_admin.blueprints.cit_citas.tasks.enviar_inasistencia",
        cit_cita_id=cit_cita_id,
        to_email=to_email,
    )

    # Si no se especifica to_email, sabemos que la tarea usará el del cliente
    if to_email is None:
        to_email = cit_cita.cit_cliente.email

    # Mostrar mensaje de termino
    click.echo(f"Se ha agregado una tarea para enviar un mensaje a {to_email}")


cli.add_command(enviar_pendiente)
cli.add_command(enviar_cancelado)
cli.add_command(enviar_asistio)
cli.add_command(enviar_inasistencia)
