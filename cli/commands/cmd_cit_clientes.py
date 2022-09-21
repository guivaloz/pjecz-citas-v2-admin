"""
Cit Clientes

- agregar: Agregar un nuevo cliente
- cambiar_contrasena: Cambiar contraseña de un cliente
- eliminar_abandonados: Eliminar los clientes que han abandonado su cuenta
- definir_booleanos: Define los booleanos es_adulto_mayor, es_mujer, etc
"""
from datetime import datetime, timedelta
import click
from sqlalchemy import text
from sqlalchemy.sql import func
from lib.database import SessionLocal
from citas_admin.blueprints.cit_citas.models import CitCita

from lib.pwgen import generar_contrasena
from lib.safe_string import safe_string

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
    nombres = safe_string(input("Nombres: "))
    apellido_primero = safe_string(input("Apellido primero: "))
    apellido_segundo = safe_string(input("Apellido segundo: "))
    curp = safe_string(input("CURP: "))
    telefono = safe_string(input("Teléfono: "))
    # Crear una contraseña aleatoria
    contrasena = generar_contrasena()
    # Definir la fecha de renovación dos meses después
    renovacion_fecha = datetime.now() + timedelta(days=60)
    # Agregar el cliente
    cit_cliente = CitCliente(
        nombres=nombres,
        apellido_primero=apellido_primero,
        apellido_segundo=apellido_segundo,
        curp=curp,
        telefono=telefono,
        email=email,
        contrasena_md5="",
        contrasena_sha256=pwd_context.hash(contrasena),
        renovacion=renovacion_fecha.date(),
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
    cit_cliente.contrasena_md5 = ""
    cit_cliente.contrasena_sha256 = pwd_context.hash(contrasena_1)
    cit_cliente.save()
    click.echo(f"Se ha cambiado la contraseña de {email} en usuarios")


@click.command()
@click.option("--test", default=True, help="Modo de pruebas en el que no se guardan los cambios")
def eliminar_abandonados(test):
    """Eliminar clientes que han abandonado su cuenta"""
    click.echo("Eliminación de Clientes abandonados - Sin contraseña SHA256 ni citas Agendadas")

    # Conteo de posibles eliminaciones
    count_cit_clientes = CitCliente.query.outerjoin(CitCita).filter(CitCliente.contrasena_sha256 == "").filter(CitCita.cit_cliente == None).count()
    click.echo(f"Se encontraron {count_cit_clientes} cuentas de clientes sin contraseña SHA256 y sin citas agendadas.")

    if test is False:
        engine = db.engine
        # Borrado permanente de clientes_recuperaciones
        borrado = text(
            "DELETE \
                FROM cit_clientes_recuperaciones \
                WHERE estatus = 'B'"
        )
        res = engine.execute(borrado)
        # Borrado permanente de clientes sin SHA256 y sin Citas
        borrado = text(
            "DELETE \
                FROM cit_clientes AS cli \
                WHERE cli.id NOT IN (SELECT cit_cliente_id FROM cit_citas WHERE cit_cliente_id = cli.id) \
                    AND cli.id NOT IN (SELECT cit_cliente_id FROM cit_clientes_recuperaciones WHERE cit_cliente_id = cli.id) \
                    AND cli.contrasena_sha256 = ''"
        )
        res = engine.execute(borrado)
        if res:
            click.echo(f"Se eliminaron {res.rowcount} clientes correctamente")
    else:
        click.echo(f"MODO DE PRUEBA - Se podrían eliminar {count_cit_clientes} clientes")


@click.command()
@click.option("--test", default=True, help="Modo de pruebas en el que no se guardan los cambios")
def definir_boleanos(test):
    """Define los booleanos es_adulto_mayor, es_mujer, etc"""

    # Consultar los clientes con estatus A y con SHA256

    # Si es adulto mayor
    contador_es_adulto_mayor = 0
    contador_no_es_adulto_mayor = 0

    # Si es mujer
    contador_es_mujer = 0
    contador_no_es_mujer = 0

    # Terminar mostrando las cantidades de actualizaciones
    click.echo(f"Se han actualizado {contador_es_adulto_mayor} registros con es_adulto mayor.")
    click.echo(f"Se han actualizado {contador_no_es_adulto_mayor} registros con NO es_adulto mayor.")


@click.command()
@click.option("--test", default=True, help="Modo de pruebas en el que no se guardan los cambios")
def evaluar_asistencia(test):
    """Penaliza o Premia al cliente dependiendo de su asistencia"""
    click.echo("Penaliza o Premia al cliente dependiendo de su asistencia")

    # # Agregar tarea en el fondo para enviar el mensaje
    # app.task_queue.enqueue(
    #     "citas_admin.blueprints.cit_clientes.tasks.evaluar_asistencia",
    #     test=test,
    # )
    _temp()
    # Mostrar mensaje de termino
    if test:
        click.echo("MODO DE PRUEBA - No se hizo ningún cambio permanente.")
    else:
        click.echo("Se han cambiado el número de citas de los clientes buenos y malos.")


def _temp(test=True):
    """temp"""
    DIAS_MARGEN = 30
    LIMITE_SIN_CITAS = 15
    LIMITE_INASISTENCIA = 2
    LIMITE_ASISTENCIA = 30
    PORCENTAJE_ASISTENCIA_ACEPTABLE = 0.8

    # Calcular fecha de vencimiento
    fecha_actual = datetime.now()
    fecha_limite = datetime(
        year=fecha_actual.year,
        month=fecha_actual.month,
        day=fecha_actual.day,
        hour=0,
        minute=0,
        second=0,
    )
    fecha_limite = fecha_limite - timedelta(days=DIAS_MARGEN)

    # Contadores de cambios realizados
    count_clientes_ajustados = 0
    count_clientes_premiados = 0
    count_clientes_penalizados = 0

    # Revisar los clientes
    clientes = CitCliente.query.filter_by(estatus="A").all()
    for cliente in clientes:
        # variables para contar las citas por cliente
        count_citas_asistio = 0
        count_citas_inasistencia = 0
        # Query para extraer el número de citas por estado
        db = SessionLocal()
        citas_cantidades = (
            db.query(
                CitCita.estado.label("estado"),
                func.count("*").label("cantidad"),
            )
            .filter_by(cit_cliente_id=cliente.id)
            .filter_by(estatus="A")
            .filter(CitCita.creado > fecha_limite)
            .group_by(CitCita.estado)
        )
        # Establecemos las cantidades
        for estado, cantidad in citas_cantidades.all():
            if estado == "ASISTIO":
                count_citas_asistio = cantidad
            elif estado == "INASISTENCIA":
                count_citas_inasistencia = cantidad
        # Calculamos los porcentajes
        total_citas = count_citas_asistio + count_citas_inasistencia
        click.echo(f"Cliente {cliente.id} citas: {total_citas}, asistio {count_citas_asistio}, faltó {count_citas_inasistencia}")  # DEBUG:
        if total_citas == 0:
            if cliente.limite_citas_pendientes == LIMITE_SIN_CITAS:
                if test is False:
                    cliente.limite_citas_pendientes = LIMITE_SIN_CITAS
                    cliente.save()
                mensaje = f"Cliente {cliente.id} sin citas en los últimos {DIAS_MARGEN} días. Se ajustó su límite de citas a {LIMITE_SIN_CITAS}."
                click.echo(mensaje)
                count_clientes_ajustados += 1
        elif (count_citas_asistio * 100) / total_citas >= PORCENTAJE_ASISTENCIA_ACEPTABLE:
            if cliente.limite_citas_pendientes == LIMITE_ASISTENCIA:
                if test is False:
                    cliente.limite_citas_pendientes = LIMITE_ASISTENCIA
                    cliente.save()
                mensaje = f"Cliente {cliente.id} con buena asistencia en los últimos {DIAS_MARGEN} días. Se ajustó su límite de citas a {LIMITE_ASISTENCIA}."
                click.echo(mensaje)
                count_clientes_premiados += 1
        else:
            if cliente.limite_citas_pendientes == LIMITE_INASISTENCIA:
                if test is False:
                    cliente.limite_citas_pendientes = LIMITE_INASISTENCIA
                    cliente.save()
                mensaje = f"Cliente {cliente.id} con mala asistencia en los últimos {DIAS_MARGEN} días. Se ajustó su límite de citas a {LIMITE_INASISTENCIA}."
                click.echo(mensaje)
                count_clientes_penalizados += 1

    mensaje_final = f"Se premiaron {count_clientes_premiados}, se ajustaron {count_clientes_ajustados}, se penalizaron {count_clientes_penalizados} clientes."
    click.echo(mensaje_final)


cli.add_command(agregar)
cli.add_command(cambiar_contrasena)
cli.add_command(eliminar_abandonados)
cli.add_command(definir_boleanos)
cli.add_command(evaluar_asistencia)
