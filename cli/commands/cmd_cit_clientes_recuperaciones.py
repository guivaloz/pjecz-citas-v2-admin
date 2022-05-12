"""
Cit Clientes Recuperaciones

- recuperar: Enviar un mensaje de recuperacion a un cliente
- recuperar_aleatorios: Agregar aleatoriamente muchas recuperaciones
"""
import click


@click.group()
def cli():
    """Cit Clientes Recuperaciones"""


@click.command()
def recuperar():
    """Enviar un mensaje de recuperacion a un cliente"""
    click.echo("Por programar")


@click.command()
def recuperar_aleatorios():
    """Agregar aleatoriamente muchas recuperaciones"""
    click.echo("Por programar")


cli.add_command(recuperar)
cli.add_command(recuperar_aleatorios)
