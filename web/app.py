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
                           obtener_cliente_por_id,
                           agregar_cliente, 
                           editar_cliente_por_id,
                           eliminar_cliente_por_id
)
from core.proyectos import(
    obtener_proyectos,
    obtener_proyecto_por_id,
    agregar_proyecto,
    editar_proyecto_por_id,
    eliminar_proyecto_por_id,
    proyecto_esta_por_vencer,
    proyectos_de_cliente
)
from core.pagos import(
    obtener_pagos,
    obtener_pago_por_id,
    agregar_pago,
    editar_pago_por_id,
    eliminar_pago_por_id,
    pagos_de_proyecto
)
from core.notas import(
    obtener_notas,
    obtener_nota_por_id,
    agregar_nota,
    editar_nota_por_id,
    eliminar_nota_por_id
)
from core.estadisticas import (
    contar_clientes,
    contar_proyectos,
    contar_pagos,
    total_cobrado,
    proyectos_por_estado,
    estadisticas_dashboard
)
from core.usuarios import (
    verificar_usuario,
    crear_usuario,
    usuarios_de_agencia,
    obtener_usuario_por_id,
    contar_admins_agencia,
    eliminar_usuario_por_id
)
from core.agencias import obtener_agencia_por_id, actualizar_configuracion_agencia
from core.importacion import importar_clientes_desde_archivo, generar_plantilla_clientes
from avisos_telegram import avisar_proyecto_individual

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
csrf = CSRFProtect(app)
limiter = Limiter(get_remote_address, app=app, default_limits=[])

# Filtro de plantilla para renderizar el markdown de las respuestas de IA como HTML
# real (negrita, listas) en vez de texto plano con asteriscos sueltos. La sanitización
# ocurre dentro de markdown_a_html_seguro, así que en los templates se usa con `| safe`.
app.jinja_env.filters["markdown"] = markdown_a_html_seguro

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

@app.context_processor
def inyectar_agencia_actual():
    if "agencia_id" in session:
        agencia = obtener_agencia_por_id(session["agencia_id"])
        if agencia:
            return {"agencia_actual": agencia[1], "rol_actual": session.get("rol")}
    return {"agencia_actual": None, "rol_actual": None}

@app.route("/")
@login_requerido
def inicio():
    datos = estadisticas_dashboard(session["agencia_id"])
    return render_template("dashboard.html", **datos, resumen=None)


@app.route("/resumen-ejecutivo", methods=["POST"])
@login_requerido
def resumen_ejecutivo():
    datos = estadisticas_dashboard(session["agencia_id"])
    resumen = generar_resumen_ejecutivo(
        datos["total_clientes"], datos["total_proyectos"],
        datos["total_pagos"], datos["cobrado"], datos["por_estado"]
    )
    return render_template("dashboard.html", **datos, resumen=resumen)
    

@app.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
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

@app.route("/configuracion", methods=["GET", "POST"])
@login_requerido
def configuracion_agencia():
    agencia = obtener_agencia_por_id(session["agencia_id"])

    if request.method == "POST":
        telegram_chat_id = request.form["telegram_chat_id"].strip() or None
        gmail_user = request.form["gmail_user"].strip() or None
        gmail_app_password = request.form["gmail_app_password"].strip() or None

        actualizar_configuracion_agencia(session["agencia_id"], telegram_chat_id, gmail_user, gmail_app_password)

        flash("Configuración actualizada correctamente.", "exito")
        return redirect(url_for("configuracion_agencia"))

    return render_template("configuracion.html", agencia=agencia)


@app.route("/usuarios", methods=["GET", "POST"])
@admin_requerido
def ver_usuarios():
    if request.method == "POST":
        nombre_usuario = request.form["nombre_usuario"].strip()
        contraseña = request.form["contraseña"]
        rol = request.form["rol"]

        if nombre_usuario == "" or contraseña == "":
            flash("Nombre de usuario y contraseña son obligatorios.", "error")
            return redirect(url_for("ver_usuarios"))

        if rol not in ("admin", "miembro"):
            flash("Rol inválido.", "error")
            return redirect(url_for("ver_usuarios"))

        try:
            crear_usuario(nombre_usuario, contraseña, session["agencia_id"], rol)
            flash("Usuario agregado correctamente.", "exito")
        except Exception:
            flash(f"Ya existe un usuario con el nombre '{nombre_usuario}'.", "error")

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
    flash("Usuario eliminado.", "exito")
    return redirect(url_for("ver_usuarios"))


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
    clientes = obtener_clientes(session["agencia_id"])
    return render_template("clientes.html", clientes=clientes)

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
        return render_template("cliente_detalle.html", cliente=cliente, notas=notas, proyectos=proyectos, resumen=None, asunto_borrador=None, cuerpo_borrador=None, mensaje_envio=None)


