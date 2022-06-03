"""
Lectura de la Base de datos de la versión 1.0
"""
import argparse
import os
import csv
from dotenv import load_dotenv
from numpy import number
from sqlalchemy import text, create_engine
from lib.safe_string import safe_string, safe_text
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
    msg_exec = "SIMULACIÓN" if simulacion else "EJECUCIÓN"
    print("=====================================")
    print(f"=== Migración de datos de v1 a v2 === ({msg_exec})")
    print("=====================================")

    # -- Migración de las Tablas --
    with engine.connect() as connection:
        if args.clientes:
            # Eliminar tabla V2 de clientes 'cit_clientes'.
            if simulacion is False:
                print("- Eliminando la tabla cit_clientes")
                conexion_v2 = db.engine.connect()
                conexion_v2.execute(text("TRUNCATE TABLE cit_clientes CASCADE"))
            # -- Migración de la Tabla 'usuario' -> cit_clientes --
            print("--Migración de la tabla: usuario -> cit_clientes")
            # extraer el número total de registros
            num_registros = 0
            result = connection.execute(text("SELECT COUNT(*) AS total FROM usuario"))
            for row in result:
                num_registros = int(row["total"])
            # leer los registros de la BD v1 de usuarios
            result = connection.execute(
                text(
                    "SELECT id, nombre, apPaterno, apMaterno, celular, email, curp, password \
                FROM usuario \
                WHERE activo = 1 \
                ORDER BY id DESC"
                )
            )
            count_insert = 0
            count_skip = 0
            for row in result:
                # Revisar CURP repetido
                registro = CitCliente.query.filter(CitCliente.curp == row["curp"]).first()
                if registro:
                    print(f"! Registro Omitido - CURP repetido {row['curp']} : [ID:{row['id']}]")
                    count_skip += 1
                    continue
                # Revisar email repetido
                registro = CitCliente.query.filter(CitCliente.email == row["email"]).first()
                if registro:
                    print(f"! Registro Omitido - email repetido {row['email']} : [ID:{row['id']}]")
                    count_skip += 1
                    continue
                # Revisar si existe un nombre
                if safe_string(row["nombre"]) == "":
                    count_skip += 1
                    print(f"! Registro Omitido - falta el nombre: [ID:{row['id']}]")
                    continue
                # Revisar si existe un apellido paterno
                if safe_string(row["apPaterno"]) == "":
                    count_skip += 1
                    print(f"! Registro Omitido - falta el apellido: [ID:{row['id']}]")
                    continue
                # Revisar si existe la CURP
                if safe_string(row["curp"]) == "":
                    count_skip += 1
                    print(f"! Registro Omitido - falta el curp: [ID:{row['id']}]")
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
                # Toma de muestras, para comprobar su funcionamiento
                if count_insert % 200 == 0:
                    porcentaje = 100 - (int(row["id"]) * 100 / num_registros)
                    print(f"({porcentaje:.2f}%) [ID:{row['id']}] =V1= CURP:{safe_string(row['curp'])}, EMAIL:{row['email']} =V2= [ID:{cliente.id}]")
            print(f"= Total de registros insertados {count_insert} de {num_registros}, omitidos {count_skip}")

        # -- Migración de la Tabla 'citas' -> cit_citas --
        if args.citas:
            tabla_parecidos = {
                "TRAMITACION DE OFICIOS / EDICTOS / EXHORTOS": 3,
                "CITAS CON ACTUARIOS": 4,
            }
            # Eliminar tabla V2 de citas 'cit_citas'.
            if simulacion is False:
                print("- Eliminando la tabla cit_citas")
                conexion_v2 = db.engine.connect()
                conexion_v2.execute(text("TRUNCATE TABLE cit_citas CASCADE"))
            print("--Migración de la tabla: citas -> cit_citas")
            # Carga de la relación de Juzgados_id --> Oficinas_id
            ruta = Path(OFICINAS_CSV)
            if not ruta.exists():
                print(f"AVISO: {ruta.name} no se encontró.")
                return
            if not ruta.is_file():
                print(f"AVISO: {ruta.name} no es un archivo.")
                return
            print("Cargando archivo de relación id_juzgados -> oficinas...")
            contador = 0
            oficinas = {}
            with open(ruta, encoding="utf-8") as puntero:
                rows = csv.DictReader(puntero)
                for row in rows:
                    oficina_id = int(row["oficina_id"])
                    oficina_id_v1 = row["id_citas_v1"]
                    if oficina_id_v1.isnumeric() and int(oficina_id_v1) > 0:
                        oficinas[int(oficina_id_v1)] = oficina_id
                        contador += 1
            print(f"-- Oficinas cargadas: {contador}")
            # extraer el número total de registros
            print("- Leyendo Tabla de citas V1")
            num_registros = 0
            result = connection.execute(text("SELECT COUNT(*) AS total FROM citas WHERE fecha >= CURDATE()"))
            for row in result:
                num_registros = int(row["total"])
            print(f"- Registros de citas a procesar de la V1: {num_registros:,} citas a migrar")
            # Lectura de la BD v1, tabla de citas
            citas_v1 = connection.execute(
                text(
                    "SELECT \
                citas.id AS citas_id, id_servicio, citas.correo, id_juzgado,\
                cat_servicios.servicio AS nombre_servicio, fecha, hora, citas.detalles\
                FROM citas\
                JOIN cat_servicios ON cat_servicios.id = citas.id_servicio \
                JOIN juzgados ON juzgados.id = citas.id_juzgado \
                WHERE fecha >= CURDATE()"
                )
            )
            count_insert = 0
            count_skip = 0
            for row in citas_v1:
                # Hacer match con el servicio de la BD v2
                # Comprobar parecido
                nombre_servicio = safe_string(row["nombre_servicio"])
                if nombre_servicio in tabla_parecidos:
                    servicio_v2 = CitServicio.query.filter(CitServicio.id == tabla_parecidos[nombre_servicio]).first()
                else:
                    servicio_v2 = CitServicio.query.filter(CitServicio.descripcion == nombre_servicio).first()
                if servicio_v2 is None:
                    count_skip += 1
                    print(f"! Servicio de la cita NO encontrado: [ID:{row['citas_id']}] = NOM-SERVICIO: {nombre_servicio}")
                    continue
                # Buscar el cliente con este email
                cliente_v2 = CitCliente.query.filter(CitCliente.email == row["correo"]).first()
                if cliente_v2 is None:
                    count_skip += 1
                    print(f"! Cliente de la cita NO encontrado: [ID:{row['citas_id']}] = EMAIL: {row['correo']}")
                    continue
                # Buscar Oficina_id en citas v1.
                if row["id_juzgado"] not in oficinas:
                    count_skip += 1
                    print(f"! Oficina de la cita NO establecida: [ID:{row['citas_id']}] = Juzgado_id: {row['id_juzgado']}")
                    continue
                # Buscar Oficina_id.
                oficina_v2 = Oficina.query.filter(Oficina.id == oficinas[row["id_juzgado"]]).first()
                if oficina_v2 is None:
                    count_skip += 1
                    print(f"! Oficina NO encontrada: [ID:{row['citas_id']}] = Juzgado_id: {row['id_juzgado']}")
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
                # Toma de muestras, para comprobar su funcionamiento
                if count_insert % 100 == 0:
                    porcentaje = int(row["citas_id"]) * 100 / num_registros
                    print(
                        f"({porcentaje:.2f}%) [ID_CITA:{row['citas_id']}] =V1= ID:{row['id_servicio']}, SERVICIO:{row['nombre_servicio']}, EMAIL:{row['correo']}\n\t\
--> =V2= ID:{servicio_v2.id}, SERVICIO:{servicio_v2.descripcion}, EMAIL:{cliente_v2.email}, INI:{cita.inicio}, EDO:{cita.estado}, DETAIL:{cita.notas}"
                    )
            print(f"Total de registros insertados {count_insert}, omitidos {count_skip}")


if __name__ == "__main__":
    main()
