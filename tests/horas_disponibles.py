"""
Lectura de la Base de datos de la versión 1.0
"""
from dotenv import load_dotenv
from datetime import date, timedelta, datetime

from citas_admin.app import create_app
from citas_admin.extensions import db

from citas_admin.blueprints.distritos.models import Distrito
from citas_admin.blueprints.oficinas.models import Oficina
from citas_admin.blueprints.cit_servicios.models import CitServicio
from citas_admin.blueprints.cit_oficinas_servicios.models import CitOficinaServicio
from citas_admin.blueprints.cit_dias_inhabiles.models import CitDiaInhabil

def main():
    """Main function"""

    # Inicializar
    load_dotenv()  # Take environment variables from .env
    app = create_app()
    db.app = app

    print("======================================================")
    print("=== SIMULACIÓN DE API ENTREGANDO HORAS-DISPONIBLES ===")
    print("======================================================")
    print("")

    # Listar los distritos diponibles
    distrito = None
    distritos = Distrito.query.filter(Distrito.estatus == "A").all()
    print("--- Listado de Distritos ---")
    print("- ID | Nombre              -")
    print("----------------------------")
    for distrito in distritos:
        print(f" {distrito.id:>3} | {distrito.nombre_corto}")
    print("----------------------------")
    while True:
        distrito_id = int(input("Seleccione un distrito ID: "))
        distrito = Distrito.query.get(distrito_id)
        if distrito:
            print(f" ID: {distrito.id} : {distrito.nombre_corto}")
            break
        else:
            print("! Distrito inválido, seleccione otro.")

    # Listar los Oficinas del Distrito Seleccionado
    oficina = None
    oficinas = Oficina.query.filter(Oficina.distrito_id == distrito_id).filter(Oficina.estatus == "A").all()
    oficinas_disponibles = []
    print("--- Listado de Oficinas ------")
    print(f"- ID | {'Clave':<16} | {'Nombre':<30} -")
    print(f"{'':-^60}")
    for oficina in oficinas:
        print(f" {oficina.id:>3} | {oficina.clave:<16} | {oficina.descripcion_corta}")
        oficinas_disponibles.append(oficina.id)
    print(f"{'':-^60}")
    while True:
        oficina_id = int(input("Seleccione una Oficina ID: "))
        if oficina_id in oficinas_disponibles:
            oficina = Oficina.query.get(oficina_id)
            if oficina:
                print(f" ID: {oficina.id} : {oficina.clave} | {oficina.descripcion_corta}")
                break
        else:
            print("! Oficina inválida, seleccione otra.")

    # Listar los servicios de la Oficina Seleccionada
    cit_servicio = None
    cit_servicios = CitServicio.query.join(CitOficinaServicio).filter(CitOficinaServicio.oficina_id == oficina_id).filter(CitServicio.estatus == "A").all()
    cit_servicios_disponibles = []
    print("--- Listado de Servicios ------")
    print(f"- ID | {'Clave':<16} | {'Nombre':<30} -")
    print(f"{'':-^60}")
    for cit_servicio in cit_servicios:
        print(f" {cit_servicio.id:>3} | {cit_servicio.clave:<16} | {cit_servicio.descripcion}")
        cit_servicios_disponibles.append(cit_servicio.id)
    print(f"{'':-^60}")
    while True:
        cit_servicio_id = int(input("Seleccione un Servicio ID: "))
        if cit_servicio_id in cit_servicios_disponibles:
            cit_servicio = CitServicio.query.get(cit_servicio_id)
            if cit_servicio:
                print(f" ID: {cit_servicio.id} : {cit_servicio.clave} | {cit_servicio.descripcion}")
                break
        else:
            print("! Servicio inválido, seleccione otro.")

    # Listar fechas disponibles
    LIMITE_DIAS = 90
    fecha = None
    dias_disponibles = []
    # consultar días inhábiles
    dias_inhabiles_obj = CitDiaInhabil.query.filter(CitDiaInhabil.fecha > date.today()).filter(CitDiaInhabil.estatus == "A").all()
    dias_inhabiles = [item.fecha for item in dias_inhabiles_obj]
    # Agregar cada día hasta el límite desde el día de mañana.
    for fecha in (date.today() + timedelta(n) for n in range(1, LIMITE_DIAS)):
        # Quitar los Sábados y Domingos
        if fecha.weekday() in (5,6):
            continue
        # Quitar los días inhábiles
        if fecha in dias_inhabiles:
            continue
        # Acumular
        dias_disponibles.append(fecha)
    print("--- Listado de Días Hábiles ------")
    print("- Fecha -")
    print("------------")
    col = 0
    for dia in dias_disponibles:
        print(f" {dia}", end ="\t")
        col += 1
        if col > 4:
            print()
            col = 0
    print()
    print("------------")
    while True:
        fecha_str = input("Seleccione una Fecha (YYYY-MM-DD):")
        print(fecha_str)
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
        if fecha in dias_disponibles:
            print(f" Día Seleccionado: {fecha_str}")
            break
        else:
            print("! Fecha inválida, seleccione otra.")

    # Listar horas disponibles
    hora = None
    horas_disponibles = []
    # consultar días inhábiles


    # Impresión de los valores seleccionados
    print(f"{'':-^60}")
    print("--- Cita Programada con éxito ---")
    print(f"Distrito: {distrito.nombre_corto}")
    print(f"Oficina: {oficina.clave} | {oficina.descripcion_corta}")
    print(f"Servicio: {cit_servicio.clave} | {oficina.descripcion}")
    print(f"Fecha: {fecha.strftime('%Y-%m-%d')}, Hora: {hora}")
    print(f"{'':-^60}")

if __name__ == "__main__":
    main()
