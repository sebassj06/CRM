from core.database import obtener_conexion


def migrar():
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute("ALTER TABLE clientes ADD COLUMN IF NOT EXISTS etapa TEXT DEFAULT 'Cliente activo'")
    # Los clientes que ya existían antes de esta columna casi seguro ya son
    # clientes activos (no prospectos recién contactados), así que el default
    # de arriba los deja bien clasificados sin tener que tocarlos uno por uno.

    conexion.commit()
    cursor.close()
    conexion.close()

    print("Migración completa: columna 'etapa' en clientes.")


if __name__ == "__main__":
    migrar()
