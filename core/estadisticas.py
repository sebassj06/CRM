from core.database import obtener_conexion
from datetime import date

NOMBRES_MES = {1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
               7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"}

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
    # Solo suma lo que de verdad se cobró — un pago "pendiente" (esperado a
    # futuro) todavía no es plata en la mano, así que no cuenta para el total.
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT SUM(monto) FROM pagos WHERE agencia_id = %s AND estado = 'cobrado'", (agencia_id,))
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


def ingresos_por_mes(agencia_id, meses=6):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT fecha, monto FROM pagos WHERE agencia_id = %s AND estado = 'cobrado'", (agencia_id,))
    filas = cursor.fetchall()
    conexion.close()

    hoy = date.today()
    año, mes = hoy.year, hoy.month
    claves = []
    for _ in range(meses):
        claves.append(f"{año:04d}-{mes:02d}")
        mes -= 1
        if mes == 0:
            mes = 12
            año -= 1
    claves.reverse()

    totales = {clave: 0.0 for clave in claves}
    for fecha, monto in filas:
        if fecha and len(fecha) >= 7 and fecha[:7] in totales:
            totales[fecha[:7]] += float(monto)

    resultado = []
    for clave in claves:
        _, mes_str = clave.split("-")
        resultado.append((NOMBRES_MES[int(mes_str)], totales[clave]))
    return resultado


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
        "completados": completados,
    }