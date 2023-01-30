"""
Pag Pagos

- enviar: Enviar mensaje con resultado de su pago
"""
from datetime import datetime, timedelta

import click

from citas_admin.blueprints.pag_pagos.models import PagPago

from citas_admin.app import create_app
from citas_admin.extensions import db

app = create_app()
db.app = app


@click.group()
@click.pass_context
def cli(ctx):
    """Pagos"""


@click.command()
@click.option("--pag_pago_id", default=None, help="ID del Pago", type=int)
@click.option("--email", default=None, help="email para probar", type=str)
@click.pass_context
def enviar(ctx, pag_pago_id=None, email=None):
    """Enviar comprobante de Pago"""
    hoy = datetime.now().date()
    click.echo(f"Enviar comprobante de pago para hoy {hoy.strftime('%Y-%m-%d')}")

    # Validar Pago
    pago = PagPago.query.get(pag_pago_id)
    if pago is None:
        click.echo(f"ERROR: El ID de Pago '{pag_pago_id}' NO existe")
        ctx.exit(1)
    if pago.estatus != "A":
        click.echo(f"ERROR: El ID {pago.id} NO tiene estatus ACTIVO")
        ctx.exit(1)

    # Si no se establece un email de prueba, se utilizará el real
    if email is None:
        email = pago.email

    # Agregar tarea en el fondo para enviar el comprobante de pago
    app.task_queue.enqueue(
        "citas_admin.blueprints.pag_pagos.tasks.enviar",
        pag_pago_id=pago.id,
        email=email,
    )

    # Mostrar mensaje de termino
    mensaje = "Se ha agregado una tarea en el fondo"
    if email is not None:
        mensaje += f" para enviar el comprobante de pago {pag_pago_id} al email {email}"
    else:
        mensaje += f" para guardar el comprobante de pago {pag_pago_id} en un archivo"
    click.echo(mensaje)
    ctx.exit(0)


@click.command()
@click.option("--email", default=None, help="email para probar", type=str)
@click.pass_context
def enviar_mensajes_comprobantes(ctx, pag_pago_id=None, email=None):
    """Enviar mensajes de comprobante de pago para pagos en estado de PAGADO y sin haber sido enviados previamente"""
    ctx.exit(0)


@click.command()
@click.pass_context
def cancelar_solicitados_expirados(ctx):
    """Pasa a estado de CANCELADO todos los pagos en estado previo de SOLICITADO"""
    tiempo_limite = datetime.now() - timedelta(hours=2)
    click.echo(f"Cancelar pagos en estado de SOLICITADO previos al tiempo {tiempo_limite.strftime('%Y-%m-%d %H:%M:%S')}")

    pagos_count = PagPago.query.filter_by(estatus="A").filter_by(estado="SOLICITADO").filter(PagPago.creado <= tiempo_limite).count()

    # Agregar tarea en el fondo para cancelar los pagos
    app.task_queue.enqueue(
        "citas_admin.blueprints.pag_pagos.tasks.cancelar_solicitados_expirados",
        tiempo_limite=tiempo_limite,
    )

    click.echo(f"Se cancelaron {pagos_count} pagos")
    ctx.exit(0)


cli.add_command(enviar)
cli.add_command(enviar_mensajes_comprobantes)
cli.add_command(cancelar_solicitados_expirados)
