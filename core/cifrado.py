import os
from cryptography.fernet import Fernet, InvalidToken

_fernet = None


def _obtener_fernet():
    global _fernet
    if _fernet is None:
        clave = os.getenv("CLAVE_CIFRADO_GMAIL")
        if not clave:
            raise RuntimeError(
                "Falta la variable de entorno CLAVE_CIFRADO_GMAIL. "
                "Generá una con: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            )
        _fernet = Fernet(clave.encode())
    return _fernet


def cifrar(texto_plano):
    if not texto_plano:
        return texto_plano
    return _obtener_fernet().encrypt(texto_plano.encode()).decode()


def descifrar(texto_cifrado):
    """Si el valor no es un token Fernet válido (por ejemplo, una contraseña
    vieja guardada en texto plano antes de esta migración, o un dato ya
    descifrado), se devuelve tal cual en vez de romper el envío de correos."""
    if not texto_cifrado:
        return texto_cifrado
    try:
        return _obtener_fernet().decrypt(texto_cifrado.encode()).decode()
    except (InvalidToken, ValueError):
        return texto_cifrado
