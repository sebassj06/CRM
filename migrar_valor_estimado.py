from core.database import obtener_conexion


def migrar():
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute("ALTER TABLE clientes ADD COLUMN IF NOT EXISTS valor_estimado REAL")

    conexion.commit()
    cursor.close()
    conexion.close()

    print("Migración completa: columna 'valor_estimado' en clientes.")


if __name__ == "__main__":
    migrar()
