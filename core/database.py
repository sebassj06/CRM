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


# Mirror exacto de migrar_indices.py / migrar_foreign_keys.py, para que una
# instalación nueva (python core/database.py) quede con el mismo esquema que
# una ya migrada, sin tener que correr los scripts sueltos a mano.
_INDICES = [
    ("idx_clientes_agencia", "clientes", "(agencia_id)"),
    ("idx_proyectos_agencia", "proyectos", "(agencia_id)"),
    ("idx_proyectos_cliente", "proyectos", "(cliente_id)"),
    ("idx_pagos_agencia", "pagos", "(agencia_id)"),
    ("idx_pagos_proyecto", "pagos", "(proyecto_id)"),
    ("idx_notas_agencia", "notas", "(agencia_id)"),
    ("idx_notas_cliente", "notas", "(cliente_id)"),
    ("idx_usuarios_agencia", "usuarios", "(agencia_id)"),
    ("idx_tareas_agencia", "tareas", "(agencia_id)"),
    ("idx_tareas_proyecto", "tareas", "(proyecto_id)"),
    ("idx_tareas_responsable", "tareas", "(responsable_id)"),
    ("idx_subtareas_tarea", "subtareas", "(tarea_id)"),
    ("idx_gastos_agencia", "gastos", "(agencia_id)"),
    ("idx_gastos_proyecto", "gastos", "(proyecto_id)"),
    ("idx_cotizaciones_agencia", "cotizaciones", "(agencia_id)"),
    ("idx_cotizaciones_cliente", "cotizaciones", "(cliente_id)"),
    ("idx_cotizaciones_proyecto", "cotizaciones", "(proyecto_id)"),
    ("idx_cotizacion_items_cotizacion", "cotizacion_items", "(cotizacion_id)"),
    ("idx_auditoria_agencia", "auditoria", "(agencia_id)"),
    ("idx_etapas_agencia_orden", "etapas", "(agencia_id, orden)"),
    ("idx_facturas_agencia", "facturas", "(agencia_id)"),
    ("idx_facturas_proyecto", "facturas", "(proyecto_id)"),
    ("idx_factura_items_factura", "factura_items", "(factura_id)"),
    ("idx_pagos_factura", "pagos", "(factura_id)"),
]

