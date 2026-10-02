from core.database import obtener_conexion


def migrar_estado_pagos():
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    # Agrega la columna si todavía no existe (seguro correrlo más de una vez).
    # Los pagos ya existentes se asumen cobrados: son plata que ya se registró
    # como recibida, no pagos pendientes a futuro.
    cursor.execute("ALTER TABLE pagos ADD COLUMN IF NOT EXISTS estado TEXT DEFAULT 'cobrado'")

    conexion.commit()
    cursor.close()
    conexion.close()

    print("Migración completa: columna 'estado' agregada a pagos (default 'cobrado').")


if __name__ == "__main__":
    migrar_estado_pagos()
