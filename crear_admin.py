from core.agencias import crear_agencia
from core.usuarios import crear_usuario
from getpass import getpass

nombre_agencia = input("Nombre de la agencia: ")
nombre_usuario = input("Nombre de usuario del administrador: ")
contraseña = getpass("Contraseña del administrador (no se mostrará mientras escribes): ")

agencia_id = crear_agencia(nombre_agencia, telegram_chat_id=None, gmail_user=None, gmail_app_password=None)
crear_usuario(nombre_usuario, contraseña, agencia_id, rol="admin")

print(f"Agencia creada con id {agencia_id}. Usuario administrador creado para esa agencia.")