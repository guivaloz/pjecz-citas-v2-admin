"""
Cit Clientes

- agregar: Agregar un nuevo cliente
- cambiar_contrasena: Cambiar contraseña de un cliente
- eliminar_abandonados: Eliminar los clientes que han abandonado su cuenta
- definir_booleanos: Define los booleanos es_adulto_mayor, es_mujer, etc
"""
from datetime import datetime, timedelta
import click
from sqlalchemy import delete, text
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
    """Eliminar los clientes que han abandonado su cuenta"""
    click.echo("Eliminación de cuentas de Clientes abandonados")
    count_cit_clientes = CitCliente.query.outerjoin(CitCita).filter(CitCliente.contrasena_sha256 == "").filter(CitCita.cit_cliente == None).count()
    click.echo(f"Se encontraron {count_cit_clientes} cuentas de clientes sin contraseña SHA256 y sin citas agendadas, posiblemente son cuentas abandonadas.")

    if test is False:
        engine = db.engine
        borrado = text(
            "DELETE \
                FROM cit_clientes AS cli \
                LEFT JOIN cit_citas AS cit ON cli.id = cit.cit_cliente_id \
                WHERE cli.contrasena_sha256 = '' AND cit.cit_cliente_id IS NULL"
        )
        res = engine.execute(borrado)
        for row in res:
            print(row)
        click.echo("¡Eliminación de registros correctamente!")
    else:
        click.echo("Para eliminar permanentemente los registros, utilize el parámetro --test false")


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


cli.add_command(agregar)
cli.add_command(cambiar_contrasena)
cli.add_command(eliminar_abandonados)
cli.add_command(definir_boleanos)
