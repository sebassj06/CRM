from core.database import obtener_conexion


def migrar_perfil():
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS email TEXT")
    cursor.execute("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS foto_perfil TEXT")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS verificaciones_email (
            id SERIAL PRIMARY KEY,
            usuario_id INTEGER,
            email_nuevo TEXT,
            codigo TEXT,
            creado_en TIMESTAMP DEFAULT NOW())
        """)

    conexion.commit()
    cursor.close()
    conexion.close()

    print("Migración completa: columnas 'email'/'foto_perfil' en usuarios, tabla 'verificaciones_email' creada.")


if __name__ == "__main__":
    migrar_perfil()