_FOREIGN_KEYS = [
    ("fk_proyectos_cliente", "proyectos", "cliente_id", "clientes", "id", None),
    ("fk_notas_cliente", "notas", "cliente_id", "clientes", "id", None),
    ("fk_cotizaciones_cliente", "cotizaciones", "cliente_id", "clientes", "id", None),
    ("fk_pagos_proyecto", "pagos", "proyecto_id", "proyectos", "id", None),
    ("fk_tareas_proyecto", "tareas", "proyecto_id", "proyectos", "id", None),
    ("fk_gastos_proyecto", "gastos", "proyecto_id", "proyectos", "id", None),
    ("fk_cotizaciones_proyecto", "cotizaciones", "proyecto_id", "proyectos", "id", "SET NULL"),
    ("fk_subtareas_tarea", "subtareas", "tarea_id", "tareas", "id", "CASCADE"),
    ("fk_cotizacion_items_cotizacion", "cotizacion_items", "cotizacion_id", "cotizaciones", "id", "CASCADE"),
    ("fk_tareas_responsable", "tareas", "responsable_id", "usuarios", "id", "SET NULL"),
    ("fk_clientes_agencia", "clientes", "agencia_id", "agencias", "id", None),
    ("fk_proyectos_agencia", "proyectos", "agencia_id", "agencias", "id", None),
    ("fk_pagos_agencia", "pagos", "agencia_id", "agencias", "id", None),
    ("fk_notas_agencia", "notas", "agencia_id", "agencias", "id", None),
    ("fk_usuarios_agencia", "usuarios", "agencia_id", "agencias", "id", None),
    ("fk_tareas_agencia", "tareas", "agencia_id", "agencias", "id", None),
    ("fk_gastos_agencia", "gastos", "agencia_id", "agencias", "id", None),
    ("fk_cotizaciones_agencia", "cotizaciones", "agencia_id", "agencias", "id", None),
    ("fk_definiciones_campo_agencia", "definiciones_campo", "agencia_id", "agencias", "id", None),
    ("fk_etapas_agencia", "etapas", "agencia_id", "agencias", "id", None),
    ("fk_auditoria_agencia", "auditoria", "agencia_id", "agencias", "id", None),
    ("fk_facturas_proyecto", "facturas", "proyecto_id", "proyectos", "id", None),
    ("fk_facturas_agencia", "facturas", "agencia_id", "agencias", "id", None),
    ("fk_factura_items_factura", "factura_items", "factura_id", "facturas", "id", "CASCADE"),
    ("fk_pagos_factura", "pagos", "factura_id", "facturas", "id", "SET NULL"),
]


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
            moneda TEXT DEFAULT 'USD',
            siguiente_numero_factura INTEGER DEFAULT 1)
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
            valor_estimado REAL,
            campos_personalizados JSONB DEFAULT '{}')
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
            archivado BOOLEAN DEFAULT false,
            campos_personalizados JSONB DEFAULT '{}')
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pagos (
            id SERIAL PRIMARY KEY,
            proyecto_id INTEGER,
            monto REAL,
            fecha TEXT,
            agencia_id INTEGER,
            estado TEXT DEFAULT 'cobrado',
            factura_id INTEGER)
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
        CREATE TABLE IF NOT EXISTS definiciones_campo (
            id SERIAL PRIMARY KEY,
            agencia_id INTEGER NOT NULL,
            entidad TEXT NOT NULL,
            nombre_campo TEXT NOT NULL,
            etiqueta TEXT NOT NULL,
            tipo TEXT NOT NULL,
            opciones TEXT,
            orden INTEGER DEFAULT 0,
            obligatorio BOOLEAN DEFAULT false)
        """)

    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ux_definiciones_campo_slug
        ON definiciones_campo (agencia_id, entidad, nombre_campo)
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS etapas (
            id SERIAL PRIMARY KEY,
            agencia_id INTEGER NOT NULL,
            nombre TEXT NOT NULL,
            orden INTEGER NOT NULL DEFAULT 0,
            es_final BOOLEAN NOT NULL DEFAULT false)
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS facturas (
            id SERIAL PRIMARY KEY,
            proyecto_id INTEGER NOT NULL,
            numero_secuencial INTEGER NOT NULL,
            estado TEXT DEFAULT 'Borrador',
            descuento REAL DEFAULT 0,
            impuesto_porcentaje REAL DEFAULT 0,
            fecha_emision TEXT,
            fecha_vencimiento TEXT,
            notas TEXT,
            token TEXT UNIQUE,
            agencia_id INTEGER,
            creado_en TIMESTAMP DEFAULT NOW())
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS factura_items (
            id SERIAL PRIMARY KEY,
            factura_id INTEGER,
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

    for nombre_indice, tabla, columnas in _INDICES:
        cursor.execute(f"CREATE INDEX IF NOT EXISTS {nombre_indice} ON {tabla} {columnas}")

    for nombre_fk, tabla, columna, tabla_ref, columna_ref, on_delete in _FOREIGN_KEYS:
        cursor.execute(
            "SELECT 1 FROM information_schema.table_constraints WHERE constraint_name = %s",
            (nombre_fk,)
        )
        if cursor.fetchone() is None:
            clausula_on_delete = f" ON DELETE {on_delete}" if on_delete else ""
            cursor.execute(
                f"ALTER TABLE {tabla} ADD CONSTRAINT {nombre_fk} "
                f"FOREIGN KEY ({columna}) REFERENCES {tabla_ref} ({columna_ref}){clausula_on_delete}"
            )

    conexion.commit()
    cursor.close()
    conexion.close()


if __name__ == "__main__":
    crear_tablas()
    print("Tablas creadas correctamente.")