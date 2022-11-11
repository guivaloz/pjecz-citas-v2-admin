"""
Cit Clientes

- agregar: Agregar un nuevo cliente
- cambiar_contrasena: Cambiar contraseña de un cliente
- eliminar_abandonados: Eliminar los clientes que han abandonado su cuenta
- definir_booleanos: Define los booleanos es_adulto_mayor, es_mujer, etc
- evaluar_asistencia: Penaliza o Premia al cliente dependiendo de su asistencia
"""
from datetime import datetime, timedelta
import click
from sqlalchemy import text

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
        limite_citas_pendientes=5,
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

    # Inicializar el engine para ejecutar comandos SQL
    engine = db.engine

    # Si esta en modo de pruebas, no se guardan los cambios
    if test is True:
        # Modo de pruebas
        count_query = text(
            "SELECT COUNT(*) AS cantidad\
                FROM cit_clientes AS cli \
                WHERE cli.id NOT IN (SELECT cit_cliente_id FROM cit_citas WHERE cit_cliente_id = cli.id) \
                    AND cli.id NOT IN (SELECT cit_cliente_id FROM cit_clientes_recuperaciones WHERE cit_cliente_id = cli.id AND estatus = 'A') \
                    AND cli.contrasena_sha256 = ''"
        )
        res = engine.execute(count_query)
        count_cit_clientes = 0
        if res:
            for cantidad in res.columns("cantidad"):
                count_cit_clientes = cantidad[0]
        click.echo(f"MODO DE PRUEBAS: Se podrían eliminar {count_cit_clientes} clientes")

    else:
        # Modo de realizar cambios

        # Borrado de recuperaciones
        borrado = text(
            "DELETE \
                FROM cit_clientes_recuperaciones \
                WHERE estatus = 'B'"
        )
        res = engine.execute(borrado)

        # Borrado de clientes sin SHA256 y sin citas
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


@click.command()
@click.option("--dias", default=30, help="Días de creación de la cuenta", type=int)
@click.option("--test", default=True, help="Modo de pruebas en el que no se guardan los cambios")
def eliminar_sin_cita(dias, test):
    """Eliminar clientes que nunca han agendado una cita"""
    click.echo("== Eliminación de Clientes sin citas Agendadas ==")

    # Inicializar el engine para ejecutar comandos SQL
    engine = db.engine

    # Si esta en modo de pruebas, no se guardan los cambios
    if test is True:
        # Modo de pruebas
        count_query = text(
            f"SELECT COUNT(*) AS cantidad, current_date - {dias} AS fecha_creacion \
                FROM cit_clientes AS cli \
                LEFT JOIN cit_citas AS cit \
                ON cli.id = cit.cit_cliente_id \
                WHERE cit.cit_cliente_id IS NULL \
                AND cli.creado <= now() - INTERVAL '{dias} day'"
        )
        res = engine.execute(count_query)
        count_cit_clientes = 0
        fecha_creacion = ""
        if res:
            for row in res:
                count_cit_clientes = row["cantidad"]
                fecha_creacion = row["fecha_creacion"]
        click.echo(f"MODO DE PRUEBAS: Se podrían eliminar {count_cit_clientes} clientes que se crearon a partir del {fecha_creacion}")

    else:  # Modo de realizar cambios
        # Agregar tarea en el fondo
        app.task_queue.enqueue(
            "citas_admin.blueprints.cit_clientes.tasks.eliminar_sin_citas",
            dias=dias,
        )


@click.command()
@click.option("--test", default=True, help="Modo de pruebas en el que no se guardan los cambios")
def evaluar_asistencia(test):
    """Penaliza o Premia al cliente dependiendo de su asistencia"""
    click.echo("Penaliza o Premia al cliente dependiendo de su asistencia")

    # Agregar tarea en el fondo
    app.task_queue.enqueue(
        "citas_admin.blueprints.cit_clientes.tasks.evaluar_asistencia",
        test=test,
    )

    # Mostrar mensaje de Prueba o Ejecución
    if test is True:
        click.echo("MODO DE PRUEBAS")
    else:
        click.echo("Se han cambiado el número de citas de los clientes buenos y malos")

    # Mostrar mensaje de termino
    click.echo("Revise cit_clientes.log para ver los detalles de las operaciones realizadas")


cli.add_command(agregar)
cli.add_command(cambiar_contrasena)
cli.add_command(eliminar_abandonados)
cli.add_command(eliminar_sin_cita)
cli.add_command(definir_boleanos)
cli.add_command(evaluar_asistencia)
