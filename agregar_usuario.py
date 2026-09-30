from core.agencias import obtener_agencias
from core.usuarios import crear_usuario, obtener_usuario_por_nombre
from getpass import getpass

agencias = obtener_agencias()

print("Agencias existentes:")
for agencia in agencias:
    print(f"  id {agencia[0]} — {agencia[1]}")

agencia_id = int(input("\nID de la agencia a la que pertenece el nuevo usuario: "))
nombre_usuario = input("Nombre de usuario: ")
rol = input("Rol ('admin' o 'miembro', default 'miembro'): ").strip() or "miembro"

if rol not in ("admin", "miembro"):
    print("Rol inválido. Tiene que ser 'admin' o 'miembro'. No se creó nada.")
elif obtener_usuario_por_nombre(nombre_usuario) is not None:
    print(f"Ya existe un usuario con el nombre '{nombre_usuario}'. No se creó nada.")
else:
    contraseña = getpass("Contraseña (no se mostrará mientras escribes): ")
    crear_usuario(nombre_usuario, contraseña, agencia_id, rol)
    print(f"Usuario '{nombre_usuario}' ({rol}) creado para la agencia id {agencia_id}.")
