import re
import unicodedata
from datetime import datetime
from psycopg2.extras import Json

from core.database import obtener_conexion

ENTIDADES_VALIDAS = ("clientes", "proyectos")
TIPOS_VALIDOS = ("texto", "numero", "fecha", "seleccion")


def generar_slug(etiqueta):
    texto = unicodedata.normalize("NFKD", etiqueta or "")
    texto = texto.encode("ascii", "ignore").decode("ascii")
    texto = texto.lower().strip()
    texto = re.sub(r"[^a-z0-9]+", "_", texto)
    texto = texto.strip("_")
    return texto or "campo"


def slug_unico(agencia_id, entidad, slug_base):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT nombre_campo FROM definiciones_campo WHERE agencia_id = %s AND entidad = %s",
        (agencia_id, entidad)
    )
    existentes = {fila[0] for fila in cursor.fetchall()}
    conexion.close()

    if slug_base not in existentes:
        return slug_base
    contador = 2
    while f"{slug_base}_{contador}" in existentes:
        contador += 1
    return f"{slug_base}_{contador}"


def agregar_definicion(agencia_id, entidad, etiqueta, tipo, opciones=None, obligatorio=False):
    slug = slug_unico(agencia_id, entidad, generar_slug(etiqueta))

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT COALESCE(MAX(orden), 0) FROM definiciones_campo WHERE agencia_id = %s AND entidad = %s", (agencia_id, entidad))
    siguiente_orden = cursor.fetchone()[0] + 1
    cursor.execute(
        """INSERT INTO definiciones_campo
           (agencia_id, entidad, nombre_campo, etiqueta, tipo, opciones, orden, obligatorio)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
        (agencia_id, entidad, slug, etiqueta, tipo, opciones, siguiente_orden, obligatorio)
    )
    definicion_id = cursor.fetchone()[0]
    conexion.commit()
    conexion.close()
    return definicion_id


def obtener_definiciones(agencia_id, entidad):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT * FROM definiciones_campo WHERE agencia_id = %s AND entidad = %s ORDER BY orden",
        (agencia_id, entidad)
    )
    resultados = cursor.fetchall()
    conexion.close()
    return resultados


def obtener_definicion_por_id(id, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM definiciones_campo WHERE id = %s AND agencia_id = %s", (id, agencia_id))
    resultado = cursor.fetchone()
    conexion.close()
    return resultado


def editar_definicion_por_id(id, agencia_id, etiqueta, opciones=None, obligatorio=False):
    """nombre_campo, tipo y entidad son inmutables una vez creada la
    definición: nombre_campo es la clave usada en el JSONB ya guardado, y
    cambiar el tipo rompería el parseo de los valores existentes."""
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        "UPDATE definiciones_campo SET etiqueta = %s, opciones = %s, obligatorio = %s WHERE id = %s AND agencia_id = %s",
        (etiqueta, opciones, obligatorio, id, agencia_id)
    )
    conexion.commit()
    conexion.close()


def eliminar_definicion_por_id(id, agencia_id):
    """Solo borra la definición. Los valores ya guardados en el JSONB de
    clientes/proyectos bajo esa clave quedan huérfanos, sin romper nada
    (no hay borrado en cascada de datos)."""
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM definiciones_campo WHERE id = %s AND agencia_id = %s", (id, agencia_id))
    conexion.commit()
    conexion.close()


def _parsear_valor(valor, definicion):
    nombre_campo, etiqueta, tipo, opciones = definicion[3], definicion[4], definicion[5], definicion[6]

    if tipo == "numero":
        try:
            return float(valor), None
        except ValueError:
            return None, f"El campo '{etiqueta}' debe ser un número válido."

    if tipo == "fecha":
        try:
            datetime.strptime(valor, "%Y-%m-%d")
        except ValueError:
            return None, f"El campo '{etiqueta}' debe ser una fecha válida."
        return valor, None

    if tipo == "seleccion":
        opciones_validas = [opcion.strip() for opcion in (opciones or "").split(",") if opcion.strip()]
        if valor not in opciones_validas:
            return None, f"El valor elegido para '{etiqueta}' no es una opción válida."
        return valor, None

    return valor, None


def validar_valores_formulario(agencia_id, entidad, formulario):
    """Valida los campos 'campo_<nombre_campo>' recibidos en un formulario
    contra las definiciones activas de esta agencia+entidad.

    Devuelve (dict_validado, None) si todo es correcto, o (None, mensaje_de_error)
    si algo falla. Cualquier clave 'campo_*' recibida que no corresponda a una
    definición activa es rechazada (evita que se inyecten claves JSONB arbitrarias)."""
    definiciones = obtener_definiciones(agencia_id, entidad)
    nombres_validos = {definicion[3] for definicion in definiciones}

    claves_recibidas = {
        clave[len("campo_"):]
        for clave in formulario.keys()
        if clave.startswith("campo_")
    }
    desconocidas = claves_recibidas - nombres_validos
    if desconocidas:
        return None, "Se recibió un campo personalizado desconocido."

    resultado = {}
    for definicion in definiciones:
        nombre_campo, obligatorio = definicion[3], definicion[8]
        valor = (formulario.get(f"campo_{nombre_campo}") or "").strip()

        if not valor:
            if obligatorio:
                return None, f"El campo '{definicion[4]}' es obligatorio."
            continue

        valor_parseado, error = _parsear_valor(valor, definicion)
        if error:
            return None, error
        resultado[nombre_campo] = valor_parseado

    return resultado, None


def fusionar_campos_personalizados(valores_actuales, valores_validados, definiciones):
    """Parte de los valores actuales (dict) y pisa solo las claves de
    definiciones vigentes: si una definición fue borrada, su valor viejo
    nunca se toca. Si un campo opcional se deja vacío, su clave se elimina."""
    resultado = dict(valores_actuales or {})
    for definicion in definiciones:
        nombre_campo = definicion[3]
        if nombre_campo in valores_validados:
            resultado[nombre_campo] = valores_validados[nombre_campo]
        else:
            resultado.pop(nombre_campo, None)
    return resultado


def campos_personalizados_json(valores):
    return Json(valores or {})
