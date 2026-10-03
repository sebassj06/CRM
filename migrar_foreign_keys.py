from core.database import obtener_conexion

# (nombre_constraint, tabla, columna, tabla_referenciada, columna_referenciada, on_delete)
#
# Política de borrado, explicada:
# - None (RESTRICT, default de Postgres): relaciones "de negocio" donde el
#   dato hijo es un registro real (proyecto, pago, nota, cotización...) que
#   NO debe desaparecer en silencio si se borra el padre. La app ahora
#   bloquea el DELETE duro de clientes/proyectos con dependientes y sugiere
#   archivar en su lugar (ver web/app.py: eliminar_cliente_ruta / eliminar_proyecto_ruta).
# - CASCADE: sub-entidades sin vida propia fuera de su padre (los ítems de
#   una cotización, las subtareas de una tarea) - borrar el padre debe
#   borrarlas también. eliminar_cotizacion_por_id ya lo hacía a mano en
#   Python para cotizacion_items; para subtareas NO existía ese paso, así
#   que hoy mismo (antes de esta migración) borrar una tarea deja sus
#   subtareas huérfanas - esta FK lo corrige a nivel de base de datos.
# - SET NULL: vínculos opcionales/informativos que no deben bloquear nada
#   (una tarea sin responsable ya es un estado válido del sistema; una
#   cotización "convertida" cuyo proyecto se borró simplemente deja de
#   mostrar el link, pero la cotización en sí sigue existiendo).
FOREIGN_KEYS = [
    ("fk_proyectos_cliente", "proyectos", "cliente_id", "clientes", "id", None),
    ("fk_notas_cliente", "notas", "cliente_id", "clientes", "id", None),
    ("fk_cotizaciones_cliente", "cotizaciones", "cliente_id", "clientes", "id", None),
    ("fk_pagos_proyecto", "pagos", "proyecto_id", "proyectos", "id", None),
    ("fk_tareas_proyecto", "tareas", "proyecto_id", "proyectos", "id", None),
    ("fk_gastos_proyecto", "gastos", "proyecto_id", "proyectos", "id", None),
    ("fk_cotizaciones_proyecto", "cotizaciones", "proyecto_id", "proyectos", "id", "SET NULL"),
    ("fk_subtareas_tarea", "subtareas", "tarea_id", "tareas", "id", "CASCADE"),
    ("fk_cotizacion_items_cotizacion", "cotizacion_items", "cotizacion_id", "cotizaciones", "id", "CASCADE"),
    ("fk_tareas_responsable", "tareas", "responsable_id", "usuarios", "id", "SET NULL"),
    ("fk_clientes_agencia", "clientes", "agencia_id", "agencias", "id", None),
    ("fk_proyectos_agencia", "proyectos", "agencia_id", "agencias", "id", None),
    ("fk_pagos_agencia", "pagos", "agencia_id", "agencias", "id", None),
    ("fk_notas_agencia", "notas", "agencia_id", "agencias", "id", None),
    ("fk_usuarios_agencia", "usuarios", "agencia_id", "agencias", "id", None),
    ("fk_tareas_agencia", "tareas", "agencia_id", "agencias", "id", None),
    ("fk_gastos_agencia", "gastos", "agencia_id", "agencias", "id", None),
    ("fk_cotizaciones_agencia", "cotizaciones", "agencia_id", "agencias", "id", None),
    ("fk_definiciones_campo_agencia", "definiciones_campo", "agencia_id", "agencias", "id", None),
    ("fk_etapas_agencia", "etapas", "agencia_id", "agencias", "id", None),
    ("fk_auditoria_agencia", "auditoria", "agencia_id", "agencias", "id", None),
]


def _ya_existe(cursor, nombre_constraint):
    cursor.execute(
        "SELECT 1 FROM information_schema.table_constraints WHERE constraint_name = %s",
        (nombre_constraint,)
    )
    return cursor.fetchone() is not None


def migrar():
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    for nombre, tabla, columna, tabla_ref, columna_ref, on_delete in FOREIGN_KEYS:
        if _ya_existe(cursor, nombre):
            print(f"  {nombre} ya existe, se omite.")
            continue

        clausula_on_delete = f" ON DELETE {on_delete}" if on_delete else ""
        sql = (
            f"ALTER TABLE {tabla} ADD CONSTRAINT {nombre} "
            f"FOREIGN KEY ({columna}) REFERENCES {tabla_ref} ({columna_ref}){clausula_on_delete}"
        )
        try:
            cursor.execute(sql)
            conexion.commit()
            print(f"  + {nombre}: {tabla}.{columna} -> {tabla_ref}.{columna_ref}{clausula_on_delete}")
        except Exception as error:
            conexion.rollback()
            print(f"  ! {nombre} FALLÓ (revisar datos huérfanos antes de reintentar): {error}")

    cursor.close()
    conexion.close()
    print("Migración de Foreign Keys completa.")


if __name__ == "__main__":
    migrar()