@app.route("/clientes/<int:id>/resumen-ia", methods=["POST"])
@login_requerido
def resumen_ia_cliente(id):
    cliente = obtener_cliente_por_id(id, session["agencia_id"])

    if cliente is None:
        flash("Cliente no encontrado.", "error")
        return redirect(url_for("ver_clientes"))

    notas = notas_de_cliente(id, session["agencia_id"])
    proyectos = proyectos_de_cliente(id, session["agencia_id"])
    resumen = resumir_notas_cliente(notas)

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

    cuerpo_borrador = redactar_correo(cliente[1], palabras_clave)

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
            flash("Nombre y email son obligatorios.", "error")
            return redirect(url_for("nuevo_cliente"))

        agregar_cliente(nombre, email, telefono, empresa, notas, session["agencia_id"])
        
        flash("Cliente agregado correctamente", "exito")
        return redirect(url_for("ver_clientes"))
          
    else:
        return render_template("cliente_form.html", cliente=None)


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
            flash("Nombre y email son obligatorios.", "error")
            return redirect(url_for("editar_cliente_ruta", id=id))

        editar_cliente_por_id(id, nombre, email, telefono, empresa, notas, session["agencia_id"])
        
        flash("Cliente actualizado correctamente.", "exito")
        return redirect(url_for("ver_clientes"))
        
    else:
        return render_template("cliente_form.html", cliente=cliente)
    
    
        
@app.route("/clientes/<int:id>/eliminar", methods=["POST"])
@login_requerido
def eliminar_cliente_ruta(id):
    eliminar_cliente_por_id(id, session["agencia_id"])
    flash("Cliente eliminado.", "exito")
    return redirect(url_for("ver_clientes"))


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
    proyectos = obtener_proyectos(session["agencia_id"])
    lista = []
    for proyecto in proyectos:
        cliente = obtener_cliente_por_id(proyecto[2], session["agencia_id"])
        if cliente is None:
            nombre_cliente = "Cliente no encontrado"
        else:
            nombre_cliente = cliente[1]
        por_vencer = proyecto_esta_por_vencer(proyecto[3], proyecto[4])
        lista.append((proyecto, nombre_cliente, por_vencer))
    return render_template("proyectos.html", proyectos=lista)


@app.route("/proyectos/nuevo",methods=["GET", "POST"])
@login_requerido
def nuevo_proyecto():
    if request.method == "POST":
        titulo = request.form["titulo"]
        cliente_id = request.form["cliente_id"]
        estado = request.form["estado"]
        fecha_entrega = request.form["fecha_entrega"]
        
        if titulo == "" or cliente_id == "":
            flash("Título y cliente son obligatorios.", "error")
            return redirect(url_for("nuevo_proyecto"))

        agregar_proyecto(titulo, cliente_id, estado, fecha_entrega, session["agencia_id"])

        if proyecto_esta_por_vencer(estado, fecha_entrega):
            agencia = obtener_agencia_por_id(session["agencia_id"])
            if agencia and agencia[2]:
                try:
                    cliente = obtener_cliente_por_id(cliente_id, session["agencia_id"])
                    nombre_cliente = cliente[1] if cliente else "Cliente no encontrado"
                    avisar_proyecto_individual(titulo, fecha_entrega, nombre_cliente, agencia[2])
                except Exception as error:
                    print(f"No se pudo enviar el aviso de Telegram: {error}")

        flash("Proyecto agregado correctamente.", "exito")
        return redirect(url_for("ver_proyectos"))
        
    else:
        clientes = obtener_clientes(session["agencia_id"])
        return render_template("proyecto_form.html", proyecto=None, clientes=clientes)
    
    
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
        return render_template("proyecto_detalle.html", proyecto=proyecto, nombre_cliente=nombre_cliente, pagos=pagos, sugerencias=None)
    
    
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
    sugerencias = generar_sugerencias_proyecto(proyecto, nombre_cliente, notas, pagos)

    return render_template("proyecto_detalle.html", proyecto=proyecto, nombre_cliente=nombre_cliente, pagos=pagos, sugerencias=sugerencias)
    

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

        if titulo == "" or cliente_id == "":
            flash("Título y cliente son obligatorios.", "error")
            return redirect(url_for("editar_proyecto_ruta", id=id))

        editar_proyecto_por_id(id, titulo, cliente_id, estado, fecha_entrega, session["agencia_id"])

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
        
        flash("Proyecto actualizado correctamente.", "exito")
        return redirect(url_for("ver_proyectos"))
    else:
        clientes = obtener_clientes(session["agencia_id"])
        return render_template("proyecto_form.html", proyecto=proyecto, clientes=clientes)
        
@app.route("/proyectos/<int:id>/eliminar", methods=["POST"])
@login_requerido
def eliminar_proyecto_ruta(id):
    eliminar_proyecto_por_id(id, session["agencia_id"])
    flash("Proyecto eliminado.", "exito")
    return redirect(url_for("ver_proyectos"))

