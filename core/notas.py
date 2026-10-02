from core.database import obtener_conexion

def agregar_nota(cliente_id, contenido, fecha, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("INSERT INTO notas (cliente_id, contenido, fecha, agencia_id) VALUES (%s, %s, %s, %s)",
                   (cliente_id, contenido, fecha, agencia_id))
    conexion.commit()
    conexion.close()

def mostrar_notas():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM notas")
    resultados = cursor.fetchall()
    conexion.close()
    for notas in resultados:
        print(f"id: {notas[0]}, cliente_id: {notas[1]}, contenido: {notas[2]}, fecha: {notas[3]}")

def notas_de_cliente(cliente_id, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM notas WHERE cliente_id = %s AND agencia_id = %s", (cliente_id, agencia_id))
    resultados = cursor.fetchall()
    conexion.close()
    return resultados

def obtener_notas(agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM notas WHERE agencia_id = %s", (agencia_id,))
    resultados = cursor.fetchall()
    conexion.close()
    return resultados

def obtener_notas_paginado(agencia_id, pagina, por_pagina):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT COUNT(*) FROM notas WHERE agencia_id = %s", (agencia_id,))
    total = cursor.fetchone()[0]
    offset = (pagina - 1) * por_pagina
    cursor.execute(
        "SELECT * FROM notas WHERE agencia_id = %s ORDER BY id LIMIT %s OFFSET %s",
        (agencia_id, por_pagina, offset)
    )
    resultados = cursor.fetchall()
    conexion.close()
    return resultados, total

def obtener_nota_por_id(id, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM notas WHERE id = %s AND agencia_id = %s", (id, agencia_id))
    resultado = cursor.fetchone()
    conexion.close()
    return resultado

def editar_nota_por_id(id, cliente_id, contenido, fecha, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("UPDATE notas SET cliente_id = %s, contenido = %s, fecha = %s WHERE id = %s AND agencia_id = %s",
                   (cliente_id, contenido, fecha, id, agencia_id)
    )
    conexion.commit()
    conexion.close()

def eliminar_nota_por_id(id, agencia_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM notas WHERE id = %s AND agencia_id = %s", (id, agencia_id))
    conexion.commit()
    conexion.close()