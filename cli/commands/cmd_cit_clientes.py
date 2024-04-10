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
from tabulate import tabulate
from sqlalchemy import text, update

from lib import database
from lib.pwgen import generar_contrasena
from lib.safe_string import safe_string

from citas_admin.app import create_app
from citas_admin.extensions import database, pwd_context

from citas_admin.blueprints.cit_clientes.models import CitCliente
from citas_admin.blueprints.cit_citas.models import CitCita
from citas_admin.blueprints.pag_pagos.models import PagPago

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

    # Mensaje final
    click.echo(f"Se ha creado el cliente {email} con contraseña {contrasena}")


@click.command()
@click.argument("email", type=str)
def cambiar_contrasena(email):
    """Cambiar contraseña de un cliente"""

    # Consultar el cliente
    cit_cliente = CitCliente.query.filter_by(email=email).first()
    if cit_cliente is None:
        click.echo(f"No existe el e-mail {email} en cit_clientes")
        return

    # Preguntar la nueva contraseña
    contrasena_1 = input("Contraseña: ").strip()
    contrasena_2 = input("De nuevo la misma contraseña: ").strip()

    # Validar que las contraseñas coincidan
    if contrasena_1 != contrasena_2:
        click.echo("No son iguales las contraseñas. Por favor intente de nuevo.")
        return

    # Actualizar la contraseña
    cit_cliente.contrasena_md5 = ""
    cit_cliente.contrasena_sha256 = pwd_context.hash(contrasena_1)
    cit_cliente.save()

    # Mensaje final
    click.echo(f"Se ha cambiado la contraseña de {email} en usuarios")


@click.command()
@click.option("--test", default=True, help="Modo de pruebas en el que no se guardan los cambios")
def eliminar_abandonados(test):
    """Eliminar clientes sin contraseña y sin citas"""
    click.echo("Eliminar clientes sin contraseña y sin citas")

    # Inicializar el engine para ejecutar comandos SQL
    engine = database.engine

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

    else:  # Modo de realizar cambios

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
    """Eliminar clientes sin citas en un periodo de tiempo"""
    click.echo("Eliminar clientes sin citas en un periodo de tiempo")

    # Inicializar el engine para ejecutar comandos SQL
    engine = database.engine

    # Si esta en modo de pruebas, no se guardan los cambios
    if test is True:  # Modo de pruebas

        # Definir valores por defecto
        cantidad = 0
        creado_hasta = ""

        # Obtener la cantidad de clientes que se podrían eliminar
        count_query = text(
            f"SELECT COUNT(*) AS cantidad, current_date - {dias} AS creado_hasta \
                FROM cit_clientes AS cli \
                LEFT JOIN cit_citas AS cit \
                    ON cli.id = cit.cit_cliente_id \
                LEFT JOIN pag_pagos AS pag \
                    ON cli.id = pag.cit_cliente_id \
                WHERE cit.cit_cliente_id IS NULL \
                    AND pag.cit_cliente_id IS NULL\
                    AND cli.creado <= now() - INTERVAL '{dias} day'"
        )
        resultado = engine.execute(count_query)
        if resultado:
            renglon = resultado.fetchone()
            cantidad = renglon["cantidad"]
            creado_hasta = renglon["creado_hasta"]

        # Mostrar el resultado
        click.echo(
            f"MODO DE PRUEBAS: Se podrían eliminar {cantidad} clientes sin citas que se crearon a partir del {creado_hasta}"
        )

    else:  # Modo de realizar cambios

        # Definir creacion para limitar los clientes a eliminar
        creado_hasta = datetime.now() - timedelta(days=dias)

        # Consultar los clientes que se van a eliminar
        db = database.SessionLocal()
        results = (
            db.query(CitCliente, CitCita, PagPago)
            .outerjoin(CitCita)
            .outerjoin(PagPago)
            .filter(CitCita.cit_cliente_id == None)
            .filter(PagPago.cit_cliente_id == None)
            .filter(CitCliente.creado <= creado_hasta)
            .all()
        )

        # Inicializar el engine
        engine = database.engine

        # Bucle para eliminar
        contador = 0
        for cliente, _, _ in results:

            # Eliminar recuperaciones
            cit_cilente_recuperacion_borrar = text(
                f"DELETE \
                    FROM cit_clientes_recuperaciones \
                    WHERE cit_cliente_id = {cliente.id}"
            )
            engine.execute(cit_cilente_recuperacion_borrar)

            # Eliminar cliente
            sql = text(f"DELETE FROM {CitCliente.__tablename__} WHERE id = {cliente.id};")
            engine.execute(sql)

            # Contador
            contador += 1

        # Mensaje final
        click.echo(f"Se eliminaron {contador} clientes por no tener citas.")


