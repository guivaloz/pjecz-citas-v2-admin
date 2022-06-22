"""
Alimentar Cit Servicios
"""
from pathlib import Path
import csv
import click

from lib.safe_string import safe_string, safe_url

from citas_admin.blueprints.cit_tramites_servicios.models import CitTramiteServicio

ARCHIVO_CSV = "seed/cit_tramites_servicios.csv"


def alimentar_cit_tramites_servicios():
    """Alimentar Tramites y Servicios de las Citas"""
    ruta = Path(ARCHIVO_CSV)
    if not ruta.exists():
        click.echo(f"AVISO: {ruta.name} no se encontró.")
        return
    if not ruta.is_file():
        click.echo(f"AVISO: {ruta.name} no es un archivo.")
        return
    click.echo("Alimentando tramites y servicios de las citas...")
    contador = 0
    with open(ruta, encoding="utf-8") as puntero:
        rows = csv.DictReader(puntero)
        for row in rows:
            servicio_id = int(row["cit_tramite_servicio_id"])
            if servicio_id != contador + 1:
                click.echo(f"  AVISO: cit_tramite_servicio_id {servicio_id} no es consecutivo")
                continue
            CitTramiteServicio(
                nombre=safe_string(row["nombre"], max_len=64, do_unidecode=False),
                costo=float(row["costo"]),
                url=safe_url(row["url"]),
                estatus=row["estatus"],
            ).save()
            contador += 1
            if contador % 100 == 0:
                click.echo(f"  Van {contador}...")
    click.echo(f"  {contador} tramites y servicios de las citas alimentados")
