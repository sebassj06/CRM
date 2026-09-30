from core.database import obtener_conexion
from werkzeug.security import generate_password_hash, check_password_hash

def crear_usuario(nombre_usuario, contraseña, agencia_id, rol="miembro"):
    contraseña_hash = generate_password_hash(contraseña)
    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor()
        cursor.execute("INSERT INTO usuarios (nombre_usuario, contraseña_hash, agencia_id, rol) VALUES (%s, %s, %s, %s)",
                       (nombre_usuario, contraseña_hash, agencia_id, rol))
        conexion.commit()
    finally:
        conexion.close()

def obtener_usuario_por_nombre(nombre_usuario):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE nombre_usuario = %s", (nombre_usuario,))
    resultado = cursor.fetchone()
    conexion.close()
    return resultado

def obtener_usuario_por_id(id, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE id = %s AND agencia_id = %s", (id, agencia_id))
    resultado = cursor.fetchone()
    conexion.close()
    return resultado

def usuarios_de_agencia(agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE agencia_id = %s ORDER BY id", (agencia_id,))
    resultado = cursor.fetchall()
    conexion.close()
    return resultado

def contar_admins_agencia(agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT COUNT(*) FROM usuarios WHERE agencia_id = %s AND rol = 'admin'", (agencia_id,))
    resultado = cursor.fetchone()[0]
    conexion.close()
    return resultado

def eliminar_usuario_por_id(id, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM usuarios WHERE id = %s AND agencia_id = %s", (id, agencia_id))
    conexion.commit()
    conexion.close()

def verificar_usuario(nombre_usuario, contraseña):
    usuario = obtener_usuario_por_nombre(nombre_usuario)

    if usuario is None:
        return None

    if check_password_hash(usuario[2], contraseña):
        return usuario
    else:
        return None