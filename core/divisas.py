import time
import requests

# Monedas más usadas por agencias hispanohablantes, más las principales
# monedas internacionales. No es la lista completa de las ~170 monedas
# ISO del mundo (eso sería ruido para un selector), sino las que un cliente
# real de este CRM va a necesitar.
MONEDAS = [
    ("USD", "Dólar estadounidense", "$"),
    ("ARS", "Peso argentino", "$"),
    ("MXN", "Peso mexicano", "$"),
    ("COP", "Peso colombiano", "$"),
    ("CLP", "Peso chileno", "$"),
    ("PEN", "Sol peruano", "S/"),
    ("UYU", "Peso uruguayo", "$"),
    ("BOB", "Boliviano", "Bs"),
    ("PYG", "Guaraní", "₲"),
    ("VES", "Bolívar venezolano", "Bs."),
    ("GTQ", "Quetzal guatemalteco", "Q"),
    ("CRC", "Colón costarricense", "₡"),
    ("DOP", "Peso dominicano", "RD$"),
    ("BRL", "Real brasileño", "R$"),
    ("EUR", "Euro", "€"),
    ("GBP", "Libra esterlina", "£"),
    ("CAD", "Dólar canadiense", "$"),
]

_SIMBOLOS = {codigo: simbolo for codigo, _, simbolo in MONEDAS}

# Cache en memoria del proceso: evita golpear la API externa en cada
# render de página. Se refresca sola cada 1 hora. Guardamos la tabla
# completa de tasas (una sola llamada sirve para cualquier moneda).
_TASAS_CACHE = None
_TASAS_CACHE_TS = 0
_TTL_SEGUNDOS = 3600


def simbolo_moneda(codigo):
    return _SIMBOLOS.get(codigo, codigo)


def _obtener_tabla_tasas():
    global _TASAS_CACHE, _TASAS_CACHE_TS

    ahora = time.time()
    if _TASAS_CACHE and (ahora - _TASAS_CACHE_TS) < _TTL_SEGUNDOS:
        return _TASAS_CACHE

    try:
        respuesta = requests.get("https://open.er-api.com/v6/latest/USD", timeout=5)
        respuesta.raise_for_status()
        datos = respuesta.json()
        if datos.get("result") != "success":
            raise ValueError("La API de cambio no devolvió un resultado válido.")
        _TASAS_CACHE = datos["rates"]
        _TASAS_CACHE_TS = ahora
        return _TASAS_CACHE
    except Exception:
        # Si falla pero ya había una tabla vieja en caché, mejor una
        # conversión desactualizada que ninguna.
        return _TASAS_CACHE


def obtener_tasa_cambio(moneda_destino):
    """Devuelve cuántas unidades de moneda_destino equivalen a 1 USD, o None
    si no se pudo consultar (y tampoco hay nada en caché para usar de respaldo)."""
    if not moneda_destino or moneda_destino == "USD":
        return 1.0

    tabla = _obtener_tabla_tasas()
    if not tabla:
        return None
    return tabla.get(moneda_destino)
