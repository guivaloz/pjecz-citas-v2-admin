"""
Lectura de la Base de datos de la versión 1.0
"""
import argparse
from dotenv import load_dotenv
from sqlalchemy import text, create_engine
from lib.safe_string import safe_string, safe_text
import os

from citas_admin.app import create_app
from citas_admin.extensions import db

from citas_admin.blueprints.cit_dias_inhabiles.models import CitDiaInhabil
from citas_admin.blueprints.cit_horas_bloqueadas.models import CitHoraBloqueada
from citas_admin.blueprints.cit_clientes.models import CitCliente


def main():
    """Main function"""

    # Inicializar
    load_dotenv()  # Take environment variables from .env
    app = create_app()
    db.app = app

    # -- Crear conexión a la BD v1 MySQL
    DB_USER = "pjeczadmin"
    DB_PASS = "papasytomates"
    DB_HOST = os.getenv("DB_HOST", "")
    engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/citas_v1")

    # Simulacion o ejecucion
    simulacion = True
    parser = argparse.ArgumentParser()
    parser.add_argument("-x", "--exec", help="Ejecutar cambio en la BD", action="store_true")
    args = parser.parse_args()
    if args.exec:
        simulacion = False
    msg_exec = "SIMULACIÓN" if simulacion else "EJECUCIÓN"
    print(f"=====================================")
    print(f"=== Migración de datos de v1 a v2 === ({msg_exec})")
    print(f"=====================================")

    # -- Migración de las Tablas --
    with engine.connect() as connection:
        # -- Migración de la Tabla 'Días inhábiles' -> cit_dias_inhabiles --
        result = connection.execute(text("select fecha from diasInhabiles"))
        print("--Migración de la tabla - diasInhabiles")
        count_insert = 0
        count_skip = 0
        for row in result:
            registro = CitDiaInhabil.query.filter(CitDiaInhabil.fecha == row["fecha"]).first()
            if registro:
                print(f"! Registro Omitido - Fecha ya ocupada {row['fecha']}")
                count_skip += 1
            else:
                if simulacion == False:
                    registro_insert = CitDiaInhabil(
                        fecha=row["fecha"],
                    ).save()
                count_insert += 1
        print(f"Total de registros insertados {count_insert}, omitidos {count_skip}")

        # -- Migración de la Tabla 'Horas Bloqueadas' -> cit_horas_bloqueadas --
        # TODO: identificar el juzgado y referenciarlo como oficina.
        result = connection.execute(text("SELECT id, id_juzgado, fecha, hora, activo FROM horasBloqueadas WHERE fecha >= CURDATE()"))
        print("--Migración de la tabla - horasBloqueadas")
        count_insert = 0
        count_skip = 0
        for row in result:
            registro = CitHoraBloqueada.query.filter(CitHoraBloqueada.fecha == row["fecha"]).filter(CitHoraBloqueada.inicio == row["hora"]).first()
            if registro:
                print(f"! Registro Omitido - Fecha ya ocupada {row['fecha']}, {row['hora']} : [ID:{row['id']}]")
                count_skip += 1
            else:
                count_insert += 1
        print(f"Total de registros insertados {count_insert}, omitidos {count_skip}")

        # -- Migración de la Tabla 'usuario' -> cit_clientes --
        result = connection.execute(text("SELECT id, nombre, apPaterno, apMaterno, celular, email, curp, password FROM usuario"))
        print("--Migración de la tabla - usuario -> cit_clientes")
        count_insert = 0
        count_skip = 0
        for row in result:
            registro = CitCliente.query.filter(CitCliente.curp == row["curp"]).first()
            if registro:
                print(f"! Registro Omitido - CURP repetido {row['curp']} : [ID:{row['id']}]")
                count_skip += 1
            else:
                registro = CitCliente.query.filter(CitCliente.curp == row["email"]).first()
                if registro:
                    print(f"! Registro Omitido - email repetido {row['email']} : [ID:{row['id']}]")
                    count_skip += 1
                else:
                    if simulacion is False:
                        cliente = CitCliente(
                            nombres=safe_string(row["nombre"]),
                            apellido_primero=safe_string(row["apPaterno"]),
                            apellido_segundo=safe_string(row["apMaterno"]),
                            curp=safe_string(row["curp"]),
                            email=safe_string(row["email"]),
                            telefono=safe_string(row["celular"]),
                            contrasena_md5=safe_string(row["password"]),
                        ).save()
                    count_insert += 1
        print(f"Total de registros insertados {count_insert}, omitidos {count_skip}")

        # -- Migración de la Tabla 'usuario' -> cit_clientes --


if __name__ == "__main__":
    main()
