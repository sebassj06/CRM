import os
from dotenv import load_dotenv

load_dotenv()

from flask import Flask, request, render_template, redirect, url_for, session, jsonify, flash, send_file
from functools import wraps
from core.correo import enviar_correo
from core.notas import notas_de_cliente
from core.ia import resumir_notas_cliente, generar_resumen_ejecutivo, generar_sugerencias_proyecto, redactar_nota, redactar_correo, markdown_a_html_seguro
from datetime import date
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_limiter.errors import RateLimitExceeded
from core.clientes import (obtener_clientes,
                           obtener_clientes_paginado,
                           obtener_cliente_por_id,
                           obtener_cliente_por_email,
                           email_valido,
                           telefono_valido,
                           agregar_cliente,
                           editar_cliente_por_id,
                           eliminar_cliente_por_id,
                           archivar_cliente_por_id,
                           desarchivar_cliente_por_id
)
from core.paginacion import normalizar_pagina, total_paginas, POR_PAGINA
from core.proyectos import(
    obtener_proyectos,
    obtener_proyecto_por_id,
    agregar_proyecto,
    editar_proyecto_por_id,
    eliminar_proyecto_por_id,
    proyecto_esta_por_vencer,
    proyectos_de_cliente,
    proyectos_recientes,
    proyectos_por_vencer,
    obtener_proyectos_paginado,
    marcar_proyecto_completado,
    archivar_proyecto_por_id,
    desarchivar_proyecto_por_id
)
from core.pagos import(
    obtener_pagos,
    obtener_pago_por_id,
    agregar_pago,
    editar_pago_por_id,
    eliminar_pago_por_id,
    pagos_de_proyecto,
    pagos_proximos,
    obtener_pagos_paginado,
    marcar_pago_cobrado,
    pagos_pendientes_vencidos
)
from core.notas import(
    obtener_notas,
    obtener_nota_por_id,
    agregar_nota,
    editar_nota_por_id,
    eliminar_nota_por_id,
    obtener_notas_paginado
)
from core.estadisticas import (
    contar_clientes,
    contar_proyectos,
    contar_pagos,
    total_cobrado,
    proyectos_por_estado,
    estadisticas_dashboard,
    ingresos_por_mes
)
from core.usuarios import (
    verificar_usuario,
    crear_usuario,
    usuarios_de_agencia,
    obtener_usuario_por_id,
    obtener_usuario_por_nombre,
    contar_admins_agencia,
    eliminar_usuario_por_id,
    verificar_password_usuario,
    actualizar_perfil_usuario,
    actualizar_foto_perfil,
    cambiar_contraseña_usuario,
    crear_verificacion_email,
    obtener_verificacion_email_pendiente,
    confirmar_verificacion_email
)
from core.agencias import obtener_agencia_por_id, actualizar_configuracion_agencia
from core.importacion import importar_clientes_desde_archivo, generar_plantilla_clientes
from core.exportacion import exportar_clientes_excel, exportar_proyectos_excel, exportar_pagos_excel, exportar_respaldo_zip
from core.busqueda import buscar_todo
from core.recibos import generar_recibo_pdf
from core.auditoria import registrar_auditoria, obtener_auditoria_paginado
from core.divisas import MONEDAS, obtener_tasa_cambio, simbolo_moneda
from core.paises import PAISES
from avisos_telegram import avisar_proyecto_individual
from werkzeug.utils import secure_filename
import random

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
csrf = CSRFProtect(app)
limiter = Limiter(get_remote_address, app=app, default_limits=[])

CARPETA_FOTOS_PERFIL = os.path.join(app.root_path, "static", "uploads", "perfiles")
EXTENSIONES_FOTO_PERMITIDAS = {"png", "jpg", "jpeg", "webp"}
TAMANO_MAXIMO_FOTO = 3 * 1024 * 1024  # 3 MB


def extension_foto_valida(nombre_archivo):
    return "." in nombre_archivo and nombre_archivo.rsplit(".", 1)[1].lower() in EXTENSIONES_FOTO_PERMITIDAS

# Filtro de plantilla para renderizar el markdown de las respuestas de IA como HTML
# real (negrita, listas) en vez de texto plano con asteriscos sueltos. La sanitización
# ocurre dentro de markdown_a_html_seguro, así que en los templates se usa con `| safe`.
app.jinja_env.filters["markdown"] = markdown_a_html_seguro


def formatear_monto(valor):
    texto = "{:,.2f}".format(valor)
    if texto.endswith(".00"):
        texto = texto[:-3]
    return texto


app.jinja_env.filters["monto"] = formatear_monto

def login_requerido(f):
    @wraps(f)
    def funcion_decorada(*args, **kwargs):
        if "usuario" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return funcion_decorada

def admin_requerido(f):
    @wraps(f)
    def funcion_decorada(*args, **kwargs):
        if "usuario" not in session:
            return redirect(url_for("login"))
        if session.get("rol") != "admin":
            flash("Esta sección es solo para administradores de la agencia.", "error")
            return redirect(url_for("inicio"))
        return f(*args, **kwargs)
    return funcion_decorada


def es_peticion_ajax():
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def auditar(accion, entidad, entidad_id, descripcion):
    registrar_auditoria(
        session.get("agencia_id"), session.get("usuario_id"), session.get("usuario"),
        accion, entidad, entidad_id, descripcion
    )


def redirigir_o_responder_error(mensaje, endpoint, **kwargs):
    if es_peticion_ajax():
        return jsonify({"exito": False, "error": mensaje}), 400
    flash(mensaje, "error")
    return redirect(url_for(endpoint, **kwargs))


@app.context_processor
def inyectar_agencia_actual():
    if "agencia_id" in session:
        agencia = obtener_agencia_por_id(session["agencia_id"])
        if agencia:
            usuario_actual = obtener_usuario_por_id(session["usuario_id"], session["agencia_id"])
            return {
                "agencia_actual": agencia[1],
                "rol_actual": session.get("rol"),
                "notificaciones": notificaciones_proyectos_por_vencer(session["agencia_id"]),
                "pagos_vencidos": pagos_pendientes_vencidos(session["agencia_id"]),
                "foto_perfil_actual": usuario_actual[6] if usuario_actual else None
            }
    return {"agencia_actual": None, "rol_actual": None, "notificaciones": [], "pagos_vencidos": [], "foto_perfil_actual": None}


def notificaciones_proyectos_por_vencer(agencia_id):
    # Esto corre en TODAS las páginas (va en el context processor, para la
    # campanita del topbar), así que evitamos una consulta de cliente por
    # cada proyecto por vencer (N+1) y resolvemos todos los nombres con una
    # sola consulta de clientes.
    proyectos = proyectos_por_vencer(agencia_id, dias=3)
    if not proyectos:
        return []

    clientes_por_id = {cliente[0]: cliente[1] for cliente in obtener_clientes(agencia_id)}
    return [
        (proyecto, clientes_por_id.get(proyecto[2], "Cliente no encontrado"))
        for proyecto in proyectos
    ]

