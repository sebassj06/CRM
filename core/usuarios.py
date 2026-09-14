from core.database import obtener_conexion
from werkzeug.security import generate_password_hash, check_password_hash

def crear_usuario(nombre_usuario, contraseña, agencia_id):
    contraseña_hash = generate_password_hash(contraseña)
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("INSERT INTO usuarios (nombre_usuario, contraseña_hash, agencia_id) VALUES (%s, %s, %s)",
                   (nombre_usuario, contraseña_hash, agencia_id))
    conexion.commit()
    conexion.close()

def obtener_usuario_por_nombre(nombre_usuario):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE nombre_usuario = %s", (nombre_usuario,))
    resultado = cursor.fetchone()
    conexion.close()
    return resultado

def verificar_usuario(nombre_usuario, contraseña):
    usuario = obtener_usuario_por_nombre(nombre_usuario)

    if usuario is None:
        return None

    if check_password_hash(usuario[2], contraseña):
        return usuario
    else:
        return None