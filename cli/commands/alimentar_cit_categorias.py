"""
Alimentar Cit Categorias
"""
from pathlib import Path
import csv
import click

from lib.safe_string import safe_string

from citas_admin.blueprints.cit_categorias.models import CitCategoria

ARCHIVO_CSV = "seed/cit_servicios.csv"


def alimentar_cit_categorias():
    """Alimentar Categorias"""
    ruta = Path(ARCHIVO_CSV)
    if not ruta.exists():
        click.echo(f"AVISO: {ruta.name} no se encontró.")
        return
    if not ruta.is_file():
        click.echo(f"AVISO: {ruta.name} no es un archivo.")
        return
    click.echo("Alimentando categorias...")
    contador = 0
    with open(ruta, encoding="utf-8") as puntero:
        rows = csv.DictReader(puntero)
        categorias_listado = []
        for row in rows:
            nombre = safe_string(row["categoria_nombre"])
            if nombre in categorias_listado:
                continue
            CitCategoria(nombre=safe_string(nombre)).save()
            categorias_listado.append(nombre)
            contador += 1
            if contador % 100 == 0:
                click.echo(f"  Van {contador}...")
    click.echo(f"  {contador} categorias alimentados")
