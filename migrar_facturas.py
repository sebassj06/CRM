from core.database import obtener_conexion

FOREIGN_KEYS = [
    ("fk_facturas_proyecto", "facturas", "proyecto_id", "proyectos", "id", None),
    ("fk_facturas_agencia", "facturas", "agencia_id", "agencias", "id", None),
    ("fk_factura_items_factura", "factura_items", "factura_id", "facturas", "id", "CASCADE"),
    ("fk_pagos_factura", "pagos", "factura_id", "facturas", "id", "SET NULL"),
]


def _ya_existe(cursor, nombre_constraint):
    cursor.execute(
        "SELECT 1 FROM information_schema.table_constraints WHERE constraint_name = %s",
        (nombre_constraint,)
    )
    return cursor.fetchone() is not None


def migrar():
    conexion = obtener_conexion()
    cursor = conexion.cursor()

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

    cursor.execute("ALTER TABLE agencias ADD COLUMN IF NOT EXISTS siguiente_numero_factura INTEGER DEFAULT 1")
    cursor.execute("ALTER TABLE pagos ADD COLUMN IF NOT EXISTS factura_id INTEGER")

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_facturas_agencia ON facturas (agencia_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_facturas_proyecto ON facturas (proyecto_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_factura_items_factura ON factura_items (factura_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pagos_factura ON pagos (factura_id)")

    conexion.commit()

    for nombre, tabla, columna, tabla_ref, columna_ref, on_delete in FOREIGN_KEYS:
        if _ya_existe(cursor, nombre):
            print(f"  {nombre} ya existe, se omite.")
            continue
        clausula_on_delete = f" ON DELETE {on_delete}" if on_delete else ""
        sql = (
            f"ALTER TABLE {tabla} ADD CONSTRAINT {nombre} "
            f"FOREIGN KEY ({columna}) REFERENCES {tabla_ref} ({columna_ref}){clausula_on_delete}"
        )
        try:
            cursor.execute(sql)
            conexion.commit()
            print(f"  + {nombre}: {tabla}.{columna} -> {tabla_ref}.{columna_ref}{clausula_on_delete}")
        except Exception as error:
            conexion.rollback()
            print(f"  ! {nombre} FALLÓ (revisar datos huérfanos antes de reintentar): {error}")

    cursor.close()
    conexion.close()
    print("Migración completa: tablas 'facturas'/'factura_items', columna 'factura_id' en pagos, 'siguiente_numero_factura' en agencias.")


if __name__ == "__main__":
    migrar()
