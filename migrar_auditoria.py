from core.database import obtener_conexion


def migrar_auditoria():
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS auditoria (
            id SERIAL PRIMARY KEY,
            agencia_id INTEGER,
            usuario_id INTEGER,
            nombre_usuario TEXT,
            accion TEXT,
            entidad TEXT,
            entidad_id INTEGER,
            descripcion TEXT,
            fecha_hora TIMESTAMP DEFAULT NOW())
        """)

    conexion.commit()
    cursor.close()
    conexion.close()

    print("Migración completa: tabla 'auditoria' creada.")


if __name__ == "__main__":
    migrar_auditoria()
