from core.database import obtener_conexion

CATEGORIAS_GASTO = ["Software/herramientas", "Freelancers/subcontratos", "Publicidad", "Viáticos", "Otro"]


def agregar_gasto(proyecto_id, descripcion, monto, categoria, proveedor, fecha, agencia_id, comprobante=None):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        """INSERT INTO gastos (proyecto_id, descripcion, monto, categoria, proveedor, fecha, comprobante, agencia_id)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
        (proyecto_id, descripcion, monto, categoria, proveedor, fecha, comprobante, agencia_id)
    )
    conexion.commit()
    conexion.close()


def obtener_gastos_proyecto(proyecto_id, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT * FROM gastos WHERE proyecto_id = %s AND agencia_id = %s ORDER BY id DESC",
        (proyecto_id, agencia_id)
    )
    resultados = cursor.fetchall()
    conexion.close()
    return resultados


def obtener_gastos_paginado(agencia_id, pagina, por_pagina):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT COUNT(*) FROM gastos WHERE agencia_id = %s", (agencia_id,))
    total = cursor.fetchone()[0]
    offset = (pagina - 1) * por_pagina
    cursor.execute(
        """SELECT gastos.*, proyectos.titulo FROM gastos
           JOIN proyectos ON proyectos.id = gastos.proyecto_id
           WHERE gastos.agencia_id = %s
           ORDER BY gastos.id DESC LIMIT %s OFFSET %s""",
        (agencia_id, por_pagina, offset)
    )
    resultados = cursor.fetchall()
    conexion.close()
    return resultados, total


def obtener_gasto_por_id(id, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM gastos WHERE id = %s AND agencia_id = %s", (id, agencia_id))
    resultado = cursor.fetchone()
    conexion.close()
    return resultado


def editar_gasto_por_id(id, proyecto_id, descripcion, monto, categoria, proveedor, fecha, agencia_id, comprobante=None):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    if comprobante is not None:
        cursor.execute(
            """UPDATE gastos SET proyecto_id = %s, descripcion = %s, monto = %s, categoria = %s,
               proveedor = %s, fecha = %s, comprobante = %s WHERE id = %s AND agencia_id = %s""",
            (proyecto_id, descripcion, monto, categoria, proveedor, fecha, comprobante, id, agencia_id)
        )
    else:
        cursor.execute(
            """UPDATE gastos SET proyecto_id = %s, descripcion = %s, monto = %s, categoria = %s,
               proveedor = %s, fecha = %s WHERE id = %s AND agencia_id = %s""",
            (proyecto_id, descripcion, monto, categoria, proveedor, fecha, id, agencia_id)
        )
    conexion.commit()
    conexion.close()


def eliminar_gasto_por_id(id, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM gastos WHERE id = %s AND agencia_id = %s", (id, agencia_id))
    conexion.commit()
    conexion.close()


def total_gastos_proyecto(proyecto_id, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT COALESCE(SUM(monto), 0) FROM gastos WHERE proyecto_id = %s AND agencia_id = %s",
        (proyecto_id, agencia_id)
    )
    total = cursor.fetchone()[0]
    conexion.close()
    return total


def rentabilidad_cliente(cliente_id, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        """SELECT COALESCE(SUM(pagos.monto), 0) FROM pagos
           JOIN proyectos ON proyectos.id = pagos.proyecto_id
           WHERE proyectos.cliente_id = %s AND proyectos.agencia_id = %s
           AND pagos.agencia_id = %s AND pagos.estado = 'cobrado'""",
        (cliente_id, agencia_id, agencia_id)
    )
    cobrado = cursor.fetchone()[0]

    cursor.execute(
        """SELECT COALESCE(SUM(gastos.monto), 0) FROM gastos
           JOIN proyectos ON proyectos.id = gastos.proyecto_id
           WHERE proyectos.cliente_id = %s AND proyectos.agencia_id = %s
           AND gastos.agencia_id = %s""",
        (cliente_id, agencia_id, agencia_id)
    )
    gastos = cursor.fetchone()[0]
    conexion.close()
    return cobrado, gastos, cobrado - gastos
