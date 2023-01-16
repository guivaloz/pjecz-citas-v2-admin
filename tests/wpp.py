"""
WPP Demostración

"""
import asyncio
from lib.wpp import create_chain_xml, encrypt_chain, send_chain, get_url_from_xml_encrypt, get_response


def main():
    """Main function"""
    chain = create_chain_xml(
        amount=100.0,
        email="guivaloz@gmail.com",
        description="ServicioTest",
        cit_client_id="123456789",
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

    # Proceso de respuesta del Banco
    strResponse = "68wsIQV967Hv1fuwTkJLyXreekm0tzefYxCCwkPyE5Y4RVmpwHk3lHAfvmgc1FK8hiO+KM5+1UF45iseIbLzhcYcM3YYkbD6pcjMskJXd7aITG2yJm43iiee1nk2fFboRm4mL3bgCmE6Wli90tXALyqP8hsnlINv4YX6Br2FNXaNMprCo9+0RWYGLpqiMSmsOBeJptM4snjhC9cel2CFB1jvpvtMeyLsJPaKOlCxwYRsjAOuIZ+aDrW7jkGd73/mCQStRWJvx3+FuIlscaWDp0+eVDqzmZAsMuedlrh+wDjy2apv23UuQvi69VSxN0kgVMM9cPxtMf2rvTzinzycwqD1K5/JBjU3kxQARKyqTV2x2peI9B+/lwjZWLFPdjdvCggVEjPVolbhWBuhy8QnUOb0vbg6rbGf5VKbCFenF7f6UgKSi+I6YcMsEcE6hvv9dRltTA8bAWM/0tLwIB+7bpaVbQleyySuNDYett9ctgZQVUmiEQGJUVd21eglhpx0pawUrzp4CtvJIutRfHH/o/OaP0VHdps1hXdJX0ec8K2YWNvnigqWsJ7m1uNOTuId5kiswYoch5qXqnxjCDPDWA7yZ4PeN40IY5Y+MKFwGpDay9nm0eRu4zXNF+S1B9USPRGOY+HZaGEKFN83FqV4uHpz+gO2CE0kIW0AnthnyS9eGD+FhO+E1FNl3TLq9Wfkzk/0cee94p3rVhHdEvZFi29Y3rbAbnROpMHSGPW6aDH1KsMghKEAy5d91FjC9TCOSZnpQ1GvdEd89M2um6FcXyKmfbOYTHEQUjwO5UbL1JwIgXXFsSOc9s3baAbIB+JL6WGvJacBNyC7TOVmL5vEOa1FXP1+yF0y7/NcaCx46VuKsO69aOxh1mZpcLsjBXIVkw8KRi+856e3KqJT5rvwaycMxuMkm/7bPwejXae01p3h2UD6Pc+p6lWxdI3vEybgqW7+2p3TTO1Yf9Yv1HXrGTWnVQ17bFFh0nDLwOgFapfZJgrocqvrb0zYDytYdzNMKM+lS7gEQwxrXlmCnGdO/wWs21BvNuXiwuhu6AxOW4++jxBUsqpxZ4wT6UZCjNF+M155fkB/fVBltPXIMyMCPiteD0it6R0mll2WHLtFcPjN9fxCyw9CO1ph9y5iP6mRUHqnlP1EpX074sLc6EWxSGZbD3sz6Qou8JpFkCDwZVLixOiPQS/BmunICuC3w/hEPC+WlFL5jJW18IYRiObmDMc+wi50WSfMAe96/dV7aq913fvHuNAfYTi3jnLwv/ujqECHc+SrTtAHi47reE8lb3Gw3orcBrOzj8cH0U/NFL+TnxrxpXJvC2mP9ctRbQET6dfGOHkXbBNAurWNp0HTWN7ZYRuDGy9BWNPWATUj4t0="

    print("=== Respuesta del Banco WPP (vía POST) ===")
    respuesta = get_response(strResponse)
    for key, value in respuesta.items():
        print(key, ":", value)


if __name__ == "__main__":
    main()
