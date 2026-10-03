"""
Script de QA: crea (o reutiliza) dos agencias de prueba con un admin y un
miembro cada una, con prefijo QA_, para pruebas de aislamiento multi-tenant.
Solo para uso LOCAL. No crea datos de negocio (clientes/proyectos/etc), eso
lo hacen los scripts de prueba específicos.
"""
from core.agencias import crear_agencia, obtener_agencias
from core.usuarios import crear_usuario, obtener_usuario_por_nombre

PASSWORD = "QA_Pass123!"

AGENCIAS = [
    {
        "nombre": "QA_Agencia A",
        "admin": "QA_admin_a",
        "miembro": "QA_miembro_a",
    },
    {
        "nombre": "QA_Agencia B",
        "admin": "QA_admin_b",
        "miembro": "QA_miembro_b",
    },
]


def main():
    existentes = {a[1]: a[0] for a in obtener_agencias()}
    resultado = {}

    for spec in AGENCIAS:
        nombre = spec["nombre"]
        if nombre in existentes:
            agencia_id = existentes[nombre]
            print(f"Agencia '{nombre}' ya existe (id={agencia_id}), reutilizando.")
        else:
            agencia_id = crear_agencia(nombre)
            print(f"Agencia '{nombre}' creada (id={agencia_id}).")

        for rol_key, username in (("admin", spec["admin"]), ("miembro", spec["miembro"])):
            if obtener_usuario_por_nombre(username) is not None:
                print(f"  Usuario '{username}' ya existe, reutilizando.")
            else:
                crear_usuario(username, PASSWORD, agencia_id, rol=rol_key)
                print(f"  Usuario '{username}' ({rol_key}) creado.")

        resultado[nombre] = agencia_id

    print("\nListo. Password comun para todos los usuarios QA_: (ver PASSWORD en este script)")
    print(resultado)


if __name__ == "__main__":
    main()
