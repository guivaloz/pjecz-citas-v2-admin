"""
Alimentar distritos
"""
from pathlib import Path
import csv
import click

from lib.safe_string import safe_string

from citas_admin.blueprints.distritos.models import Distrito

DISTRITOS_CSV = "seed/distritos.csv"


def alimentar_distritos():
    """Alimentar distritos"""
    ruta = Path(DISTRITOS_CSV)
    if not ruta.exists():
        click.echo(f"AVISO: {ruta.name} no se encontró.")
        return
    if not ruta.is_file():
        click.echo(f"AVISO: {ruta.name} no es un archivo.")
        return
    click.echo("Alimentando distritos...")
    contador = 0
    with open(ruta, encoding="utf8") as puntero:
        rows = csv.DictReader(puntero)
        for row in rows:
            distrito_id = int(row["distrito_id"])
            if distrito_id != contador + 1:
                click.echo(f"  AVISO: distrito_id {distrito_id} no es consecutivo")
                continue
            Distrito(
                nombre=safe_string(row["nombre"], do_unidecode=False),
                nombre_corto=safe_string(row["nombre_corto"], do_unidecode=False),
                es_distrito_judicial=(row["es_distrito_judicial"] == "1"),
                estatus=row["estatus"],
            ).save()
            contador += 1
            if contador % 100 == 0:
                click.echo(f"  Van {contador}...")
    click.echo(f"  {contador} distritos alimentados.")


def eliminar_distritos_sin_autoridades():
    """Eliminar distritos sin autoridades (que se hayan eliminado)"""
    click.echo("Eliminado distritos sin autoridades...")
    contador = 0
    for distrito in Distrito.query.filter_by(estatus="A").all():
        autoridades_activas_contador = 0
        for autoridad in distrito.autoridades:
            if autoridad.estatus == "A":
                autoridades_activas_contador += 1
        if autoridades_activas_contador == 0:
            distrito.estatus = "B"
            distrito.save()
            contador += 1
    click.echo(f"  {contador} distritos eliminados.")
