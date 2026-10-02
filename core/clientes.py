import re
from core.database import obtener_conexion
from core.paises import PAISES

PATRON_EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def email_valido(email):
    """True si el texto tiene forma de email (algo@algo.algo). No verifica que
    el dominio exista de verdad, solo que el formato sea razonable."""
    return bool(PATRON_EMAIL.match(email))


def telefono_valido(telefono):
    """El teléfono es opcional: vacío siempre es válido. Si viene cargado con
    un prefijo de país reconocido (ej. "+54 91112345678"), exige que la parte
    numérica tenga exactamente la cantidad de dígitos esperada para ese país.
    Si el prefijo no se reconoce (números viejos cargados como texto libre
    antes de que existiera el selector de país), no se valida para no romper
    datos existentes."""
    telefono = (telefono or "").strip()
    if not telefono:
        return True

    prefijos = sorted((pais[1] for pais in PAISES), key=len, reverse=True)
    prefijo_encontrado = next((prefijo for prefijo in prefijos if telefono.startswith(prefijo)), None)
    if not prefijo_encontrado:
        return True

    longitud_esperada = next(longitud for _, prefijo, longitud in PAISES if prefijo == prefijo_encontrado)
    numero = re.sub(r"\D", "", telefono[len(prefijo_encontrado):])
    return len(numero) == longitud_esperada


def agregar_cliente(nombre, email, telefono, empresa, notas, agencia_id, cliente_desde=None):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        "INSERT INTO clientes (nombre, email, telefono, empresa, notas, agencia_id, cliente_desde) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (nombre, email, telefono, empresa, notas, agencia_id, cliente_desde)
    )
    conexion.commit()
    conexion.close()

def mostrar_clientes():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM clientes")
    resultados = cursor.fetchall()
    conexion.close()
    for cliente in resultados:
        print(f"id: {cliente[0]} nombre: {cliente[1]}, email: {cliente[2]}, telefono: {cliente[3]}, empresa: {cliente[4]}, notas: {cliente[5]}")

def buscar_cliente(nombre):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM clientes WHERE nombre = %s", (nombre,))
    resultado = cursor.fetchone()
    conexion.close()
    return resultado

def eliminar_cliente(nombre):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM clientes WHERE nombre = %s", (nombre,))
    conexion.commit()
    conexion.close()

def editar_cliente(nombre, campo, nuevo_valor):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(f"UPDATE clientes SET {campo} = %s WHERE nombre = %s", (nuevo_valor, nombre))
    conexion.commit()
    conexion.close()

def eliminar_cliente_por_id(id, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM clientes WHERE id = %s AND agencia_id = %s", (id, agencia_id))
    conexion.commit()
    conexion.close()

def editar_cliente_por_id(id, nombre, email, telefono, empresa, notas, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("UPDATE clientes SET nombre = %s, email = %s, telefono = %s, empresa = %s, notas = %s WHERE id = %s AND agencia_id = %s",
                   (nombre, email, telefono, empresa, notas, id, agencia_id)
                   )
    conexion.commit()
    conexion.close()

def obtener_clientes(agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM clientes WHERE agencia_id = %s AND archivado = false", (agencia_id,))
    resultados = cursor.fetchall()
    conexion.close()
    return resultados

def obtener_clientes_paginado(agencia_id, pagina, por_pagina, archivados=False):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM clientes WHERE agencia_id = %s AND archivado = %s",
        (agencia_id, archivados)
    )
    total = cursor.fetchone()[0]
    offset = (pagina - 1) * por_pagina
    cursor.execute(
        "SELECT * FROM clientes WHERE agencia_id = %s AND archivado = %s ORDER BY id LIMIT %s OFFSET %s",
        (agencia_id, archivados, por_pagina, offset)
    )
    resultados = cursor.fetchall()
    conexion.close()
    return resultados, total

def archivar_cliente_por_id(id, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("UPDATE clientes SET archivado = true WHERE id = %s AND agencia_id = %s", (id, agencia_id))
    conexion.commit()
    conexion.close()

def desarchivar_cliente_por_id(id, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("UPDATE clientes SET archivado = false WHERE id = %s AND agencia_id = %s", (id, agencia_id))
    conexion.commit()
    conexion.close()

def obtener_cliente_por_id(id, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM clientes WHERE id = %s AND agencia_id = %s", (id, agencia_id))
    resultado = cursor.fetchone()
    conexion.close()
    return resultado

def obtener_cliente_por_email(email, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM clientes WHERE email = %s AND agencia_id = %s", (email, agencia_id))
    resultado = cursor.fetchone()
    conexion.close()
    return resultado