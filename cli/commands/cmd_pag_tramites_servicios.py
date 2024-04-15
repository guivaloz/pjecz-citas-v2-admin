"""
Pagos Tramites y Servicios

- alimentar
"""

from pathlib import Path

import csv
import click

from lib.safe_string import safe_clave, safe_string
from citas_admin.app import create_app
from citas_admin.extensions import database
from citas_admin.blueprints.pag_tramites_servicios.models import PagTramiteServicio

app = create_app()
app.app_context().push()
database.app = app


@click.group()
def cli():
    """Pagos Tramites y Servicios"""


@click.command()
@click.argument("entrada_csv")
def alimentar(entrada_csv):
    """Alimentar a partir de un archivo CSV"""
    ruta = Path(entrada_csv)
    if not ruta.exists():
        click.echo(f"AVISO: {ruta.name} no se encontró.")
        return
    if not ruta.is_file():
        click.echo(f"AVISO: {ruta.name} no es un archivo.")
        return
    click.echo("Alimentando tramites y servicios...")
    contador = 0
    with open(ruta, encoding="utf8") as puntero:
        rows = csv.DictReader(puntero)
        for row in rows:
            PagTramiteServicio(
                clave=safe_clave(row["clave"]),
                descripcion=safe_string(row["descripcion"], to_uppercase=True, save_enie=True),
                costo=float(row["costo"]),
                url=row["url"],
                estatus=row["estatus"],
            ).save()
            contador += 1
            if contador % 100 == 0:
                click.echo(f"  Van {contador}...")
    click.echo(f"{contador} tramites y servicios alimentados.")


cli.add_command(alimentar)
