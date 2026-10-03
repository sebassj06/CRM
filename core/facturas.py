import secrets
from datetime import date
from core.database import obtener_conexion

ESTADOS_FACTURA = ["Borrador", "Emitida", "Pagada", "Anulada"]
# "Vencida" es derivado/visual (ver factura_esta_vencida), nunca se guarda —
# igual que cotizacion_esta_vencida.


def agregar_factura(proyecto_id, descuento, impuesto_porcentaje, fecha_emision, fecha_vencimiento, notas, agencia_id):
    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor()
        token = secrets.token_urlsafe(24)
        # Numeración atómica por agencia: el UPDATE...RETURNING toma el lock
        # de la fila de 'agencias' hasta el commit, así que una segunda
        # factura de la misma agencia creada en simultáneo espera ese lock
        # en vez de repetir el número. No hace falta SEQUENCE ni locking
        # explícito nuevo.
        cursor.execute(
            "UPDATE agencias SET siguiente_numero_factura = siguiente_numero_factura + 1 "
            "WHERE id = %s RETURNING siguiente_numero_factura - 1",
            (agencia_id,)
        )
        numero = cursor.fetchone()[0]
        cursor.execute(
            """INSERT INTO facturas (proyecto_id, numero_secuencial, estado, descuento, impuesto_porcentaje,
               fecha_emision, fecha_vencimiento, notas, token, agencia_id)
               VALUES (%s, %s, 'Borrador', %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
            (proyecto_id, numero, descuento, impuesto_porcentaje, fecha_emision, fecha_vencimiento, notas, token, agencia_id)
        )
        factura_id = cursor.fetchone()[0]
        conexion.commit()
    finally:
        conexion.close()
    return factura_id


def facturas_pendientes_de_pago(agencia_id):
    # Para el <select> opcional "Factura" del modal de pagos: solo tiene
    # sentido vincular un pago a una factura que todavía puede recibir pagos.
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT * FROM facturas WHERE agencia_id = %s AND estado IN ('Borrador', 'Emitida') ORDER BY numero_secuencial DESC",
        (agencia_id,)
    )
    resultados = cursor.fetchall()
    conexion.close()
    return resultados


def facturas_de_proyecto(proyecto_id, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT * FROM facturas WHERE proyecto_id = %s AND agencia_id = %s ORDER BY id DESC",
        (proyecto_id, agencia_id)
    )
    resultados = cursor.fetchall()
    conexion.close()
    return resultados


def facturas_de_cliente(cliente_id, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        """SELECT facturas.* FROM facturas
           JOIN proyectos ON proyectos.id = facturas.proyecto_id
           WHERE proyectos.cliente_id = %s AND proyectos.agencia_id = %s AND facturas.agencia_id = %s
           ORDER BY facturas.id DESC""",
        (cliente_id, agencia_id, agencia_id)
    )
    resultados = cursor.fetchall()
    conexion.close()
    return resultados


def obtener_facturas_paginado(agencia_id, pagina, por_pagina):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT COUNT(*) FROM facturas WHERE agencia_id = %s", (agencia_id,))
    total = cursor.fetchone()[0]
    offset = (pagina - 1) * por_pagina
    cursor.execute(
        """SELECT facturas.*, proyectos.titulo, clientes.nombre FROM facturas
           JOIN proyectos ON proyectos.id = facturas.proyecto_id
           JOIN clientes ON clientes.id = proyectos.cliente_id
           WHERE facturas.agencia_id = %s
           ORDER BY facturas.id DESC LIMIT %s OFFSET %s""",
        (agencia_id, por_pagina, offset)
    )
    resultados = cursor.fetchall()
    conexion.close()
    return resultados, total


def obtener_factura_por_id(id, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM facturas WHERE id = %s AND agencia_id = %s", (id, agencia_id))
    resultado = cursor.fetchone()
    conexion.close()
    return resultado


def obtener_factura_por_token(token):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM facturas WHERE token = %s", (token,))
    resultado = cursor.fetchone()
    conexion.close()
    return resultado


def editar_factura_por_id(id, proyecto_id, descuento, impuesto_porcentaje, fecha_emision, fecha_vencimiento, notas, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        """UPDATE facturas SET proyecto_id = %s, descuento = %s, impuesto_porcentaje = %s,
           fecha_emision = %s, fecha_vencimiento = %s, notas = %s WHERE id = %s AND agencia_id = %s""",
        (proyecto_id, descuento, impuesto_porcentaje, fecha_emision, fecha_vencimiento, notas, id, agencia_id)
    )
    conexion.commit()
    conexion.close()


def eliminar_factura_por_id(id, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM factura_items WHERE factura_id = %s", (id,))
    cursor.execute("DELETE FROM facturas WHERE id = %s AND agencia_id = %s", (id, agencia_id))
    conexion.commit()
    conexion.close()


def cambiar_estado_factura(id, estado, agencia_id=None):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    if agencia_id is not None:
        cursor.execute("UPDATE facturas SET estado = %s WHERE id = %s AND agencia_id = %s", (estado, id, agencia_id))
    else:
        cursor.execute("UPDATE facturas SET estado = %s WHERE id = %s", (estado, id))
    conexion.commit()
    conexion.close()


def reemplazar_items_factura(factura_id, items):
    # items: lista de tuplas (descripcion, cantidad, precio_unitario). Mismo
    # patrón "borrar todo e insertar de nuevo" que cotizacion_items.
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM factura_items WHERE factura_id = %s", (factura_id,))
    for orden, (descripcion, cantidad, precio_unitario) in enumerate(items):
        cursor.execute(
            "INSERT INTO factura_items (factura_id, descripcion, cantidad, precio_unitario, orden) VALUES (%s, %s, %s, %s, %s)",
            (factura_id, descripcion, cantidad, precio_unitario, orden)
        )
    conexion.commit()
    conexion.close()


def obtener_items_factura(factura_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM factura_items WHERE factura_id = %s ORDER BY orden, id", (factura_id,))
    resultados = cursor.fetchall()
    conexion.close()
    return resultados


def calcular_totales_factura(items, descuento, impuesto_porcentaje):
    subtotal = sum((item[3] or 0) * (item[4] or 0) for item in items)
    con_descuento = max(subtotal - (descuento or 0), 0)
    total = con_descuento * (1 + (impuesto_porcentaje or 0) / 100)
    return subtotal, total


def factura_esta_vencida(factura):
    if factura[3] != "Emitida" or not factura[7]:
        return False
    return factura[7] < date.today().isoformat()


def cobrado_factura(factura_id, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT COALESCE(SUM(monto), 0) FROM pagos WHERE factura_id = %s AND agencia_id = %s AND estado = 'cobrado'",
        (factura_id, agencia_id)
    )
    total = cursor.fetchone()[0]
    conexion.close()
    return total


def saldo_factura(factura_id, agencia_id):
    items = obtener_items_factura(factura_id)
    factura = obtener_factura_por_id(factura_id, agencia_id)
    if factura is None:
        return 0
    _, total = calcular_totales_factura(items, factura[4], factura[5])
    return total - cobrado_factura(factura_id, agencia_id)


def sincronizar_estado_factura(factura_id, agencia_id):
    """Recalcula si la factura ya está cubierta por los pagos vinculados y
    actualiza su estado. Se llama explícitamente desde las rutas de pagos y
    de facturas después de cada cambio (mismo patrón que convertir_cotizacion:
    orquestación visible en la ruta, no lógica escondida en core/pagos.py)."""
    factura = obtener_factura_por_id(factura_id, agencia_id)
    if factura is None or factura[3] not in ("Emitida", "Pagada"):
        return
    saldo = saldo_factura(factura_id, agencia_id)
    nuevo_estado = "Pagada" if saldo <= 0.01 else "Emitida"
    if nuevo_estado != factura[3]:
        cambiar_estado_factura(factura_id, nuevo_estado, agencia_id)


def formatear_numero_factura(numero_secuencial):
    return f"F-{numero_secuencial:04d}"
