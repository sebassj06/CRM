import io
import zipfile
import openpyxl
from core.clientes import obtener_clientes, obtener_cliente_por_id
from core.proyectos import obtener_proyectos
from core.pagos import obtener_pagos
from core.notas import obtener_notas


def _libro_con_hoja(titulo, encabezados):
    libro = openpyxl.Workbook()
    hoja = libro.active
    hoja.title = titulo
    hoja.append(encabezados)
    return libro, hoja


def _a_buffer(libro):
    buffer = io.BytesIO()
    libro.save(buffer)
    buffer.seek(0)
    return buffer


def exportar_clientes_excel(agencia_id):
    libro, hoja = _libro_con_hoja("Clientes", ["nombre", "email", "telefono", "empresa", "notas", "cliente_desde"])
    for cliente in obtener_clientes(agencia_id):
        hoja.append([
            cliente[1], cliente[2], cliente[3] or "", cliente[4] or "",
            cliente[5] or "", cliente[7] if len(cliente) > 7 else ""
        ])
    return _a_buffer(libro)


def exportar_proyectos_excel(agencia_id):
    libro, hoja = _libro_con_hoja("Proyectos", ["titulo", "cliente", "estado", "fecha_entrega"])
    for proyecto in obtener_proyectos(agencia_id):
        cliente = obtener_cliente_por_id(proyecto[2], agencia_id)
        nombre_cliente = cliente[1] if cliente else "Cliente no encontrado"
        hoja.append([proyecto[1], nombre_cliente, proyecto[3], proyecto[4] or ""])
    return _a_buffer(libro)


def exportar_pagos_excel(agencia_id):
    from core.proyectos import obtener_proyecto_por_id

    libro, hoja = _libro_con_hoja("Pagos", ["proyecto", "monto", "fecha"])
    for pago in obtener_pagos(agencia_id):
        proyecto = obtener_proyecto_por_id(pago[1], agencia_id)
        titulo_proyecto = proyecto[1] if proyecto else "Proyecto no encontrado"
        hoja.append([titulo_proyecto, pago[2], pago[3] or ""])
    return _a_buffer(libro)


def exportar_notas_excel(agencia_id):
    libro, hoja = _libro_con_hoja("Notas", ["cliente", "contenido", "fecha"])
    for nota in obtener_notas(agencia_id):
        cliente = obtener_cliente_por_id(nota[1], agencia_id)
        nombre_cliente = cliente[1] if cliente else "Cliente no encontrado"
        hoja.append([nombre_cliente, nota[2], nota[3] or ""])
    return _a_buffer(libro)


def exportar_respaldo_zip(agencia_id):
    """Backup de los datos de ESTA agencia nada más (clientes/proyectos/pagos/notas
    como Excel, comprimidos en un .zip). A propósito no usamos pg_dump acá: eso
    volcaría la base entera, con los datos de todas las agencias — en una app
    multi-tenant, exponer eso por un botón del CRM sería una fuga de datos entre
    agencias. Esto es el equivalente seguro, acotado a lo que esa agencia puede ver."""
    buffer_zip = io.BytesIO()
    archivos = {
        "clientes.xlsx": exportar_clientes_excel(agencia_id),
        "proyectos.xlsx": exportar_proyectos_excel(agencia_id),
        "pagos.xlsx": exportar_pagos_excel(agencia_id),
        "notas.xlsx": exportar_notas_excel(agencia_id),
    }
    with zipfile.ZipFile(buffer_zip, "w", zipfile.ZIP_DEFLATED) as archivo_zip:
        for nombre, contenido in archivos.items():
            archivo_zip.writestr(nombre, contenido.read())
    buffer_zip.seek(0)
    return buffer_zip
