"""
Responde la preguntas de las encuestas
"""

import argparse
import logging
import random
from dotenv import load_dotenv
from datetime import datetime, timedelta

from citas_admin.app import create_app
from citas_admin.extensions import database

from citas_admin.blueprints.enc_servicios.models import EncServicio
from citas_admin.blueprints.enc_sistemas.models import EncSistema
from citas_admin.blueprints.cit_clientes.models import CitCliente
from citas_admin.blueprints.oficinas.models import Oficina

ESTADOS = [
    "PENDIENTE",
    "CANCELADO",
    "CONTESTADO",
]


def main():
    """Main function"""

    # Inicializar
    random.seed(10)
    load_dotenv()  # Take environment variables from .env
    app = create_app()
    db.app = app

    # Manejo de un Log
    bitacora = logging.getLogger("encuestas")
    bitacora.setLevel(logging.INFO)
    formato = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
    empunadura = logging.FileHandler("encuestas.log")
    empunadura.setFormatter(formato)
    bitacora.addHandler(empunadura)

    # Selección de Opciones
    parser = argparse.ArgumentParser(description="Inserta respuestas aleatorias en la encuesta elegida.")
    parser.add_argument("-l", "--list", help="Listado de encuestas disponibles")
    parser.add_argument("-enc", help="Selección de la encuesta", choices=["sistemas", "servicios"])
    parser.add_argument("-n", help="Número de respuestas (default=100)", default=100)
    args = parser.parse_args()
    # Mostrar el listado de encuestas
    if args.list:
        print("Encuestas Disponibles:")
        encuestas = listado_encuestas()
        for encuesta in encuestas:
            print(encuesta)
        return 0
    elif args.enc:
        print(f"Responder la encuesta: {args.enc}")
        print(f"Cantidad de respuestas: {args.n}")
        print("-----------------------------")
        if args.enc == "sistemas":
            responder_encuesta_sistema(args.n)
            bitacora.info(f"Se insertaron en la encuesta '{EncSistema.__tablename__}', {args.n} registros nuevos")
        elif args.enc == "servicios":
            responder_encuesta_servicios(args.n)
            bitacora.info(f"Se insertaron en la encuesta '{EncServicio.__tablename__}', {args.n} registros nuevos")
        return 0

    parser.print_help()


def listado_encuestas():
    """Listado de encuestas disponibles"""
    encuestas = []
    encuestas.append("sistemas - Encuesta del Sistema")
    encuestas.append("servicios - Encuesta de Servicio")
    # Regresa el listado
    return encuestas


def responder_encuesta_sistema(num_respuestas):
    """Genera las respuestas para la encuesta de Sistema"""
    num = int(num_respuestas)
    respuestas_02 = [
        "Fue fácil",
        "Muy intuitivo",
        "Tiene pocas opciones",
        "Difícil, batalle un poco al principio",
        "Funciona bien",
    ]
    respuestas_03 = [
        "Nada",
        "Excelente!",
        "Gracias",
        "Me gustaría poder ver mi historial de citas pasadas.",
        "En mi iPhone a veces no se puede acceder del todo.",
        "Creo que los colores no son muy adecuados",
        "Quisiera acceder con la contraseña de mi teléfono.",
        "Podrían integrarlo todo a un solo sitio, es complicado tener tantos sitios e usuarios y contraseñas.",
        "",
        "Todo bien, funciona muy bien.",
    ]
    for i in range(num):
        # Seleccionar un cliente que no haya participado en la encuesta
        while True:
            cliente_id = _seleccionar_cliente()
            cliente_en_encuesta = EncSistema.query.filter_by(cit_cliente_id=cliente_id).first()
            if cliente_en_encuesta is None:
                break
        estado = random.choice(ESTADOS)
        if estado == "CONTESTADO":
            respuesta_01 = random.randint(1, 5)
            respuesta_02 = random.choice(respuestas_02)
            respuesta_03 = random.choice(respuestas_03)
        else:
            respuesta_01 = None
            respuesta_02 = None
            respuesta_03 = None

        # Impresión en pantalla de muestras
        if i % 25 == 0:
            print(
                f"{i+1} - c_id: {cliente_id}, r01: {respuesta_01}, r02: {respuesta_02}, r03: {respuesta_03}, estado: {estado}"
            )

        # Inserción en la BD
        EncSistema(
            cit_cliente_id=cliente_id,
            respuesta_01=respuesta_01,
            respuesta_02=respuesta_02,
            respuesta_03=respuesta_03,
            estado=estado,
        ).save()


def responder_encuesta_servicios(num_respuestas):
    """Genera las respuestas para la encuesta de Servicio"""
    num = int(num_respuestas)
    # Grupo de respuestas
    respuestas_04 = [
        "",
        "El sistema para marcar la asistencia no suele ser muy efectivo.",
        "Deberían poder adelantar citas si los demás no llegan.",
        "No sé por qué piden cita, si no te atienden a tiempo.",
        "Deberían poder enviar los documento vía email.",
        "Podrían ampliar los horarios.",
        "Se tardan mucho.",
        "Deberían ser más ágiles.",
        "No hay muchas citas.",
        "El tiempo de espera es mucho.",
        "Su servicio es pésimo.",
        "Me parece perfecto.",
    ]
    # Crea el número de respuestas elegido
    for i in range(num):
        # Seleccionar un cliente que no haya participado en la encuesta
        while True:
            cliente_id = _seleccionar_cliente()
            cliente_en_encuesta = EncServicio.query.filter_by(cit_cliente_id=cliente_id).first()
            if cliente_en_encuesta is None:
                break
        oficina_id = _seleccionar_oficina()
        estado = random.choice(ESTADOS)
        if estado == "CONTESTADO":
            respuesta_01 = random.randint(1, 5)
            respuesta_02 = random.randint(1, 5)
            respuesta_03 = random.randint(1, 5)
            respuesta_04 = random.choice(respuestas_04)
        else:
            respuesta_01 = None
            respuesta_02 = None
            respuesta_03 = None
            respuesta_04 = None

        # Impresión en pantalla de muestras
        if i % 25 == 0:
            print(
                f"{i+1} - cli_id: {cliente_id}, ofi_id: {oficina_id} | r01: {respuesta_01}, r02: {respuesta_02}, r03: {respuesta_03}, r04: {respuesta_04}, estado: {estado}"
            )

        # Inserción en la BD
        EncServicio(
            cit_cliente_id=cliente_id,
            oficina_id=oficina_id,
            respuesta_01=respuesta_01,
            respuesta_02=respuesta_02,
            respuesta_03=respuesta_03,
            respuesta_04=respuesta_04,
            estado=estado,
        ).save()


def _seleccionar_cliente():
    """Regresa un cliente id al asar"""
    while True:
        id_random = random.randint(1, 13000)
        cliente = CitCliente.query.filter_by(estatus="A").filter_by(id=id_random).first()
        if cliente:
            return cliente.id


def _seleccionar_oficina():
    """Regresa una Oficina id al asar"""
    while True:
        id_random = random.randint(1, 200)
        oficina = Oficina.query.filter_by(estatus="A").filter_by(id=id_random).first()
        if oficina:
            return oficina.id


if __name__ == "__main__":
    main()
