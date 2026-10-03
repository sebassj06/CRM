from core.database import obtener_conexion

ETAPAS_POR_DEFECTO = [
    ("Pendiente", 1, False),
    ("En progreso", 2, False),
    ("Completado", 3, True),
]


def contar_etapas(agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT COUNT(*) FROM etapas WHERE agencia_id = %s", (agencia_id,))
    total = cursor.fetchone()[0]
    conexion.close()
    return total


def contar_etapas_finales(agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT COUNT(*) FROM etapas WHERE agencia_id = %s AND es_final = true", (agencia_id,))
    total = cursor.fetchone()[0]
    conexion.close()
    return total


def sembrar_etapas_default(agencia_id):
    if contar_etapas(agencia_id) > 0:
        return
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    for nombre, orden, es_final in ETAPAS_POR_DEFECTO:
        cursor.execute(
            "INSERT INTO etapas (agencia_id, nombre, orden, es_final) VALUES (%s, %s, %s, %s)",
            (agencia_id, nombre, orden, es_final)
        )
    conexion.commit()
    conexion.close()


def agregar_etapa(agencia_id, nombre, es_final=False):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT COALESCE(MAX(orden), 0) FROM etapas WHERE agencia_id = %s", (agencia_id,))
    siguiente_orden = cursor.fetchone()[0] + 1
    cursor.execute(
        "INSERT INTO etapas (agencia_id, nombre, orden, es_final) VALUES (%s, %s, %s, %s) RETURNING id",
        (agencia_id, nombre, siguiente_orden, es_final)
    )
    etapa_id = cursor.fetchone()[0]
    conexion.commit()
    conexion.close()
    return etapa_id


def obtener_etapas(agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM etapas WHERE agencia_id = %s ORDER BY orden", (agencia_id,))
    resultados = cursor.fetchall()
    conexion.close()
    return resultados


def obtener_etapa_por_id(id, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM etapas WHERE id = %s AND agencia_id = %s", (id, agencia_id))
    resultado = cursor.fetchone()
    conexion.close()
    return resultado


def editar_etapa_por_id(id, agencia_id, nombre, es_final):
    """Si el nombre cambia, actualiza también los proyectos que ya tenían el
    nombre viejo como 'estado' (proyectos.estado es TEXT libre, sin FK a esta
    tabla) para que no queden desenganchados del catálogo de etapas."""
    etapa_actual = obtener_etapa_por_id(id, agencia_id)
    if etapa_actual is None:
        return

    nombre_anterior = etapa_actual[2]

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        "UPDATE etapas SET nombre = %s, es_final = %s WHERE id = %s AND agencia_id = %s",
        (nombre, es_final, id, agencia_id)
    )
    if nombre != nombre_anterior:
        cursor.execute(
            "UPDATE proyectos SET estado = %s WHERE estado = %s AND agencia_id = %s",
            (nombre, nombre_anterior, agencia_id)
        )
    conexion.commit()
    conexion.close()


def eliminar_etapa_por_id(id, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM etapas WHERE id = %s AND agencia_id = %s", (id, agencia_id))
    conexion.commit()
    conexion.close()


def mover_etapa(id, agencia_id, direccion):
    """direccion: 'arriba' o 'abajo'. Intercambia el 'orden' con la etapa
    vecina en esa dirección."""
    etapas = obtener_etapas(agencia_id)
    posicion = next((i for i, etapa in enumerate(etapas) if etapa[0] == id), None)
    if posicion is None:
        return

    vecina = posicion - 1 if direccion == "arriba" else posicion + 1
    if vecina < 0 or vecina >= len(etapas):
        return

    etapa_actual = etapas[posicion]
    etapa_vecina = etapas[vecina]

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        "UPDATE etapas SET orden = %s WHERE id = %s AND agencia_id = %s",
        (etapa_vecina[3], etapa_actual[0], agencia_id)
    )
    cursor.execute(
        "UPDATE etapas SET orden = %s WHERE id = %s AND agencia_id = %s",
        (etapa_actual[3], etapa_vecina[0], agencia_id)
    )
    conexion.commit()
    conexion.close()


def nombres_etapas(agencia_id):
    return [etapa[2] for etapa in obtener_etapas(agencia_id)]


def nombres_etapas_finales(agencia_id):
    return [etapa[2] for etapa in obtener_etapas(agencia_id) if etapa[4]]


def etapa_es_final(agencia_id, nombre):
    return nombre in nombres_etapas_finales(agencia_id)


def etapa_final_principal(agencia_id):
    """La etapa es_final=true con menor 'orden', o None si la agencia no
    tiene ninguna etapa final configurada (no debería pasar en la práctica,
    ya que la eliminación/edición de etapas garantiza al menos una)."""
    for etapa in obtener_etapas(agencia_id):
        if etapa[4]:
            return etapa
    return None


def nombre_etapa_duplicado(agencia_id, nombre, excluir_id=None):
    for etapa in obtener_etapas(agencia_id):
        if etapa[2].strip().lower() == nombre.strip().lower() and etapa[0] != excluir_id:
            return True
    return False


def mapa_clases_badge(agencia_id):
    """Generaliza el viejo diccionario fijo {'Pendiente': ..., 'En progreso':
    ..., 'Completado': ...} a cualquier cantidad de etapas con nombres
    arbitrarios: la primera etapa no-final es 'pendiente', las finales son
    'completado', y todo lo demás (el 'medio' del pipeline) es 'progreso'."""
    etapas = obtener_etapas(agencia_id)
    no_finales = [etapa for etapa in etapas if not etapa[4]]
    primera_no_final_id = no_finales[0][0] if no_finales else None

    clases = {}
    for etapa in etapas:
        if etapa[4]:
            clases[etapa[2]] = "badge-completado"
        elif etapa[0] == primera_no_final_id:
            clases[etapa[2]] = "badge-pendiente"
        else:
            clases[etapa[2]] = "badge-progreso"
    return clases
