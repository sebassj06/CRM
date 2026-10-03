from core.database import obtener_conexion
from core.cifrado import cifrar, descifrar

def crear_agencia(nombre, telegram_chat_id=None, gmail_user=None, gmail_app_password=None):
    from core.etapas import sembrar_etapas_default

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        "INSERT INTO agencias (nombre, telegram_chat_id, gmail_user, gmail_app_password) VALUES (%s, %s, %s, %s) RETURNING id",
        (nombre, telegram_chat_id, gmail_user, cifrar(gmail_app_password))
    )
    agencia_id = cursor.fetchone()[0]
    conexion.commit()
    conexion.close()
    sembrar_etapas_default(agencia_id)
    return agencia_id

def actualizar_configuracion_agencia(agencia_id, telegram_chat_id, gmail_user, gmail_app_password, moneda="USD"):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        """UPDATE agencias
           SET telegram_chat_id = %s,
               gmail_user = %s,
               gmail_app_password = COALESCE(%s, gmail_app_password),
               moneda = %s
           WHERE id = %s""",
        (telegram_chat_id, gmail_user, cifrar(gmail_app_password), moneda, agencia_id)
    )
    conexion.commit()
    conexion.close()

def obtener_agencia_por_id(id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM agencias WHERE id = %s", (id,))
    resultado = cursor.fetchone()
    conexion.close()
    if resultado is not None:
        # gmail_app_password (índice 4) se guarda cifrado en reposo; se
        # descifra acá para que el resto del código (enviar_correo, etc.)
        # siga leyendo agencia[4] como la contraseña real, sin cambios.
        resultado = resultado[:4] + (descifrar(resultado[4]),) + resultado[5:]
    return resultado

def obtener_agencias():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM agencias")
    resultados = cursor.fetchall()
    conexion.close()
    return resultados