"""
Respaldar Pagos Tramites y Servicios
"""
from pathlib import Path
import csv
import click

from citas_admin.blueprints.pag_tramites_servicios.models import PagTramiteServicio


def respaldar_pag_tramites_servicios(salida: str = "cit_tramites_servicios.csv"):
    """Respaldar Tramites y Servicios a un archivo CSV"""
    ruta = Path(salida)
    if ruta.exists():
        click.echo(f"AVISO: {salida} existe, no voy a sobreescribirlo.")
        return
    click.echo("Respaldando Tramites y Servicios...")
    contador = 0
    id = 1
    servicios = PagTramiteServicio.query.filter(PagTramiteServicio.estatus == "A").order_by(PagTramiteServicio.id).all()
    with open(ruta, "w", encoding="utf8") as puntero:
        respaldo = csv.writer(puntero)
        respaldo.writerow(
            [
                "cit_tramite_servicio_id",
                "clave",
                "descripcion",
                "costo",
                "url",
                "estatus",
            ]
        )
        for servicio in servicios:
            respaldo.writerow(
                [
                    id,
                    servicio.clave,
                    servicio.descripcion,
                    servicio.costo,
                    servicio.url,
                    servicio.estatus,
                ]
            )
            id += 1
            contador += 1
            if contador % 100 == 0:
                click.echo(f"  Van {contador}...")
    click.echo(f"  {contador} en {ruta.name}")