def datos_dashboard_extra(agencia_id):
    clases_estado = {"Pendiente": "badge-pendiente", "En progreso": "badge-progreso", "Completado": "badge-completado"}

    proyectos_lista = []
    for proyecto in proyectos_recientes(agencia_id, limite=5):
        cliente = obtener_cliente_por_id(proyecto[2], agencia_id)
        nombre_cliente = cliente[1] if cliente else "Cliente no encontrado"
        proyectos_lista.append((proyecto, nombre_cliente, clases_estado.get(proyecto[3], "badge-pendiente")))

    pagos_lista = []
    for pago in pagos_proximos(agencia_id, limite=5):
        proyecto = obtener_proyecto_por_id(pago[1], agencia_id)
        titulo_proyecto = proyecto[1] if proyecto else "Proyecto no encontrado"
        pagos_lista.append((pago, titulo_proyecto))

    ingresos_mensuales = ingresos_por_mes(agencia_id, meses=6)
    max_ingreso_mensual = max((valor for _, valor in ingresos_mensuales), default=0) or 1
    hay_ingresos_mensuales = any(valor > 0 for _, valor in ingresos_mensuales)

    return {
        "proyectos_recientes": proyectos_lista,
        "pagos_proximos": pagos_lista,
        "ingresos_mensuales": ingresos_mensuales,
        "max_ingreso_mensual": max_ingreso_mensual,
        "hay_ingresos_mensuales": hay_ingresos_mensuales
    }


def datos_conversion(agencia_id):
    agencia = obtener_agencia_por_id(agencia_id)
    moneda = agencia[5] if agencia and len(agencia) > 5 and agencia[5] else "USD"
    tasa = obtener_tasa_cambio(moneda) if moneda != "USD" else None
    return {
        "moneda_actual": moneda,
        "simbolo_actual": simbolo_moneda(moneda),
        "tasa_cambio": tasa
    }


@app.route("/buscar")
@login_requerido
def buscar():
    termino = request.args.get("q", "").strip()
    resultados = buscar_todo(session["agencia_id"], termino)

    pagos_con_titulo = []
    for pago in resultados["pagos"]:
        proyecto = obtener_proyecto_por_id(pago[1], session["agencia_id"])
        titulo_proyecto = proyecto[1] if proyecto else "Proyecto no encontrado"
        pagos_con_titulo.append((pago, titulo_proyecto))

    notas_con_cliente = []
    for nota in resultados["notas"]:
        cliente = obtener_cliente_por_id(nota[1], session["agencia_id"])
        nombre_cliente = cliente[1] if cliente else "Cliente no encontrado"
        notas_con_cliente.append((nota, nombre_cliente))

    proyectos_con_cliente = []
    for proyecto in resultados["proyectos"]:
        cliente = obtener_cliente_por_id(proyecto[2], session["agencia_id"])
        nombre_cliente = cliente[1] if cliente else "Cliente no encontrado"
        proyectos_con_cliente.append((proyecto, nombre_cliente))

    total_resultados = len(resultados["clientes"]) + len(proyectos_con_cliente) + len(pagos_con_titulo) + len(notas_con_cliente)
    conversion = datos_conversion(session["agencia_id"])

    return render_template(
        "buscar.html", termino=termino, clientes=resultados["clientes"],
        proyectos=proyectos_con_cliente, pagos=pagos_con_titulo, notas=notas_con_cliente,
        total_resultados=total_resultados, **conversion
    )


@app.route("/")
@login_requerido
def inicio():
    datos = estadisticas_dashboard(session["agencia_id"])
    extra = datos_dashboard_extra(session["agencia_id"])
    conversion = datos_conversion(session["agencia_id"])
    return render_template("dashboard.html", **datos, **extra, **conversion, resumen=None)


@app.route("/resumen-ejecutivo", methods=["POST"])
@login_requerido
def resumen_ejecutivo():
    datos = estadisticas_dashboard(session["agencia_id"])
    extra = datos_dashboard_extra(session["agencia_id"])
    conversion = datos_conversion(session["agencia_id"])

    try:
        resumen = generar_resumen_ejecutivo(
            datos["total_clientes"], datos["total_proyectos"],
            datos["total_pagos"], datos["cobrado"], datos["por_estado"]
        )
    except Exception:
        flash("No se pudo generar el resumen ejecutivo en este momento. Probá de nuevo en un rato.", "error")
        resumen = None

    return render_template("dashboard.html", **datos, **extra, **conversion, resumen=resumen)
    

@app.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def login():
    if request.method == "POST":
        nombre_usuario = request.form["nombre_usuario"]
        contraseña = request.form["contraseña"]

        usuario = verificar_usuario(nombre_usuario, contraseña)

        if usuario is None:
            return render_template("login.html", error="Usuario o contraseña incorrectos.")

        session["usuario"] = usuario[1]
        session["agencia_id"] = usuario[3]
        session["usuario_id"] = usuario[0]
        # len(usuario) > 4: si todavía no corriste la migración que agrega la
        # columna 'rol', el login sigue funcionando (con rol 'miembro' por
        # default) en vez de romperse por un índice que no existe.
        session["rol"] = usuario[4] if len(usuario) > 4 else "miembro"
        return redirect(url_for("inicio"))
    else:
        return render_template("login.html", error=None)

@app.route("/configuracion/respaldo")
@admin_requerido
def descargar_respaldo():
    buffer = exportar_respaldo_zip(session["agencia_id"])
    nombre = f"respaldo_{date.today().isoformat()}.zip"
    return send_file(buffer, as_attachment=True, download_name=nombre, mimetype="application/zip")


@app.route("/configuracion", methods=["GET", "POST"])
@admin_requerido
def configuracion_agencia():
    agencia = obtener_agencia_por_id(session["agencia_id"])

    if request.method == "POST":
        telegram_chat_id = request.form["telegram_chat_id"].strip() or None
        gmail_user = request.form["gmail_user"].strip() or None
        gmail_app_password = request.form["gmail_app_password"].strip() or None
        moneda = request.form.get("moneda", "USD").strip() or "USD"

        actualizar_configuracion_agencia(session["agencia_id"], telegram_chat_id, gmail_user, gmail_app_password, moneda)

        flash("Configuración actualizada correctamente.", "exito")
        return redirect(url_for("configuracion_agencia"))

    return render_template("configuracion.html", agencia=agencia, monedas=MONEDAS)


@app.route("/usuarios", methods=["GET", "POST"])
@admin_requerido
def ver_usuarios():
    if request.method == "POST":
        nombre_usuario = request.form["nombre_usuario"].strip()
        contraseña = request.form["contraseña"]
        rol = request.form["rol"]

        if nombre_usuario == "" or contraseña == "":
            return redirigir_o_responder_error("Nombre de usuario y contraseña son obligatorios.", "ver_usuarios")

        if rol not in ("admin", "miembro"):
            return redirigir_o_responder_error("Rol inválido.", "ver_usuarios")

        try:
            crear_usuario(nombre_usuario, contraseña, session["agencia_id"], rol)
        except Exception:
            return redirigir_o_responder_error(f"Ya existe un usuario con el nombre '{nombre_usuario}'.", "ver_usuarios")

        auditar("crear", "usuario", None, f"Creó el usuario '{nombre_usuario}' ({rol}).")

        if es_peticion_ajax():
            return jsonify({"exito": True})

        flash("Usuario agregado correctamente.", "exito")
        return redirect(url_for("ver_usuarios"))

    usuarios = usuarios_de_agencia(session["agencia_id"])
    return render_template("usuarios.html", usuarios=usuarios)