@app.route("/pagos")
@login_requerido
def ver_pagos():
    pagos = obtener_pagos(session["agencia_id"])
    lista = []
    for pago in pagos:
        proyecto = obtener_proyecto_por_id(pago[1], session["agencia_id"])
        if proyecto is None:
            titulo_proyecto = "Proyecto no encontrado"
        else:
            titulo_proyecto = proyecto[1]
        lista.append((pago, titulo_proyecto))
    return render_template("pagos.html", pagos=lista)
        
        
@app.route("/pagos/nuevo", methods=["GET", "POST"])
@login_requerido
def nuevo_pago():
    if request.method == "POST":
        proyecto_id = request.form["proyecto_id"]
        monto = request.form["monto"]
        fecha = request.form["fecha"]

        if proyecto_id == "" or monto == "":
            flash("Proyecto y monto son obligatorios.", "error")
            return redirect(url_for("nuevo_pago"))

        try:
            monto = float(monto)
        except ValueError:
            flash("El monto debe ser un número válido.", "error")
            return redirect(url_for("nuevo_pago"))

        agregar_pago(proyecto_id, monto, fecha, session["agencia_id"])

        flash("Pago agregado correctamente.", "exito")
        return redirect(url_for("ver_pagos"))

    else:
        proyectos = obtener_proyectos(session["agencia_id"])
        return render_template("pago_form.html", pago=None, proyectos=proyectos)
    
    
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
        return render_template("pago_detalle.html", pago=pago, titulo_proyecto=titulo_proyecto)
    

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

        if proyecto_id == "" or monto == "":
            flash("Proyecto y monto son obligatorios.", "error")
            return redirect(url_for("editar_pago_ruta", id=id))

        try:
            monto = float(monto)
        except ValueError:
            flash("El monto debe ser un número válido.", "error")
            return redirect(url_for("editar_pago_ruta", id=id))

        editar_pago_por_id(id, proyecto_id, monto, fecha, session["agencia_id"])
        flash("Pago actualizado correctamente.", "exito")
        return redirect(url_for("ver_pago", id=id))

    else:
        proyectos = obtener_proyectos(session["agencia_id"])
        return render_template("pago_form.html", pago=pago, proyectos=proyectos)
        
@app.route("/pagos/<int:id>/eliminar", methods=["POST"])
@login_requerido
def eliminar_pago_ruta(id):
    eliminar_pago_por_id(id, session["agencia_id"])
    flash("Pago eliminado.", "exito")
    return redirect(url_for("ver_pagos"))

@app.route("/notas")
@login_requerido
def ver_notas():
    notas = obtener_notas(session["agencia_id"])
    lista = []
    for nota in notas:
        cliente = obtener_cliente_por_id(nota[1], session["agencia_id"])
        if cliente is None:
            nombre_cliente = "Cliente no encontrado"
        else:
            nombre_cliente = cliente[1]
        lista.append((nota, nombre_cliente))
    return render_template("notas.html", notas=lista)
        

@app.route("/notas/nuevo", methods=["GET", "POST"])
@login_requerido
def nueva_nota():
    if request.method == "POST":
        cliente_id = request.form["cliente_id"]
        contenido = request.form["contenido"]
        fecha = request.form["fecha"]
        
        if cliente_id == "" or contenido == "":
            flash("Cliente y contenido son obligatorios.", "error")
            return redirect(url_for("nueva_nota"))

        agregar_nota(cliente_id, contenido, fecha, session["agencia_id"])
        
        flash("Nota agregada correctamente.", "exito")
        return redirect(url_for("ver_notas"))
        
    else:
        clientes = obtener_clientes(session["agencia_id"])
        return render_template("nota_form.html", nota=None, clientes=clientes, fecha_hoy=date.today().isoformat())
    
@app.route("/notas/generar-ia", methods=["POST"])
@login_requerido
def generar_nota_ia():
    cliente_id = request.form["cliente_id"]
    palabras_clave = request.form["palabras_clave"]

    borrador_ia = redactar_nota(palabras_clave)

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
        return render_template("nota_detalle.html", nota=nota, nombre_cliente=nombre_cliente)
    
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
            flash("Cliente y contenido son obligatorios.", "error")
            return redirect(url_for("editar_nota_ruta", id=id))

        editar_nota_por_id(id, cliente_id, contenido, fecha, session["agencia_id"])
        
        flash("Nota actualizada correctamente.", "exito")
        return redirect(url_for("ver_notas"))
        
    else:
        clientes = obtener_clientes(session["agencia_id"])
        return render_template("nota_form.html", nota=nota, clientes=clientes)
        
@app.route("/notas/<int:id>/eliminar", methods=["POST"])
@login_requerido
def eliminar_nota_ruta(id):
    eliminar_nota_por_id(id, session["agencia_id"])
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