from core.database import obtener_conexion


def migrar():
    conexion = obtener_conexion()
    cursor = conexion.cursor()

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

    conexion.commit()
    cursor.close()
    conexion.close()

    print("Migración completa: tablas 'tareas' y 'subtareas'.")


if __name__ == "__main__":
    migrar()
