"""
Alimentar Domicilios
"""
from pathlib import Path
import csv
import click

from lib.safe_string import safe_string

from citas_admin.blueprints.domicilios.models import Domicilio

DOMICILIOS_CSV = "seed/domicilios.csv"


def alimentar_domicilios():
    """Alimentar domicilios"""
    ruta = Path(DOMICILIOS_CSV)
    if not ruta.exists():
        click.echo(f"AVISO: {ruta.name} no se encontró.")
        return
    if not ruta.is_file():
        click.echo(f"AVISO: {ruta.name} no es un archivo.")
        return
    click.echo("Alimentando domicilios...")
    contador = 0
    with open(ruta, encoding="utf-8") as puntero:
        rows = csv.DictReader(puntero)
        for row in rows:
            domicilio_id = int(row["domicilio_id"])
            if domicilio_id != contador + 1:
                click.echo(f"  AVISO: domicilio_id {domicilio_id} no es consecutivo")
                continue
            domicilio = Domicilio()
            domicilio.estado = safe_string(row["estado"], max_len=64)
            domicilio.municipio = safe_string(row["municipio"], max_len=64)
            domicilio.calle = safe_string(row["calle"], max_len=256, do_unidecode=False)
            domicilio.num_ext = safe_string(row["num_ext"], max_len=24, do_unidecode=False)
            domicilio.num_int = safe_string(row["num_int"], max_len=24, do_unidecode=False)
            domicilio.colonia = safe_string(row["colonia"], max_len=256, do_unidecode=False)
            domicilio.cp = int(row["cp"])
            domicilio.completo = domicilio.elaborar_completo()
            domicilio.estatus = row["estatus"]
            domicilio.save()
            contador += 1
            if contador % 100 == 0:
                click.echo(f"  Van {contador}...")
    click.echo(f"  {contador} domicilios alimentados")
