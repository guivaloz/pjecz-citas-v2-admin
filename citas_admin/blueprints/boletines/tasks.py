"""
Boletines, tareas en el fondo
"""
import logging

from dotenv import load_dotenv

load_dotenv()  # Take environment variables from .env

bitacora = logging.getLogger(__name__)
bitacora.setLevel(logging.INFO)
formato = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
empunadura = logging.FileHandler("boletines.log")
empunadura.setFormatter(formato)
bitacora.addHandler(empunadura)


def enviar(boletin_id, to_email=None):
    """Enviar boletin"""
