"""
WPP Demostracion

"""
import asyncio
from lib.wpp import create_chain_xml, encrypt_chain, send_chain, get_url_from_xml_encrypt


def main():
    """
    Main function
    """
    chain = create_chain_xml(
        amount=100.0,
        email="guivaloz@gmail.com",
        description="Servicio Test",
        client_id="123456789",
    )
    chain_encrypt = encrypt_chain(chain).decode()  # bytes
    respuesta = ""
    try:
        respuesta = asyncio.run(send_chain(chain_encrypt))
    except asyncio.TimeoutError as error:
        print(f"ERROR: No hay respuesta en el limite de tiempo. {str(error)}")
    except Exception as error:
        print(f"ERROR: Algo a salido mal en el envío. {str(error)}")
    if respuesta != "":
        url_pay = get_url_from_xml_encrypt(respuesta)
        print(url_pay)  # URL del link de formulario de pago
    else:
        print("¡ERROR!")


if __name__ == "__main__":
    main()
