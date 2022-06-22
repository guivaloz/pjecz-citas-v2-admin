"""
Respaldar Cit Tramites Servicios
"""
from pathlib import Path
import csv
import click

from citas_admin.blueprints.cit_tramites_servicios.models import CitTramiteServicio


def respaldar_cit_tramites_servicios(salida: str = "cit_tramites_servicios.csv"):
    """Respaldar Citas Tramites y Servicios a un archivo CSV"""
    ruta = Path(salida)
    if ruta.exists():
        click.echo(f"AVISO: {salida} existe, no voy a sobreescribirlo.")
        return
    click.echo("Respaldando Tramites y Servicios de las citas...")
    contador = 0
    id = 1
    servicios = CitTramiteServicio.query.filter(CitTramiteServicio.estatus == "A").order_by(CitTramiteServicio.id).all()
    with open(ruta, "w", encoding="utf8") as puntero:
        respaldo = csv.writer(puntero)
        respaldo.writerow(
            [
                "cit_tramite_servicio_id",
                "nombre",
                "costo",
                "url",
            ]
        )
        for servicio in servicios:
            respaldo.writerow(
                [
                    id,
                    servicio.nombre,
                    servicio.costo,
                    servicio.url,
                ]
            )
            id += 1
            contador += 1
            if contador % 100 == 0:
                click.echo(f"  Van {contador}...")
    click.echo(f"  {contador} en {ruta.name}")
