import os
import psycopg2
from psycopg2 import pool as psycopg2_pool
from dotenv import load_dotenv

load_dotenv()

_pool = None


def _obtener_pool():
    global _pool
    if _pool is None:
        _pool = psycopg2_pool.ThreadedConnectionPool(2, 15, os.getenv("DATABASE_URL"))
    return _pool


class _ConexionDelPool:
    """Envuelve una conexión real tomada del pool para que se comporte
    exactamente como una conexión de psycopg2 normal (cursor(), commit(),
    etc.) ante el resto del código. La única diferencia es close(): en vez
    de cerrar la conexión TCP de verdad, la devuelve al pool para que la
    reuse la siguiente consulta. Así, los ~70 lugares que ya hacen
    `conexion = obtener_conexion(); ...; conexion.close()` no necesitan
    cambiar nada, pero dejan de pagar el costo de abrir una conexión nueva
    a Postgres (y su handshake) en cada una de las varias consultas que
    hace cada página — eso era lo que hacía lenta la navegación entre
    secciones."""

    def __init__(self, conexion, pool):
        object.__setattr__(self, "_conexion", conexion)
        object.__setattr__(self, "_pool", pool)

    def __getattr__(self, nombre):
        return getattr(self._conexion, nombre)

    def close(self):
        conexion = self._conexion
        pool = self._pool
        try:
            if conexion.closed:
                pool.putconn(conexion, close=True)
            else:
                # Por si quedó una transacción implícita sin commit (lecturas
                # que nunca escriben no llaman a commit()): la cerramos antes
                # de devolver la conexión, para que el próximo que la tome
                # arranque limpio.
                conexion.rollback()
                pool.putconn(conexion)
        except Exception:
            pool.putconn(conexion, close=True)


def obtener_conexion():
    pool = _obtener_pool()
    return _ConexionDelPool(pool.getconn(), pool)


def crear_tablas():
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agencias (
            id SERIAL PRIMARY KEY,
            nombre TEXT,
            telegram_chat_id TEXT,
            gmail_user TEXT,
            gmail_app_password TEXT,
            moneda TEXT DEFAULT 'USD')
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
            cliente_desde TEXT,
            archivado BOOLEAN DEFAULT false,
            etapa TEXT DEFAULT 'Cliente activo',
            valor_estimado REAL)
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS proyectos (
            id SERIAL PRIMARY KEY,
            titulo TEXT,
            cliente_id INTEGER,
            estado TEXT,
            fecha_entrega TEXT,
            agencia_id INTEGER,
            presupuesto REAL,
            archivado BOOLEAN DEFAULT false)
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pagos (
            id SERIAL PRIMARY KEY,
            proyecto_id INTEGER,
            monto REAL,
            fecha TEXT,
            agencia_id INTEGER,
            estado TEXT DEFAULT 'cobrado')
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
            agencia_id INTEGER,
            rol TEXT DEFAULT 'miembro',
            email TEXT,
            foto_perfil TEXT)
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS verificaciones_email (
            id SERIAL PRIMARY KEY,
            usuario_id INTEGER,
            email_nuevo TEXT,
            codigo TEXT,
            creado_en TIMESTAMP DEFAULT NOW())
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tareas (
            id SERIAL PRIMARY KEY,
            proyecto_id INTEGER,
            titulo TEXT,
            descripcion TEXT,
            responsable_id INTEGER,
            prioridad TEXT DEFAULT 'Media',
            estado TEXT DEFAULT 'Pendiente',
            fecha_limite TEXT,
            agencia_id INTEGER,
            creado_en TIMESTAMP DEFAULT NOW())
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subtareas (
            id SERIAL PRIMARY KEY,
            tarea_id INTEGER,
            texto TEXT,
            completada BOOLEAN DEFAULT false,
            orden INTEGER DEFAULT 0)
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gastos (
            id SERIAL PRIMARY KEY,
            proyecto_id INTEGER,
            descripcion TEXT,
            monto REAL,
            categoria TEXT,
            proveedor TEXT,
            fecha TEXT,
            comprobante TEXT,
            agencia_id INTEGER)
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cotizaciones (
            id SERIAL PRIMARY KEY,
            cliente_id INTEGER,
            titulo TEXT,
            estado TEXT DEFAULT 'Borrador',
            descuento REAL DEFAULT 0,
            impuesto_porcentaje REAL DEFAULT 0,
            fecha_vencimiento TEXT,
            notas TEXT,
            token TEXT UNIQUE,
            proyecto_id INTEGER,
            agencia_id INTEGER,
            creado_en TIMESTAMP DEFAULT NOW())
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cotizacion_items (
            id SERIAL PRIMARY KEY,
            cotizacion_id INTEGER,
            descripcion TEXT,
            cantidad REAL DEFAULT 1,
            precio_unitario REAL,
            orden INTEGER DEFAULT 0)
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS auditoria (
            id SERIAL PRIMARY KEY,
            agencia_id INTEGER,
            usuario_id INTEGER,
            nombre_usuario TEXT,
            accion TEXT,
            entidad TEXT,
            entidad_id INTEGER,
            descripcion TEXT,
            fecha_hora TIMESTAMP DEFAULT NOW())
        """)

    conexion.commit()
    cursor.close()
    conexion.close()


if __name__ == "__main__":
    crear_tablas()
    print("Tablas creadas correctamente.")