@app.route("/usuarios/<int:id>/eliminar", methods=["POST"])
@admin_requerido
def eliminar_usuario_ruta(id):
    usuario = obtener_usuario_por_id(id, session["agencia_id"])

    if usuario is None:
        flash("Usuario no encontrado.", "error")
        return redirect(url_for("ver_usuarios"))

    if id == session["usuario_id"]:
        flash("No podés eliminar tu propio usuario.", "error")
        return redirect(url_for("ver_usuarios"))

    if usuario[4] == "admin" and contar_admins_agencia(session["agencia_id"]) <= 1:
        flash("No podés eliminar al único administrador de la agencia.", "error")
        return redirect(url_for("ver_usuarios"))

    eliminar_usuario_por_id(id, session["agencia_id"])
    auditar("eliminar", "usuario", id, f"Eliminó al usuario '{usuario[1]}'.")
    flash("Usuario eliminado.", "exito")
    return redirect(url_for("ver_usuarios"))


@app.route("/perfil", methods=["GET", "POST"])
@login_requerido
def ver_perfil():
    usuario = obtener_usuario_por_id(session["usuario_id"], session["agencia_id"])
    if usuario is None:
        flash("Usuario no encontrado.", "error")
        return redirect(url_for("inicio"))

    if request.method == "POST":
        nombre_usuario = request.form.get("nombre_usuario", "").strip()
        if nombre_usuario == "":
            return redirigir_o_responder_error("El nombre de usuario no puede estar vacío.", "ver_perfil")

        if nombre_usuario != usuario[1]:
            otro_usuario = obtener_usuario_por_nombre(nombre_usuario)
            if otro_usuario and otro_usuario[0] != session["usuario_id"]:
                return redirigir_o_responder_error(f"Ya existe un usuario con el nombre '{nombre_usuario}'.", "ver_perfil")

        archivo = request.files.get("foto_perfil")
        if archivo and archivo.filename:
            if not extension_foto_valida(archivo.filename):
                return redirigir_o_responder_error("La foto debe ser .png, .jpg, .jpeg o .webp.", "ver_perfil")

            archivo.seek(0, os.SEEK_END)
            tamano = archivo.tell()
            archivo.seek(0)
            if tamano > TAMANO_MAXIMO_FOTO:
                return redirigir_o_responder_error("La foto no puede superar los 3 MB.", "ver_perfil")

            os.makedirs(CARPETA_FOTOS_PERFIL, exist_ok=True)
            if usuario[6]:
                ruta_anterior = os.path.join(app.root_path, "static", usuario[6])
                if os.path.exists(ruta_anterior):
                    try:
                        os.remove(ruta_anterior)
                    except OSError:
                        pass

            extension = secure_filename(archivo.filename).rsplit(".", 1)[1].lower()
            nombre_archivo = f"usuario_{session['usuario_id']}.{extension}"
            archivo.save(os.path.join(CARPETA_FOTOS_PERFIL, nombre_archivo))
            actualizar_foto_perfil(session["usuario_id"], f"uploads/perfiles/{nombre_archivo}")

        nombre_cambio = nombre_usuario != usuario[1]
        actualizar_perfil_usuario(session["usuario_id"], nombre_usuario)
        session["usuario"] = nombre_usuario
        if nombre_cambio:
            auditar("editar", "perfil", session["usuario_id"], "Actualizó su nombre de usuario.")

        email_nuevo = request.form.get("email", "").strip()
        if email_nuevo and email_nuevo != (usuario[5] or ""):
            if not email_valido(email_nuevo):
                return redirigir_o_responder_error("El email no tiene un formato válido.", "ver_perfil")

            agencia = obtener_agencia_por_id(session["agencia_id"])
            if not (agencia and agencia[3] and agencia[4]):
                return redirigir_o_responder_error(
                    "Tu agencia no tiene Gmail configurado en Configuración, así que no podemos enviarte un código de verificación.",
                    "ver_perfil"
                )

            codigo = f"{random.randint(0, 999999):06d}"
            crear_verificacion_email(session["usuario_id"], email_nuevo, codigo)
            try:
                enviar_correo(
                    email_nuevo,
                    "Confirmá tu nuevo email · CRM Agencia",
                    f"Tu código de verificación es: {codigo}\n\nIngresalo en tu perfil para confirmar el cambio de email. Vence en 15 minutos.",
                    agencia[3], agencia[4]
                )
            except Exception as error:
                return redirigir_o_responder_error(f"No se pudo enviar el código de verificación: {error}", "ver_perfil")

            if es_peticion_ajax():
                return jsonify({"exito": True, "verificacion_pendiente": True})
            flash(f"Te enviamos un código de verificación a {email_nuevo}.", "exito")
            return redirect(url_for("ver_perfil"))

        if es_peticion_ajax():
            return jsonify({"exito": True})
        flash("Perfil actualizado correctamente.", "exito")
        return redirect(url_for("ver_perfil"))

    verificacion_pendiente = obtener_verificacion_email_pendiente(session["usuario_id"])
    return render_template("perfil.html", usuario=usuario, verificacion_pendiente=verificacion_pendiente)


@app.route("/perfil/confirmar-email", methods=["POST"])
@login_requerido
def confirmar_email_perfil():
    codigo = request.form.get("codigo", "").strip()

    if confirmar_verificacion_email(session["usuario_id"], codigo):
        auditar("editar", "perfil", session["usuario_id"], "Confirmó el cambio de email.")
        if es_peticion_ajax():
            return jsonify({"exito": True})
        flash("Email confirmado correctamente.", "exito")
        return redirect(url_for("ver_perfil"))

    return redirigir_o_responder_error("El código es incorrecto o venció. Pedí uno nuevo cambiando el email de vuelta.", "ver_perfil")


@app.route("/perfil/cambiar-password", methods=["POST"])
@login_requerido
def cambiar_password_perfil():
    contraseña_actual = request.form.get("contraseña_actual", "")
    contraseña_nueva = request.form.get("contraseña_nueva", "")

    if not verificar_password_usuario(session["usuario_id"], contraseña_actual):
        return redirigir_o_responder_error("La contraseña actual no es correcta.", "ver_perfil")

    if len(contraseña_nueva) < 6:
        return redirigir_o_responder_error("La nueva contraseña debe tener al menos 6 caracteres.", "ver_perfil")

    cambiar_contraseña_usuario(session["usuario_id"], contraseña_nueva)
    auditar("editar", "perfil", session["usuario_id"], "Cambió su contraseña.")

    if es_peticion_ajax():
        return jsonify({"exito": True})
    flash("Contraseña actualizada correctamente.", "exito")
    return redirect(url_for("ver_perfil"))


@app.route("/logout")
def logout():
    session.pop("usuario", None)
    session.pop("agencia_id", None)
    session.pop("usuario_id", None)
    session.pop("rol", None)
    return redirect(url_for("login"))


