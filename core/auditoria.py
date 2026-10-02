from core.database import obtener_conexion


def registrar_auditoria(agencia_id, usuario_id, nombre_usuario, accion, entidad, entidad_id, descripcion):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        """INSERT INTO auditoria (agencia_id, usuario_id, nombre_usuario, accion, entidad, entidad_id, descripcion)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (agencia_id, usuario_id, nombre_usuario, accion, entidad, entidad_id, descripcion)
    )
    conexion.commit()
    conexion.close()


def obtener_auditoria_paginado(agencia_id, pagina, por_pagina):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT COUNT(*) FROM auditoria WHERE agencia_id = %s", (agencia_id,))
    total = cursor.fetchone()[0]
    offset = (pagina - 1) * por_pagina
    cursor.execute(
        """SELECT * FROM auditoria WHERE agencia_id = %s
           ORDER BY fecha_hora DESC LIMIT %s OFFSET %s""",
        (agencia_id, por_pagina, offset)
    )
    resultados = cursor.fetchall()
    conexion.close()
    return resultados, total
