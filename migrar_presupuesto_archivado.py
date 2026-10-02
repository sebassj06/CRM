from core.database import obtener_conexion


def migrar():
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute("ALTER TABLE proyectos ADD COLUMN IF NOT EXISTS presupuesto REAL")
    cursor.execute("ALTER TABLE proyectos ADD COLUMN IF NOT EXISTS archivado BOOLEAN DEFAULT false")
    cursor.execute("ALTER TABLE clientes ADD COLUMN IF NOT EXISTS archivado BOOLEAN DEFAULT false")

    conexion.commit()
    cursor.close()
    conexion.close()

    print("Migración completa: 'presupuesto'/'archivado' en proyectos, 'archivado' en clientes.")


if __name__ == "__main__":
    migrar()
