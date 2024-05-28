"""
Respaldar Autoridades
"""

import csv
import sys
from pathlib import Path

import click

from citas_admin.blueprints.autoridades.models import Autoridad

AUTORIDADES_CSV = "seed/autoridades.csv"


def respaldar_autoridades():
    """Respaldar Autoridades"""
    ruta = Path(AUTORIDADES_CSV)
    if ruta.exists():
        click.echo(f"AVISO: {AUTORIDADES_CSV} ya existe, no voy a sobreescribirlo.")
        sys.exit(1)
    click.echo("Respaldando autoridades: ", nl=False)
    contador = 0
    with open(ruta, "w", encoding="utf8") as puntero:
        respaldo = csv.writer(puntero)
        respaldo.writerow(
            [
                "autoridad_id",
                "distrito_id",
                "materia_id",
                "clave",
                "descripcion",
                "descripcion_corta",
                "es_jurisdiccional",
                "es_notaria",
                "organo_jurisdiccional",
                "estatus",
            ]
        )
        for autoridad in Autoridad.query.order_by(Autoridad.id).all():
            respaldo.writerow(
                [
                    autoridad.id,
                    autoridad.distrito_id,
                    autoridad.materia_id,
                    autoridad.clave,
                    autoridad.descripcion,
                    autoridad.descripcion_corta,
                    int(autoridad.es_jurisdiccional),
                    int(autoridad.es_notaria),
                    autoridad.organo_jurisdiccional,
                    autoridad.estatus,
                ]
            )
            contador += 1
            click.echo(click.style(".", fg="green"), nl=False)
    click.echo()
    click.echo(click.style(f"  {contador} autoridades respaldadas.", fg="green"))
