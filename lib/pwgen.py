"""
Generador de contraseñas
"""
import random
import string


def generar_contrasena(largo=16):
    """Generar contraseña con minúsculas, mayúsculas, dígitos y signos"""
    minusculas = string.ascii_lowercase
    mayusculas = string.ascii_uppercase
    digitos = string.digits
    simbolos = string.punctuation
    todos = minusculas + mayusculas + digitos + simbolos
    temp = random.sample(todos, largo)
    return "".join(temp)


def generar_aleatorio(largo=16):
    """Generar cadena de texto aleatorio con minúsculas, mayúsculas y dígitos"""
    minusculas = string.ascii_lowercase
    mayusculas = string.ascii_uppercase
    digitos = string.digits
    todos = minusculas + mayusculas + digitos
    temp = random.sample(todos, largo)
    return "".join(temp)


def generar_codigo_asistencia(largo=4):
    """Generar código asistencia"""
    digitos = string.digits
    temp = random.sample(digitos, largo)
    return "".join(temp)
