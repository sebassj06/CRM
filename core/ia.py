import os
import markdown as markdown_lib
import bleach
from anthropic import Anthropic
from dotenv import load_dotenv
from datetime import date

load_dotenv()

cliente_ia = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Etiquetas HTML que dejamos pasar cuando convertimos el markdown de la IA a HTML.
# Nada de scripts, links ni imágenes: la IA solo puede enfatizar texto y hacer listas.
ETIQUETAS_PERMITIDAS = ["p", "strong", "em", "ul", "ol", "li", "br"]


def markdown_a_html_seguro(texto):
    """Convierte texto markdown (que puede venir de una respuesta de IA) a HTML,
    y lo sanitiza para permitir solo un conjunto reducido de etiquetas seguras.
    Esto evita que texto de origen semi-controlado (notas escritas por el equipo)
    termine renderizado como HTML/JS arbitrario si la IA lo repitiera tal cual."""
    html = markdown_lib.markdown(texto)
    return bleach.clean(html, tags=ETIQUETAS_PERMITIDAS, attributes={}, strip=True)


def resumir_notas_cliente(notas):
    if not notas:
        return "Este cliente todavía no tiene notas para resumir."

    texto_notas = ""
    for nota in notas:
        texto_notas += f"- ({nota[3]}) {nota[2]}\n"

    respuesta = cliente_ia.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[
            {
                "role": "user",
                "content": (
                    "Resumí en un párrafo corto, en español, el estado general de este cliente "
                    f"según sus notas:\n\n{texto_notas}\n\n"
                    "Podés usar **negrita** de markdown para destacar lo más importante, pero no "
                    "uses títulos ni listas: mantenelo en formato de párrafo."
                )
            }
        ]
    )

    return respuesta.content[0].text


def generar_resumen_ejecutivo(total_clientes, total_proyectos, total_pagos, cobrado, por_estado):
    texto_estado = ""
    for estado, cantidad in por_estado:
        texto_estado += f"- {estado}: {cantidad}\n"

    prompt = (
        "Sos un asistente que redacta resúmenes ejecutivos cortos para el dueño de una "
        "agencia de marketing digital, en español. Con estos datos:\n\n"
        f"- Clientes totales: {total_clientes}\n"
        f"- Proyectos totales: {total_proyectos}\n"
        f"- Pagos registrados: {total_pagos}\n"
        f"- Total cobrado: ${cobrado}\n"
        "- Proyectos por estado:\n"
        f"{texto_estado}\n"
        "Redactá un resumen ejecutivo de 2 a 3 oraciones sobre el estado general del negocio, "
        "en tono profesional pero cercano, sin repetir los números tal cual como una lista. "
        "Podés usar **negrita** de markdown para destacar lo más importante, pero no uses "
        "títulos ni listas: mantenelo en formato de párrafo."
    )

    respuesta = cliente_ia.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return respuesta.content[0].text


def generar_sugerencias_proyecto(proyecto, nombre_cliente, notas, pagos):
    if notas:
        texto_notas = ""
        for nota in notas:
            texto_notas += f"- ({nota[3]}) {nota[2]}\n"
    else:
        texto_notas = "(el cliente no tiene notas registradas)\n"

    if pagos:
        texto_pagos = ""
        for pago in pagos:
            texto_pagos += f"- ${pago[2]} el {pago[3]}\n"
    else:
        texto_pagos = "(el proyecto no tiene pagos registrados)\n"

    prompt = (
        "Sos un asistente que ayuda a gestionar proyectos de una agencia de marketing digital, "
        "en español. Con estos datos de un proyecto:\n\n"
        f"- Título: {proyecto[1]}\n"
        f"- Cliente: {nombre_cliente}\n"
        f"- Estado: {proyecto[3]}\n"
        f"- Fecha de entrega: {proyecto[4]}\n"
        f"- Fecha de hoy: {date.today()}\n\n"
        "Notas del cliente:\n"
        f"{texto_notas}\n"
        "Pagos registrados del proyecto:\n"
        f"{texto_pagos}\n"
        "Basándote en esto, sugerí en 2 a 4 oraciones los próximos pasos a seguir con este "
        "proyecto, y señalá si detectás algún riesgo (por ejemplo, entrega próxima o vencida "
        "sin pagos registrados, o notas que mencionen algún problema). Podés usar viñetas "
        "(con guiones) para los próximos pasos y **negrita** de markdown para destacar "
        "riesgos, pero no uses títulos ni encabezados."
    )

    respuesta = cliente_ia.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return respuesta.content[0].text


def redactar_nota(palabras_clave):
    prompt = (
        "Sos un asistente que redacta notas breves y profesionales para el CRM de una "
        "agencia de marketing digital, en español. A partir de estas palabras clave escritas "
        f"por el usuario:\n\n{palabras_clave}\n\n"
        "Redactá el contenido de la nota en 1 a 2 oraciones, en tono profesional, "
        "como si la estuviera escribiendo un miembro del equipo sobre un cliente. "
        "Respondé en texto plano, sin usar Markdown (nada de asteriscos, títulos ni negritas)."
    )

    respuesta = cliente_ia.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return respuesta.content[0].text


def redactar_correo(nombre_cliente, palabras_clave):
    prompt = (
        "Sos un asistente que redacta correos breves y profesionales para el cliente de una "
        "agencia de marketing digital, en español. El correo es para el cliente "
        f"{nombre_cliente}. A partir de estas palabras clave escritas por el usuario:\n\n"
        f"{palabras_clave}\n\n"
        "Redactá el cuerpo del correo (sin incluir el asunto), en tono profesional y cordial, "
        "con un saludo inicial y una despedida. Respondé en texto plano, sin usar Markdown."
    )

    respuesta = cliente_ia.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=400,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return respuesta.content[0].text