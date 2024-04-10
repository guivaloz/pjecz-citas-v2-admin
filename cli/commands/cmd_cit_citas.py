"""
Cit Citas

- actualizar_cencelar_antes: Actualizar el campo cancelar_antes
- consultar: Consultar las citas
- enviar_pendiente: Envía mensaje vía email agendada
- enviar_cancelado: Envía mensaje vía email cancelada
- enviar_asistio: Envía mensaje vía email asistió
- enviar_inasistencia: Envía mensaje vía email inasistencia
- marcar_inasistencia: Marca citas pasadas y pendientes como inasistencia
- contar_citas_dobles: Cuenta las citas que se crearon más de una vez
"""

import click
from datetime import date, datetime, timedelta
from tabulate import tabulate

from citas_admin.app import create_app
from citas_admin.extensions import database

from citas_admin.blueprints.cit_citas.models import CitCita
from citas_admin.blueprints.cit_dias_inhabiles.models import CitDiaInhabil

app = create_app()
db.app = app

OFFSET = 0
LIMIT = 40


@click.group()
@click.pass_context
def cli(ctx):
    """Cit Citas"""


@click.command()
@click.pass_context
def actualizar_cancelar_antes(ctx):
    """Actualizar el campo cancelar_antes"""
    click.echo("Actualizar el campo cancelar_antes")

    # Consultar dias inhabiles
    dias_inhabiles = CitDiaInhabil.query.filter(CitDiaInhabil.fecha >= date.today()).filter_by(estatus="A").all()

    # Bucle en todas las citas en el futuro que no tienen cancelar_antes
    contador = 0
    for cit_cita in CitCita.query.filter(CitCita.inicio > datetime.now()).filter(CitCita.cancelar_antes == None).all():

        # Definir cancelar_antes con 24 horas antes de la cita
        cancelar_antes = cit_cita.inicio - timedelta(hours=24)

        # Si cancelar_antes es un dia inhabil, domingo o sabado, se busca el dia habil anterior
        while cancelar_antes.date() in dias_inhabiles or cancelar_antes.weekday() == 6 or cancelar_antes.weekday() == 5:
            if cancelar_antes.date() in dias_inhabiles:
                cancelar_antes = cancelar_antes - timedelta(days=1)
            if cancelar_antes.weekday() == 6:  # Si es domingo, se cambia a viernes
                cancelar_antes = cancelar_antes - timedelta(days=2)
            if cancelar_antes.weekday() == 5:  # Si es sábado, se cambia a viernes
                cancelar_antes = cancelar_antes - timedelta(days=1)

        # Actualizar
        cit_cita.cancelar_antes = cancelar_antes
        cit_cita.save()

        # Incrementar contador
        contador += 1
        if contador % 100 == 0:
            click.echo(f"Van {contador} citas actualizadas...")

    click.echo(f"Se actualizaron {contador} citas")
    ctx.exit(0)


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
    """Envía mensaje vía email cita agendada"""
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
        "citas_admin.blueprints.cit_citas.tasks.enviar_pendiente",
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
def enviar_cancelado(ctx, cit_cita_id, to_email):
    """Envía mensaje vía email cita Cancelada"""
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
        "citas_admin.blueprints.cit_citas.tasks.enviar_cancelado",
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
    """Envía mensaje vía email Asistió"""
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
        "citas_admin.blueprints.cit_citas.tasks.enviar_asistio",
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
    """Envía mensaje vía email Inasistencia"""
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
        "citas_admin.blueprints.cit_citas.tasks.enviar_inasistencia",
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
@click.option("--enviar", default=False, help="Se envía una notificación al cliente", type=bool)
@click.pass_context
def marcar_inasistencia(ctx, test, enviar):
    """Marca citas pasadas y PENDIENTES como 'INASISTENCIA'"""
    click.echo("Marcar las citas pasadas y PENDIENTES con INASISTENCIA")

    # Calcular fecha de vencimiento
    fecha_actual = datetime.now()
    fecha_limite = datetime(
        year=fecha_actual.year,
        month=fecha_actual.month,
        day=fecha_actual.day,
        hour=23,
        minute=59,
        second=59,
    )
    fecha_limite = fecha_limite - timedelta(days=1)
    click.echo(f"Fecha de Vencimiento: {fecha_limite}, citas anteriores a esta fecha.")

    # Conteo de citas para cambiar de PENDIENTE a INASISTENCIA
    citas_count = (
        CitCita.query.filter_by(estado="PENDIENTE").filter(CitCita.inicio <= fecha_limite).filter_by(estatus="A").count()
    )

    if test:
        click.echo(f"MODO DE PRUEBA - citas a cambiar {citas_count}, No se hizo ningún cambio permanente.")
    else:
        # Enviar mensaje de INASISTENCIA al cliente
        if enviar is True:
            citas = (
                CitCita.query.filter_by(estado="PENDIENTE").filter(CitCita.inicio <= fecha_limite).filter_by(estatus="A").all()
            )
            for cita in citas:
                # Agregar tarea en el fondo para enviar el mensaje de inasistencia
                app.task_queue.enqueue(
                    "citas_admin.blueprints.cit_citas.tasks.enviar_inasistencia",
                    cit_cita_id=cita.id,
                )
            click.echo(f"Se han enviado {len(citas)} mensajes de INASISTENCIA")
        else:
            citas_count = (
                CitCita.query.filter_by(estado="PENDIENTE")
                .filter(CitCita.inicio <= fecha_limite)
                .filter_by(estatus="A")
                .count()
            )
            click.echo(f"SIN ENVÍO: Se podrían enviar {citas_count} mensajes de correo a los clientes.")

    if citas_count > 0:
        # Agregar tarea en el fondo para marcar las citas vencidas
        app.task_queue.enqueue(
            "citas_admin.blueprints.cit_citas.tasks.marcar_inasistencia",
            test=test,
        )
        click.echo(f"Se han cambiado {citas_count} citas a estado de INASISTENCIA")

    ctx.exit(0)


