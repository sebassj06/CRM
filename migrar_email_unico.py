from core.database import obtener_conexion


def migrar():
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute(
        "SELECT 1 FROM information_schema.table_constraints WHERE constraint_name = 'ux_clientes_agencia_email'"
    )
    if cursor.fetchone() is not None:
        print("ux_clientes_agencia_email ya existe, se omite.")
        cursor.close()
        conexion.close()
        return

    # NULL no choca contra NULL en un UNIQUE de Postgres, así que clientes sin
    # email (si los hubiera) no se ven afectados; solo se exige unicidad
    # entre emails realmente cargados dentro de la misma agencia.
    cursor.execute(
        "ALTER TABLE clientes ADD CONSTRAINT ux_clientes_agencia_email UNIQUE (agencia_id, email)"
    )
    conexion.commit()
    cursor.close()
    conexion.close()
    print("Migración completa: email único por agencia en clientes.")


if __name__ == "__main__":
    migrar()