@app.route("/clientes")
@login_requerido
def ver_clientes():
    pagina = normalizar_pagina(request.args.get("pagina"))
    ver_archivados = request.args.get("archivados") == "1"
    clientes, total = obtener_clientes_paginado(session["agencia_id"], pagina, POR_PAGINA, archivados=ver_archivados)
    return render_template(
        "clientes.html", clientes=clientes, paises=PAISES, ver_archivados=ver_archivados,
        pagina=pagina, total_paginas=total_paginas(total, POR_PAGINA), total_registros=total
    )

@app.route("/clientes/<int:id>")
@login_requerido
def ver_cliente(id):
    cliente = obtener_cliente_por_id(id, session["agencia_id"])

    if cliente is None:
        flash("Cliente no encontrado.", "error")
        return redirect(url_for("ver_clientes"))
    else:
        notas = notas_de_cliente(id, session["agencia_id"])
        proyectos = proyectos_de_cliente(id, session["agencia_id"])
        return render_template("cliente_detalle.html", cliente=cliente, notas=notas, proyectos=proyectos, resumen=None, asunto_borrador=None, cuerpo_borrador=None, mensaje_envio=None, paises=PAISES)


@app.route("/clientes/<int:id>/resumen-ia", methods=["POST"])
@login_requerido
def resumen_ia_cliente(id):
    cliente = obtener_cliente_por_id(id, session["agencia_id"])

    if cliente is None:
        flash("Cliente no encontrado.", "error")
        return redirect(url_for("ver_clientes"))

    notas = notas_de_cliente(id, session["agencia_id"])
    proyectos = proyectos_de_cliente(id, session["agencia_id"])

    try:
        resumen = resumir_notas_cliente(notas)
    except Exception:
        flash("No se pudo generar el resumen en este momento. Probá de nuevo en un rato.", "error")
        resumen = None

    return render_template("cliente_detalle.html", cliente=cliente, notas=notas, proyectos=proyectos, resumen=resumen, asunto_borrador=None, cuerpo_borrador=None, mensaje_envio=None)


@app.route("/clientes/<int:id>/correo-ia/generar", methods=["POST"])
@login_requerido
def generar_correo_ia(id):
    cliente = obtener_cliente_por_id(id, session["agencia_id"])

    if cliente is None:
        flash("Cliente no encontrado.", "error")
        return redirect(url_for("ver_clientes"))

    asunto = request.form["asunto"]
    palabras_clave = request.form["palabras_clave"]

    try:
        cuerpo_borrador = redactar_correo(cliente[1], palabras_clave)
    except Exception:
        flash("No se pudo generar el borrador en este momento. Probá de nuevo en un rato.", "error")
        cuerpo_borrador = None

    notas = notas_de_cliente(id, session["agencia_id"])
    proyectos = proyectos_de_cliente(id, session["agencia_id"])
    return render_template("cliente_detalle.html", cliente=cliente, notas=notas, proyectos=proyectos, resumen=None, asunto_borrador=asunto, cuerpo_borrador=cuerpo_borrador, mensaje_envio=None)


@app.route("/clientes/<int:id>/correo-ia/enviar", methods=["POST"])
@login_requerido
def enviar_correo_ia(id):
    cliente = obtener_cliente_por_id(id, session["agencia_id"])

    if cliente is None:
        flash("Cliente no encontrado.", "error")
        return redirect(url_for("ver_clientes"))

    asunto = request.form["asunto"]
    cuerpo = request.form["cuerpo"]

    agencia = obtener_agencia_por_id(session["agencia_id"])

    if not cliente[2]:
        mensaje_envio = "Este cliente no tiene email registrado."
    elif not agencia[3] or not agencia[4]:
        mensaje_envio = "Tu agencia todavía no configuró una cuenta de Gmail para enviar correos."
    else:
        try:
            enviar_correo(cliente[2], asunto, cuerpo, agencia[3], agencia[4])
            mensaje_envio = "Correo enviado correctamente."
        except Exception as error:
            mensaje_envio = f"No se pudo enviar el correo: {error}"

    notas = notas_de_cliente(id, session["agencia_id"])
    proyectos = proyectos_de_cliente(id, session["agencia_id"])
    return render_template("cliente_detalle.html", cliente=cliente, notas=notas, proyectos=proyectos, resumen=None, asunto_borrador=None, cuerpo_borrador=None, mensaje_envio=mensaje_envio)

   
@app.route("/clientes/nuevo", methods=["GET", "POST"])
@login_requerido
def nuevo_cliente():
    if request.method == "POST":
        nombre = request.form["nombre"]
        email = request.form["email"]
        telefono = request.form["telefono"]
        empresa = request.form["empresa"]
        notas = request.form["notas"]
        
        if nombre == "" or email == "":
            return redirigir_o_responder_error("Nombre y email son obligatorios.", "nuevo_cliente")

        if not email_valido(email):
            return redirigir_o_responder_error("El email no tiene un formato válido (ejemplo: nombre@dominio.com).", "nuevo_cliente")

        if not telefono_valido(telefono):
            return redirigir_o_responder_error("El teléfono no tiene la cantidad de números esperada para el país seleccionado.", "nuevo_cliente")

        if obtener_cliente_por_email(email, session["agencia_id"]):
            return redirigir_o_responder_error(f"Ya existe un cliente con el email '{email}'.", "nuevo_cliente")

        agregar_cliente(nombre, email, telefono, empresa, notas, session["agencia_id"])
        auditar("crear", "cliente", None, f"Creó el cliente '{nombre}'.")

        if es_peticion_ajax():
            return jsonify({"exito": True})

        flash("Cliente agregado correctamente", "exito")
        return redirect(url_for("ver_clientes"))
          
    else:
        return redirect(url_for("ver_clientes", nuevo=1))


@app.route("/clientes/importar", methods=["GET", "POST"])
@login_requerido
def importar_clientes():
    if request.method == "POST":
        archivo = request.files.get("archivo_csv")

        if not archivo or archivo.filename == "":
            flash("No se seleccionó ningún archivo.", "error")
            return redirect(url_for("importar_clientes"))

        resultado = importar_clientes_desde_archivo(archivo, session["agencia_id"])

        if resultado is None:
            flash("Formato de archivo no soportado. Subí un archivo .csv o .xlsx.", "error")
            return redirect(url_for("importar_clientes"))

        flash(
            f"Importación completa: {resultado['importados']} clientes importados, "
            f"{resultado['duplicados']} duplicados omitidos, {resultado['invalidos']} filas inválidas omitidas.",
            "exito"
        )
        return redirect(url_for("ver_clientes"))

    else:
        return render_template("importar_clientes.html")


