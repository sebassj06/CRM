from core.database import obtener_conexion


def migrar_moneda_agencias():
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    # Agrega la columna si todavía no existe (seguro correrlo más de una vez).
    cursor.execute("ALTER TABLE agencias ADD COLUMN IF NOT EXISTS moneda TEXT DEFAULT 'USD'")

    conexion.commit()
    cursor.close()
    conexion.close()

    print("Migración completa: columna 'moneda' agregada a agencias (default 'USD').")


if __name__ == "__main__":
    migrar_moneda_agencias()