@click.command()
@click.pass_context
def contar_citas_dobles(ctx):
    """Cuenta las citas que se crearon más de una vez"""
    click.echo("=== Reporte de citas dobles ===")

    # Recorrido de las citas
    citas = CitCita.query.filter_by(estatus="A").order_by(CitCita.id).all()

    contador = 0
    count_citas_dobles = 0
    for cita in citas:
        contador += 1
        # Buscar cita repetida
        cita_repetida = (
            CitCita.query.filter(CitCita.id > cita.id)
            .filter_by(creado=cita.creado)
            .filter_by(inicio=cita.inicio)
            .filter_by(cit_cliente=cita.cit_cliente)
            .filter_by(oficina_id=cita.oficina_id)
            .filter_by(cit_servicio_id=cita.cit_servicio_id)
            .order_by(CitCita.id)
            .first()
        )
        if cita_repetida:
            click.echo(f"! CITA REPETIDA: {cita.id} y {cita_repetida.id}")
            count_citas_dobles += 1
        # Muestra de avance
        if contador % 1000 == 0:
            click.echo(
                "Progreso [{porcentaje:.2f}%] : conteo {contador}".format(
                    porcentaje=((contador * 100) / len(citas)), contador=count_citas_dobles
                )
            )

    click.echo(f"= RESULTADO: Se han encontrado {count_citas_dobles} citas dobles")

    ctx.exit(0)


cli.add_command(actualizar_cancelar_antes)
cli.add_command(consultar)
cli.add_command(enviar_pendiente)
cli.add_command(enviar_cancelado)
cli.add_command(enviar_asistio)
cli.add_command(enviar_inasistencia)
cli.add_command(marcar_inasistencia)
cli.add_command(contar_citas_dobles)
