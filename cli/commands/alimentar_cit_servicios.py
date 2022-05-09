"""
Alimentar Cit Servicios
"""
from datetime import datetime
from pathlib import Path
import csv
import click

from lib.safe_string import safe_string

from citas_admin.blueprints.cit_categorias.models import CitCategoria
from citas_admin.blueprints.cit_servicios.models import CitServicio

ARCHIVO_CSV = "seed/cit_servicios.csv"


def alimentar_cit_servicios():
    """Alimentar Servicios de las Citas"""
    ruta = Path(ARCHIVO_CSV)
    if not ruta.exists():
        click.echo(f"AVISO: {ruta.name} no se encontró.")
        return
    if not ruta.is_file():
        click.echo(f"AVISO: {ruta.name} no es un archivo.")
        return
    click.echo("Alimentando servicios de las citas...")
    contador = 0
    with open(ruta, encoding="utf-8") as puntero:
        rows = csv.DictReader(puntero)
        for row in rows:
            servicio_id = int(row["cit_servicio_id"])
            if servicio_id != contador + 1:
                click.echo(f"  AVISO: servicio_id {servicio_id} no es consecutivo")
                continue
            CitServicio(
                cit_categoria=CitCategoria.query.filter_by(nombre=safe_string(row["categoria_nombre"])).first(),
                clave=safe_string(row["clave"]),
                descripcion=safe_string(row["descripcion"]),
                duracion=datetime.strptime(row["duracion"], "%H:%M:%S"),
                documentos_limite=int(row["documentos_limite"]),
                estatus=row["estatus"],
            ).save()
            contador += 1
            if contador % 100 == 0:
                click.echo(f"  Van {contador}...")
    click.echo(f"  {contador} servicios de las citas alimentados")
