from core.agencias import actualizar_configuracion_agencia

agencia_id = 1
telegram_chat_id = "6955551111"
gmail_user = "slch0383@gmail.com"
gmail_app_password = "kgdzcvkueempvkpv"

actualizar_configuracion_agencia(agencia_id, telegram_chat_id, gmail_user, gmail_app_password)

print(f"Configuración actualizada para la agencia {agencia_id}.")