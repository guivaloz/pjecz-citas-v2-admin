"""
CLI Pag Pagos

- exportar_xlsx: Exportar Pagos PAGADOS y ENTREGADOS a un archivo XLSX
"""

import sys
from datetime import datetime

import click

from citas_admin.blueprints.pag_pagos.tasks import exportar_xlsx as exportar_xlsx_task
from lib.exceptions import MyAnyError


@click.group()
def cli():
    """Pag Pagos"""


@click.command()
@click.option("--desde", help="Fecha de inicio (YYYY-MM-DD)")
@click.option("--hasta", help="Fecha de termino (YYYY-MM-DD)")
def exportar_xlsx(desde: str = None, hasta: str = None):
    """Exportar Pagos PAGADOS y ENTREGADOS a un archivo XLSX"""

    # Convertir las fechas desde y hasta a dates
    try:
        desde = datetime.strptime(desde, "%Y-%m-%d").date() if desde else None
        hasta = datetime.strptime(hasta, "%Y-%m-%d").date() if hasta else None
    except ValueError:
        click.echo(click.style("Las fechas deben tener el formato YYYY-MM-DD", fg="red"))
        sys.exit(1)

    # Ejecutar la tarea
    try:
        mensaje_termino, _, _ = exportar_xlsx_task(desde, hasta)
    except MyAnyError as error:
        click.echo(click.style(str(error), fg="red"))
        sys.exit(1)

    # Mensaje de termino
    click.echo(click.style(mensaje_termino, fg="green"))


cli.add_command(exportar_xlsx)
