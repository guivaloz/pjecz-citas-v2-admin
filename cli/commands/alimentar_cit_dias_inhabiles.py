"""
Alimentar Cit Dias Inhabiles
"""
from datetime import datetime
from pathlib import Path
import csv
import click

from lib.safe_string import safe_string

from citas_admin.blueprints.cit_dias_inhabiles.models import CitDiaInhabil

ARCHIVO_CSV = "seed/cit_dias_inhabiles.csv"


def alimentar_cit_dias_inhabiles():
    """Alimentar Dias Inhabiles"""
    ruta = Path(ARCHIVO_CSV)
    if not ruta.exists():
        click.echo(f"AVISO: {ruta.name} no se encontró.")
        return
    if not ruta.is_file():
        click.echo(f"AVISO: {ruta.name} no es un archivo.")
        return
    click.echo("Alimentando dias inhabiles...")
    contador = 0
    with open(ruta, encoding="utf-8") as puntero:
        rows = csv.DictReader(puntero)
        for row in rows:
            cit_dia_inhabil_id = int(row["cit_dia_inhabil_id"])
            if cit_dia_inhabil_id != contador + 1:
                click.echo(f"  AVISO: cit_dia_inhabil_id {cit_dia_inhabil_id} no es consecutivo")
                continue
            try:
                fecha = datetime.strptime(row["fecha"], "%Y-%m-%d")
            except ValueError:
                click.echo(f"  AVISO: {row['fecha']} no es una fecha válida")
                continue
            CitDiaInhabil(
                fecha=fecha,
                descripcion=safe_string(row["descripcion"], do_unidecode=False),
                estatus=row["estatus"],
            ).save()
            contador += 1
            if contador % 100 == 0:
                click.echo(f"  Van {contador}...")
    click.echo(f"  {contador} dias inhabiles alimentados")
