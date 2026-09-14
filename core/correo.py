import smtplib
from email.message import EmailMessage


def enviar_correo(destinatario, asunto, cuerpo, gmail_user, gmail_app_password):
    mensaje = EmailMessage()
    mensaje["Subject"] = asunto
    mensaje["From"] = gmail_user
    mensaje["To"] = destinatario
    mensaje.set_content(cuerpo)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
        servidor.login(gmail_user, gmail_app_password)
        servidor.send_message(mensaje)