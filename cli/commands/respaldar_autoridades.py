"""
Respaldar Autoridades
"""
from pathlib import Path
import csv
import click

from citas_admin.blueprints.autoridades.models import Autoridad


def respaldar_autoridades(salida: str = "autoridades.csv"):
    """Respaldar Autoridades a un archivo CSV"""
    ruta = Path(salida)
    if ruta.exists():
        click.echo(f"AVISO: {salida} existe, no voy a sobreescribirlo.")
        return
    click.echo("Respaldando autoridades...")
    contador = 0
    autoridades = Autoridad.query.order_by(Autoridad.id).all()
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
        for autoridad in autoridades:
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
            if contador % 100 == 0:
                click.echo(f"  Van {contador}...")
    click.echo(f"  {contador} en {ruta.name}")
