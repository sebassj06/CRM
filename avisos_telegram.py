import os
import requests
from dotenv import load_dotenv
from core.proyectos import proyectos_por_vencer
from core.clientes import obtener_cliente_por_id
from core.agencias import obtener_agencias

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


def enviar_mensaje(chat_id, texto):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    datos = {"chat_id": chat_id, "text": texto}
    respuesta = requests.post(url, data=datos)
    if respuesta.status_code != 200:
        print(f"Error al enviar por Telegram: {respuesta.status_code} - {respuesta.text}")
        return False
    return True

def avisar_proyectos_por_vencer():
    agencias = obtener_agencias()

    for agencia in agencias:
        agencia_id = agencia[0]
        nombre_agencia = agencia[1]
        chat_id = agencia[2]

        if not chat_id:
            print(f"Agencia '{nombre_agencia}' no tiene chat_id de Telegram configurado, se omite.")
            continue

        proyectos = proyectos_por_vencer(agencia_id, dias=3)

        if not proyectos:
            print(f"Agencia '{nombre_agencia}': no hay proyectos por vencer en los próximos días.")
            continue

        mensaje = "Proyectos por vencer:\n\n"
        for proyecto in proyectos:
            cliente = obtener_cliente_por_id(proyecto[2], agencia_id)
            nombre_cliente = cliente[1] if cliente else "Cliente no encontrado"
            mensaje += f"- {proyecto[1]} ({nombre_cliente}) - entrega: {proyecto[4]}\n"

        if enviar_mensaje(chat_id, mensaje):
            print(f"Aviso enviado por Telegram para la agencia '{nombre_agencia}'.")


if __name__ == "__main__":
    avisar_proyectos_por_vencer()