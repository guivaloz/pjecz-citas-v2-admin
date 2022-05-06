"""
Alimentar autoridades
"""
from pathlib import Path
import csv
import click

from citas_admin.blueprints.autoridades.models import Autoridad
from citas_admin.blueprints.distritos.models import Distrito
from citas_admin.blueprints.materias.models import Materia

AUTORIDADES_CSV = "seed/autoridades.csv"


def alimentar_autoridades():
    """Alimentar autoridades"""
    ruta = Path(AUTORIDADES_CSV)
    if not ruta.exists():
        click.echo(f"AVISO: {ruta.name} no se encontró.")
        return
    if not ruta.is_file():
        click.echo(f"AVISO: {ruta.name} no es un archivo.")
        return
    click.echo("Alimentando autoridades...")
    contador = 0
    with open(ruta, encoding="utf8") as puntero:
        rows = csv.DictReader(puntero)
        for row in rows:
            distrito_id = int(row["distrito_id"])
            distrito = Distrito.query.get(distrito_id)
            if distrito is None:
                click.echo(f"  AVISO: Falta el distrito {distrito_id}")
                continue
            materia_id = int(row["materia_id"])
            materia = Materia.query.get(materia_id)
            if materia is None:
                click.echo(f"  AVISO: Falta la materia {materia_id}")
                continue
            autoridad_id = int(row["autoridad_id"])
            if autoridad_id != contador + 1:
                click.echo(f"  AVISO: autoridad_id {autoridad_id} no es consecutivo")
                continue
            Autoridad(
                distrito=distrito,
                materia=materia,
                clave=row["clave"],
                descripcion=row["descripcion"],
                descripcion_corta=row["descripcion_corta"],
                es_jurisdiccional=(row["es_jurisdiccional"] == "1"),
                es_notaria=(row["es_notaria"] == "1"),
                organo_jurisdiccional=row["organo_jurisdiccional"],
                estatus=row["estatus"],
            ).save()
            contador += 1
            if contador % 100 == 0:
                click.echo(f"  Van {contador}...")
    click.echo(f"  {contador} autoridades alimentadas.")
