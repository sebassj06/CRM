from core.database import obtener_conexion

def contar_clientes():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT COUNT(*) FROM clientes")
    resultado = cursor.fetchone()
    conexion.close()
    return resultado[0]

def contar_proyectos():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT COUNT(*) FROM proyectos")
    resultado = cursor.fetchone()
    conexion.close()
    return resultado[0]

def contar_pagos():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT COUNT(*) FROM pagos")
    resultado = cursor.fetchone()
    conexion.close()
    return resultado[0]

def total_cobrado():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT SUM(monto) FROM pagos")
    resultado = cursor.fetchone()
    conexion.close()
    return resultado[0] or 0

def proyectos_por_estado():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT estado, COUNT(*) FROM proyectos GROUP BY estado")
    resultados = cursor.fetchall()
    conexion.close()
    return resultados


def estadisticas_dashboard():
    total_clientes = contar_clientes()
    total_proyectos = contar_proyectos()
    total_pagos = contar_pagos()
    cobrado = total_cobrado()
    por_estado = proyectos_por_estado()

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