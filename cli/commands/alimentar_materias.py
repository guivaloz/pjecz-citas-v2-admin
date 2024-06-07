"""
Alimentar Materias
"""

import csv
import sys
from pathlib import Path

import click

from citas_admin.blueprints.materias.models import Materia
from lib.safe_string import safe_string

MATERIAS_CSV = "seed/materias.csv"


def alimentar_materias():
    """Alimentar Materias"""
    ruta = Path(MATERIAS_CSV)
    if not ruta.exists():
        click.echo(f"AVISO: {ruta.name} no se encontró.")
        sys.exit(1)
    if not ruta.is_file():
        click.echo(f"AVISO: {ruta.name} no es un archivo.")
        sys.exit(1)
    click.echo("Alimentando materias: ", nl=False)
    contador = 0
    with open(ruta, encoding="utf8") as puntero:
        rows = csv.DictReader(puntero)
        for row in rows:
            materia_id = int(row["materia_id"])
            nombre = safe_string(row["nombre"], save_enie=True)
            estatus = row["estatus"]
            if materia_id != contador + 1:
                click.echo(click.style(f"  AVISO: materia_id {materia_id} no es consecutivo", fg="red"))
                sys.exit(1)
            Materia(
                nombre=nombre,
                estatus=estatus,
            ).save()
            contador += 1
            click.echo(click.style(".", fg="green"), nl=False)
    click.echo()
    click.echo(click.style(f"  {contador} materias alimentadas.", fg="green"))
