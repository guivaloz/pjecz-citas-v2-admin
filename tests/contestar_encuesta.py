"""
Responde la preguntas de las encuestas
"""
import argparse
import logging
import random
from dotenv import load_dotenv
from datetime import datetime, timedelta

from citas_admin.app import create_app
from citas_admin.extensions import db

from citas_admin.blueprints.encuestas.models import EncuestaSistema
from citas_admin.blueprints.cit_clientes.models import CitCliente

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
    parser = argparse.ArgumentParser(description='Inserta respuestas aleatorias en la encuesta elegida.')
    parser.add_argument("-l", "--list", help="Listado de encuestas disponibles")
    parser.add_argument("-enc", help="Selección de la encuesta", choices=["sistema","servicio"])
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
        if args.enc == "sistema":
            responder_encuesta_sistema(args.n)
            bitacora.info(f"Se insertaron en la encuesta '{EncuestaSistema.__tablename__}', {args.n} registros nuevos")
        return 0
    
    parser.print_help()


def listado_encuestas():
    """Listado de encuestas disponibles"""
    encuestas = []
    encuestas.append("sistema - Encuesta del Sistema")
    encuestas.append("servicio - Encuesta de Servicio")
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
        "Todo bien",
        "Gracias",
        "",
        "Me gustaría ...",
    ]
    for i in range(num):
        # Seleccionar un cliente que no haya participado en la encuesta
        while True:
            cliente_id = _seleccionar_cliente()
            cliente_en_encuesta = EncuestaSistema.query.filter_by(cit_cliente_id=cliente_id).first()
            if cliente_en_encuesta is None:
                break
        respuesta_01 = random.randint(1, 5)
        respuesta_02 = random.choice(respuestas_02)
        respuesta_03 = random.choice(respuestas_03)
        estado = random.choice(ESTADOS)

        # Impresión en pantalla de muestras
        if i % 25 == 0:
            print(f"{i+1} - c_id: {cliente_id}, r01: {respuesta_01}, r02: {respuesta_02}, r03: {respuesta_03}, estado: {estado}")

        # Inserción en la BD
        EncuestaSistema(
            cit_cliente_id=cliente_id,
            respuesta_01=respuesta_01,
            respuesta_02=respuesta_02,
            respuesta_03=respuesta_03,
            estado=estado,
        ).save()


def _seleccionar_cliente():
    """Regresa un cliente id al asar"""
    while True:
        id_random = random.randint(1, 13000)
        cliente = CitCliente.query.filter_by(estatus='A').filter_by(id=id_random).first()
        if cliente:
            return cliente.id


if __name__ == "__main__":
    main()
