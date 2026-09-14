from core.database import obtener_conexion

def agregar_pago(proyecto_id, monto, fecha, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("INSERT INTO pagos (proyecto_id, monto, fecha, agencia_id) VALUES (%s, %s, %s, %s)",
                   (proyecto_id, monto, fecha, agencia_id))
    conexion.commit()
    conexion.close()

def mostrar_pagos():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM pagos")
    resultados = cursor.fetchall()
    conexion.close()
    for pagos in resultados:
        print(f"id: {pagos[0]}, proyecto_id: {pagos[1]}, monto: {pagos[2]}, fecha: {pagos[3]}")

def pagos_de_proyecto(proyecto_id, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM pagos WHERE proyecto_id = %s AND agencia_id = %s", (proyecto_id, agencia_id))
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

def obtener_pago_por_id(id, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM pagos WHERE id = %s AND agencia_id = %s", (id, agencia_id))
    resultado = cursor.fetchone()
    conexion.close()
    return resultado

def editar_pago_por_id(id, proyecto_id, monto, fecha, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("UPDATE pagos SET proyecto_id = %s, monto = %s, fecha = %s WHERE id = %s AND agencia_id = %s",
                   (proyecto_id, monto, fecha, id, agencia_id)
    )
    conexion.commit()
    conexion.close()

def eliminar_pago_por_id(id, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM pagos WHERE id = %s AND agencia_id = %s", (id, agencia_id))
    conexion.commit()
    conexion.close()