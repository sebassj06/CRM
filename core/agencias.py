from core.database import obtener_conexion

def crear_agencia(nombre, telegram_chat_id=None, gmail_user=None, gmail_app_password=None):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        "INSERT INTO agencias (nombre, telegram_chat_id, gmail_user, gmail_app_password) VALUES (%s, %s, %s, %s) RETURNING id",
        (nombre, telegram_chat_id, gmail_user, gmail_app_password)
    )
    agencia_id = cursor.fetchone()[0]
    conexion.commit()
    conexion.close()
    return agencia_id

def actualizar_configuracion_agencia(agencia_id, telegram_chat_id, gmail_user, gmail_app_password):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        """UPDATE agencias
           SET telegram_chat_id = %s,
               gmail_user = %s,
               gmail_app_password = COALESCE(%s, gmail_app_password)
           WHERE id = %s""",
        (telegram_chat_id, gmail_user, gmail_app_password, agencia_id)
    )
    conexion.commit()
    conexion.close()

def obtener_agencia_por_id(id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM agencias WHERE id = %s", (id,))
    resultado = cursor.fetchone()
    conexion.close()
    return resultado

def obtener_agencias():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM agencias")
    resultados = cursor.fetchall()
    conexion.close()
    return resultados