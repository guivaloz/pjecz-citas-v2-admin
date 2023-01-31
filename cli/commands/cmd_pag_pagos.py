"""
Pag Pagos

- enviar_mensaje_pagado: Envía mensaje de estado PAGADO
- enviar_mensajes_comprobantes: Envía los mensajes de estado PAGADO pendientes por enviar antes de un tiempo indicado.
- cancelar_solicitados_expirados : Cambia el estado a CANCELADO de los pagos SOLICITADOS creados antes de un tiempo indicado.
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
@click.argument("pag_pago_id", type=int)
@click.option("--to_email", default=None, help="email para probar", type=str)
@click.pass_context
def enviar_mensaje_pagado(ctx, pag_pago_id, to_email=None):
    """Enviar comprobante de Pago"""
    click.echo("Enviar comprobante de pago")

    # Validar Pago
    pago = PagPago.query.get(pag_pago_id)
    if pago is None:
        click.echo(f"ERROR: El ID de Pago '{pag_pago_id}' NO existe")
        ctx.exit(1)
    if pago.estatus != "A":
        click.echo(f"ERROR: El ID {pago.id} NO tiene estatus ACTIVO")
        ctx.exit(1)
    if pago.estado != "PAGADO":
        click.echo(f"ERROR: El ID {pago.id} NO tiene estado PAGADO")
        ctx.exit(1)

    # Agregar tarea en el fondo para enviar el comprobante de pago
    app.task_queue.enqueue(
        "citas_admin.blueprints.pag_pagos.tasks.enviar_mensaje_pagado",
        pag_pago_id=pago.id,
        to_email=to_email,
    )

    # Mostrar mensaje de termino
    mensaje = f"Se ha agregado una tarea en el fondo para enviar el comprobante de pago {pag_pago_id} "
    if to_email is not None:
        mensaje += f"al email de prueba {to_email}"
    else:
        mensaje += f"al email {pago.email}"
    click.echo(mensaje)
    ctx.exit(0)


@click.command()
@click.pass_context
@click.option("--before_creado", default=30, help="Minutos antes de la hora actual", type=int)
@click.option("--to_email", default=None, help="email para probar", type=str)
def enviar_mensajes_comprobantes(ctx, before_creado, to_email=None):
    """Enviar comprobante para pagos en estado de PAGADO y sin haber sido enviados previamente"""
    tiempo = datetime.now() - timedelta(minutes=before_creado)
    click.echo(f"Envío de comprobantes de pago exitosos pendientes por enviar creados antes del {tiempo.strftime('%Y-%m-%d %H:%M:%S')}")

    # Conteo de registros a consultar
    pagos_count = PagPago.query.filter_by(estatus="A").filter_by(estado="PAGADO").filter_by(ya_se_envio_comprobante=False).filter(PagPago.creado <= tiempo).count()

    # Agregar tarea en el fondo para cancelar los pagos
    app.task_queue.enqueue(
        "citas_admin.blueprints.pag_pagos.tasks.enviar_mensajes_comprobantes",
        before_creado=tiempo,
        to_email=to_email,
    )

    # Mostrar resultado
    mensaje = f"Se ha agregado una tarea en el fondo para enviar {pagos_count} comprobantes de pago "
    if to_email is not None:
        mensaje += f"al email de prueba {to_email}"
    click.echo(mensaje)
    ctx.exit(0)


@click.command()
@click.pass_context
@click.option("--before_creado", default=120, help="Minutos antes de la hora actual", type=int)
def cancelar_solicitados_expirados(ctx, before_creado):
    """Cambia el estado a CANCELADO de los pagos SOLICITADOS creados antes de before_creado"""
    tiempo = datetime.now() - timedelta(minutes=before_creado)
    click.echo(f"Cancelar pagos en estado SOLICITADO creados antes del {tiempo.strftime('%Y-%m-%d %H:%M:%S')}")

    # Conteo de registros a afectar
    pagos_count = PagPago.query.filter_by(estatus="A").filter_by(estado="SOLICITADO").filter(PagPago.creado <= tiempo).count()

    # Agregar tarea en el fondo para cancelar los pagos
    app.task_queue.enqueue(
        "citas_admin.blueprints.pag_pagos.tasks.cancelar_solicitados_expirados",
        before_creado=tiempo,
    )

    # Mostrar resultado
    click.echo(f"Se cancelaron {pagos_count} pagos")
    ctx.exit(0)


cli.add_command(enviar_mensaje_pagado)
cli.add_command(enviar_mensajes_comprobantes)
cli.add_command(cancelar_solicitados_expirados)
