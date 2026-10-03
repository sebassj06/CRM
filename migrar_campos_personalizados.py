from core.database import obtener_conexion


def migrar():
    conexion = obtener_conexion()
    cursor = conexion.cursor()

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

    cursor.execute("ALTER TABLE clientes ADD COLUMN IF NOT EXISTS campos_personalizados JSONB DEFAULT '{}'")
    cursor.execute("ALTER TABLE proyectos ADD COLUMN IF NOT EXISTS campos_personalizados JSONB DEFAULT '{}'")

    conexion.commit()
    cursor.close()
    conexion.close()
    print("Migración completa: tabla 'definiciones_campo' y columna 'campos_personalizados' en clientes/proyectos.")


if __name__ == "__main__":
    migrar()
