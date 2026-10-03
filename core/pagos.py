from datetime import date
from core.database import obtener_conexion

def agregar_pago(proyecto_id, monto, fecha, agencia_id, estado="cobrado", factura_id=None):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("INSERT INTO pagos (proyecto_id, monto, fecha, agencia_id, estado, factura_id) VALUES (%s, %s, %s, %s, %s, %s)",
                   (proyecto_id, monto, fecha, agencia_id, estado, factura_id))
    conexion.commit()
    conexion.close()


def pagos_de_proyecto(proyecto_id, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM pagos WHERE proyecto_id = %s AND agencia_id = %s", (proyecto_id, agencia_id))
    resultados = cursor.fetchall()
    conexion.close()
    return resultados


def pagos_de_cliente(cliente_id, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        """SELECT pagos.*, proyectos.titulo FROM pagos
           JOIN proyectos ON proyectos.id = pagos.proyecto_id
           WHERE proyectos.cliente_id = %s AND proyectos.agencia_id = %s AND pagos.agencia_id = %s
           ORDER BY pagos.fecha DESC""",
        (cliente_id, agencia_id, agencia_id)
    )
    resultados = cursor.fetchall()
    conexion.close()
    return resultados


def pagos_de_factura(factura_id, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT * FROM pagos WHERE factura_id = %s AND agencia_id = %s ORDER BY fecha DESC",
        (factura_id, agencia_id)
    )
    resultados = cursor.fetchall()
    conexion.close()
    return resultados

def obtener_pagos(agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM pagos WHERE agencia_id = %s", (agencia_id,))
    resultados = cursor.fetchall()
    conexion.close()
    return resultados

def obtener_pagos_paginado(agencia_id, pagina, por_pagina):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT COUNT(*) FROM pagos WHERE agencia_id = %s", (agencia_id,))
    total = cursor.fetchone()[0]
    offset = (pagina - 1) * por_pagina
    cursor.execute(
        "SELECT * FROM pagos WHERE agencia_id = %s ORDER BY id LIMIT %s OFFSET %s",
        (agencia_id, por_pagina, offset)
    )
    resultados = cursor.fetchall()
    conexion.close()
    return resultados, total

def pagos_proximos(agencia_id, desde=None, limite=5):
    # "Próximos pagos" ahora es lo que de verdad significa: pagos marcados
    # como pendientes (sin importar si la fecha ya pasó o no — un pago
    # pendiente vencido sigue siendo algo que hay que cobrar).
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT * FROM pagos WHERE agencia_id = %s AND estado = 'pendiente' ORDER BY fecha ASC LIMIT %s",
        (agencia_id, limite)
    )
    resultados = cursor.fetchall()
    conexion.close()
    return resultados

def pagos_pendientes_vencidos(agencia_id):
    # Pagos "pendiente" cuya fecha ya pasó: plata que se esperaba cobrar y
    # todavía no se cobró. Alimenta la campanita de notificaciones, igual
    # que los proyectos por vencer.
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        """SELECT pagos.*, proyectos.titulo FROM pagos
           JOIN proyectos ON proyectos.id = pagos.proyecto_id
           WHERE pagos.agencia_id = %s AND pagos.estado = 'pendiente' AND pagos.fecha < %s
           ORDER BY pagos.fecha ASC""",
        (agencia_id, date.today().isoformat())
    )
    resultados = cursor.fetchall()
    conexion.close()
    return resultados


def obtener_pago_por_id(id, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM pagos WHERE id = %s AND agencia_id = %s", (id, agencia_id))
    resultado = cursor.fetchone()
    conexion.close()
    return resultado

def editar_pago_por_id(id, proyecto_id, monto, fecha, agencia_id, estado="cobrado", factura_id=None):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("UPDATE pagos SET proyecto_id = %s, monto = %s, fecha = %s, estado = %s, factura_id = %s WHERE id = %s AND agencia_id = %s",
                   (proyecto_id, monto, fecha, estado, factura_id, id, agencia_id)
    )
    conexion.commit()
    conexion.close()

def marcar_pago_cobrado(id, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("UPDATE pagos SET estado = 'cobrado' WHERE id = %s AND agencia_id = %s", (id, agencia_id))
    conexion.commit()
    conexion.close()

def eliminar_pago_por_id(id, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM pagos WHERE id = %s AND agencia_id = %s", (id, agencia_id))
    conexion.commit()
    conexion.close()