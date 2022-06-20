"""
Web Pay Plus
"""
import os

import asyncio
import aiohttp

from dotenv import load_dotenv
import xml.etree.ElementTree as ET
import requests

from lib.AESEncryption import AES128Encryption

load_dotenv()  # Take environment variables from .env


def create_chain_xml(amount, email, description, client_id):
    """Crear cadena XML"""
    root = ET.Element("P")

    business = ET.SubElement(root, "business")
    ET.SubElement(business, "id_company").text = "SNBX"
    ET.SubElement(business, "id_branch").text = "01SNBXBRNCH"
    ET.SubElement(business, "user").text = "SNBXUSR01"
    ET.SubElement(business, "pwd").text = "SECRETO"

    url = ET.SubElement(root, "url")
    ET.SubElement(url, "reference").text = "FACTURA999"
    ET.SubElement(url, "amount").text = str(amount)
    ET.SubElement(url, "moneda").text = "MXN"
    ET.SubElement(url, "canal").text = "W"
    ET.SubElement(url, "omitir_notif_default").text = "1"
    ET.SubElement(url, "st_correo").text = "1"
    ET.SubElement(url, "fh_vigencia").text = "28/07/2022"
    ET.SubElement(url, "mail_cliente").text = email
    ET.SubElement(url, "st_cr").text = "A"

    data = ET.SubElement(url, "datos_adicionales")
    data1 = ET.SubElement(data, "data")
    data1.attrib["id"] = "1"
    data1.attrib["display"] = "true"
    label1 = ET.SubElement(data1, "label")
    label1.text = description
    value1 = ET.SubElement(data1, "value")
    value1.text = str(client_id)

    ET.SubElement(url, "version").text = "IntegraWPP"

    return ET.tostring(root, encoding="unicode")


def encrypt_chain(chain: str):
    """Cifrar cadena XML"""
    key = os.getenv("WPP_KEY")
    if key is None:
        return None
    aes_encryptor = AES128Encryption()
    ciphertext = aes_encryptor.encrypt(chain, key)
    return ciphertext


def decrypt_chain(chain_encrypted: str):
    """Descifrar cadena XML"""
    key = os.getenv("WPP_KEY")
    if key is None:
        return None
    aes_encryptor = AES128Encryption()
    plaintext = aes_encryptor.decrypt(key, chain_encrypted)
    return plaintext


async def send(chain: str):
    """Send to WPP"""

    # Get the commerce ID
    commerce_id = os.getenv("WPP_COMMERCE_ID")
    if commerce_id is None:
        return None

    # Get the WPP URL
    wpp_url = os.getenv("WPP_URL")
    if wpp_url is None:
        return None

    # Pack the chain
    root = ET.Element("pgs")
    ET.SubElement(root, "data0").text = commerce_id
    ET.SubElement(root, "data").text = chain

    chain_bytes = ET.tostring(root, encoding="unicode")

    # Send the chain
    page = ''
    try:
        timeout = aiohttp.ClientTimeout(total=10.0)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(wpp_url, data={"xml": chain_bytes}) as resp:
                page = await resp.text()
                if resp.status != 200:
                    raise asyncio.TimeoutError('Status: %s' % resp.status)
    except (
            UnicodeDecodeError,
            asyncio.TimeoutError,
    ) as err:
        page = ''

    return page


def get_url_from_xml_encrypt(xml_encrypt: str):
    """Extrae la url del xml de respuesta"""
    xml = decrypt_chain(xml_encrypt)
    root = ET.fromstring(xml)
    return root.find("nb_url").text


if __name__ == "__main__":
    chain = create_chain_xml(
        amount=100.0,
        email="guivaloz@gmail.com",
        description="Servicio Test",
        client_id="123456789",
    )

    chain_encrypt = encrypt_chain(chain).decode()  # bytes
    respuesta = ''
    try:
        respuesta = asyncio.run(send(chain_encrypt))
    except asyncio.TimeoutError as err:
        print(f"ERROR: Algo a salido mal en el envío. {err}")

    if respuesta != '':
        url_pay = get_url_from_xml_encrypt(respuesta)
        print(url_pay)  # URL del link de formulario de pago

    print('¡ERROR!')


def create_pay_link(email: str, service_detail: str, client_id: int, amount: float):
    """Regresa el link para mostrar el formulario de pago"""

    chain = create_chain_xml(
        amount=amount,
        email=email,
        description=service_detail,
        client_id=client_id,
    )

    chain_encrypt = encrypt_chain(chain).decode()  # bytes
    # return chain_encrypt
    try:
        respuesta = asyncio.run(send(chain_encrypt))
        url_pay = get_url_from_xml_encrypt(respuesta)
    except Exception as err:
        raise BaseException(f"ERROR: Algo a salido mal en el envío. {err}")

    return url_pay  # URL del link de formulario de pago
