from core.database import obtener_conexion


def migrar():
    conexion = obtener_conexion()
    cursor = conexion.cursor()

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

    conexion.commit()
    cursor.close()
    conexion.close()

    print("Migración completa: tablas 'cotizaciones' y 'cotizacion_items'.")


if __name__ == "__main__":
    migrar()
