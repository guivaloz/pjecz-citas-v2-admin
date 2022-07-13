"""
Lectura de la Base de datos de la versión 1.0
"""
import argparse
import logging
import os
import csv
from dotenv import load_dotenv
from sqlalchemy import text, create_engine
from lib.safe_string import safe_string, safe_email, safe_curp
from pathlib import Path
from datetime import datetime, timedelta

from citas_admin.app import create_app
from citas_admin.extensions import db

from citas_admin.blueprints.cit_clientes.models import CitCliente
from citas_admin.blueprints.cit_servicios.models import CitServicio
from citas_admin.blueprints.oficinas.models import Oficina
from citas_admin.blueprints.cit_citas.models import CitCita

OFICINAS_CSV = "seed/oficinas_table.csv"


def main():
    """Main function"""

    # Inicializar
    load_dotenv()  # Take environment variables from .env
    app = create_app()
    db.app = app

    # Manejo de un Log
    bitacora = logging.getLogger("migracion")
    bitacora.setLevel(logging.INFO)
    formato = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
    empunadura = logging.FileHandler("migracion_db_v1.log")
    empunadura.setFormatter(formato)
    bitacora.addHandler(empunadura)

    # -- Crear conexión a la BD v1 MySQL
    load_dotenv(".env")  # Se necesita un arhivo .env local para cargar la variable de la BD v1
    ENGINE_V1 = os.getenv("ENGINE_V1", "")  # Ruta de conexión de la BD V1.
    engine = create_engine(ENGINE_V1)

    # Simulacion o ejecucion
    simulacion = True
    parser = argparse.ArgumentParser()
    parser.add_argument("-x", "--exec", help="Ejecutar cambio en la BD", action="store_true")
    parser.add_argument("-cli", "--clientes", help="Migrar tabla de clientes", action="store_true")
    parser.add_argument("-cit", "--citas", help="Migrar tabla de citas", action="store_true")
    args = parser.parse_args()
    if args.exec:
        simulacion = False

    # -- Migración de las Tablas --
    with engine.connect() as connection:
        if args.clientes:
            # Se crea la bitácora de errores de la migración de clientes
            bitacora_clientes_errores = logging.getLogger("errores-clientes")
            bitacora_clientes_errores.setLevel(logging.INFO)
            empunadura_cli = logging.FileHandler(filename="migracion_errores-clientes.log", mode="w")
            bitacora_clientes_errores.addHandler(empunadura_cli)
            bitacora_clientes_errores.info(f"{datetime.now()} - Último reporte de errores de la migración de la tabla de *clientes*")
            # Eliminar tabla V2 de clientes 'cit_clientes'.
            if simulacion is False:
                print("- Eliminando la tabla cit_clientes")
                conexion_v2 = db.engine.connect()
                conexion_v2.execute(text("TRUNCATE TABLE cit_clientes CASCADE"))
                conexion_v2.execute(text("ALTER SEQUENCE cit_clientes_id_seq RESTART WITH 1"))  # Reinicia la Secuencia
            # -- Migración de la Tabla 'usuario' -> cit_clientes --
            bitacora.info("Comienzo de la migración de la tabla: usuario -> cit_clientes")
            # extraer el número total de registros
            num_registros_total = 0
            result = connection.execute(text("SELECT COUNT(*) AS total FROM usuario WHERE activo=1 AND idRol = 1"))
            for row in result:
                num_registros_total = int(row["total"])
            # leer los registros de la BD v1 de usuarios
            result = connection.execute(
                text(
                    "SELECT id, nombre, apPaterno, apMaterno, celular, lower(email) as email, upper(curp) as curp, password \
                FROM usuario \
                WHERE activo = 1 AND idRol = 1\
                ORDER BY id DESC"
                )
            )
            count_insert = 0
            count_error = {
                "email_vacio": 0,
                "email_invalido": 0,
                "email_repetido": 0,
                "curp_vacio": 0,
                "curp_invalido": 0,
                "curp_repetido": 0,
                "nombre_vacio": 0,
                "apellido_paterno_vacio": 0,
            }
            for row in result:
                # Validar email v1
                if row["email"] == "" or row["email"] is None:
                    bitacora_clientes_errores.info(f"EMAIL vacío [ID:{row['id']}]")
                    count_error["email_vacio"] += 1
                    continue
                if safe_email(row["email"]) is None:
                    bitacora_clientes_errores.info(f"EMAIL inválido {row['email']} [ID:{row['id']}]")
                    count_error["email_invalido"] += 1
                    continue
                # Validar CURP v1
                if safe_string(row["curp"]) == "" or row["curp"] is None:
                    bitacora_clientes_errores.info(f"CURP vacío [ID:{row['id']}]")
                    count_error["curp_vacio"] += 1
                    continue
                if safe_curp(row["curp"]) is None:
                    bitacora_clientes_errores.info(f"CURP inválido {row['curp']} [ID:{row['id']}]")
                    count_error["curp_invalido"] += 1
                    continue
                # Revisar CURP repetido
                registro = CitCliente.query.filter(CitCliente.curp == row["curp"]).first()
                if registro:
                    bitacora_clientes_errores.info(f"CURP repetido {row['curp']} [ID:{row['id']}]")
                    count_error["curp_repetido"] += 1
                    continue
                # Revisar email repetido
                registro = CitCliente.query.filter(CitCliente.email == row["email"]).first()
                if registro:
                    bitacora_clientes_errores.info(f"EMAIL repetido {row['email']} [ID:{row['id']}]")
                    count_error["email_repetido"] += 1
                    continue
                # Revisar si existe un nombre
                if safe_string(row["nombre"]) == "":
                    bitacora_clientes_errores.info("NOMBRE vacío [ID:%d]", {row["id"]})
                    count_error["nombre_vacio"] += 1
                    continue
                # Revisar si existe un apellido paterno
                if safe_string(row["apPaterno"]) == "":
                    bitacora_clientes_errores.info("APELLIDO PATERNO vacío [ID:%d]", {row["id"]})
                    count_error["apellido_paterno_vacio"] += 1
                    continue
                # Insertar registro
                count_insert += 1
                cliente = CitCliente(
                    nombres=safe_string(row["nombre"]),
                    apellido_primero=safe_string(row["apPaterno"]),
                    apellido_segundo=safe_string(row["apMaterno"]),
                    curp=safe_string(row["curp"]),
                    email=row["email"],
                    telefono=safe_string(row["celular"]),
                    contrasena_md5=safe_string(row["password"]),
                    contrasena_sha256="",
                    renovacion=datetime.now() + timedelta(days=60),
                )
                if simulacion is False:
                    cliente.save()

            # Da el total de errores encontrados
            sum_errors = 0
            for key, value in count_error.items():
                sum_errors += value
            bitacora.info(f"Total de clientes insertados {count_insert} de {num_registros_total}, omitidos {sum_errors}:{count_error}")
            if sum_errors == 0:
                bitacora_clientes_errores.info("¡¡¡Sin Errores!!!")
            else:
                bitacora_clientes_errores.info(f"Total de errores: {sum_errors}")

        # -- Migración de la Tabla 'citas' -> cit_citas --
        if args.citas:
            # Se crea la bitácora de errores de la migración de citas
            bitacora_citas_errores = logging.getLogger("errores-citas")
            bitacora_citas_errores.setLevel(logging.INFO)
            empunadura_cit = logging.FileHandler(filename="migracion_errores-citas.log", mode="w")
            bitacora_citas_errores.addHandler(empunadura_cit)
            bitacora_citas_errores.info(f"{datetime.now()} - Último reporte de errores de la migración de la tabla de *citas*")
            # Hardcode de las variones de servicios
            tabla_parecidos = {
                "TRAMITACION DE OFICIOS / EDICTOS / EXHORTOS": 3,
                "CITAS CON ACTUARIOS": 4,
            }
            # Eliminar tabla V2 de citas 'cit_citas'.
            if simulacion is False:
                print("- Eliminando la tabla cit_citas")
                conexion_v2 = db.engine.connect()
                conexion_v2.execute(text("TRUNCATE TABLE cit_citas CASCADE"))
                conexion_v2.execute(text("ALTER SEQUENCE cit_citas_id_seq RESTART WITH 1"))  # Reinicia la Secuencia
            # -- Migración de la Tabla 'usuario' -> cit_clientes --
            bitacora.info("Comienzo de la migración de la tabla: citas -> cit_citas")
            # Carga de la relación de Juzgados_id --> Oficinas_id
            ruta = Path(OFICINAS_CSV)
            if not ruta.exists():
                print(f"AVISO: {ruta.name} no se encontró.")
                return
            if not ruta.is_file():
                print(f"AVISO: {ruta.name} no es un archivo.")
                return

            oficinas = {}
            with open(ruta, encoding="utf-8") as puntero:
                rows = csv.DictReader(puntero)
                for row in rows:
                    oficina_id = int(row["oficina_id"])
                    oficina_id_v1 = row["id_citas_v1"]
                    if oficina_id_v1.isnumeric() and int(oficina_id_v1) > 0:
                        oficinas[int(oficina_id_v1)] = oficina_id
            bitacora.info(f"Oficinas cargadas: {len(oficinas)}")
            # extraer el número total de registros
            num_registros_total = 0
            result = connection.execute(text("SELECT COUNT(*) AS total FROM citas WHERE fecha >= CURDATE() AND fecha <= CURDATE() + 90"))
            for row in result:
                num_registros_total = int(row["total"])
            # Lectura de la BD v1, tabla de citas, solo migra las citas a futuro y no mayor a 90 días.
            citas_v1 = connection.execute(
                text(
                    "SELECT \
                citas.id AS citas_id, id_servicio, lower(citas.correo) as correo, id_juzgado,\
                cat_servicios.servicio AS nombre_servicio, fecha, hora, citas.detalles\
                FROM citas\
                JOIN cat_servicios ON cat_servicios.id = citas.id_servicio \
                JOIN juzgados ON juzgados.id = citas.id_juzgado \
                WHERE fecha >= CURDATE() AND fecha <= CURDATE() + 90"
                )
            )
            count_insert = 0
            count_error = {
                "servicio_no_encontrado": 0,
                "email_no_encontrado": 0,
                "oficina_no_establecida": 0,
                "oficina_no_encontrada": 0,
            }
            for row in citas_v1:
                # Hacer match con el servicio de la BD v2
                # Comprobar parecido
                nombre_servicio = safe_string(row["nombre_servicio"])
                if nombre_servicio in tabla_parecidos:
                    servicio_v2 = CitServicio.query.filter(CitServicio.id == tabla_parecidos[nombre_servicio]).first()
                else:
                    servicio_v2 = CitServicio.query.filter(CitServicio.descripcion == nombre_servicio).first()
                if servicio_v2 is None:
                    count_error["servicio_no_encontrado"] += 1
                    bitacora_citas_errores.info("Servicio de la cita NO encontrado, id=%d. NOM-SERVICIO:%s", row["citas_id"], nombre_servicio)
                    continue
                # Buscar el cliente con este email
                cliente_v2 = CitCliente.query.filter(CitCliente.email == row["correo"]).first()
                if cliente_v2 is None:
                    count_error["email_no_encontrado"] += 1
                    bitacora_citas_errores.info("Cliente de la cita NO encontrado, id=%d. EMAIL:%s", row["citas_id"], row["correo"])
                    continue
                # Buscar Oficina_id en citas v1.
                if row["id_juzgado"] not in oficinas:
                    count_error["oficina_no_establecida"] += 1
                    bitacora_citas_errores.info("Oficina NO establecida, id=%d. Juzgado_id:%d", row["citas_id"], row["id_juzgado"])
                    continue
                # Buscar Oficina_id.
                oficina_v2 = Oficina.query.filter(Oficina.id == oficinas[row["id_juzgado"]]).first()
                if oficina_v2 is None:
                    count_error["oficina_no_encontrada"] += 1
                    bitacora_citas_errores.info("Oficina NO encontrada, id=%d. Juzgado_id:%d", row["citas_id"], row["id_juzgado"])
                    continue
                # Insertar la cita v2
                count_insert += 1
                fecha_inicio_str = f"{row['fecha']} {row['hora']}"
                fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d %H:%M:%S")
                cita = CitCita(
                    cit_servicio_id=servicio_v2.id,
                    cit_cliente_id=cliente_v2.id,
                    oficina_id=oficinas[row["id_juzgado"]],
                    inicio=fecha_inicio,
                    termino=fecha_inicio + timedelta(minutes=30),
                    notas=row["detalles"],
                    estado="PENDIENTE",
                    asistencia=None,
                )
                if simulacion == False:
                    cita.save()
            # Da el total de errores encontrados
            sum_errors = 0
            for key, value in count_error.items():
                sum_errors += value
            bitacora.info(f"Total de citas insertadas {count_insert} de {num_registros_total}, omitidos {sum_errors}:{count_error}")
            if sum_errors == 0:
                bitacora_citas_errores.info("¡¡¡Sin Errores!!!")
            else:
                bitacora_citas_errores.info(f"Total de errores: {sum_errors}")


if __name__ == "__main__":
    main()