@click.command()
@click.option("--dias", default=30, help="Días para contar las citas", type=int)
@click.option("--test", default=True, help="Modo de pruebas en el que no se guardan los cambios")
def cambiar_enviar_boletin_verdadero(dias, test):
    """Pone en verdadero enviar_boletin a los clientes con citas recientes"""
    click.echo("Pone en verdadero enviar_boletin a los clientes con citas recientes")

    # Consultar clientes y citas
    consulta = database.SessionLocal().query(CitCliente.id, CitCliente.email).select_from(CitCliente).join(CitCita)

    # Filtrar por los que han tenido citas en los últimos días
    consulta = consulta.filter(CitCita.creado >= datetime.now() - timedelta(days=dias))

    # Filtrar citas que no han sido canceladas
    consulta = consulta.filter(CitCita.estado != "CANCELO")

    # Filtrar clientes que NO tienen enviar_boletin en verdadero
    consulta = consulta.filter(CitCliente.enviar_boletin == False)

    # Filtrar clientes que autorizan el envío de boletines
    consulta = consulta.filter(CitCliente.autoriza_mensajes == True)

    # Filtrar clientes activos
    consulta = consulta.filter(CitCliente.estatus == "A")

    # Ordenar por id
    consulta = consulta.order_by(CitCliente.id)

    # Unicos
    consulta = consulta.distinct()

    # Si no hay clientes, terminar
    if consulta.count() == 0:
        click.echo("No hay clientes con citas recientes")
        return

    # Modo de pruebas, se muestran los clientes con tabulate
    if test is True:
        datos = []
        for cliente in consulta.all():
            datos.append(
                [
                    cliente.id,
                    cliente.email,
                ]
            )
        click.echo(tabulate(datos, headers=["ID", "e-mail", "A.M.", "E.B."]))
        click.echo(f"Se encontraron {len(datos)} clientes con citas recientes")
        return

    # Actualizar los cliente con enviar_boletin en verdadero
    contador = 0
    for cliente in consulta.all():
        cit_cliente = CitCliente.query.get(cliente.id)
        cit_cliente.enviar_boletin = True
        cit_cliente.save()
        contador += 1
    click.echo(f"Se actualizaron {contador} clientes con enviar_boletin en verdadero")


@click.command()
@click.option("--dias", default=30, help="Días para contar las citas", type=int)
@click.option("--test", default=True, help="Modo de pruebas en el que no se guardan los cambios")
def cambiar_enviar_boletin_falso(dias, test):
    """Pone en falso enviar_boletin a TODOS los clientes"""
    click.echo("Pone en falso enviar_boletin a TODOS los clientes")

    # Modo de pruebas, se muestra la cantidad de clientes
    if test is True:
        cit_clientes = CitCliente.query.filter(CitCliente.estatus == "A").filter(CitCliente.enviar_boletin == True)
        click.echo(f"Se encontraron {cit_clientes.count()} clientes con enviar_boletin en verdadero")
        return

    # Inicializar el engine para ejecutar comandos SQL
    engine = database.engine

    # Actualizar los cliente con enviar_boletin en falso
    comando = (
        update(CitCliente)
        .where(CitCliente.estatus == "A")
        .filter(CitCliente.enviar_boletin == True)
        .values(enviar_boletin=False)
    )
    resultado = engine.execute(comando)
    click.echo(f"Se actualizaron {resultado.rowcount} clientes con enviar_boletin en falso")


cli.add_command(agregar)
cli.add_command(cambiar_contrasena)
cli.add_command(cambiar_enviar_boletin_verdadero)
cli.add_command(cambiar_enviar_boletin_falso)
cli.add_command(eliminar_abandonados)
cli.add_command(eliminar_sin_cita)
