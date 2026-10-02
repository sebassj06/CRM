from core.database import obtener_conexion

LIMITE_POR_TIPO = 8


def buscar_todo(agencia_id, termino):
    termino = (termino or "").strip()
    if not termino:
        return {"clientes": [], "proyectos": [], "pagos": [], "notas": []}

    patron = f"%{termino}%"
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute(
        """SELECT * FROM clientes WHERE agencia_id = %s
           AND (nombre ILIKE %s OR email ILIKE %s OR empresa ILIKE %s)
           ORDER BY nombre LIMIT %s""",
        (agencia_id, patron, patron, patron, LIMITE_POR_TIPO)
    )
    clientes = cursor.fetchall()

    cursor.execute(
        """SELECT * FROM proyectos WHERE agencia_id = %s AND titulo ILIKE %s
           ORDER BY id DESC LIMIT %s""",
        (agencia_id, patron, LIMITE_POR_TIPO)
    )
    proyectos = cursor.fetchall()

    cursor.execute(
        """SELECT pagos.* FROM pagos
           JOIN proyectos ON proyectos.id = pagos.proyecto_id
           WHERE pagos.agencia_id = %s AND proyectos.titulo ILIKE %s
           ORDER BY pagos.id DESC LIMIT %s""",
        (agencia_id, patron, LIMITE_POR_TIPO)
    )
    pagos = cursor.fetchall()

    cursor.execute(
        """SELECT * FROM notas WHERE agencia_id = %s AND contenido ILIKE %s
           ORDER BY id DESC LIMIT %s""",
        (agencia_id, patron, LIMITE_POR_TIPO)
    )
    notas = cursor.fetchall()

    conexion.close()
    return {"clientes": clientes, "proyectos": proyectos, "pagos": pagos, "notas": notas}
