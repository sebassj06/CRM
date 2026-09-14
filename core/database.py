import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def obtener_conexion():
    return psycopg2.connect(os.getenv("DATABASE_URL"))


def crear_tablas():
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agencias (
            id SERIAL PRIMARY KEY,
            nombre TEXT,
            telegram_chat_id TEXT,
            gmail_user TEXT,
            gmail_app_password TEXT)
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id SERIAL PRIMARY KEY,
            nombre TEXT,
            email TEXT,
            telefono TEXT,
            empresa TEXT,
            notas TEXT,
            agencia_id INTEGER,
            cliente_desde TEXT)
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS proyectos (
            id SERIAL PRIMARY KEY,
            titulo TEXT,
            cliente_id INTEGER,
            estado TEXT,
            fecha_entrega TEXT,
            agencia_id INTEGER)
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pagos (
            id SERIAL PRIMARY KEY,
            proyecto_id INTEGER,
            monto REAL,
            fecha TEXT,
            agencia_id INTEGER)
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notas (
            id SERIAL PRIMARY KEY,
            cliente_id INTEGER,
            contenido TEXT,
            fecha TEXT,
            agencia_id INTEGER)
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            nombre_usuario TEXT UNIQUE,
            contraseña_hash TEXT,
            agencia_id INTEGER)
        """)

    conexion.commit()
    cursor.close()
    conexion.close()


if __name__ == "__main__":
    crear_tablas()
    print("Tablas creadas correctamente.")