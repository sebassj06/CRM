from core.database import obtener_conexion


def migrar():
    conexion = obtener_conexion()
    cursor = conexion.cursor()

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

    conexion.commit()
    cursor.close()
    conexion.close()

    print("Migración completa: tabla 'gastos'.")


if __name__ == "__main__":
    migrar()
