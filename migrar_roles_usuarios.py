from core.database import obtener_conexion


def migrar_roles_usuarios():
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    # Agrega la columna si todavía no existe (seguro correrlo más de una vez).
    cursor.execute("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS rol TEXT DEFAULT 'miembro'")

    # El usuario con el id más bajo de cada agencia es, casi siempre, el primero
    # que se creó (los ids son autoincrementales) — lo marcamos como admin.
    # El resto queda con el default 'miembro'.
    cursor.execute("""
        UPDATE usuarios
        SET rol = 'admin'
        WHERE id IN (
            SELECT MIN(id) FROM usuarios GROUP BY agencia_id
        )
    """)

    conexion.commit()
    filas_afectadas = cursor.rowcount
    cursor.close()
    conexion.close()

    print(f"Migración completa: columna 'rol' agregada. {filas_afectadas} usuario(s) marcado(s) como admin (uno por agencia).")


if __name__ == "__main__":
    migrar_roles_usuarios()
