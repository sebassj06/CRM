from core.clientes import agregar_cliente, mostrar_clientes, buscar_cliente, eliminar_cliente, editar_cliente

from core.proyectos import agregar_proyecto, mostrar_proyectos, proyectos_de_cliente

from core.pagos import agregar_pago, mostrar_pagos, pagos_de_proyecto

from core.notas import agregar_nota, mostrar_notas, notas_de_cliente


mostrar_notas()
print(notas_de_cliente(5))
