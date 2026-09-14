from core.agencias import crear_agencia
from core.usuarios import crear_usuario

agencia_id = crear_agencia("LLC", telegram_chat_id=None, gmail_user=None, gmail_app_password=None)
crear_usuario("LLC23", "Latina030305$", agencia_id)

print(f"Agencia creada con id {agencia_id}. Usuario administrador creado para esa agencia.")