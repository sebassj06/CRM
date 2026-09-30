import re
from core.database import obtener_conexion

PATRON_EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def email_valido(email):
    """True si el texto tiene forma de email (algo@algo.algo). No verifica que
    el dominio exista de verdad, solo que el formato sea razonable."""
    return bool(PATRON_EMAIL.match(email))


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
    cursor.execute("SELECT * FROM clientes WHERE agencia_id = %s", (agencia_id,))
    resultados = cursor.fetchall()
    conexion.close()
    return resultados

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