@app.route("/clientes/importar/plantilla")
@login_requerido
def descargar_plantilla_clientes():
    buffer = generar_plantilla_clientes()
    return send_file(
        buffer,
        as_attachment=True,
        download_name="plantilla_clientes.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


MIMETYPE_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@app.route("/clientes/exportar")
@login_requerido
def exportar_clientes():
    buffer = exportar_clientes_excel(session["agencia_id"])
    return send_file(buffer, as_attachment=True, download_name="clientes.xlsx", mimetype=MIMETYPE_XLSX)


@app.route("/proyectos/exportar")
@login_requerido
def exportar_proyectos():
    buffer = exportar_proyectos_excel(session["agencia_id"])
    return send_file(buffer, as_attachment=True, download_name="proyectos.xlsx", mimetype=MIMETYPE_XLSX)


@app.route("/pagos/exportar")
@login_requerido
def exportar_pagos():
    buffer = exportar_pagos_excel(session["agencia_id"])
    return send_file(buffer, as_attachment=True, download_name="pagos.xlsx", mimetype=MIMETYPE_XLSX)

        
@app.route("/clientes/<int:id>/editar", methods=["GET", "POST"])
@login_requerido
def editar_cliente_ruta(id):
    cliente = obtener_cliente_por_id(id, session["agencia_id"])

    if cliente is None:
        flash("Cliente no encontrado.", "error")
        return redirect(url_for("ver_clientes"))

    if request.method == "POST":
        nombre = request.form["nombre"]
        email = request.form["email"]
        telefono = request.form["telefono"]
        empresa = request.form["empresa"]
        notas = request.form["notas"]
        
        if nombre == "" or email == "":
            return redirigir_o_responder_error("Nombre y email son obligatorios.", "editar_cliente_ruta", id=id)

        if not email_valido(email):
            return redirigir_o_responder_error("El email no tiene un formato válido (ejemplo: nombre@dominio.com).", "editar_cliente_ruta", id=id)

        if not telefono_valido(telefono):
            return redirigir_o_responder_error("El teléfono no tiene la cantidad de números esperada para el país seleccionado.", "editar_cliente_ruta", id=id)

        otro_cliente = obtener_cliente_por_email(email, session["agencia_id"])
        if otro_cliente and otro_cliente[0] != id:
            return redirigir_o_responder_error(f"Ya existe otro cliente con el email '{email}'.", "editar_cliente_ruta", id=id)

        editar_cliente_por_id(id, nombre, email, telefono, empresa, notas, session["agencia_id"])
        auditar("editar", "cliente", id, f"Editó el cliente '{nombre}'.")

        if es_peticion_ajax():
            return jsonify({"exito": True})

        flash("Cliente actualizado correctamente.", "exito")
        return redirect(url_for("ver_clientes"))
        
    else:
        return redirect(url_for("ver_clientes", editar=id))
    
    
        
@app.route("/clientes/<int:id>/eliminar", methods=["POST"])
@admin_requerido
def eliminar_cliente_ruta(id):
    cliente = obtener_cliente_por_id(id, session["agencia_id"])
    eliminar_cliente_por_id(id, session["agencia_id"])
    auditar("eliminar", "cliente", id, f"Eliminó el cliente '{cliente[1] if cliente else id}'.")
    flash("Cliente eliminado.", "exito")
    return redirect(url_for("ver_clientes"))


@app.route("/clientes/<int:id>/archivar", methods=["POST"])
@login_requerido
def archivar_cliente_ruta(id):
    cliente = obtener_cliente_por_id(id, session["agencia_id"])
    if cliente is None:
        return redirigir_o_responder_error("Cliente no encontrado.", "ver_clientes")

    archivar_cliente_por_id(id, session["agencia_id"])
    auditar("editar", "cliente", id, f"Archivó al cliente '{cliente[1]}'.")

    if es_peticion_ajax():
        return jsonify({"exito": True})

    flash("Cliente archivado.", "exito")
    return redirect(request.referrer or url_for("ver_clientes"))


@app.route("/clientes/<int:id>/desarchivar", methods=["POST"])
@login_requerido
def desarchivar_cliente_ruta(id):
    cliente = obtener_cliente_por_id(id, session["agencia_id"])
    if cliente is None:
        return redirigir_o_responder_error("Cliente no encontrado.", "ver_clientes")

    desarchivar_cliente_por_id(id, session["agencia_id"])
    auditar("editar", "cliente", id, f"Desarchivó al cliente '{cliente[1]}'.")

    if es_peticion_ajax():
        return jsonify({"exito": True})

    flash("Cliente restaurado.", "exito")
    return redirect(request.referrer or url_for("ver_clientes"))


@app.route("/api/clientes")
@login_requerido
def api_clientes():
    clientes = obtener_clientes(session["agencia_id"])
    lista = []
    for cliente in clientes:
        lista.append({
            "id": cliente[0],
            "nombre": cliente[1],
            "email": cliente[2],
            "telefono": cliente[3],
            "empresa": cliente[4],
            "notas": cliente[5]
        })
    return jsonify(lista)


@app.route("/api/clientes/<int:id>")
@login_requerido
def api_cliente(id):
    cliente = obtener_cliente_por_id(id, session["agencia_id"])
    if cliente is None:
        return jsonify({"error": "Cliente no encontrado"}), 404
    return jsonify({
        "id": cliente[0],
        "nombre": cliente[1],
        "email": cliente[2],
        "telefono": cliente[3],
        "empresa": cliente[4],
        "notas": cliente[5]
    })


@app.route("/proyectos")
@login_requerido
def ver_proyectos():
    pagina = normalizar_pagina(request.args.get("pagina"))
    ver_archivados = request.args.get("archivados") == "1"
    proyectos, total = obtener_proyectos_paginado(session["agencia_id"], pagina, POR_PAGINA, archivados=ver_archivados)
    lista = []
    for proyecto in proyectos:
        cliente = obtener_cliente_por_id(proyecto[2], session["agencia_id"])
        if cliente is None:
            nombre_cliente = "Cliente no encontrado"
        else:
            nombre_cliente = cliente[1]
        por_vencer = proyecto_esta_por_vencer(proyecto[3], proyecto[4])
        lista.append((proyecto, nombre_cliente, por_vencer))
    clientes = obtener_clientes(session["agencia_id"])
    return render_template(
        "proyectos.html", proyectos=lista, clientes=clientes, ver_archivados=ver_archivados,
        pagina=pagina, total_paginas=total_paginas(total, POR_PAGINA), total_registros=total
    )


@app.route("/proyectos/nuevo",methods=["GET", "POST"])
@login_requerido
def nuevo_proyecto():
    if request.method == "POST":
        titulo = request.form["titulo"]
        cliente_id = request.form["cliente_id"]
        estado = request.form["estado"]
        fecha_entrega = request.form["fecha_entrega"]
        presupuesto_texto = request.form.get("presupuesto", "").strip()

        if titulo == "" or cliente_id == "":
            return redirigir_o_responder_error("Título y cliente son obligatorios.", "nuevo_proyecto")

        if fecha_entrega and fecha_entrega < date.today().isoformat():
            return redirigir_o_responder_error("La fecha de entrega no puede ser anterior a hoy.", "nuevo_proyecto")

        presupuesto = None
        if presupuesto_texto:
            try:
                presupuesto = float(presupuesto_texto)
            except ValueError:
                return redirigir_o_responder_error("El presupuesto debe ser un número válido.", "nuevo_proyecto")
            if presupuesto < 0:
                return redirigir_o_responder_error("El presupuesto no puede ser negativo.", "nuevo_proyecto")

        agregar_proyecto(titulo, cliente_id, estado, fecha_entrega, session["agencia_id"], presupuesto)
        auditar("crear", "proyecto", None, f"Creó el proyecto '{titulo}'.")

        if proyecto_esta_por_vencer(estado, fecha_entrega):
            agencia = obtener_agencia_por_id(session["agencia_id"])
            if agencia and agencia[2]:
                try:
                    cliente = obtener_cliente_por_id(cliente_id, session["agencia_id"])
                    nombre_cliente = cliente[1] if cliente else "Cliente no encontrado"
                    avisar_proyecto_individual(titulo, fecha_entrega, nombre_cliente, agencia[2])
                except Exception as error:
                    print(f"No se pudo enviar el aviso de Telegram: {error}")

        if es_peticion_ajax():
            return jsonify({"exito": True})

        flash("Proyecto agregado correctamente.", "exito")
        return redirect(url_for("ver_proyectos"))

    else:
        return redirect(url_for("ver_proyectos", nuevo=1))
    
    
@app.route("/proyectos/<int:id>")
@login_requerido
def ver_proyecto(id):
    proyecto = obtener_proyecto_por_id(id, session["agencia_id"])

    if proyecto is None:
        flash("Proyecto no encontrado.", "error")
        return redirect(url_for("ver_proyectos"))
    else:
        cliente = obtener_cliente_por_id(proyecto[2], session["agencia_id"])
        if cliente is None:
            nombre_cliente = "Cliente no encontrado"
        else:
            nombre_cliente = cliente[1]
        pagos = pagos_de_proyecto(id, session["agencia_id"])
        conversion = datos_conversion(session["agencia_id"])
        clientes = obtener_clientes(session["agencia_id"])
        cobrado_proyecto = sum(pago[2] for pago in pagos if pago[5] == "cobrado")
        saldo_pendiente = proyecto[6] - cobrado_proyecto if proyecto[6] is not None else None
        return render_template(
            "proyecto_detalle.html", proyecto=proyecto, nombre_cliente=nombre_cliente, pagos=pagos,
            sugerencias=None, clientes=clientes, cobrado_proyecto=cobrado_proyecto,
            saldo_pendiente=saldo_pendiente, **conversion
        )
    
    
@app.route("/proyectos/<int:id>/sugerencias-ia", methods=["POST"])
@login_requerido
def sugerencias_ia_proyecto(id):
    proyecto = obtener_proyecto_por_id(id, session["agencia_id"])

    if proyecto is None:
        flash("Proyecto no encontrado.", "error")
        return redirect(url_for("ver_proyectos"))

    cliente = obtener_cliente_por_id(proyecto[2], session["agencia_id"])
    if cliente is None:
        nombre_cliente = "Cliente no encontrado"
    else:
        nombre_cliente = cliente[1]

    notas = notas_de_cliente(proyecto[2], session["agencia_id"])
    pagos = pagos_de_proyecto(id, session["agencia_id"])
    conversion = datos_conversion(session["agencia_id"])

    try:
        sugerencias = generar_sugerencias_proyecto(proyecto, nombre_cliente, notas, pagos)
    except Exception:
        flash("No se pudieron generar las sugerencias en este momento. Probá de nuevo en un rato.", "error")
        sugerencias = None

    clientes = obtener_clientes(session["agencia_id"])
    cobrado_proyecto = sum(pago[2] for pago in pagos if pago[5] == "cobrado")
    saldo_pendiente = proyecto[6] - cobrado_proyecto if proyecto[6] is not None else None
    return render_template(
        "proyecto_detalle.html", proyecto=proyecto, nombre_cliente=nombre_cliente, pagos=pagos,
        sugerencias=sugerencias, clientes=clientes, cobrado_proyecto=cobrado_proyecto,
        saldo_pendiente=saldo_pendiente, **conversion
    )
    

@app.route("/proyectos/<int:id>/editar", methods=["GET", "POST"])
@login_requerido
def editar_proyecto_ruta(id):
    proyecto = obtener_proyecto_por_id(id, session["agencia_id"])

    if proyecto is None:
        flash("Proyecto no encontrado.", "error")
        return redirect(url_for("ver_proyectos"))

    if request.method == "POST":
        estado_anterior = proyecto[3]
        fecha_entrega_anterior = proyecto[4]

        titulo = request.form["titulo"]
        cliente_id = request.form["cliente_id"]
        estado = request.form["estado"]
        fecha_entrega = request.form["fecha_entrega"]
        presupuesto_texto = request.form.get("presupuesto", "").strip()

        if titulo == "" or cliente_id == "":
            return redirigir_o_responder_error("Título y cliente son obligatorios.", "editar_proyecto_ruta", id=id)

        if fecha_entrega and fecha_entrega != fecha_entrega_anterior and fecha_entrega < date.today().isoformat():
            return redirigir_o_responder_error("La fecha de entrega no puede ser anterior a hoy.", "editar_proyecto_ruta", id=id)

        presupuesto = None
        if presupuesto_texto:
            try:
                presupuesto = float(presupuesto_texto)
            except ValueError:
                return redirigir_o_responder_error("El presupuesto debe ser un número válido.", "editar_proyecto_ruta", id=id)
            if presupuesto < 0:
                return redirigir_o_responder_error("El presupuesto no puede ser negativo.", "editar_proyecto_ruta", id=id)

        editar_proyecto_por_id(id, titulo, cliente_id, estado, fecha_entrega, session["agencia_id"], presupuesto)
        auditar("editar", "proyecto", id, f"Editó el proyecto '{titulo}'.")

        if fecha_entrega != fecha_entrega_anterior and proyecto_esta_por_vencer(estado, fecha_entrega):
            agencia = obtener_agencia_por_id(session["agencia_id"])
            if agencia and agencia[2]:
                try:
                    cliente = obtener_cliente_por_id(cliente_id, session["agencia_id"])
                    nombre_cliente = cliente[1] if cliente else "Cliente no encontrado"
                    avisar_proyecto_individual(titulo, fecha_entrega, nombre_cliente, agencia[2])
                except Exception as error:
                    print(f"No se pudo enviar el aviso de Telegram: {error}")

        if estado == "Completado" and estado_anterior != "Completado":
            cliente = obtener_cliente_por_id(cliente_id, session["agencia_id"])
            agencia = obtener_agencia_por_id(session["agencia_id"])
            if cliente and cliente[2] and agencia[3] and agencia[4]:
                try:
                    enviar_correo(
                        cliente[2],
                        f"Proyecto completado: {titulo}",
                        f"Hola {cliente[1]},\n\nTu proyecto '{titulo}' ha sido marcado como completado.\n\nSaludos.",
                        agencia[3],
                        agencia[4]
                    )
                except Exception as error:
                    print(f"No se pudo enviar el correo: {error}")

        if es_peticion_ajax():
            return jsonify({"exito": True})

        flash("Proyecto actualizado correctamente.", "exito")
        return redirect(url_for("ver_proyectos"))
    else:
        return redirect(url_for("ver_proyectos", editar=id))


@app.route("/proyectos/<int:id>/marcar-completado", methods=["POST"])
@login_requerido
def marcar_proyecto_completado_ruta(id):
    proyecto = obtener_proyecto_por_id(id, session["agencia_id"])
    if proyecto is None:
        return redirigir_o_responder_error("Proyecto no encontrado.", "ver_proyectos")

    if proyecto[3] != "Completado":
        marcar_proyecto_completado(id, session["agencia_id"])
        auditar("editar", "proyecto", id, f"Marcó como completado el proyecto '{proyecto[1]}'.")

        cliente = obtener_cliente_por_id(proyecto[2], session["agencia_id"])
        agencia = obtener_agencia_por_id(session["agencia_id"])
        if cliente and cliente[2] and agencia[3] and agencia[4]:
            try:
                enviar_correo(
                    cliente[2],
                    f"Proyecto completado: {proyecto[1]}",
                    f"Hola {cliente[1]},\n\nTu proyecto '{proyecto[1]}' ha sido marcado como completado.\n\nSaludos.",
                    agencia[3],
                    agencia[4]
                )
            except Exception as error:
                print(f"No se pudo enviar el correo: {error}")

    if es_peticion_ajax():
        return jsonify({"exito": True})

    flash("Proyecto marcado como completado.", "exito")
    return redirect(request.referrer or url_for("ver_proyectos"))


@app.route("/proyectos/<int:id>/eliminar", methods=["POST"])
@admin_requerido
def eliminar_proyecto_ruta(id):
    proyecto = obtener_proyecto_por_id(id, session["agencia_id"])
    eliminar_proyecto_por_id(id, session["agencia_id"])
    auditar("eliminar", "proyecto", id, f"Eliminó el proyecto '{proyecto[1] if proyecto else id}'.")
    flash("Proyecto eliminado.", "exito")
    return redirect(url_for("ver_proyectos"))


@app.route("/proyectos/<int:id>/archivar", methods=["POST"])
@login_requerido
def archivar_proyecto_ruta(id):
    proyecto = obtener_proyecto_por_id(id, session["agencia_id"])
    if proyecto is None:
        return redirigir_o_responder_error("Proyecto no encontrado.", "ver_proyectos")

    archivar_proyecto_por_id(id, session["agencia_id"])
    auditar("editar", "proyecto", id, f"Archivó el proyecto '{proyecto[1]}'.")

    if es_peticion_ajax():
        return jsonify({"exito": True})

    flash("Proyecto archivado.", "exito")
    return redirect(request.referrer or url_for("ver_proyectos"))


@app.route("/proyectos/<int:id>/desarchivar", methods=["POST"])
@login_requerido
def desarchivar_proyecto_ruta(id):
    proyecto = obtener_proyecto_por_id(id, session["agencia_id"])
    if proyecto is None:
        return redirigir_o_responder_error("Proyecto no encontrado.", "ver_proyectos")

    desarchivar_proyecto_por_id(id, session["agencia_id"])
    auditar("editar", "proyecto", id, f"Desarchivó el proyecto '{proyecto[1]}'.")

    if es_peticion_ajax():
        return jsonify({"exito": True})

    flash("Proyecto restaurado.", "exito")
    return redirect(request.referrer or url_for("ver_proyectos"))


@app.route("/pagos")
@login_requerido
def ver_pagos():
    pagina = normalizar_pagina(request.args.get("pagina"))
    pagos, total = obtener_pagos_paginado(session["agencia_id"], pagina, POR_PAGINA)
    lista = []
    for pago in pagos:
        proyecto = obtener_proyecto_por_id(pago[1], session["agencia_id"])
        if proyecto is None:
            titulo_proyecto = "Proyecto no encontrado"
        else:
            titulo_proyecto = proyecto[1]
        lista.append((pago, titulo_proyecto))
    proyectos = obtener_proyectos(session["agencia_id"])
    conversion = datos_conversion(session["agencia_id"])
    return render_template(
        "pagos.html", pagos=lista, proyectos=proyectos, **conversion,
        pagina=pagina, total_paginas=total_paginas(total, POR_PAGINA), total_registros=total
    )
        
        
@app.route("/pagos/nuevo", methods=["GET", "POST"])
@login_requerido
def nuevo_pago():
    if request.method == "POST":
        proyecto_id = request.form["proyecto_id"]
        monto = request.form["monto"]
        fecha = request.form["fecha"]
        estado = request.form.get("estado", "cobrado")
        if estado not in ("cobrado", "pendiente"):
            estado = "cobrado"

        if proyecto_id == "" or monto == "":
            return redirigir_o_responder_error("Proyecto y monto son obligatorios.", "nuevo_pago")

        try:
            monto = float(monto)
        except ValueError:
            return redirigir_o_responder_error("El monto debe ser un número válido.", "nuevo_pago")

        if monto <= 0:
            return redirigir_o_responder_error("El monto tiene que ser mayor a 0.", "nuevo_pago")

        agregar_pago(proyecto_id, monto, fecha, session["agencia_id"], estado)
        auditar("crear", "pago", None, f"Registró un pago de ${monto:,.2f} ({estado}).")

        if es_peticion_ajax():
            return jsonify({"exito": True})

        flash("Pago agregado correctamente.", "exito")
        return redirect(url_for("ver_pagos"))

    else:
        return redirect(url_for("ver_pagos", nuevo=1))
    
    
@app.route("/pagos/<int:id>/recibo")
@login_requerido
def recibo_pago(id):
    pago = obtener_pago_por_id(id, session["agencia_id"])
    if pago is None:
        flash("Pago no encontrado.", "error")
        return redirect(url_for("ver_pagos"))

    proyecto = obtener_proyecto_por_id(pago[1], session["agencia_id"])
    titulo_proyecto = proyecto[1] if proyecto else "Proyecto no encontrado"
    nombre_cliente = "Cliente no encontrado"
    if proyecto:
        cliente = obtener_cliente_por_id(proyecto[2], session["agencia_id"])
        if cliente:
            nombre_cliente = cliente[1]

    agencia = obtener_agencia_por_id(session["agencia_id"])
    conversion = datos_conversion(session["agencia_id"])

    buffer = generar_recibo_pdf(
        pago, titulo_proyecto, nombre_cliente, agencia[1] if agencia else None,
        conversion["moneda_actual"], conversion["simbolo_actual"], conversion["tasa_cambio"]
    )
    return send_file(buffer, as_attachment=True, download_name=f"recibo_pago_{id}.pdf", mimetype="application/pdf")


@app.route("/pagos/<int:id>")
@login_requerido
def ver_pago(id):
    pago = obtener_pago_por_id(id, session["agencia_id"])

    if pago is None:
        flash("Pago no encontrado.", "error")
        return redirect(url_for("ver_pagos"))
    else:
        proyecto = obtener_proyecto_por_id(pago[1], session["agencia_id"])
        if proyecto is None:
            titulo_proyecto = "Proyecto no encontrado"
        else:
            titulo_proyecto = proyecto[1]
        conversion = datos_conversion(session["agencia_id"])
        proyectos = obtener_proyectos(session["agencia_id"])
        return render_template("pago_detalle.html", pago=pago, titulo_proyecto=titulo_proyecto, proyectos=proyectos, **conversion)
    

@app.route("/pagos/<int:id>/editar", methods=["GET", "POST"])
@login_requerido
def editar_pago_ruta(id):
    pago = obtener_pago_por_id(id, session["agencia_id"])

    if pago is None:
        flash("Pago no encontrado.", "error")
        return redirect(url_for("ver_pagos"))

    if request.method == "POST":
        proyecto_id = request.form["proyecto_id"]
        monto = request.form["monto"]
        fecha = request.form["fecha"]
        estado = request.form.get("estado", "cobrado")
        if estado not in ("cobrado", "pendiente"):
            estado = "cobrado"

        if proyecto_id == "" or monto == "":
            return redirigir_o_responder_error("Proyecto y monto son obligatorios.", "editar_pago_ruta", id=id)

        try:
            monto = float(monto)
        except ValueError:
            return redirigir_o_responder_error("El monto debe ser un número válido.", "editar_pago_ruta", id=id)

        if monto <= 0:
            return redirigir_o_responder_error("El monto tiene que ser mayor a 0.", "editar_pago_ruta", id=id)

        editar_pago_por_id(id, proyecto_id, monto, fecha, session["agencia_id"], estado)
        auditar("editar", "pago", id, f"Editó el pago #{id} (${monto:,.2f}, {estado}).")

        if es_peticion_ajax():
            return jsonify({"exito": True})

        flash("Pago actualizado correctamente.", "exito")
        return redirect(url_for("ver_pago", id=id))

    else:
        return redirect(url_for("ver_pagos", editar=id))
        
@app.route("/pagos/<int:id>/eliminar", methods=["POST"])
@admin_requerido
def eliminar_pago_ruta(id):
    pago = obtener_pago_por_id(id, session["agencia_id"])
    eliminar_pago_por_id(id, session["agencia_id"])
    auditar("eliminar", "pago", id, f"Eliminó el pago #{id}" + (f" (${pago[2]:,.2f})." if pago else "."))
    flash("Pago eliminado.", "exito")
    return redirect(url_for("ver_pagos"))

@app.route("/pagos/<int:id>/marcar-cobrado", methods=["POST"])
@login_requerido
def marcar_pago_cobrado_ruta(id):
    pago = obtener_pago_por_id(id, session["agencia_id"])
    if pago is None:
        return redirigir_o_responder_error("Pago no encontrado.", "ver_pagos")

    marcar_pago_cobrado(id, session["agencia_id"])
    auditar("editar", "pago", id, f"Marcó como cobrado el pago #{id} (${pago[2]:,.2f}).")

    if es_peticion_ajax():
        return jsonify({"exito": True})

    flash("Pago marcado como cobrado.", "exito")
    return redirect(request.referrer or url_for("ver_pagos"))

@app.route("/notas")
@login_requerido
def ver_notas():
    pagina = normalizar_pagina(request.args.get("pagina"))
    notas, total = obtener_notas_paginado(session["agencia_id"], pagina, POR_PAGINA)
    lista = []
    for nota in notas:
        cliente = obtener_cliente_por_id(nota[1], session["agencia_id"])
        if cliente is None:
            nombre_cliente = "Cliente no encontrado"
        else:
            nombre_cliente = cliente[1]
        lista.append((nota, nombre_cliente))
    clientes = obtener_clientes(session["agencia_id"])
    return render_template(
        "notas.html", notas=lista, clientes=clientes, fecha_hoy=date.today().isoformat(),
        pagina=pagina, total_paginas=total_paginas(total, POR_PAGINA), total_registros=total
    )


@app.route("/notas/nuevo", methods=["GET", "POST"])
@login_requerido
def nueva_nota():
    if request.method == "POST":
        cliente_id = request.form["cliente_id"]
        contenido = request.form["contenido"]
        fecha = request.form["fecha"]

        if cliente_id == "" or contenido == "":
            return redirigir_o_responder_error("Cliente y contenido son obligatorios.", "nueva_nota")

        agregar_nota(cliente_id, contenido, fecha, session["agencia_id"])
        auditar("crear", "nota", None, "Agregó una nota.")

        if es_peticion_ajax():
            return jsonify({"exito": True})

        flash("Nota agregada correctamente.", "exito")
        return redirect(url_for("ver_notas"))

    else:
        return redirect(url_for("ver_notas", nuevo=1))

@app.route("/notas/generar-ia", methods=["POST"])
@login_requerido
def generar_nota_ia():
    cliente_id = request.form["cliente_id"]
    palabras_clave = request.form["palabras_clave"]

    try:
        borrador_ia = redactar_nota(palabras_clave)
    except Exception:
        if es_peticion_ajax():
            return jsonify({"exito": False, "error": "No se pudo generar el borrador. Probá de nuevo."}), 400
        flash("No se pudo generar el borrador en este momento. Probá de nuevo en un rato.", "error")
        return redirect(url_for("ver_notas"))

    if es_peticion_ajax():
        return jsonify({"exito": True, "borrador": borrador_ia})

    clientes = obtener_clientes(session["agencia_id"])
    return render_template("nota_form.html", nota=None, clientes=clientes, borrador_ia=borrador_ia, cliente_id_seleccionado=cliente_id, fecha_hoy=date.today().isoformat())
    
        
@app.route("/notas/<int:id>")
@login_requerido
def ver_nota(id):
    nota = obtener_nota_por_id(id, session["agencia_id"])

    if nota is None:
        flash("Nota no encontrada.", "error")
        return redirect(url_for("ver_notas"))
    else:
        cliente = obtener_cliente_por_id(nota[1], session["agencia_id"])
        if cliente is None:
            nombre_cliente = "Cliente no encontrado"
        else:
            nombre_cliente = cliente[1]
        clientes = obtener_clientes(session["agencia_id"])
        return render_template("nota_detalle.html", nota=nota, nombre_cliente=nombre_cliente, clientes=clientes)
    
@app.route("/notas/<int:id>/editar", methods=["GET", "POST"])
@login_requerido
def editar_nota_ruta(id):
    nota = obtener_nota_por_id(id, session["agencia_id"])

    if nota is None:
        flash("Nota no encontrada.", "error")
        return redirect(url_for("ver_notas"))

    if request.method == "POST":
        cliente_id = request.form["cliente_id"]
        contenido = request.form["contenido"]
        fecha = request.form["fecha"]
        
        if cliente_id == "" or contenido == "":
            return redirigir_o_responder_error("Cliente y contenido son obligatorios.", "editar_nota_ruta", id=id)

        editar_nota_por_id(id, cliente_id, contenido, fecha, session["agencia_id"])
        auditar("editar", "nota", id, f"Editó la nota #{id}.")

        if es_peticion_ajax():
            return jsonify({"exito": True})

        flash("Nota actualizada correctamente.", "exito")
        return redirect(url_for("ver_notas"))

    else:
        return redirect(url_for("ver_notas", editar=id))
        
@app.route("/notas/<int:id>/eliminar", methods=["POST"])
@admin_requerido
def eliminar_nota_ruta(id):
    eliminar_nota_por_id(id, session["agencia_id"])
    auditar("eliminar", "nota", id, f"Eliminó la nota #{id}.")
    flash("Nota eliminada.", "exito")
    return redirect(url_for("ver_notas"))


@app.errorhandler(404)
def pagina_no_encontrada(error):
    return render_template("404.html"), 404


@app.errorhandler(RateLimitExceeded)
def limite_excedido(error):
    return render_template(
        "login.html",
        error="Demasiados intentos de inicio de sesión. Esperá un minuto e intentá de nuevo."
    ), 429


if __name__ == "__main__":
    modo_debug = os.getenv("FLASK_DEBUG", "False") == "True"
    app.run(debug=modo_debug)