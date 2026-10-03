from core.database import obtener_conexion

# agencia_id es la columna de filtro de practicamente cada query del sistema
# (aislamiento multi-tenant), y ninguna tabla tenia un indice sobre ella.
# Con pocas filas por agencia no se nota; con miles, cada listado hace un
# table scan completo. Estos indices son puramente aditivos: no cambian
# ningun comportamiento, solo aceleran las lecturas.
INDICES = [
    ("idx_clientes_agencia", "clientes", "(agencia_id)"),
    ("idx_proyectos_agencia", "proyectos", "(agencia_id)"),
    ("idx_proyectos_cliente", "proyectos", "(cliente_id)"),
    ("idx_pagos_agencia", "pagos", "(agencia_id)"),
    ("idx_pagos_proyecto", "pagos", "(proyecto_id)"),
    ("idx_notas_agencia", "notas", "(agencia_id)"),
    ("idx_notas_cliente", "notas", "(cliente_id)"),
    ("idx_usuarios_agencia", "usuarios", "(agencia_id)"),
    ("idx_tareas_agencia", "tareas", "(agencia_id)"),
    ("idx_tareas_proyecto", "tareas", "(proyecto_id)"),
    ("idx_tareas_responsable", "tareas", "(responsable_id)"),
    ("idx_subtareas_tarea", "subtareas", "(tarea_id)"),
    ("idx_gastos_agencia", "gastos", "(agencia_id)"),
    ("idx_gastos_proyecto", "gastos", "(proyecto_id)"),
    ("idx_cotizaciones_agencia", "cotizaciones", "(agencia_id)"),
    ("idx_cotizaciones_cliente", "cotizaciones", "(cliente_id)"),
    ("idx_cotizaciones_proyecto", "cotizaciones", "(proyecto_id)"),
    ("idx_cotizacion_items_cotizacion", "cotizacion_items", "(cotizacion_id)"),
    ("idx_auditoria_agencia", "auditoria", "(agencia_id)"),
    # compuesto: cubre tanto "todas las etapas de esta agencia" como el ORDER BY orden
    # que ya hace obtener_etapas() en cada lectura.
    ("idx_etapas_agencia_orden", "etapas", "(agencia_id, orden)"),
]


def migrar():
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    for nombre, tabla, columnas in INDICES:
        cursor.execute(f"CREATE INDEX IF NOT EXISTS {nombre} ON {tabla} {columnas}")
        print(f"  {nombre} -> {tabla}{columnas}")

    conexion.commit()
    cursor.close()
    conexion.close()
    print(f"Migración completa: {len(INDICES)} índices verificados/creados.")


if __name__ == "__main__":
    migrar()
