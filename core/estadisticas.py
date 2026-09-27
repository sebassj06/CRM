from core.database import obtener_conexion

def contar_clientes(agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT COUNT(*) FROM clientes WHERE agencia_id = %s", (agencia_id,))
    resultado = cursor.fetchone()
    conexion.close()
    return resultado[0]

def contar_proyectos(agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT COUNT(*) FROM proyectos WHERE agencia_id = %s", (agencia_id,))
    resultado = cursor.fetchone()
    conexion.close()
    return resultado[0]

def contar_pagos(agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT COUNT(*) FROM pagos WHERE agencia_id = %s", (agencia_id,))
    resultado = cursor.fetchone()
    conexion.close()
    return resultado[0]

def total_cobrado(agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT SUM(monto) FROM pagos WHERE agencia_id = %s", (agencia_id,))
    resultado = cursor.fetchone()
    conexion.close()
    return resultado[0] or 0

def proyectos_por_estado(agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT estado, COUNT(*) FROM proyectos WHERE agencia_id = %s GROUP BY estado", (agencia_id,))
    resultados = cursor.fetchall()
    conexion.close()
    return resultados


def estadisticas_dashboard(agencia_id):
    total_clientes = contar_clientes(agencia_id)
    total_proyectos = contar_proyectos(agencia_id)
    total_pagos = contar_pagos(agencia_id)
    cobrado = total_cobrado(agencia_id)
    por_estado = proyectos_por_estado(agencia_id)

    estados_con_porcentaje = []
    completados = 0
    for estado, cantidad in por_estado:
        if total_proyectos > 0:
            porcentaje = round(cantidad / total_proyectos * 100)
        else:
            porcentaje = 0
        estados_con_porcentaje.append((estado, cantidad, porcentaje))
        if estado == "Completado":
            completados = cantidad

    if total_proyectos > 0:
        porcentaje_completado = round(completados / total_proyectos * 100)
    else:
        porcentaje_completado = 0

    return {
        "total_clientes": total_clientes,
        "total_proyectos": total_proyectos,
        "total_pagos": total_pagos,
        "cobrado": cobrado,
        "por_estado": por_estado,
        "estados_con_porcentaje": estados_con_porcentaje,
        "porcentaje_completado": porcentaje_completado,
    }