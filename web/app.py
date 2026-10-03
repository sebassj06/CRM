import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)

from flask import Flask, request, render_template, redirect, url_for, session, jsonify, flash, send_file
from functools import wraps
from psycopg2.errors import UniqueViolation
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
                           desarchivar_cliente_por_id,
                           actualizar_etapa_cliente,
                           ETAPAS_CLIENTE
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
    desarchivar_proyecto_por_id,
    contar_proyectos_con_estado
)
from core.etapas import (
    obtener_etapas,
    obtener_etapa_por_id,
    agregar_etapa,
    editar_etapa_por_id,
    eliminar_etapa_por_id,
    mover_etapa,
    nombres_etapas,
    nombres_etapas_finales,
    etapa_es_final,
    etapa_final_principal,
    mapa_clases_badge,
    contar_etapas,
    contar_etapas_finales,
    nombre_etapa_duplicado
)
from core.campos_personalizados import (
    ENTIDADES_VALIDAS,
    TIPOS_VALIDOS,
    agregar_definicion,
    obtener_definiciones,
    obtener_definicion_por_id,
    editar_definicion_por_id,
    eliminar_definicion_por_id,
    validar_valores_formulario,
    fusionar_campos_personalizados
)
from core.pagos import(
    obtener_pagos,
    obtener_pago_por_id,
    agregar_pago,
    editar_pago_por_id,
    eliminar_pago_por_id,
    pagos_de_proyecto,
    pagos_de_cliente,
    pagos_de_factura,
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
from core.cotizaciones import (
    ESTADOS_COTIZACION,
    agregar_cotizacion,
    obtener_cotizaciones_paginado,
    obtener_cotizacion_por_id,
    obtener_cotizacion_por_token,
    editar_cotizacion_por_id,
    eliminar_cotizacion_por_id,
    cambiar_estado_cotizacion,
    marcar_convertida,
    reemplazar_items,
    obtener_items,
    calcular_totales,
    cotizacion_esta_vencida,
    contar_cotizaciones_cliente,
    contar_cotizaciones_proyecto,
    cotizaciones_de_cliente
)
from core.facturas import (
    ESTADOS_FACTURA,
    agregar_factura,
    facturas_de_proyecto,
    facturas_pendientes_de_pago,
    facturas_de_cliente,
    obtener_facturas_paginado,
    obtener_factura_por_id,
    obtener_factura_por_token,
    editar_factura_por_id,
    eliminar_factura_por_id,
    cambiar_estado_factura,
    reemplazar_items_factura,
    obtener_items_factura,
    calcular_totales_factura,
    factura_esta_vencida,
    cobrado_factura,
    saldo_factura,
    sincronizar_estado_factura,
    formatear_numero_factura
)
from core.gastos import (
    CATEGORIAS_GASTO,
    agregar_gasto,
    obtener_gastos_proyecto,
    obtener_gastos_paginado,
    obtener_gasto_por_id,
    editar_gasto_por_id,
    eliminar_gasto_por_id,
    total_gastos_proyecto,
    rentabilidad_cliente
)
from core.tareas import (
    PRIORIDADES,
    ESTADOS as ESTADOS_TAREA,
    agregar_tarea,
    obtener_tareas_proyecto,
    obtener_tareas,
    tareas_de_cliente,
    obtener_tareas_paginado,
    obtener_tarea_por_id,
    editar_tarea_por_id,
    eliminar_tarea_por_id,
    marcar_estado_tarea,
    tareas_por_vencer,
    progreso_proyecto,
    agregar_subtarea,
    obtener_subtareas,
    obtener_subtarea_por_id,
    alternar_subtarea,
    eliminar_subtarea
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
from core.recibos import generar_recibo_pdf, generar_cotizacion_pdf, generar_factura_pdf
from core.auditoria import registrar_auditoria, obtener_auditoria_paginado
from core.divisas import MONEDAS, obtener_tasa_cambio, simbolo_moneda
from core.paises import PAISES
from avisos_telegram import avisar_proyecto_individual
from werkzeug.utils import secure_filename
import random
import secrets

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
app.config.update(
    SESSION_COOKIE_SAMESITE="Lax",
    # Secure (cookie solo por HTTPS) solo fuera de modo debug: en local se
    # corre por HTTP sin TLS, y con esto activado el login no funcionaría.
    # En Render (producción) FLASK_DEBUG no está seteado, así que queda en True.
    SESSION_COOKIE_SECURE=os.getenv("FLASK_DEBUG", "False") != "True",
)
csrf = CSRFProtect(app)
limiter = Limiter(get_remote_address, app=app, default_limits=[])

CARPETA_FOTOS_PERFIL = os.path.join(app.root_path, "static", "uploads", "perfiles")
EXTENSIONES_FOTO_PERMITIDAS = {"png", "jpg", "jpeg", "webp"}
TAMANO_MAXIMO_FOTO = 3 * 1024 * 1024  # 3 MB

CARPETA_COMPROBANTES = os.path.join(app.root_path, "static", "uploads", "comprobantes")
EXTENSIONES_COMPROBANTE_PERMITIDAS = {"png", "jpg", "jpeg", "webp", "pdf"}
TAMANO_MAXIMO_COMPROBANTE = 5 * 1024 * 1024  # 5 MB


def extension_foto_valida(nombre_archivo):
    return "." in nombre_archivo and nombre_archivo.rsplit(".", 1)[1].lower() in EXTENSIONES_FOTO_PERMITIDAS


def extension_comprobante_valida(nombre_archivo):
    return "." in nombre_archivo and nombre_archivo.rsplit(".", 1)[1].lower() in EXTENSIONES_COMPROBANTE_PERMITIDAS


def guardar_comprobante(archivo):
    # Devuelve la ruta relativa a 'static/' del comprobante guardado, o None si
    # no se subió ningún archivo. Lanza ValueError con un mensaje para el
    # usuario si el archivo no pasa las validaciones.
    if not archivo or not archivo.filename:
        return None

    if not extension_comprobante_valida(archivo.filename):
        raise ValueError("El comprobante debe ser .png, .jpg, .jpeg, .webp o .pdf.")

    archivo.seek(0, os.SEEK_END)
    tamano = archivo.tell()
    archivo.seek(0)
    if tamano > TAMANO_MAXIMO_COMPROBANTE:
        raise ValueError("El comprobante no puede superar los 5 MB.")

    os.makedirs(CARPETA_COMPROBANTES, exist_ok=True)
    extension = secure_filename(archivo.filename).rsplit(".", 1)[1].lower()
    nombre_archivo = f"gasto_{secrets.token_hex(8)}.{extension}"
    archivo.save(os.path.join(CARPETA_COMPROBANTES, nombre_archivo))
    return f"uploads/comprobantes/{nombre_archivo}"

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
                "tareas_vencidas": tareas_por_vencer(session["agencia_id"]),
                "foto_perfil_actual": usuario_actual[6] if usuario_actual else None
            }
    return {"agencia_actual": None, "rol_actual": None, "notificaciones": [], "pagos_vencidos": [], "tareas_vencidas": [], "foto_perfil_actual": None}


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
    clases_estado = mapa_clases_badge(agencia_id)

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
        "hay_ingresos_mensuales": hay_ingresos_mensuales,
        "clases_estado": clases_estado
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
        app.logger.exception("Falló la generación del resumen ejecutivo con IA.")
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


@app.route("/configuracion/campos")
@admin_requerido
def ver_campos_personalizados():
    definiciones_clientes = obtener_definiciones(session["agencia_id"], "clientes")
    definiciones_proyectos = obtener_definiciones(session["agencia_id"], "proyectos")
    return render_template(
        "campos_personalizados.html",
        definiciones_clientes=definiciones_clientes,
        definiciones_proyectos=definiciones_proyectos
    )


@app.route("/configuracion/campos/nuevo", methods=["POST"])
@admin_requerido
def nueva_definicion_campo():
    entidad = request.form.get("entidad", "")
    etiqueta = request.form.get("etiqueta", "").strip()
    tipo = request.form.get("tipo", "")
    opciones = request.form.get("opciones", "").strip() or None
    obligatorio = request.form.get("obligatorio") == "on"

    if entidad not in ENTIDADES_VALIDAS:
        return redirigir_o_responder_error("Entidad inválida.", "ver_campos_personalizados")
    if tipo not in TIPOS_VALIDOS:
        return redirigir_o_responder_error("Tipo de campo inválido.", "ver_campos_personalizados")
    if etiqueta == "":
        return redirigir_o_responder_error("La etiqueta es obligatoria.", "ver_campos_personalizados")
    if tipo == "seleccion" and not opciones:
        return redirigir_o_responder_error("Las opciones son obligatorias para un campo de selección.", "ver_campos_personalizados")

    definicion_id = agregar_definicion(session["agencia_id"], entidad, etiqueta, tipo, opciones, obligatorio)
    auditar("crear", "definicion_campo", definicion_id, f"Creó el campo personalizado '{etiqueta}' ({entidad}).")

    if es_peticion_ajax():
        return jsonify({"exito": True})
    flash("Campo personalizado agregado correctamente.", "exito")
    return redirect(url_for("ver_campos_personalizados"))


@app.route("/configuracion/campos/<int:id>/editar", methods=["POST"])
@admin_requerido
def editar_definicion_campo_ruta(id):
    definicion = obtener_definicion_por_id(id, session["agencia_id"])
    if definicion is None:
        return redirigir_o_responder_error("Campo personalizado no encontrado.", "ver_campos_personalizados")

    etiqueta = request.form.get("etiqueta", "").strip()
    opciones = request.form.get("opciones", "").strip() or None
    obligatorio = request.form.get("obligatorio") == "on"

    if etiqueta == "":
        return redirigir_o_responder_error("La etiqueta es obligatoria.", "ver_campos_personalizados")
    if definicion[5] == "seleccion" and not opciones:
        return redirigir_o_responder_error("Las opciones son obligatorias para un campo de selección.", "ver_campos_personalizados")

    editar_definicion_por_id(id, session["agencia_id"], etiqueta, opciones, obligatorio)
    auditar("editar", "definicion_campo", id, f"Editó el campo personalizado '{etiqueta}'.")

    if es_peticion_ajax():
        return jsonify({"exito": True})
    flash("Campo personalizado actualizado correctamente.", "exito")
    return redirect(url_for("ver_campos_personalizados"))


@app.route("/configuracion/campos/<int:id>/eliminar", methods=["POST"])
@admin_requerido
def eliminar_definicion_campo_ruta(id):
    definicion = obtener_definicion_por_id(id, session["agencia_id"])
    if definicion is None:
        return redirigir_o_responder_error("Campo personalizado no encontrado.", "ver_campos_personalizados")

    eliminar_definicion_por_id(id, session["agencia_id"])
    auditar("eliminar", "definicion_campo", id, f"Eliminó el campo personalizado '{definicion[4]}'.")
    flash("Campo personalizado eliminado.", "exito")
    return redirect(url_for("ver_campos_personalizados"))


@app.route("/configuracion/etapas")
@admin_requerido
def ver_etapas():
    etapas = obtener_etapas(session["agencia_id"])
    return render_template("etapas.html", etapas=etapas)


@app.route("/configuracion/etapas/nueva", methods=["POST"])
@admin_requerido
def nueva_etapa():
    nombre = request.form.get("nombre", "").strip()
    es_final = request.form.get("es_final") == "on"

    if nombre == "":
        return redirigir_o_responder_error("El nombre de la etapa es obligatorio.", "ver_etapas")
    if nombre_etapa_duplicado(session["agencia_id"], nombre):
        return redirigir_o_responder_error(f"Ya existe una etapa llamada '{nombre}'.", "ver_etapas")

    etapa_id = agregar_etapa(session["agencia_id"], nombre, es_final)
    auditar("crear", "etapa", etapa_id, f"Creó la etapa '{nombre}'.")

    if es_peticion_ajax():
        return jsonify({"exito": True})
    flash("Etapa agregada correctamente.", "exito")
    return redirect(url_for("ver_etapas"))


@app.route("/configuracion/etapas/<int:id>/editar", methods=["POST"])
@admin_requerido
def editar_etapa_ruta(id):
    etapa = obtener_etapa_por_id(id, session["agencia_id"])
    if etapa is None:
        return redirigir_o_responder_error("Etapa no encontrada.", "ver_etapas")

    nombre = request.form.get("nombre", "").strip()
    es_final = request.form.get("es_final") == "on"

    if nombre == "":
        return redirigir_o_responder_error("El nombre de la etapa es obligatorio.", "ver_etapas")
    if nombre_etapa_duplicado(session["agencia_id"], nombre, excluir_id=id):
        return redirigir_o_responder_error(f"Ya existe una etapa llamada '{nombre}'.", "ver_etapas")
    if etapa[4] and not es_final and contar_etapas_finales(session["agencia_id"]) <= 1:
        return redirigir_o_responder_error("Tiene que quedar al menos una etapa final.", "ver_etapas")

    editar_etapa_por_id(id, session["agencia_id"], nombre, es_final)
    auditar("editar", "etapa", id, f"Editó la etapa '{nombre}'.")

    if es_peticion_ajax():
        return jsonify({"exito": True})
    flash("Etapa actualizada correctamente.", "exito")
    return redirect(url_for("ver_etapas"))


@app.route("/configuracion/etapas/<int:id>/mover", methods=["POST"])
@admin_requerido
def mover_etapa_ruta(id):
    etapa = obtener_etapa_por_id(id, session["agencia_id"])
    if etapa is None:
        return redirigir_o_responder_error("Etapa no encontrada.", "ver_etapas")

    direccion = request.form.get("direccion", "")
    if direccion not in ("arriba", "abajo"):
        return redirigir_o_responder_error("Dirección inválida.", "ver_etapas")

    mover_etapa(id, session["agencia_id"], direccion)

    if es_peticion_ajax():
        return jsonify({"exito": True})
    return redirect(url_for("ver_etapas"))


@app.route("/configuracion/etapas/<int:id>/eliminar", methods=["POST"])
@admin_requerido
def eliminar_etapa_ruta(id):
    etapa = obtener_etapa_por_id(id, session["agencia_id"])
    if etapa is None:
        return redirigir_o_responder_error("Etapa no encontrada.", "ver_etapas")

    if contar_etapas(session["agencia_id"]) <= 1:
        return redirigir_o_responder_error("No podés eliminar la última etapa.", "ver_etapas")
    if etapa[4] and contar_etapas_finales(session["agencia_id"]) <= 1:
        return redirigir_o_responder_error("Tiene que quedar al menos una etapa final.", "ver_etapas")
    if contar_proyectos_con_estado(session["agencia_id"], etapa[2]) > 0:
        return redirigir_o_responder_error("Hay proyectos en esta etapa; movelos antes de eliminarla.", "ver_etapas")

    eliminar_etapa_por_id(id, session["agencia_id"])
    auditar("eliminar", "etapa", id, f"Eliminó la etapa '{etapa[2]}'.")
    flash("Etapa eliminada.", "exito")
    return redirect(url_for("ver_etapas"))


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
                app.logger.exception("Falló el envío del código de verificación de email.")
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
    definiciones_campo = obtener_definiciones(session["agencia_id"], "clientes")
    return render_template(
        "clientes.html", clientes=clientes, paises=PAISES, ver_archivados=ver_archivados, etapas=ETAPAS_CLIENTE,
        pagina=pagina, total_paginas=total_paginas(total, POR_PAGINA), total_registros=total,
        definiciones_campo=definiciones_campo
    )

def _contexto_cliente_detalle(cliente, agencia_id):
    """Contexto común a las 4 rutas que renderizan cliente_detalle.html — la
    ficha de cliente como vista 360°: notas, proyectos, rentabilidad, campos
    personalizados, y ahora también cotizaciones/facturas/tareas/pagos del
    cliente (vía join a sus proyectos donde hace falta)."""
    id = cliente[0]
    proyectos = proyectos_de_cliente(id, agencia_id)

    cotizaciones_cliente = []
    for cotizacion in cotizaciones_de_cliente(id, agencia_id):
        items = obtener_items(cotizacion[0])
        _, total_cotizacion = calcular_totales(items, cotizacion[4], cotizacion[5])
        cotizaciones_cliente.append((cotizacion, total_cotizacion, cotizacion_esta_vencida(cotizacion)))

    facturas_cliente = []
    for factura in facturas_de_cliente(id, agencia_id):
        items = obtener_items_factura(factura[0])
        _, total_factura = calcular_totales_factura(items, factura[4], factura[5])
        facturas_cliente.append((factura, total_factura, factura_esta_vencida(factura)))

    return {
        "notas": notas_de_cliente(id, agencia_id),
        "proyectos": proyectos,
        "rentabilidad": rentabilidad_cliente(id, agencia_id),
        "definiciones_campo": obtener_definiciones(agencia_id, "clientes"),
        "definiciones_campo_proyecto": obtener_definiciones(agencia_id, "proyectos"),
        "clientes": obtener_clientes(agencia_id),
        "paises": PAISES,
        "etapas": ETAPAS_CLIENTE,
        "etapas_proyecto": obtener_etapas(agencia_id),
        "cotizaciones_cliente": cotizaciones_cliente,
        "facturas_cliente": facturas_cliente,
        "tareas_cliente": tareas_de_cliente(id, agencia_id),
        "pagos_cliente": pagos_de_cliente(id, agencia_id),
        "fecha_hoy": date.today().isoformat(),
    }


@app.route("/clientes/<int:id>")
@login_requerido
def ver_cliente(id):
    cliente = obtener_cliente_por_id(id, session["agencia_id"])

    if cliente is None:
        flash("Cliente no encontrado.", "error")
        return redirect(url_for("ver_clientes"))
    else:
        return render_template(
            "cliente_detalle.html", cliente=cliente, resumen=None, asunto_borrador=None,
            cuerpo_borrador=None, mensaje_envio=None,
            **_contexto_cliente_detalle(cliente, session["agencia_id"])
        )


@app.route("/clientes/<int:id>/resumen-ia", methods=["POST"])
@login_requerido
def resumen_ia_cliente(id):
    cliente = obtener_cliente_por_id(id, session["agencia_id"])

    if cliente is None:
        flash("Cliente no encontrado.", "error")
        return redirect(url_for("ver_clientes"))

    notas = notas_de_cliente(id, session["agencia_id"])

    try:
        resumen = resumir_notas_cliente(notas)
    except Exception:
        app.logger.exception("Falló la generación del resumen de notas del cliente con IA.")
        flash("No se pudo generar el resumen en este momento. Probá de nuevo en un rato.", "error")
        resumen = None

    return render_template(
        "cliente_detalle.html", cliente=cliente, resumen=resumen, asunto_borrador=None,
        cuerpo_borrador=None, mensaje_envio=None,
        **_contexto_cliente_detalle(cliente, session["agencia_id"])
    )


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
        app.logger.exception("Falló la generación del borrador de correo con IA.")
        flash("No se pudo generar el borrador en este momento. Probá de nuevo en un rato.", "error")
        cuerpo_borrador = None

    return render_template(
        "cliente_detalle.html", cliente=cliente, resumen=None, asunto_borrador=asunto,
        cuerpo_borrador=cuerpo_borrador, mensaje_envio=None,
        **_contexto_cliente_detalle(cliente, session["agencia_id"])
    )


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
            app.logger.exception("Falló el envío de correo asistido por IA a un cliente.")
            mensaje_envio = f"No se pudo enviar el correo: {error}"

    return render_template(
        "cliente_detalle.html", cliente=cliente, resumen=None, asunto_borrador=None,
        cuerpo_borrador=None, mensaje_envio=mensaje_envio,
        **_contexto_cliente_detalle(cliente, session["agencia_id"])
    )

   
@app.route("/clientes/nuevo", methods=["GET", "POST"])
@login_requerido
def nuevo_cliente():
    if request.method == "POST":
        nombre = request.form["nombre"]
        email = request.form["email"]
        telefono = request.form["telefono"]
        empresa = request.form["empresa"]
        notas = request.form["notas"]
        etapa = request.form.get("etapa", "Prospecto")
        if etapa not in ETAPAS_CLIENTE:
            etapa = "Prospecto"
        valor_estimado_texto = request.form.get("valor_estimado", "").strip()

        if nombre == "" or email == "":
            return redirigir_o_responder_error("Nombre y email son obligatorios.", "nuevo_cliente")

        if not email_valido(email):
            return redirigir_o_responder_error("El email no tiene un formato válido (ejemplo: nombre@dominio.com).", "nuevo_cliente")

        if not telefono_valido(telefono):
            return redirigir_o_responder_error("El teléfono no tiene la cantidad de números esperada para el país seleccionado.", "nuevo_cliente")

        if obtener_cliente_por_email(email, session["agencia_id"]):
            return redirigir_o_responder_error(f"Ya existe un cliente con el email '{email}'.", "nuevo_cliente")

        valor_estimado = None
        if valor_estimado_texto:
            try:
                valor_estimado = float(valor_estimado_texto)
            except ValueError:
                return redirigir_o_responder_error("El valor estimado debe ser un número válido.", "nuevo_cliente")
            if valor_estimado < 0:
                return redirigir_o_responder_error("El valor estimado no puede ser negativo.", "nuevo_cliente")

        campos_validados, error_campos = validar_valores_formulario(session["agencia_id"], "clientes", request.form)
        if error_campos:
            return redirigir_o_responder_error(error_campos, "nuevo_cliente")
        definiciones = obtener_definiciones(session["agencia_id"], "clientes")
        campos_personalizados = fusionar_campos_personalizados({}, campos_validados, definiciones)

        try:
            agregar_cliente(nombre, email, telefono, empresa, notas, session["agencia_id"], etapa=etapa, valor_estimado=valor_estimado, campos_personalizados=campos_personalizados)
        except UniqueViolation:
            # Red de seguridad por si dos requests casi simultáneas pasan la
            # verificación de "ya existe" de arriba al mismo tiempo (carrera
            # check-then-act); la constraint de la base es la que corta esto de verdad.
            return redirigir_o_responder_error(f"Ya existe un cliente con el email '{email}'.", "nuevo_cliente")
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
        etapa = request.form.get("etapa", "Prospecto")
        if etapa not in ETAPAS_CLIENTE:
            etapa = "Prospecto"
        valor_estimado_texto = request.form.get("valor_estimado", "").strip()

        if nombre == "" or email == "":
            return redirigir_o_responder_error("Nombre y email son obligatorios.", "editar_cliente_ruta", id=id)

        if not email_valido(email):
            return redirigir_o_responder_error("El email no tiene un formato válido (ejemplo: nombre@dominio.com).", "editar_cliente_ruta", id=id)

        if not telefono_valido(telefono):
            return redirigir_o_responder_error("El teléfono no tiene la cantidad de números esperada para el país seleccionado.", "editar_cliente_ruta", id=id)

        otro_cliente = obtener_cliente_por_email(email, session["agencia_id"])
        if otro_cliente and otro_cliente[0] != id:
            return redirigir_o_responder_error(f"Ya existe otro cliente con el email '{email}'.", "editar_cliente_ruta", id=id)

        valor_estimado = None
        if valor_estimado_texto:
            try:
                valor_estimado = float(valor_estimado_texto)
            except ValueError:
                return redirigir_o_responder_error("El valor estimado debe ser un número válido.", "editar_cliente_ruta", id=id)
            if valor_estimado < 0:
                return redirigir_o_responder_error("El valor estimado no puede ser negativo.", "editar_cliente_ruta", id=id)

        campos_validados, error_campos = validar_valores_formulario(session["agencia_id"], "clientes", request.form)
        if error_campos:
            return redirigir_o_responder_error(error_campos, "editar_cliente_ruta", id=id)
        definiciones = obtener_definiciones(session["agencia_id"], "clientes")
        campos_personalizados = fusionar_campos_personalizados(cliente[11] if len(cliente) > 11 else {}, campos_validados, definiciones)

        try:
            editar_cliente_por_id(id, nombre, email, telefono, empresa, notas, session["agencia_id"], etapa=etapa, valor_estimado=valor_estimado, campos_personalizados=campos_personalizados)
        except UniqueViolation:
            return redirigir_o_responder_error(f"Ya existe otro cliente con el email '{email}'.", "editar_cliente_ruta", id=id)
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
    if cliente is None:
        flash("Cliente no encontrado.", "error")
        return redirect(url_for("ver_clientes"))

    tiene_proyectos = len(proyectos_de_cliente(id, session["agencia_id"])) > 0
    tiene_notas = len(notas_de_cliente(id, session["agencia_id"])) > 0
    tiene_cotizaciones = contar_cotizaciones_cliente(id, session["agencia_id"]) > 0
    if tiene_proyectos or tiene_notas or tiene_cotizaciones:
        flash(
            f"No se puede eliminar a '{cliente[1]}' porque tiene proyectos, notas o cotizaciones asociadas. "
            "Archivalo en su lugar si querés sacarlo de la vista principal sin perder su historial.",
            "error"
        )
        return redirect(url_for("ver_clientes"))

    eliminar_cliente_por_id(id, session["agencia_id"])
    auditar("eliminar", "cliente", id, f"Eliminó el cliente '{cliente[1]}'.")
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


@app.route("/pipeline")
@login_requerido
def ver_pipeline():
    clientes = obtener_clientes(session["agencia_id"])
    clientes_por_etapa = {etapa: [] for etapa in ETAPAS_CLIENTE}
    totales_por_etapa = {etapa: 0 for etapa in ETAPAS_CLIENTE}

    for cliente in clientes:
        etapa = cliente[9] if cliente[9] in ETAPAS_CLIENTE else "Prospecto"
        clientes_por_etapa[etapa].append(cliente)
        totales_por_etapa[etapa] += cliente[10] or 0

    return render_template(
        "pipeline.html", etapas=ETAPAS_CLIENTE,
        clientes_por_etapa=clientes_por_etapa, totales_por_etapa=totales_por_etapa
    )


@app.route("/clientes/<int:id>/cambiar-etapa", methods=["POST"])
@login_requerido
def cambiar_etapa_cliente_ruta(id):
    cliente = obtener_cliente_por_id(id, session["agencia_id"])
    if cliente is None:
        return jsonify({"exito": False, "error": "Cliente no encontrado."}), 404

    etapa = request.form.get("etapa", "")
    if etapa not in ETAPAS_CLIENTE:
        return jsonify({"exito": False, "error": "Etapa inválida."}), 400

    actualizar_etapa_cliente(id, session["agencia_id"], etapa)
    auditar("editar", "cliente", id, f"Movió a '{cliente[1]}' a la etapa '{etapa}'.")
    return jsonify({"exito": True})


def _parsear_items(form):
    descripciones = form.getlist("item_descripcion[]")
    cantidades = form.getlist("item_cantidad[]")
    precios = form.getlist("item_precio[]")
    items = []
    for descripcion, cantidad, precio in zip(descripciones, cantidades, precios):
        descripcion = descripcion.strip()
        if not descripcion:
            continue
        try:
            cantidad_val = float(cantidad) if cantidad else 1
            precio_val = float(precio) if precio else 0
        except ValueError:
            raise ValueError("Cantidad y precio de los ítems deben ser números válidos.")
        items.append((descripcion, cantidad_val, precio_val))
    return items


@app.route("/cotizaciones")
@login_requerido
def ver_cotizaciones():
    pagina = normalizar_pagina(request.args.get("pagina"))
    cotizaciones, total = obtener_cotizaciones_paginado(session["agencia_id"], pagina, POR_PAGINA)
    lista = []
    for cotizacion in cotizaciones:
        items = obtener_items(cotizacion[0])
        _, total_cotizacion = calcular_totales(items, cotizacion[4], cotizacion[5])
        items_json = [[item[2], item[3], item[4]] for item in items]
        lista.append((cotizacion, total_cotizacion, cotizacion_esta_vencida(cotizacion), items_json))
    clientes = obtener_clientes(session["agencia_id"])
    return render_template(
        "cotizaciones.html", cotizaciones=lista, clientes=clientes,
        pagina=pagina, total_paginas=total_paginas(total, POR_PAGINA), total_registros=total
    )


@app.route("/cotizaciones/nueva", methods=["GET", "POST"])
@login_requerido
def nueva_cotizacion():
    if request.method == "POST":
        cliente_id = request.form.get("cliente_id", "")
        titulo = request.form.get("titulo", "").strip()
        descuento = request.form.get("descuento", "").strip()
        impuesto = request.form.get("impuesto_porcentaje", "").strip()
        fecha_vencimiento = request.form.get("fecha_vencimiento", "").strip() or None
        notas = request.form.get("notas", "").strip() or None

        if cliente_id == "" or titulo == "":
            return redirigir_o_responder_error("Cliente y título son obligatorios.", "nueva_cotizacion")

        if obtener_cliente_por_id(cliente_id, session["agencia_id"]) is None:
            return redirigir_o_responder_error("Cliente inválido.", "nueva_cotizacion")

        try:
            descuento_val = float(descuento) if descuento else 0
            impuesto_val = float(impuesto) if impuesto else 0
        except ValueError:
            return redirigir_o_responder_error("Descuento e impuesto deben ser números válidos.", "nueva_cotizacion")

        try:
            items = _parsear_items(request.form)
        except ValueError as error:
            return redirigir_o_responder_error(str(error), "nueva_cotizacion")

        if not items:
            return redirigir_o_responder_error("Agregá al menos un ítem a la cotización.", "nueva_cotizacion")

        cotizacion_id = agregar_cotizacion(cliente_id, titulo, descuento_val, impuesto_val, fecha_vencimiento, notas, session["agencia_id"])
        reemplazar_items(cotizacion_id, items)
        auditar("crear", "cotizacion", cotizacion_id, f"Creó la cotización '{titulo}'.")

        if es_peticion_ajax():
            return jsonify({"exito": True, "redirigir_a": url_for("ver_cotizacion", id=cotizacion_id)})

        flash("Cotización creada correctamente.", "exito")
        return redirect(url_for("ver_cotizacion", id=cotizacion_id))
    else:
        return redirect(url_for("ver_cotizaciones", nueva=1))


@app.route("/cotizaciones/<int:id>")
@login_requerido
def ver_cotizacion(id):
    cotizacion = obtener_cotizacion_por_id(id, session["agencia_id"])
    if cotizacion is None:
        flash("Cotización no encontrada.", "error")
        return redirect(url_for("ver_cotizaciones"))

    cliente = obtener_cliente_por_id(cotizacion[1], session["agencia_id"])
    items = obtener_items(id)
    subtotal, total = calcular_totales(items, cotizacion[4], cotizacion[5])
    items_json = [[item[2], item[3], item[4]] for item in items]
    enlace_publico = url_for("ver_cotizacion_publica", token=cotizacion[8], _external=True)
    clientes = obtener_clientes(session["agencia_id"])
    return render_template(
        "cotizacion_detalle.html", cotizacion=cotizacion, cliente=cliente, items=items, items_json=items_json,
        subtotal=subtotal, total=total, vencida=cotizacion_esta_vencida(cotizacion),
        enlace_publico=enlace_publico, clientes=clientes
    )


@app.route("/cotizaciones/<int:id>/editar", methods=["GET", "POST"])
@login_requerido
def editar_cotizacion_ruta(id):
    cotizacion = obtener_cotizacion_por_id(id, session["agencia_id"])
    if cotizacion is None:
        flash("Cotización no encontrada.", "error")
        return redirect(url_for("ver_cotizaciones"))

    if request.method == "POST":
        cliente_id = request.form.get("cliente_id", "")
        titulo = request.form.get("titulo", "").strip()
        descuento = request.form.get("descuento", "").strip()
        impuesto = request.form.get("impuesto_porcentaje", "").strip()
        fecha_vencimiento = request.form.get("fecha_vencimiento", "").strip() or None
        notas = request.form.get("notas", "").strip() or None

        if cliente_id == "" or titulo == "":
            return redirigir_o_responder_error("Cliente y título son obligatorios.", "editar_cotizacion_ruta", id=id)

        if obtener_cliente_por_id(cliente_id, session["agencia_id"]) is None:
            return redirigir_o_responder_error("Cliente inválido.", "editar_cotizacion_ruta", id=id)

        try:
            descuento_val = float(descuento) if descuento else 0
            impuesto_val = float(impuesto) if impuesto else 0
        except ValueError:
            return redirigir_o_responder_error("Descuento e impuesto deben ser números válidos.", "editar_cotizacion_ruta", id=id)

        try:
            items = _parsear_items(request.form)
        except ValueError as error:
            return redirigir_o_responder_error(str(error), "editar_cotizacion_ruta", id=id)

        if not items:
            return redirigir_o_responder_error("Agregá al menos un ítem a la cotización.", "editar_cotizacion_ruta", id=id)

        editar_cotizacion_por_id(id, cliente_id, titulo, descuento_val, impuesto_val, fecha_vencimiento, notas, session["agencia_id"])
        reemplazar_items(id, items)
        auditar("editar", "cotizacion", id, f"Editó la cotización '{titulo}'.")

        if es_peticion_ajax():
            return jsonify({"exito": True})

        flash("Cotización actualizada correctamente.", "exito")
        return redirect(url_for("ver_cotizacion", id=id))
    else:
        return redirect(url_for("ver_cotizaciones", editar=id))


@app.route("/cotizaciones/<int:id>/eliminar", methods=["POST"])
@admin_requerido
def eliminar_cotizacion_ruta(id):
    cotizacion = obtener_cotizacion_por_id(id, session["agencia_id"])
    eliminar_cotizacion_por_id(id, session["agencia_id"])
    auditar("eliminar", "cotizacion", id, f"Eliminó la cotización '{cotizacion[2] if cotizacion else id}'.")
    flash("Cotización eliminada.", "exito")
    return redirect(url_for("ver_cotizaciones"))


@app.route("/cotizaciones/<int:id>/marcar-enviada", methods=["POST"])
@login_requerido
def marcar_cotizacion_enviada(id):
    cotizacion = obtener_cotizacion_por_id(id, session["agencia_id"])
    if cotizacion is None:
        return redirigir_o_responder_error("Cotización no encontrada.", "ver_cotizaciones")

    cambiar_estado_cotizacion(id, "Enviada", session["agencia_id"])
    auditar("editar", "cotizacion", id, f"Marcó como enviada la cotización '{cotizacion[2]}'.")

    flash("Cotización marcada como enviada. Ya podés compartir el enlace con el cliente.", "exito")
    return redirect(url_for("ver_cotizacion", id=id))


@app.route("/cotizaciones/<int:id>/convertir", methods=["POST"])
@login_requerido
def convertir_cotizacion(id):
    cotizacion = obtener_cotizacion_por_id(id, session["agencia_id"])
    if cotizacion is None:
        return redirigir_o_responder_error("Cotización no encontrada.", "ver_cotizaciones")

    if cotizacion[3] != "Aceptada":
        return redirigir_o_responder_error("Solo se puede convertir una cotización aceptada.", "ver_cotizacion", id=id)

    if cotizacion[9]:
        return redirigir_o_responder_error("Esta cotización ya fue convertida en un proyecto.", "ver_cotizacion", id=id)

    items = obtener_items(id)
    _, total = calcular_totales(items, cotizacion[4], cotizacion[5])
    proyecto_id = agregar_proyecto(cotizacion[2], cotizacion[1], "Pendiente", None, session["agencia_id"], total)
    marcar_convertida(id, proyecto_id, session["agencia_id"])
    auditar("crear", "proyecto", proyecto_id, f"Convirtió la cotización '{cotizacion[2]}' en un proyecto.")

    flash("Cotización convertida en proyecto.", "exito")
    return redirect(url_for("ver_proyecto", id=proyecto_id))


@app.route("/cotizaciones/<int:id>/pdf")
@login_requerido
def cotizacion_pdf(id):
    cotizacion = obtener_cotizacion_por_id(id, session["agencia_id"])
    if cotizacion is None:
        flash("Cotización no encontrada.", "error")
        return redirect(url_for("ver_cotizaciones"))

    cliente = obtener_cliente_por_id(cotizacion[1], session["agencia_id"])
    nombre_cliente = cliente[1] if cliente else "Cliente no encontrado"
    agencia = obtener_agencia_por_id(session["agencia_id"])
    items = obtener_items(id)
    subtotal, total = calcular_totales(items, cotizacion[4], cotizacion[5])

    buffer = generar_cotizacion_pdf(cotizacion, nombre_cliente, agencia[1] if agencia else None, items, subtotal, total)
    return send_file(buffer, as_attachment=True, download_name=f"cotizacion_{id}.pdf", mimetype="application/pdf")


@app.route("/cotizacion/<token>")
def ver_cotizacion_publica(token):
    cotizacion = obtener_cotizacion_por_token(token)
    if cotizacion is None or cotizacion[3] == "Borrador":
        return render_template("404.html"), 404

    cliente = obtener_cliente_por_id(cotizacion[1], cotizacion[10])
    agencia = obtener_agencia_por_id(cotizacion[10])
    items = obtener_items(cotizacion[0])
    subtotal, total = calcular_totales(items, cotizacion[4], cotizacion[5])
    return render_template(
        "cotizacion_publica.html", cotizacion=cotizacion, cliente=cliente, agencia=agencia,
        items=items, subtotal=subtotal, total=total, vencida=cotizacion_esta_vencida(cotizacion)
    )


@app.route("/cotizacion/<token>/responder", methods=["POST"])
def responder_cotizacion_publica(token):
    cotizacion = obtener_cotizacion_por_token(token)
    if cotizacion is None or cotizacion[3] != "Enviada":
        flash("Esta cotización ya no está disponible para responder.", "error")
        return redirect(url_for("ver_cotizacion_publica", token=token))

    respuesta = request.form.get("respuesta")
    if respuesta not in ("Aceptada", "Rechazada"):
        flash("Respuesta inválida.", "error")
        return redirect(url_for("ver_cotizacion_publica", token=token))

    cambiar_estado_cotizacion(cotizacion[0], respuesta)
    return redirect(url_for("ver_cotizacion_publica", token=token))


@app.route("/facturas")
@login_requerido
def ver_facturas():
    pagina = normalizar_pagina(request.args.get("pagina"))
    facturas, total = obtener_facturas_paginado(session["agencia_id"], pagina, POR_PAGINA)
    lista = []
    for factura in facturas:
        items = obtener_items_factura(factura[0])
        _, total_factura = calcular_totales_factura(items, factura[4], factura[5])
        saldo = total_factura - cobrado_factura(factura[0], session["agencia_id"])
        items_json = [[item[2], item[3], item[4]] for item in items]
        lista.append((factura, total_factura, saldo, factura_esta_vencida(factura), items_json))
    proyectos = obtener_proyectos(session["agencia_id"])
    return render_template(
        "facturas.html", facturas=lista, proyectos=proyectos,
        pagina=pagina, total_paginas=total_paginas(total, POR_PAGINA), total_registros=total
    )


@app.route("/facturas/nueva", methods=["GET", "POST"])
@login_requerido
def nueva_factura():
    if request.method == "POST":
        proyecto_id = request.form.get("proyecto_id", "")
        descuento = request.form.get("descuento", "").strip()
        impuesto = request.form.get("impuesto_porcentaje", "").strip()
        fecha_emision = request.form.get("fecha_emision", "").strip() or None
        fecha_vencimiento = request.form.get("fecha_vencimiento", "").strip() or None
        notas = request.form.get("notas", "").strip() or None

        if proyecto_id == "":
            return redirigir_o_responder_error("El proyecto es obligatorio.", "nueva_factura")

        if obtener_proyecto_por_id(proyecto_id, session["agencia_id"]) is None:
            return redirigir_o_responder_error("Proyecto inválido.", "nueva_factura")

        try:
            descuento_val = float(descuento) if descuento else 0
            impuesto_val = float(impuesto) if impuesto else 0
        except ValueError:
            return redirigir_o_responder_error("Descuento e impuesto deben ser números válidos.", "nueva_factura")

        try:
            items = _parsear_items(request.form)
        except ValueError as error:
            return redirigir_o_responder_error(str(error), "nueva_factura")

        if not items:
            return redirigir_o_responder_error("Agregá al menos un ítem a la factura.", "nueva_factura")

        factura_id = agregar_factura(proyecto_id, descuento_val, impuesto_val, fecha_emision, fecha_vencimiento, notas, session["agencia_id"])
        reemplazar_items_factura(factura_id, items)
        auditar("crear", "factura", factura_id, f"Creó la factura #{factura_id}.")

        if es_peticion_ajax():
            return jsonify({"exito": True, "redirigir_a": url_for("ver_factura", id=factura_id)})

        flash("Factura creada correctamente.", "exito")
        return redirect(url_for("ver_factura", id=factura_id))
    else:
        return redirect(url_for("ver_facturas", nueva=1))


@app.route("/facturas/<int:id>")
@login_requerido
def ver_factura(id):
    factura = obtener_factura_por_id(id, session["agencia_id"])
    if factura is None:
        flash("Factura no encontrada.", "error")
        return redirect(url_for("ver_facturas"))

    proyecto = obtener_proyecto_por_id(factura[1], session["agencia_id"])
    nombre_proyecto = proyecto[1] if proyecto else "Proyecto no encontrado"
    cliente = obtener_cliente_por_id(proyecto[2], session["agencia_id"]) if proyecto else None
    items = obtener_items_factura(id)
    subtotal, total = calcular_totales_factura(items, factura[4], factura[5])
    saldo = total - cobrado_factura(id, session["agencia_id"])
    pagos_factura = pagos_de_factura(id, session["agencia_id"])
    enlace_publico = url_for("ver_factura_publica", token=factura[9], _external=True)
    proyectos = obtener_proyectos(session["agencia_id"])
    items_json = [[item[2], item[3], item[4]] for item in items]
    return render_template(
        "factura_detalle.html", factura=factura, numero=formatear_numero_factura(factura[2]),
        proyecto=proyecto, nombre_proyecto=nombre_proyecto, cliente=cliente, items=items, items_json=items_json,
        subtotal=subtotal, total=total, saldo=saldo, pagos_factura=pagos_factura,
        vencida=factura_esta_vencida(factura), enlace_publico=enlace_publico, proyectos=proyectos
    )


@app.route("/facturas/<int:id>/editar", methods=["GET", "POST"])
@login_requerido
def editar_factura_ruta(id):
    factura = obtener_factura_por_id(id, session["agencia_id"])
    if factura is None:
        flash("Factura no encontrada.", "error")
        return redirect(url_for("ver_facturas"))

    if request.method == "POST":
        proyecto_id = request.form.get("proyecto_id", "")
        descuento = request.form.get("descuento", "").strip()
        impuesto = request.form.get("impuesto_porcentaje", "").strip()
        fecha_emision = request.form.get("fecha_emision", "").strip() or None
        fecha_vencimiento = request.form.get("fecha_vencimiento", "").strip() or None
        notas = request.form.get("notas", "").strip() or None

        if proyecto_id == "":
            return redirigir_o_responder_error("El proyecto es obligatorio.", "editar_factura_ruta", id=id)

        if obtener_proyecto_por_id(proyecto_id, session["agencia_id"]) is None:
            return redirigir_o_responder_error("Proyecto inválido.", "editar_factura_ruta", id=id)

        try:
            descuento_val = float(descuento) if descuento else 0
            impuesto_val = float(impuesto) if impuesto else 0
        except ValueError:
            return redirigir_o_responder_error("Descuento e impuesto deben ser números válidos.", "editar_factura_ruta", id=id)

        try:
            items = _parsear_items(request.form)
        except ValueError as error:
            return redirigir_o_responder_error(str(error), "editar_factura_ruta", id=id)

        if not items:
            return redirigir_o_responder_error("Agregá al menos un ítem a la factura.", "editar_factura_ruta", id=id)

        editar_factura_por_id(id, proyecto_id, descuento_val, impuesto_val, fecha_emision, fecha_vencimiento, notas, session["agencia_id"])
        reemplazar_items_factura(id, items)
        sincronizar_estado_factura(id, session["agencia_id"])
        auditar("editar", "factura", id, f"Editó la factura #{id}.")

        if es_peticion_ajax():
            return jsonify({"exito": True})

        flash("Factura actualizada correctamente.", "exito")
        return redirect(url_for("ver_factura", id=id))
    else:
        return redirect(url_for("ver_facturas", editar=id))


@app.route("/facturas/<int:id>/eliminar", methods=["POST"])
@admin_requerido
def eliminar_factura_ruta(id):
    factura = obtener_factura_por_id(id, session["agencia_id"])
    eliminar_factura_por_id(id, session["agencia_id"])
    auditar("eliminar", "factura", id, f"Eliminó la factura #{id if factura else id}.")
    flash("Factura eliminada.", "exito")
    return redirect(url_for("ver_facturas"))


@app.route("/facturas/<int:id>/marcar-emitida", methods=["POST"])
@login_requerido
def marcar_factura_emitida(id):
    factura = obtener_factura_por_id(id, session["agencia_id"])
    if factura is None:
        return redirigir_o_responder_error("Factura no encontrada.", "ver_facturas")

    cambiar_estado_factura(id, "Emitida", session["agencia_id"])
    sincronizar_estado_factura(id, session["agencia_id"])
    auditar("editar", "factura", id, f"Marcó como emitida la factura #{id}.")

    flash("Factura marcada como emitida. Ya podés compartir el enlace con el cliente.", "exito")
    return redirect(url_for("ver_factura", id=id))


@app.route("/facturas/<int:id>/anular", methods=["POST"])
@login_requerido
def anular_factura_ruta(id):
    factura = obtener_factura_por_id(id, session["agencia_id"])
    if factura is None:
        return redirigir_o_responder_error("Factura no encontrada.", "ver_facturas")

    if factura[3] == "Pagada":
        return redirigir_o_responder_error("No se puede anular una factura ya pagada.", "ver_factura", id=id)

    cambiar_estado_factura(id, "Anulada", session["agencia_id"])
    auditar("editar", "factura", id, f"Anuló la factura #{id}.")

    flash("Factura anulada.", "exito")
    return redirect(url_for("ver_factura", id=id))


@app.route("/facturas/<int:id>/pdf")
@login_requerido
def factura_pdf(id):
    factura = obtener_factura_por_id(id, session["agencia_id"])
    if factura is None:
        flash("Factura no encontrada.", "error")
        return redirect(url_for("ver_facturas"))

    proyecto = obtener_proyecto_por_id(factura[1], session["agencia_id"])
    nombre_proyecto = proyecto[1] if proyecto else "Proyecto no encontrado"
    cliente = obtener_cliente_por_id(proyecto[2], session["agencia_id"]) if proyecto else None
    nombre_cliente = cliente[1] if cliente else "Cliente no encontrado"
    agencia = obtener_agencia_por_id(session["agencia_id"])
    items = obtener_items_factura(id)
    subtotal, total = calcular_totales_factura(items, factura[4], factura[5])
    saldo = total - cobrado_factura(id, session["agencia_id"])

    buffer = generar_factura_pdf(
        factura, formatear_numero_factura(factura[2]), nombre_proyecto, nombre_cliente,
        agencia[1] if agencia else None, items, subtotal, total, saldo
    )
    return send_file(buffer, as_attachment=True, download_name=f"factura_{formatear_numero_factura(factura[2])}.pdf", mimetype="application/pdf")


@app.route("/factura/<token>")
def ver_factura_publica(token):
    factura = obtener_factura_por_token(token)
    if factura is None or factura[3] == "Borrador":
        return render_template("404.html"), 404

    proyecto = obtener_proyecto_por_id(factura[1], factura[10])
    cliente = obtener_cliente_por_id(proyecto[2], factura[10]) if proyecto else None
    agencia = obtener_agencia_por_id(factura[10])
    items = obtener_items_factura(factura[0])
    subtotal, total = calcular_totales_factura(items, factura[4], factura[5])
    saldo = total - cobrado_factura(factura[0], factura[10])
    return render_template(
        "factura_publica.html", factura=factura, numero=formatear_numero_factura(factura[2]),
        proyecto=proyecto, cliente=cliente, agencia=agencia,
        items=items, subtotal=subtotal, total=total, saldo=saldo, vencida=factura_esta_vencida(factura)
    )


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
        por_vencer = proyecto_esta_por_vencer(proyecto[3], proyecto[4], session["agencia_id"])
        lista.append((proyecto, nombre_cliente, por_vencer))
    clientes = obtener_clientes(session["agencia_id"])
    definiciones_campo = obtener_definiciones(session["agencia_id"], "proyectos")
    etapas_proyecto = obtener_etapas(session["agencia_id"])
    return render_template(
        "proyectos.html", proyectos=lista, clientes=clientes, ver_archivados=ver_archivados,
        pagina=pagina, total_paginas=total_paginas(total, POR_PAGINA), total_registros=total,
        definiciones_campo=definiciones_campo, etapas_proyecto=etapas_proyecto,
        clases_estado=mapa_clases_badge(session["agencia_id"]),
        nombres_etapas_finales=nombres_etapas_finales(session["agencia_id"])
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

        if obtener_cliente_por_id(cliente_id, session["agencia_id"]) is None:
            return redirigir_o_responder_error("Cliente inválido.", "nuevo_proyecto")

        if estado not in nombres_etapas(session["agencia_id"]):
            return redirigir_o_responder_error("Etapa inválida.", "nuevo_proyecto")

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

        campos_validados, error_campos = validar_valores_formulario(session["agencia_id"], "proyectos", request.form)
        if error_campos:
            return redirigir_o_responder_error(error_campos, "nuevo_proyecto")
        definiciones = obtener_definiciones(session["agencia_id"], "proyectos")
        campos_personalizados = fusionar_campos_personalizados({}, campos_validados, definiciones)

        proyecto_id = agregar_proyecto(titulo, cliente_id, estado, fecha_entrega, session["agencia_id"], presupuesto, campos_personalizados)
        auditar("crear", "proyecto", proyecto_id, f"Creó el proyecto '{titulo}'.")

        if proyecto_esta_por_vencer(estado, fecha_entrega, session["agencia_id"]):
            agencia = obtener_agencia_por_id(session["agencia_id"])
            if agencia and agencia[2]:
                try:
                    cliente = obtener_cliente_por_id(cliente_id, session["agencia_id"])
                    nombre_cliente = cliente[1] if cliente else "Cliente no encontrado"
                    avisar_proyecto_individual(titulo, fecha_entrega, nombre_cliente, agencia[2])
                except Exception as error:
                    app.logger.warning(f"No se pudo enviar el aviso de Telegram: {error}")

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
        tareas = obtener_tareas_proyecto(id, session["agencia_id"])
        tareas_completadas, tareas_total = progreso_proyecto(id, session["agencia_id"])
        usuarios = usuarios_de_agencia(session["agencia_id"])
        usuarios_por_id = {usuario[0]: usuario[1] for usuario in usuarios}
        gastos = obtener_gastos_proyecto(id, session["agencia_id"])
        total_gastos = total_gastos_proyecto(id, session["agencia_id"])
        margen = cobrado_proyecto - total_gastos
        definiciones_campo = obtener_definiciones(session["agencia_id"], "proyectos")
        etapas_proyecto = obtener_etapas(session["agencia_id"])
        proyectos = obtener_proyectos(session["agencia_id"])
        facturas = facturas_de_proyecto(id, session["agencia_id"])
        return render_template(
            "proyecto_detalle.html", proyecto=proyecto, nombre_cliente=nombre_cliente, pagos=pagos,
            sugerencias=None, clientes=clientes, cobrado_proyecto=cobrado_proyecto,
            saldo_pendiente=saldo_pendiente, tareas=tareas, tareas_completadas=tareas_completadas,
            tareas_total=tareas_total, usuarios=usuarios, usuarios_por_id=usuarios_por_id,
            prioridades=PRIORIDADES, gastos=gastos, total_gastos=total_gastos, margen=margen,
            categorias_gasto=CATEGORIAS_GASTO, definiciones_campo=definiciones_campo,
            etapas_proyecto=etapas_proyecto, clases_estado=mapa_clases_badge(session["agencia_id"]),
            nombres_etapas_finales=nombres_etapas_finales(session["agencia_id"]),
            proyectos=proyectos, facturas=facturas, **conversion
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
        app.logger.exception("Falló la generación de sugerencias de proyecto con IA.")
        flash("No se pudieron generar las sugerencias en este momento. Probá de nuevo en un rato.", "error")
        sugerencias = None

    clientes = obtener_clientes(session["agencia_id"])
    cobrado_proyecto = sum(pago[2] for pago in pagos if pago[5] == "cobrado")
    saldo_pendiente = proyecto[6] - cobrado_proyecto if proyecto[6] is not None else None
    tareas = obtener_tareas_proyecto(id, session["agencia_id"])
    tareas_completadas, tareas_total = progreso_proyecto(id, session["agencia_id"])
    usuarios = usuarios_de_agencia(session["agencia_id"])
    usuarios_por_id = {usuario[0]: usuario[1] for usuario in usuarios}
    gastos = obtener_gastos_proyecto(id, session["agencia_id"])
    total_gastos = total_gastos_proyecto(id, session["agencia_id"])
    margen = cobrado_proyecto - total_gastos
    definiciones_campo = obtener_definiciones(session["agencia_id"], "proyectos")
    etapas_proyecto = obtener_etapas(session["agencia_id"])
    proyectos = obtener_proyectos(session["agencia_id"])
    facturas = facturas_de_proyecto(id, session["agencia_id"])
    return render_template(
        "proyecto_detalle.html", proyecto=proyecto, nombre_cliente=nombre_cliente, pagos=pagos,
        sugerencias=sugerencias, clientes=clientes, cobrado_proyecto=cobrado_proyecto,
        saldo_pendiente=saldo_pendiente, tareas=tareas, tareas_completadas=tareas_completadas,
        tareas_total=tareas_total, usuarios=usuarios, usuarios_por_id=usuarios_por_id,
        prioridades=PRIORIDADES, gastos=gastos, total_gastos=total_gastos, margen=margen,
        categorias_gasto=CATEGORIAS_GASTO, definiciones_campo=definiciones_campo,
        etapas_proyecto=etapas_proyecto, clases_estado=mapa_clases_badge(session["agencia_id"]),
        nombres_etapas_finales=nombres_etapas_finales(session["agencia_id"]),
        proyectos=proyectos, facturas=facturas, **conversion
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

        if obtener_cliente_por_id(cliente_id, session["agencia_id"]) is None:
            return redirigir_o_responder_error("Cliente inválido.", "editar_proyecto_ruta", id=id)

        if estado not in nombres_etapas(session["agencia_id"]):
            return redirigir_o_responder_error("Etapa inválida.", "editar_proyecto_ruta", id=id)

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

        campos_validados, error_campos = validar_valores_formulario(session["agencia_id"], "proyectos", request.form)
        if error_campos:
            return redirigir_o_responder_error(error_campos, "editar_proyecto_ruta", id=id)
        definiciones = obtener_definiciones(session["agencia_id"], "proyectos")
        campos_personalizados = fusionar_campos_personalizados(proyecto[8] if len(proyecto) > 8 else {}, campos_validados, definiciones)

        editar_proyecto_por_id(id, titulo, cliente_id, estado, fecha_entrega, session["agencia_id"], presupuesto, campos_personalizados)
        auditar("editar", "proyecto", id, f"Editó el proyecto '{titulo}'.")

        if fecha_entrega != fecha_entrega_anterior and proyecto_esta_por_vencer(estado, fecha_entrega, session["agencia_id"]):
            agencia = obtener_agencia_por_id(session["agencia_id"])
            if agencia and agencia[2]:
                try:
                    cliente = obtener_cliente_por_id(cliente_id, session["agencia_id"])
                    nombre_cliente = cliente[1] if cliente else "Cliente no encontrado"
                    avisar_proyecto_individual(titulo, fecha_entrega, nombre_cliente, agencia[2])
                except Exception as error:
                    app.logger.warning(f"No se pudo enviar el aviso de Telegram: {error}")

        principal = etapa_final_principal(session["agencia_id"])
        if principal and estado == principal[2] and estado_anterior != principal[2]:
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
                    app.logger.warning(f"No se pudo enviar el correo: {error}")

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

    if not etapa_es_final(session["agencia_id"], proyecto[3]):
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
                app.logger.warning(f"No se pudo enviar el correo: {error}")

    if es_peticion_ajax():
        return jsonify({"exito": True})

    flash("Proyecto marcado como completado.", "exito")
    return redirect(request.referrer or url_for("ver_proyectos"))


@app.route("/proyectos/<int:id>/eliminar", methods=["POST"])
@admin_requerido
def eliminar_proyecto_ruta(id):
    proyecto = obtener_proyecto_por_id(id, session["agencia_id"])
    if proyecto is None:
        flash("Proyecto no encontrado.", "error")
        return redirect(url_for("ver_proyectos"))

    tiene_pagos = len(pagos_de_proyecto(id, session["agencia_id"])) > 0
    tiene_tareas = len(obtener_tareas_proyecto(id, session["agencia_id"])) > 0
    tiene_gastos = len(obtener_gastos_proyecto(id, session["agencia_id"])) > 0
    tiene_cotizaciones = contar_cotizaciones_proyecto(id, session["agencia_id"]) > 0
    if tiene_pagos or tiene_tareas or tiene_gastos or tiene_cotizaciones:
        flash(
            f"No se puede eliminar '{proyecto[1]}' porque tiene pagos, tareas, gastos o cotizaciones asociadas. "
            "Archivalo en su lugar si querés sacarlo de la vista principal sin perder su historial.",
            "error"
        )
        return redirect(url_for("ver_proyectos"))

    eliminar_proyecto_por_id(id, session["agencia_id"])
    auditar("eliminar", "proyecto", id, f"Eliminó el proyecto '{proyecto[1]}'.")
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


@app.route("/tareas")
@login_requerido
def ver_tareas():
    pagina = normalizar_pagina(request.args.get("pagina"))
    ver_todas = request.args.get("todas") == "1"
    responsable_id = None if ver_todas else session["usuario_id"]
    tareas, total = obtener_tareas_paginado(session["agencia_id"], pagina, POR_PAGINA, responsable_id=responsable_id)
    proyectos = obtener_proyectos(session["agencia_id"])
    usuarios = usuarios_de_agencia(session["agencia_id"])
    usuarios_por_id = {usuario[0]: usuario[1] for usuario in usuarios}
    hoy = date.today().isoformat()
    return render_template(
        "tareas.html", tareas=tareas, proyectos=proyectos, usuarios=usuarios, usuarios_por_id=usuarios_por_id,
        ver_todas=ver_todas, prioridades=PRIORIDADES, estados_tarea=ESTADOS_TAREA, hoy=hoy,
        pagina=pagina, total_paginas=total_paginas(total, POR_PAGINA), total_registros=total
    )


@app.route("/tareas/nueva", methods=["GET", "POST"])
@login_requerido
def nueva_tarea():
    if request.method == "POST":
        proyecto_id = request.form["proyecto_id"]
        titulo = request.form["titulo"]
        descripcion = request.form.get("descripcion", "").strip() or None
        responsable_id = request.form.get("responsable_id") or None
        prioridad = request.form.get("prioridad", "Media")
        estado = request.form.get("estado", "Pendiente")
        fecha_limite = request.form.get("fecha_limite", "").strip() or None

        if proyecto_id == "" or titulo == "":
            return redirigir_o_responder_error("Proyecto y título son obligatorios.", "nueva_tarea")

        if obtener_proyecto_por_id(proyecto_id, session["agencia_id"]) is None:
            return redirigir_o_responder_error("Proyecto inválido.", "nueva_tarea")

        if responsable_id and obtener_usuario_por_id(responsable_id, session["agencia_id"]) is None:
            return redirigir_o_responder_error("Responsable inválido.", "nueva_tarea")

        if prioridad not in PRIORIDADES:
            prioridad = "Media"
        if estado not in ESTADOS_TAREA:
            estado = "Pendiente"

        if fecha_limite and fecha_limite < date.today().isoformat():
            return redirigir_o_responder_error("La fecha límite no puede ser anterior a hoy.", "nueva_tarea")

        agregar_tarea(proyecto_id, titulo, descripcion, responsable_id, prioridad, fecha_limite, session["agencia_id"], estado)
        auditar("crear", "tarea", None, f"Creó la tarea '{titulo}'.")

        if es_peticion_ajax():
            return jsonify({"exito": True})

        flash("Tarea agregada correctamente.", "exito")
        return redirect(url_for("ver_tareas"))
    else:
        return redirect(url_for("ver_tareas", nueva=1))


@app.route("/tareas/<int:id>")
@login_requerido
def ver_tarea(id):
    tarea = obtener_tarea_por_id(id, session["agencia_id"])
    if tarea is None:
        flash("Tarea no encontrada.", "error")
        return redirect(url_for("ver_tareas"))

    proyecto = obtener_proyecto_por_id(tarea[1], session["agencia_id"])
    titulo_proyecto = proyecto[1] if proyecto else "Proyecto no encontrado"
    responsable = obtener_usuario_por_id(tarea[4], session["agencia_id"]) if tarea[4] else None
    nombre_responsable = responsable[1] if responsable else None
    subtareas = obtener_subtareas(id)
    proyectos = obtener_proyectos(session["agencia_id"])
    usuarios = usuarios_de_agencia(session["agencia_id"])
    return render_template(
        "tarea_detalle.html", tarea=tarea, proyecto=proyecto, titulo_proyecto=titulo_proyecto,
        nombre_responsable=nombre_responsable, subtareas=subtareas, proyectos=proyectos,
        usuarios=usuarios, prioridades=PRIORIDADES, estados_tarea=ESTADOS_TAREA
    )


@app.route("/tareas/<int:id>/editar", methods=["GET", "POST"])
@login_requerido
def editar_tarea_ruta(id):
    tarea = obtener_tarea_por_id(id, session["agencia_id"])
    if tarea is None:
        flash("Tarea no encontrada.", "error")
        return redirect(url_for("ver_tareas"))

    if request.method == "POST":
        fecha_limite_anterior = tarea[7]

        proyecto_id = request.form["proyecto_id"]
        titulo = request.form["titulo"]
        descripcion = request.form.get("descripcion", "").strip() or None
        responsable_id = request.form.get("responsable_id") or None
        prioridad = request.form.get("prioridad", "Media")
        estado = request.form.get("estado", "Pendiente")
        fecha_limite = request.form.get("fecha_limite", "").strip() or None

        if proyecto_id == "" or titulo == "":
            return redirigir_o_responder_error("Proyecto y título son obligatorios.", "editar_tarea_ruta", id=id)

        if obtener_proyecto_por_id(proyecto_id, session["agencia_id"]) is None:
            return redirigir_o_responder_error("Proyecto inválido.", "editar_tarea_ruta", id=id)

        if responsable_id and obtener_usuario_por_id(responsable_id, session["agencia_id"]) is None:
            return redirigir_o_responder_error("Responsable inválido.", "editar_tarea_ruta", id=id)

        if prioridad not in PRIORIDADES:
            prioridad = "Media"
        if estado not in ESTADOS_TAREA:
            estado = "Pendiente"

        if fecha_limite and fecha_limite != fecha_limite_anterior and fecha_limite < date.today().isoformat():
            return redirigir_o_responder_error("La fecha límite no puede ser anterior a hoy.", "editar_tarea_ruta", id=id)

        editar_tarea_por_id(id, proyecto_id, titulo, descripcion, responsable_id, prioridad, estado, fecha_limite, session["agencia_id"])
        auditar("editar", "tarea", id, f"Editó la tarea '{titulo}'.")

        if es_peticion_ajax():
            return jsonify({"exito": True})

        flash("Tarea actualizada correctamente.", "exito")
        return redirect(url_for("ver_tareas"))
    else:
        return redirect(url_for("ver_tareas", editar=id))


@app.route("/tareas/<int:id>/eliminar", methods=["POST"])
@admin_requerido
def eliminar_tarea_ruta(id):
    tarea = obtener_tarea_por_id(id, session["agencia_id"])
    eliminar_tarea_por_id(id, session["agencia_id"])
    auditar("eliminar", "tarea", id, f"Eliminó la tarea '{tarea[2] if tarea else id}'.")
    flash("Tarea eliminada.", "exito")
    return redirect(url_for("ver_tareas"))


@app.route("/tareas/<int:id>/marcar-completado", methods=["POST"])
@login_requerido
def marcar_tarea_completada_ruta(id):
    tarea = obtener_tarea_por_id(id, session["agencia_id"])
    if tarea is None:
        return redirigir_o_responder_error("Tarea no encontrada.", "ver_tareas")

    if tarea[6] != "Completado":
        marcar_estado_tarea(id, session["agencia_id"], "Completado")
        auditar("editar", "tarea", id, f"Marcó como completada la tarea '{tarea[2]}'.")

    if es_peticion_ajax():
        return jsonify({"exito": True})

    flash("Tarea marcada como completada.", "exito")
    return redirect(request.referrer or url_for("ver_tareas"))


@app.route("/tareas/<int:id>/subtareas/nueva", methods=["POST"])
@login_requerido
def nueva_subtarea_ruta(id):
    tarea = obtener_tarea_por_id(id, session["agencia_id"])
    if tarea is None:
        return jsonify({"exito": False, "error": "Tarea no encontrada."}), 404

    texto = request.form.get("texto", "").strip()
    if texto == "":
        return jsonify({"exito": False, "error": "El ítem no puede estar vacío."}), 400

    agregar_subtarea(id, texto)
    return jsonify({"exito": True})


@app.route("/tareas/<int:id>/subtareas/<int:sub_id>/alternar", methods=["POST"])
@login_requerido
def alternar_subtarea_ruta(id, sub_id):
    tarea = obtener_tarea_por_id(id, session["agencia_id"])
    if tarea is None:
        return jsonify({"exito": False, "error": "Tarea no encontrada."}), 404

    subtarea = obtener_subtarea_por_id(sub_id, id)
    if subtarea is None:
        return jsonify({"exito": False, "error": "Ítem no encontrado."}), 404

    alternar_subtarea(sub_id, id)
    return jsonify({"exito": True})


@app.route("/tareas/<int:id>/subtareas/<int:sub_id>/eliminar", methods=["POST"])
@login_requerido
def eliminar_subtarea_ruta(id, sub_id):
    tarea = obtener_tarea_por_id(id, session["agencia_id"])
    if tarea is None:
        return jsonify({"exito": False, "error": "Tarea no encontrada."}), 404

    subtarea = obtener_subtarea_por_id(sub_id, id)
    if subtarea is None:
        return jsonify({"exito": False, "error": "Ítem no encontrado."}), 404

    eliminar_subtarea(sub_id, id)
    return jsonify({"exito": True})


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
    facturas = facturas_pendientes_de_pago(session["agencia_id"])
    conversion = datos_conversion(session["agencia_id"])
    return render_template(
        "pagos.html", pagos=lista, proyectos=proyectos, facturas=facturas, **conversion,
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

        factura_id = request.form.get("factura_id") or None

        if proyecto_id == "" or monto == "":
            return redirigir_o_responder_error("Proyecto y monto son obligatorios.", "nuevo_pago")

        if obtener_proyecto_por_id(proyecto_id, session["agencia_id"]) is None:
            return redirigir_o_responder_error("Proyecto inválido.", "nuevo_pago")

        if factura_id:
            factura = obtener_factura_por_id(factura_id, session["agencia_id"])
            if factura is None or str(factura[1]) != str(proyecto_id):
                return redirigir_o_responder_error("Factura inválida.", "nuevo_pago")

        try:
            monto = float(monto)
        except ValueError:
            return redirigir_o_responder_error("El monto debe ser un número válido.", "nuevo_pago")

        if monto <= 0:
            return redirigir_o_responder_error("El monto tiene que ser mayor a 0.", "nuevo_pago")

        agregar_pago(proyecto_id, monto, fecha, session["agencia_id"], estado, factura_id)
        auditar("crear", "pago", None, f"Registró un pago de ${monto:,.2f} ({estado}).")

        if factura_id:
            sincronizar_estado_factura(factura_id, session["agencia_id"])

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
        cliente = None
        if proyecto is None:
            titulo_proyecto = "Proyecto no encontrado"
        else:
            titulo_proyecto = proyecto[1]
            cliente = obtener_cliente_por_id(proyecto[2], session["agencia_id"])
        conversion = datos_conversion(session["agencia_id"])
        proyectos = obtener_proyectos(session["agencia_id"])
        facturas = facturas_pendientes_de_pago(session["agencia_id"])
        return render_template("pago_detalle.html", pago=pago, proyecto=proyecto, cliente=cliente, titulo_proyecto=titulo_proyecto, proyectos=proyectos, facturas=facturas, **conversion)
    

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

        factura_id = request.form.get("factura_id") or None
        factura_id_anterior = pago[6] if len(pago) > 6 else None

        if proyecto_id == "" or monto == "":
            return redirigir_o_responder_error("Proyecto y monto son obligatorios.", "editar_pago_ruta", id=id)

        if obtener_proyecto_por_id(proyecto_id, session["agencia_id"]) is None:
            return redirigir_o_responder_error("Proyecto inválido.", "editar_pago_ruta", id=id)

        if factura_id:
            factura = obtener_factura_por_id(factura_id, session["agencia_id"])
            if factura is None or str(factura[1]) != str(proyecto_id):
                return redirigir_o_responder_error("Factura inválida.", "editar_pago_ruta", id=id)

        try:
            monto = float(monto)
        except ValueError:
            return redirigir_o_responder_error("El monto debe ser un número válido.", "editar_pago_ruta", id=id)

        if monto <= 0:
            return redirigir_o_responder_error("El monto tiene que ser mayor a 0.", "editar_pago_ruta", id=id)

        editar_pago_por_id(id, proyecto_id, monto, fecha, session["agencia_id"], estado, factura_id)
        auditar("editar", "pago", id, f"Editó el pago #{id} (${monto:,.2f}, {estado}).")

        for id_factura_afectada in {factura_id, factura_id_anterior}:
            if id_factura_afectada:
                sincronizar_estado_factura(id_factura_afectada, session["agencia_id"])

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
    if pago and len(pago) > 6 and pago[6]:
        sincronizar_estado_factura(pago[6], session["agencia_id"])
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

    if len(pago) > 6 and pago[6]:
        sincronizar_estado_factura(pago[6], session["agencia_id"])

    if es_peticion_ajax():
        return jsonify({"exito": True})

    flash("Pago marcado como cobrado.", "exito")
    return redirect(request.referrer or url_for("ver_pagos"))


@app.route("/gastos")
@login_requerido
def ver_gastos():
    pagina = normalizar_pagina(request.args.get("pagina"))
    gastos, total = obtener_gastos_paginado(session["agencia_id"], pagina, POR_PAGINA)
    proyectos = obtener_proyectos(session["agencia_id"])
    return render_template(
        "gastos.html", gastos=gastos, proyectos=proyectos, categorias_gasto=CATEGORIAS_GASTO,
        pagina=pagina, total_paginas=total_paginas(total, POR_PAGINA), total_registros=total
    )


@app.route("/gastos/nuevo", methods=["GET", "POST"])
@login_requerido
def nuevo_gasto():
    if request.method == "POST":
        proyecto_id = request.form["proyecto_id"]
        descripcion = request.form.get("descripcion", "").strip()
        monto = request.form.get("monto", "")
        categoria = request.form.get("categoria", "Otro")
        proveedor = request.form.get("proveedor", "").strip() or None
        fecha = request.form.get("fecha", "").strip() or None

        if proyecto_id == "" or descripcion == "" or monto == "":
            return redirigir_o_responder_error("Proyecto, descripción y monto son obligatorios.", "nuevo_gasto")

        if obtener_proyecto_por_id(proyecto_id, session["agencia_id"]) is None:
            return redirigir_o_responder_error("Proyecto inválido.", "nuevo_gasto")

        try:
            monto = float(monto)
        except ValueError:
            return redirigir_o_responder_error("El monto debe ser un número válido.", "nuevo_gasto")

        if monto <= 0:
            return redirigir_o_responder_error("El monto tiene que ser mayor a 0.", "nuevo_gasto")

        if categoria not in CATEGORIAS_GASTO:
            categoria = "Otro"

        try:
            comprobante = guardar_comprobante(request.files.get("comprobante"))
        except ValueError as error:
            return redirigir_o_responder_error(str(error), "nuevo_gasto")

        agregar_gasto(proyecto_id, descripcion, monto, categoria, proveedor, fecha, session["agencia_id"], comprobante)
        auditar("crear", "gasto", None, f"Registró un gasto de ${monto:,.2f} ({descripcion}).")

        if es_peticion_ajax():
            return jsonify({"exito": True})

        flash("Gasto agregado correctamente.", "exito")
        return redirect(url_for("ver_gastos"))
    else:
        return redirect(url_for("ver_gastos", nuevo=1))


@app.route("/gastos/<int:id>")
@login_requerido
def ver_gasto(id):
    gasto = obtener_gasto_por_id(id, session["agencia_id"])
    if gasto is None:
        flash("Gasto no encontrado.", "error")
        return redirect(url_for("ver_gastos"))

    proyecto = obtener_proyecto_por_id(gasto[1], session["agencia_id"])
    titulo_proyecto = proyecto[1] if proyecto else "Proyecto no encontrado"
    cliente = obtener_cliente_por_id(proyecto[2], session["agencia_id"]) if proyecto else None
    proyectos = obtener_proyectos(session["agencia_id"])
    return render_template(
        "gasto_detalle.html", gasto=gasto, proyecto=proyecto, titulo_proyecto=titulo_proyecto,
        cliente=cliente, proyectos=proyectos, categorias_gasto=CATEGORIAS_GASTO
    )


@app.route("/gastos/<int:id>/editar", methods=["GET", "POST"])
@login_requerido
def editar_gasto_ruta(id):
    gasto = obtener_gasto_por_id(id, session["agencia_id"])
    if gasto is None:
        flash("Gasto no encontrado.", "error")
        return redirect(url_for("ver_gastos"))

    if request.method == "POST":
        proyecto_id = request.form["proyecto_id"]
        descripcion = request.form.get("descripcion", "").strip()
        monto = request.form.get("monto", "")
        categoria = request.form.get("categoria", "Otro")
        proveedor = request.form.get("proveedor", "").strip() or None
        fecha = request.form.get("fecha", "").strip() or None

        if proyecto_id == "" or descripcion == "" or monto == "":
            return redirigir_o_responder_error("Proyecto, descripción y monto son obligatorios.", "editar_gasto_ruta", id=id)

        if obtener_proyecto_por_id(proyecto_id, session["agencia_id"]) is None:
            return redirigir_o_responder_error("Proyecto inválido.", "editar_gasto_ruta", id=id)

        try:
            monto = float(monto)
        except ValueError:
            return redirigir_o_responder_error("El monto debe ser un número válido.", "editar_gasto_ruta", id=id)

        if monto <= 0:
            return redirigir_o_responder_error("El monto tiene que ser mayor a 0.", "editar_gasto_ruta", id=id)

        if categoria not in CATEGORIAS_GASTO:
            categoria = "Otro"

        try:
            comprobante = guardar_comprobante(request.files.get("comprobante"))
        except ValueError as error:
            return redirigir_o_responder_error(str(error), "editar_gasto_ruta", id=id)

        editar_gasto_por_id(id, proyecto_id, descripcion, monto, categoria, proveedor, fecha, session["agencia_id"], comprobante)
        auditar("editar", "gasto", id, f"Editó el gasto '{descripcion}'.")

        if es_peticion_ajax():
            return jsonify({"exito": True})

        flash("Gasto actualizado correctamente.", "exito")
        return redirect(url_for("ver_gastos"))
    else:
        return redirect(url_for("ver_gastos", editar=id))


@app.route("/gastos/<int:id>/eliminar", methods=["POST"])
@admin_requerido
def eliminar_gasto_ruta(id):
    gasto = obtener_gasto_por_id(id, session["agencia_id"])
    eliminar_gasto_por_id(id, session["agencia_id"])
    auditar("eliminar", "gasto", id, f"Eliminó el gasto '{gasto[2] if gasto else id}'.")
    flash("Gasto eliminado.", "exito")
    return redirect(url_for("ver_gastos"))


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

        if obtener_cliente_por_id(cliente_id, session["agencia_id"]) is None:
            return redirigir_o_responder_error("Cliente inválido.", "nueva_nota")

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
        app.logger.exception("Falló la generación de un borrador de nota con IA.")
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

        if obtener_cliente_por_id(cliente_id, session["agencia_id"]) is None:
            return redirigir_o_responder_error("Cliente inválido.", "editar_nota_ruta", id=id)

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