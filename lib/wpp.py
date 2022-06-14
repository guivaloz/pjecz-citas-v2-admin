"""
Web Pay Plus
"""
import xml.etree.ElementTree as ET


def create_chain_xml(amount):
    """Crear cadena XML"""
    root = ET.Element("P")

    business = ET.SubElement(root, "business")
    ET.SubElement(business, "id_company", name="blah").text = "SNBX"
    ET.SubElement(business, "id_branch", name="blah").text = "01SNBXBRNCH"
    ET.SubElement(business, "user", name="blah").text = "SNBXUSR01"
    ET.SubElement(business, "pwd", name="blah").text = "SECRETO"

    url = ET.SubElement(root, "url")
    ET.SubElement(url, "references", name="blah").text = "123456"
    ET.SubElement(url, "amount", name="blah").text = str(amount)
    ET.SubElement(url, "moneda", name="blah").text = "MXN"
    ET.SubElement(url, "canal", name="blah").text = "W"

    return ET.tostring(root)


def encrypt_chain():
    """Cifrar cadena XML"""
    return None
