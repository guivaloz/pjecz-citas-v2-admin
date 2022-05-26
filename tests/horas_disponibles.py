"""
Lectura de la Base de datos de la versión 1.0
"""
from dotenv import load_dotenv
from datetime import date, timedelta

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
    if False:
        # Listar los distritos diponibles
        distritos = Distrito.query.filter(Distrito.estatus == "A").all()
        print("--- Listado de Distritos ---")
        print("- ID | Nombre              -")
        print("----------------------------")
        for distrito in distritos:
            print(f" {distrito.id:>3} | {distrito.nombre_corto}")
        print("----------------------------")
        distrito_id = input("Seleccione un distrito ID: ")

        # Listar los Oficinas del Distrito Seleccionado
        oficinas = Oficina.query.filter(Oficina.distrito_id == distrito_id).filter(Oficina.estatus == "A").all()
        print("--- Listado de Oficinas ------")
        print(f"- ID | {'Clave':<16} | {'Nombre':<30} -")
        print(f"{'':-^60}")
        for oficina in oficinas:
            print(f" {oficina.id:>3} | {oficina.clave:<16} | {oficina.descripcion_corta}")
        print(f"{'':-^60}")
        oficina_id = input("Seleccione una oficina ID: ")

        # Listar los servicios de la Oficina Seleccionada
        cit_servicios = CitServicio.query.join(CitOficinaServicio).filter(CitOficinaServicio.oficina_id == oficina_id).filter(CitServicio.estatus == "A").all()
        print("--- Listado de Servicios ------")
        print(f"- ID | {'Clave':<16} | {'Nombre':<30} -")
        print(f"{'':-^60}")
        for cit_servicio in cit_servicios:
            print(f" {cit_servicio.id:>3} | {cit_servicio.clave:<16} | {cit_servicio.descripcion}")
        print(f"{'':-^60}")
        cit_servicio_id = input("Seleccione un Servicio ID: ")

    # Listar fechas disponibles
    LIMITE_DIAS = 90
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
        if col > 5:
            print()
            col = 0
    print()
    print("------------")
    fecha = input("Seleccione una Fecha (YYYY-MM-DD): ")



if __name__ == "__main__":
    main()
