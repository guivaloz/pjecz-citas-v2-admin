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


@click.command()
@click.argument("cit_cita_id", type=int)
@click.option("--to_email", default=None, help="Email del destinatario", type=str)
@click.pass_context
def enviar_pendiente(ctx, cit_cita_id, to_email):
    """Envía mensaje vía email para informar de la cita agendada"""
    click.echo("Envío de mensaje de cita agendada")
    # Validar cita
    cit_cita = CitCita.query.get(cit_cita_id)
    if cit_cita is None:
        click.echo(f"ERROR: No se encontró la cita con el id {cit_cita_id}")
        ctx.exit(1)
    if cit_cita.estatus != "A":
        click.echo("La cita no tiene un estatus 'A'")
        ctx.exit(1)
    if cit_cita.estado != "PENDIENTE":
        click.echo("ADVERTENCIA: La cita tiene un estado diferente a PENDIENTE")

    # Agregar tarea en el fondo para enviar el mensaje
    app.task_queue.enqueue(
        "citas_admin.blueprints.cit_citas.tasks.enviar_msg_agendada",
        cit_cita_id=cit_cita_id,
        to_email=to_email,
    )

    # Si no se especifica un email de debug se utilizara el del cliente de la cita
    if to_email is None:
        to_email = cit_cita.cit_cliente.email

    # Mostrar mensaje de termino
    click.echo(f"Se ha enviado un mensaje a {to_email} de su cita agendada con ID {cit_cita_id}")
    ctx.exit(0)


@click.command()
@click.argument("cit_cita_id", type=int)
@click.option("--to_email", default=None, help="Email del destinatario", type=str)
@click.pass_context
def enviar_cancelada(ctx, cit_cita_id, to_email):
    """Envía mensaje vía email para informar que se canceló la cita con éxito"""
    click.echo("Envío de mensaje de cita cancelada")
    # Validar cita
    cit_cita = CitCita.query.get(cit_cita_id)
    if cit_cita is None:
        click.echo(f"ERROR: No se encontró la cita con el id {cit_cita_id}")
        ctx.exit(1)
    if cit_cita.estatus != "A":
        click.echo("La cita no tiene un estatus 'A'")
        ctx.exit(1)
    if cit_cita.estado != "CANCELO":
        click.echo("ADVERTENCIA: La cita tiene un estado diferente a CANCELO")

    # Agregar tarea en el fondo para enviar el mensaje
    app.task_queue.enqueue(
        "citas_admin.blueprints.cit_citas.tasks.enviar_msg_cancelacion",
        cit_cita_id=cit_cita_id,
        to_email=to_email,
    )

    # Si no se especifica un email de debug se utilizara el del cliente de la cita
    if to_email is None:
        to_email = cit_cita.cit_cliente.email

    # Mostrar mensaje de termino
    click.echo(f"Se ha enviado un mensaje a {to_email} de su cita CANCELADA con ID {cit_cita_id}")
    ctx.exit(0)


@click.command()
@click.argument("cit_cita_id", type=int)
@click.option("--to_email", default=None, help="Email del destinatario", type=str)
@click.pass_context
def enviar_asistio(ctx, cit_cita_id, to_email):
    """Envía mensaje vía email para informar que se marcó la asistencia a la cita con éxito"""
    click.echo("Envío de mensaje de cita asistida")
    # Validar cita
    cit_cita = CitCita.query.get(cit_cita_id)
    if cit_cita is None:
        click.echo(f"ERROR: No se encontró la cita con el id {cit_cita_id}")
        ctx.exit(1)
    if cit_cita.estatus != "A":
        click.echo("La cita no tiene un estatus 'A'")
        ctx.exit(1)
    if cit_cita.estado != "ASISTIO":
        click.echo("ADVERTENCIA: La cita tiene un estado diferente a ASISTIO")

    # Agregar tarea en el fondo para enviar el mensaje
    app.task_queue.enqueue(
        "citas_admin.blueprints.cit_citas.tasks.enviar_msg_asistencia",
        cit_cita_id=cit_cita_id,
        to_email=to_email,
    )

    # Si no se especifica un email de debug se utilizara el del cliente de la cita
    if to_email is None:
        to_email = cit_cita.cit_cliente.email

    # Mostrar mensaje de termino
    click.echo(f"Se ha enviado un mensaje a {to_email} de ASISTIÓ a su cita con ID {cit_cita_id}")
    ctx.exit(0)


@click.command()
@click.argument("cit_cita_id", type=int)
@click.option("--to_email", default=None, help="Email del destinatario", type=str)
@click.pass_context
def enviar_inasistencia(ctx, cit_cita_id, to_email):
    """Envía mensaje vía email para informar que se marcó la asistencia a la cita con éxito"""
    click.echo("Envío de mensaje de cita NO asistida")
    # Validar cita
    cit_cita = CitCita.query.get(cit_cita_id)
    if cit_cita is None:
        click.echo(f"ERROR: No se encontró la cita con el id {cit_cita_id}")
        ctx.exit(1)
    if cit_cita.estatus != "A":
        click.echo("La cita no tiene un estatus 'A'")
        ctx.exit(1)
    if cit_cita.estado != "INASISTENCIA":
        click.echo("ADVERTENCIA: La cita tiene un estado diferente a INASISTENCIA")

    # Agregar tarea en el fondo para enviar el mensaje
    app.task_queue.enqueue(
        "citas_admin.blueprints.cit_citas.tasks.enviar_msg_no_asistencia",
        cit_cita_id=cit_cita_id,
        to_email=to_email,
    )

    # Si no se especifica un email de debug se utilizara el del cliente de la cita
    if to_email is None:
        to_email = cit_cita.cit_cliente.email

    # Mostrar mensaje de termino
    click.echo(f"Se ha enviado un mensaje a {to_email} de ASISTIÓ a su cita con ID {cit_cita_id}")
    ctx.exit(0)


@click.command()
@click.option("--test", default=True, help="Se ejecuta en modo de prueba", type=bool)
@click.pass_context
def marcar_vencidas(ctx, test):
    """Marca las citas pasadas y es estado de pendientes como vencidas (INASISTENCIA)"""
    click.echo("Marcar las citas viejas y pendientes como vencidas")

    if test:
        click.echo("MODO DE PRUEBA - No se hará ningún cambio permanente.")

    # Agregar tarea en el fondo para enviar el mensaje
    app.task_queue.enqueue(
        "citas_admin.blueprints.cit_citas.tasks.marcar_citas_vencidas",
        test=test,
    )

    # Mostrar mensaje de termino
    click.echo("Se han marcado las citas pasadas y en estado de PENDIENTES como vencidas (INASISTENCIA)")
    ctx.exit(0)


cli.add_command(consultar)
cli.add_command(enviar_pendiente)
cli.add_command(enviar_cancelada)
cli.add_command(enviar_asistio)
cli.add_command(enviar_inasistencia)
cli.add_command(marcar_vencidas)
