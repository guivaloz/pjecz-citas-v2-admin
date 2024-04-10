"""
Tres de Tres - Partidos

- alimentar: Alimentar los partidos a partir de un archivo CSV
"""

from pathlib import Path
import csv
import click

from lib.safe_string import safe_string

from citas_admin.app import create_app
from citas_admin.extensions import database

from citas_admin.blueprints.tdt_partidos.models import TdtPartido

app = create_app()
db.app = app


@click.group()
def cli():
    """Tres de Tres - Partidos"""


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
    click.echo("Alimentando partidos...")
    contador = 0
    with open(ruta, encoding="utf8") as puntero:
        rows = csv.DictReader(puntero)
        for row in rows:
            TdtPartido(
                nombre=safe_string(row["nombre"], to_uppercase=True, save_enie=True),
                siglas=safe_string(row["siglas"], to_uppercase=True, save_enie=True),
                estatus=row["estatus"],
            ).save()
            contador += 1
            if contador % 100 == 0:
                click.echo(f"  Van {contador}...")
    click.echo(f"{contador} partidos alimentados.")


cli.add_command(alimentar)
