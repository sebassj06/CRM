import secrets
from datetime import date
from core.database import obtener_conexion

ESTADOS_COTIZACION = ["Borrador", "Enviada", "Aceptada", "Rechazada"]


def agregar_cotizacion(cliente_id, titulo, descuento, impuesto_porcentaje, fecha_vencimiento, notas, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    token = secrets.token_urlsafe(24)
    cursor.execute(
        """INSERT INTO cotizaciones (cliente_id, titulo, estado, descuento, impuesto_porcentaje, fecha_vencimiento, notas, token, agencia_id)
           VALUES (%s, %s, 'Borrador', %s, %s, %s, %s, %s, %s) RETURNING id""",
        (cliente_id, titulo, descuento, impuesto_porcentaje, fecha_vencimiento, notas, token, agencia_id)
    )
    cotizacion_id = cursor.fetchone()[0]
    conexion.commit()
    conexion.close()
    return cotizacion_id


def obtener_cotizaciones_paginado(agencia_id, pagina, por_pagina):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT COUNT(*) FROM cotizaciones WHERE agencia_id = %s", (agencia_id,))
    total = cursor.fetchone()[0]
    offset = (pagina - 1) * por_pagina
    cursor.execute(
        """SELECT cotizaciones.*, clientes.nombre FROM cotizaciones
           JOIN clientes ON clientes.id = cotizaciones.cliente_id
           WHERE cotizaciones.agencia_id = %s
           ORDER BY cotizaciones.id DESC LIMIT %s OFFSET %s""",
        (agencia_id, por_pagina, offset)
    )
    resultados = cursor.fetchall()
    conexion.close()
    return resultados, total


def obtener_cotizacion_por_id(id, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM cotizaciones WHERE id = %s AND agencia_id = %s", (id, agencia_id))
    resultado = cursor.fetchone()
    conexion.close()
    return resultado


def obtener_cotizacion_por_token(token):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM cotizaciones WHERE token = %s", (token,))
    resultado = cursor.fetchone()
    conexion.close()
    return resultado


def editar_cotizacion_por_id(id, cliente_id, titulo, descuento, impuesto_porcentaje, fecha_vencimiento, notas, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        """UPDATE cotizaciones SET cliente_id = %s, titulo = %s, descuento = %s, impuesto_porcentaje = %s,
           fecha_vencimiento = %s, notas = %s WHERE id = %s AND agencia_id = %s""",
        (cliente_id, titulo, descuento, impuesto_porcentaje, fecha_vencimiento, notas, id, agencia_id)
    )
    conexion.commit()
    conexion.close()


def eliminar_cotizacion_por_id(id, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM cotizacion_items WHERE cotizacion_id = %s", (id,))
    cursor.execute("DELETE FROM cotizaciones WHERE id = %s AND agencia_id = %s", (id, agencia_id))
    conexion.commit()
    conexion.close()


def cambiar_estado_cotizacion(id, estado, agencia_id=None):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    if agencia_id is not None:
        cursor.execute("UPDATE cotizaciones SET estado = %s WHERE id = %s AND agencia_id = %s", (estado, id, agencia_id))
    else:
        cursor.execute("UPDATE cotizaciones SET estado = %s WHERE id = %s", (estado, id))
    conexion.commit()
    conexion.close()


def marcar_convertida(id, proyecto_id, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        "UPDATE cotizaciones SET proyecto_id = %s WHERE id = %s AND agencia_id = %s",
        (proyecto_id, id, agencia_id)
    )
    conexion.commit()
    conexion.close()


def reemplazar_items(cotizacion_id, items):
    # items: lista de tuplas (descripcion, cantidad, precio_unitario). Se borran
    # los ítems anteriores y se insertan los nuevos, más simple y robusto que
    # tratar de reconciliar updates fila por fila desde un formulario con filas
    # dinámicas agregadas/quitadas en el cliente.
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM cotizacion_items WHERE cotizacion_id = %s", (cotizacion_id,))
    for orden, (descripcion, cantidad, precio_unitario) in enumerate(items):
        cursor.execute(
            "INSERT INTO cotizacion_items (cotizacion_id, descripcion, cantidad, precio_unitario, orden) VALUES (%s, %s, %s, %s, %s)",
            (cotizacion_id, descripcion, cantidad, precio_unitario, orden)
        )
    conexion.commit()
    conexion.close()


def obtener_items(cotizacion_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM cotizacion_items WHERE cotizacion_id = %s ORDER BY orden, id", (cotizacion_id,))
    resultados = cursor.fetchall()
    conexion.close()
    return resultados


def calcular_totales(items, descuento, impuesto_porcentaje):
    subtotal = sum((item[3] or 0) * (item[4] or 0) for item in items)
    con_descuento = max(subtotal - (descuento or 0), 0)
    total = con_descuento * (1 + (impuesto_porcentaje or 0) / 100)
    return subtotal, total


def cotizacion_esta_vencida(cotizacion):
    if cotizacion[3] != "Enviada" or not cotizacion[6]:
        return False
    return cotizacion[6] < date.today().isoformat()
