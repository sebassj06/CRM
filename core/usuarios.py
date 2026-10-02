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


def verificar_password_usuario(id, contraseña):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT contraseña_hash FROM usuarios WHERE id = %s", (id,))
    resultado = cursor.fetchone()
    conexion.close()
    return bool(resultado and check_password_hash(resultado[0], contraseña))


def actualizar_perfil_usuario(id, nombre_usuario):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("UPDATE usuarios SET nombre_usuario = %s WHERE id = %s", (nombre_usuario, id))
    conexion.commit()
    conexion.close()


def actualizar_foto_perfil(id, ruta_foto):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("UPDATE usuarios SET foto_perfil = %s WHERE id = %s", (ruta_foto, id))
    conexion.commit()
    conexion.close()


def cambiar_contraseña_usuario(id, contraseña_nueva):
    contraseña_hash = generate_password_hash(contraseña_nueva)
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("UPDATE usuarios SET contraseña_hash = %s WHERE id = %s", (contraseña_hash, id))
    conexion.commit()
    conexion.close()


def crear_verificacion_email(usuario_id, email_nuevo, codigo):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    # Solo puede haber un código pendiente a la vez por usuario: los anteriores quedan obsoletos.
    cursor.execute("DELETE FROM verificaciones_email WHERE usuario_id = %s", (usuario_id,))
    cursor.execute(
        "INSERT INTO verificaciones_email (usuario_id, email_nuevo, codigo) VALUES (%s, %s, %s)",
        (usuario_id, email_nuevo, codigo)
    )
    conexion.commit()
    conexion.close()


def obtener_verificacion_email_pendiente(usuario_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        """SELECT * FROM verificaciones_email
           WHERE usuario_id = %s AND creado_en > NOW() - INTERVAL '15 minutes'
           ORDER BY creado_en DESC LIMIT 1""",
        (usuario_id,)
    )
    resultado = cursor.fetchone()
    conexion.close()
    return resultado


def confirmar_verificacion_email(usuario_id, codigo):
    verificacion = obtener_verificacion_email_pendiente(usuario_id)
    if verificacion is None or verificacion[3] != codigo:
        return False

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("UPDATE usuarios SET email = %s WHERE id = %s", (verificacion[2], usuario_id))
    cursor.execute("DELETE FROM verificaciones_email WHERE usuario_id = %s", (usuario_id,))
    conexion.commit()
    conexion.close()
    return True