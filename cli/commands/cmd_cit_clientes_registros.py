"""
Cit Clientes Registros

- agregar: Agregar manualmente un nuevo cliente
- agregar_aleatorios: Agregar aleatoriamente muchos clientes
"""
import click


@click.group()
def cli():
    """Cit Clientes Registros"""


@click.command()
def agregar():
    """Agregar manualmente un nuevo cliente"""
    click.echo("Por programar")


@click.command()
def agregar_aleatorios():
    """Agregar aleatoriamente muchos clientes"""
    click.echo("Por programar")


cli.add_command(agregar)
cli.add_command(agregar_aleatorios)
