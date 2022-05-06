"""
Comandos Click para instalar con pip install --editable .
"""
from setuptools import setup


setup(
    name="citas_admin",
    version="0.1",
    packages=["citas_admin"],
    entry_points="""
        [console_scripts]
        citas=cli.cli:cli
    """,
)
