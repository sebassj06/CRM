from core.agencias import actualizar_configuracion_agencia

agencia_id = 1
telegram_chat_id = ""
gmail_user = ""
gmail_app_password = ""

actualizar_configuracion_agencia(agencia_id, telegram_chat_id, gmail_user, gmail_app_password)

print(f"Configuración actualizada para la agencia {agencia_id}.")