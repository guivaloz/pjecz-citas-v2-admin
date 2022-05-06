"""
Respaldar Citas Servicios
"""
from pathlib import Path
import csv
import click

from citas_admin.blueprints.cit_servicios.models import CitServicio


def respaldar_cit_servicios(salida: str = "cit_servicios.csv"):
    """Respaldar Citas Servicios a un archivo CSV"""
    ruta = Path(salida)
    if ruta.exists():
        click.echo(f"AVISO: {salida} existe, no voy a sobreescribirlo.")
        return
    click.echo("Respaldando servicios de las citas...")
    contador = 0
    servicios = CitServicio.query.order_by(CitServicio.id).all()
    with open(ruta, "w", encoding="utf8") as puntero:
        respaldo = csv.writer(puntero)
        respaldo.writerow(
            [
                "cit_servicio_id",
                "clave",
                "nombre",
                "solicitar_expedientes",
                "duracion",
                "estatus",
            ]
        )
        for servicio in servicios:
            respaldo.writerow(
                [
                    servicio.id,
                    servicio.clave,
                    servicio.nombre,
                    1 if servicio.solicitar_expedientes else 0,
                    servicio.duracion,
                    servicio.estatus,
                ]
            )
            contador += 1
            if contador % 100 == 0:
                click.echo(f"  Van {contador}...")
    click.echo(f"  {contador} en {ruta.name}")
