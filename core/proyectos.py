from core.database import obtener_conexion
from datetime import datetime, timedelta

def agregar_proyecto(titulo, cliente_id, estado, fecha_entrega, agencia_id, presupuesto=None):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("INSERT INTO proyectos (titulo, cliente_id, estado, fecha_entrega, agencia_id, presupuesto) VALUES(%s, %s, %s, %s, %s, %s)",
                   (titulo, cliente_id, estado, fecha_entrega, agencia_id, presupuesto))
    conexion.commit()
    conexion.close()

def mostrar_proyectos():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM proyectos")
    resultados = cursor.fetchall()
    conexion.close()
    for proyecto in resultados:
        print(f"id: {proyecto[0]}, titulo: {proyecto[1]}, cliente_id: {proyecto[2]}, estado: {proyecto[3]}, fecha_entrega: {proyecto[4]}")

def proyectos_de_cliente(cliente_id, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT * FROM proyectos WHERE cliente_id = %s AND agencia_id = %s AND archivado = false",
        (cliente_id, agencia_id)
    )
    resultados = cursor.fetchall()
    conexion.close()
    return resultados

def obtener_proyectos(agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM proyectos WHERE agencia_id = %s", (agencia_id,))
    resultados = cursor.fetchall()
    conexion.close()
    return resultados

def obtener_proyectos_paginado(agencia_id, pagina, por_pagina, archivados=False):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM proyectos WHERE agencia_id = %s AND archivado = %s",
        (agencia_id, archivados)
    )
    total = cursor.fetchone()[0]
    offset = (pagina - 1) * por_pagina
    cursor.execute(
        "SELECT * FROM proyectos WHERE agencia_id = %s AND archivado = %s ORDER BY id LIMIT %s OFFSET %s",
        (agencia_id, archivados, por_pagina, offset)
    )
    resultados = cursor.fetchall()
    conexion.close()
    return resultados, total

def proyectos_recientes(agencia_id, limite=5):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT * FROM proyectos WHERE agencia_id = %s AND archivado = false ORDER BY id DESC LIMIT %s",
        (agencia_id, limite)
    )
    resultados = cursor.fetchall()
    conexion.close()
    return resultados

def obtener_proyecto_por_id(id, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM proyectos WHERE id = %s AND agencia_id = %s", (id, agencia_id))
    resultado = cursor.fetchone()
    conexion.close()
    return resultado

def editar_proyecto_por_id(id, titulo, cliente_id, estado, fecha_entrega, agencia_id, presupuesto=None):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("UPDATE proyectos SET titulo = %s, cliente_id = %s, estado = %s, fecha_entrega = %s, presupuesto = %s WHERE id = %s AND agencia_id = %s",
                   (titulo, cliente_id, estado, fecha_entrega, presupuesto, id, agencia_id)
    )
    conexion.commit()
    conexion.close()

def marcar_proyecto_completado(id, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("UPDATE proyectos SET estado = 'Completado' WHERE id = %s AND agencia_id = %s", (id, agencia_id))
    conexion.commit()
    conexion.close()

def archivar_proyecto_por_id(id, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("UPDATE proyectos SET archivado = true WHERE id = %s AND agencia_id = %s", (id, agencia_id))
    conexion.commit()
    conexion.close()

def desarchivar_proyecto_por_id(id, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("UPDATE proyectos SET archivado = false WHERE id = %s AND agencia_id = %s", (id, agencia_id))
    conexion.commit()
    conexion.close()

def eliminar_proyecto_por_id(id, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM proyectos WHERE id = %s AND agencia_id = %s", (id, agencia_id))
    conexion.commit()
    conexion.close()

def _parsear_fecha(fecha_texto):
    for formato in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(fecha_texto, formato).date()
        except ValueError:
            continue
    return None

def proyecto_esta_por_vencer(estado, fecha_entrega, dias=3):
    if estado == "Completado":
        return False

    fecha = _parsear_fecha(fecha_entrega)
    if fecha is None:
        return False

    hoy = datetime.now().date()
    limite = hoy + timedelta(days=dias)
    return hoy <= fecha <= limite

def proyectos_por_vencer(agencia_id, dias=3):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT * FROM proyectos WHERE estado != 'Completado' AND agencia_id = %s AND archivado = false",
        (agencia_id,)
    )
    resultados = cursor.fetchall()
    conexion.close()

    hoy = datetime.now().date()
    limite = hoy + timedelta(days=dias)

    proyectos_filtrados = []
    for proyecto in resultados:
        fecha_entrega = _parsear_fecha(proyecto[4])
        if fecha_entrega is None:
            continue
        if hoy <= fecha_entrega <= limite:
            proyectos_filtrados.append(proyecto)

    return proyectos_filtrados