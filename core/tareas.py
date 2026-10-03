from datetime import date, timedelta
from core.database import obtener_conexion

PRIORIDADES = ["Baja", "Media", "Alta"]
ESTADOS = ["Pendiente", "En progreso", "Completado"]


def agregar_tarea(proyecto_id, titulo, descripcion, responsable_id, prioridad, fecha_limite, agencia_id, estado="Pendiente"):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        """INSERT INTO tareas (proyecto_id, titulo, descripcion, responsable_id, prioridad, estado, fecha_limite, agencia_id)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
        (proyecto_id, titulo, descripcion, responsable_id, prioridad, estado, fecha_limite, agencia_id)
    )
    conexion.commit()
    conexion.close()


def obtener_tareas_proyecto(proyecto_id, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT * FROM tareas WHERE proyecto_id = %s AND agencia_id = %s ORDER BY id",
        (proyecto_id, agencia_id)
    )
    resultados = cursor.fetchall()
    conexion.close()
    return resultados


def tareas_de_cliente(cliente_id, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        """SELECT tareas.*, proyectos.titulo FROM tareas
           JOIN proyectos ON proyectos.id = tareas.proyecto_id
           WHERE proyectos.cliente_id = %s AND proyectos.agencia_id = %s AND tareas.agencia_id = %s
           ORDER BY tareas.id DESC""",
        (cliente_id, agencia_id, agencia_id)
    )
    resultados = cursor.fetchall()
    conexion.close()
    return resultados


def obtener_tareas(agencia_id, responsable_id=None):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    if responsable_id is not None:
        cursor.execute(
            """SELECT tareas.*, proyectos.titulo FROM tareas
               JOIN proyectos ON proyectos.id = tareas.proyecto_id
               WHERE tareas.agencia_id = %s AND tareas.responsable_id = %s
               ORDER BY tareas.id DESC""",
            (agencia_id, responsable_id)
        )
    else:
        cursor.execute(
            """SELECT tareas.*, proyectos.titulo FROM tareas
               JOIN proyectos ON proyectos.id = tareas.proyecto_id
               WHERE tareas.agencia_id = %s
               ORDER BY tareas.id DESC""",
            (agencia_id,)
        )
    resultados = cursor.fetchall()
    conexion.close()
    return resultados


def obtener_tareas_paginado(agencia_id, pagina, por_pagina, responsable_id=None):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    if responsable_id is not None:
        cursor.execute(
            "SELECT COUNT(*) FROM tareas WHERE agencia_id = %s AND responsable_id = %s",
            (agencia_id, responsable_id)
        )
        total = cursor.fetchone()[0]
        offset = (pagina - 1) * por_pagina
        cursor.execute(
            """SELECT tareas.*, proyectos.titulo FROM tareas
               JOIN proyectos ON proyectos.id = tareas.proyecto_id
               WHERE tareas.agencia_id = %s AND tareas.responsable_id = %s
               ORDER BY tareas.id DESC LIMIT %s OFFSET %s""",
            (agencia_id, responsable_id, por_pagina, offset)
        )
    else:
        cursor.execute("SELECT COUNT(*) FROM tareas WHERE agencia_id = %s", (agencia_id,))
        total = cursor.fetchone()[0]
        offset = (pagina - 1) * por_pagina
        cursor.execute(
            """SELECT tareas.*, proyectos.titulo FROM tareas
               JOIN proyectos ON proyectos.id = tareas.proyecto_id
               WHERE tareas.agencia_id = %s
               ORDER BY tareas.id DESC LIMIT %s OFFSET %s""",
            (agencia_id, por_pagina, offset)
        )
    resultados = cursor.fetchall()
    conexion.close()
    return resultados, total


def obtener_tarea_por_id(id, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM tareas WHERE id = %s AND agencia_id = %s", (id, agencia_id))
    resultado = cursor.fetchone()
    conexion.close()
    return resultado


def editar_tarea_por_id(id, proyecto_id, titulo, descripcion, responsable_id, prioridad, estado, fecha_limite, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        """UPDATE tareas SET proyecto_id = %s, titulo = %s, descripcion = %s, responsable_id = %s,
           prioridad = %s, estado = %s, fecha_limite = %s WHERE id = %s AND agencia_id = %s""",
        (proyecto_id, titulo, descripcion, responsable_id, prioridad, estado, fecha_limite, id, agencia_id)
    )
    conexion.commit()
    conexion.close()


def eliminar_tarea_por_id(id, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM tareas WHERE id = %s AND agencia_id = %s", (id, agencia_id))
    conexion.commit()
    conexion.close()


def marcar_estado_tarea(id, agencia_id, estado):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        "UPDATE tareas SET estado = %s WHERE id = %s AND agencia_id = %s",
        (estado, id, agencia_id)
    )
    conexion.commit()
    conexion.close()


def tareas_por_vencer(agencia_id, dias=3):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    hoy = date.today()
    limite = hoy + timedelta(days=dias)
    cursor.execute(
        """SELECT tareas.*, proyectos.titulo FROM tareas
           JOIN proyectos ON proyectos.id = tareas.proyecto_id
           WHERE tareas.agencia_id = %s AND tareas.estado != 'Completado'
           AND tareas.fecha_limite >= %s AND tareas.fecha_limite <= %s
           ORDER BY tareas.fecha_limite ASC""",
        (agencia_id, hoy.isoformat(), limite.isoformat())
    )
    resultados = cursor.fetchall()
    conexion.close()
    return resultados


def progreso_proyecto(proyecto_id, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT COUNT(*), COUNT(*) FILTER (WHERE estado = 'Completado') FROM tareas WHERE proyecto_id = %s AND agencia_id = %s",
        (proyecto_id, agencia_id)
    )
    total, completadas = cursor.fetchone()
    conexion.close()
    return completadas, total


def agregar_subtarea(tarea_id, texto):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT COALESCE(MAX(orden), -1) + 1 FROM subtareas WHERE tarea_id = %s",
        (tarea_id,)
    )
    orden = cursor.fetchone()[0]
    cursor.execute(
        "INSERT INTO subtareas (tarea_id, texto, orden) VALUES (%s, %s, %s)",
        (tarea_id, texto, orden)
    )
    conexion.commit()
    conexion.close()


def obtener_subtareas(tarea_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT * FROM subtareas WHERE tarea_id = %s ORDER BY orden, id",
        (tarea_id,)
    )
    resultados = cursor.fetchall()
    conexion.close()
    return resultados


def obtener_subtarea_por_id(id, tarea_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM subtareas WHERE id = %s AND tarea_id = %s", (id, tarea_id))
    resultado = cursor.fetchone()
    conexion.close()
    return resultado


def alternar_subtarea(id, tarea_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        "UPDATE subtareas SET completada = NOT completada WHERE id = %s AND tarea_id = %s",
        (id, tarea_id)
    )
    conexion.commit()
    conexion.close()


def eliminar_subtarea(id, tarea_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM subtareas WHERE id = %s AND tarea_id = %s", (id, tarea_id))
    conexion.commit()
    conexion.close()
