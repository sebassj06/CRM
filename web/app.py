import os
from dotenv import load_dotenv

load_dotenv()

from flask import Flask, request, render_template, redirect, url_for, session, jsonify, flash, send_file
from functools import wraps
from core.correo import enviar_correo
from core.notas import notas_de_cliente
from core.ia import resumir_notas_cliente, generar_resumen_ejecutivo, generar_sugerencias_proyecto, redactar_nota, redactar_correo
from datetime import date
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
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
    eliminar_proyecto_por_id
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
from core.usuarios import verificar_usuario
from core.agencias import obtener_agencia_por_id
from core.importacion import importar_clientes_desde_archivo, generar_plantilla_clientes

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
csrf = CSRFProtect(app)
limiter = Limiter(get_remote_address, app=app, default_limits=[])

def login_requerido(f):
    @wraps(f)
    def funcion_decorada(*args, **kwargs):
        if "usuario" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return funcion_decorada

@app.route("/")
@login_requerido
def inicio():
    datos = estadisticas_dashboard()
    return render_template("dashboard.html", **datos, resumen=None)
    
    
@app.route("/resumen-ejecutivo", methods=["POST"])
@login_requerido
def resumen_ejecutivo():
    datos = estadisticas_dashboard()
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
        return redirect(url_for("inicio"))
    else:
        return render_template("login.html", error=None)

@app.route("/logout")
def logout():
    session.pop("usuario", None)
    session.pop("agencia_id", None)
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
        return "Cliente no encontrado"
    else:
        notas = notas_de_cliente(id, session["agencia_id"])
        return render_template("cliente_detalle.html", cliente=cliente, notas=notas, resumen=None, asunto_borrador=None, cuerpo_borrador=None, mensaje_envio=None)


@app.route("/clientes/<int:id>/resumen-ia", methods=["POST"])
@login_requerido
def resumen_ia_cliente(id):
    cliente = obtener_cliente_por_id(id, session["agencia_id"])

    if cliente is None:
        return "Cliente no encontrado"

    notas = notas_de_cliente(id, session["agencia_id"])
    resumen = resumir_notas_cliente(notas)

    return render_template("cliente_detalle.html", cliente=cliente, notas=notas, resumen=resumen, asunto_borrador=None, cuerpo_borrador=None, mensaje_envio=None)


@app.route("/clientes/<int:id>/correo-ia/generar", methods=["POST"])
@login_requerido
def generar_correo_ia(id):
    cliente = obtener_cliente_por_id(id, session["agencia_id"])

    if cliente is None:
        return "Cliente no encontrado"

    asunto = request.form["asunto"]
    palabras_clave = request.form["palabras_clave"]

    cuerpo_borrador = redactar_correo(cliente[1], palabras_clave)

    notas = notas_de_cliente(id, session["agencia_id"])
    return render_template("cliente_detalle.html", cliente=cliente, notas=notas, resumen=None, asunto_borrador=asunto, cuerpo_borrador=cuerpo_borrador, mensaje_envio=None)


@app.route("/clientes/<int:id>/correo-ia/enviar", methods=["POST"])
@login_requerido
def enviar_correo_ia(id):
    cliente = obtener_cliente_por_id(id, session["agencia_id"])

    if cliente is None:
        return "Cliente no encontrado"

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
    return render_template("cliente_detalle.html", cliente=cliente, notas=notas, resumen=None, asunto_borrador=None, cuerpo_borrador=None, mensaje_envio=mensaje_envio)

   
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
            return "<p>Error: nombre y email son obligatorios.</p><a href='/clientes/nuevo'>Volver al formulario</a>"
        
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
        return "Cliente no encontrado"
    
    if request.method == "POST":
        nombre = request.form["nombre"]
        email = request.form["email"]
        telefono = request.form["telefono"]
        empresa = request.form["empresa"]
        notas = request.form["notas"]
        
        if nombre == "" or email == "":
            return f"<p>Error: nombre y email son obligatorios.</p><a href='/clientes/{id}/editar'>Volver</a>"
        
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
        lista.append((proyecto, nombre_cliente))
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
            return "<p>Error: titulo y cliente son obligatorios.</p><a href='/proyectos/nuevo'>Volver</a>"
        
        agregar_proyecto(titulo, cliente_id, estado, fecha_entrega, session["agencia_id"])
        
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
        return "Proyecto no encontrado"
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
        return "Proyecto no encontrado"

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
        return "Proyecto no encontrado"

    if request.method == "POST":
        estado_anterior = proyecto[3]

        titulo = request.form["titulo"]
        cliente_id = request.form["cliente_id"]
        estado = request.form["estado"]
        fecha_entrega = request.form["fecha_entrega"]

        if titulo == "" or cliente_id == "":
            return f"<p>Error: titulo y cliente son obligatorios.</p><a href='/proyectos/{id}/editar'>Volver</a>"

        editar_proyecto_por_id(id, titulo, cliente_id, estado, fecha_entrega, session["agencia_id"])

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
            return "<p>Error: proyecto y monto son obligatorios.</p><a href='/pagos/nuevo'>Volver</a>"

        try:
            monto = float(monto)
        except ValueError:
            return "<p>Error: el monto debe ser un número válido.</p><a href='/pagos/nuevo'>Volver</a>"

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
        return "Pago no encontrado"
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
        return "Pago no encontrado"

    if request.method == "POST":
        proyecto_id = request.form["proyecto_id"]
        monto = request.form["monto"]
        fecha = request.form["fecha"]

        if proyecto_id == "" or monto == "":
            return f"<p>Error: proyecto y monto son obligatorios.</p><a href='/pagos/{id}/editar'>Volver</a>"

        try:
            monto = float(monto)
        except ValueError:
            return f"<p>Error: el monto debe ser un número válido.</p><a href='/pagos/{id}/editar'>Volver</a>"

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
            return "<p>Error: cliente y contenido son obligatorios.</p><a href='/notas/nuevo'>Volver</a>"
        
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
        return "Nota no encontrada"
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
        return "Nota no encontrada"
    
    if request.method == "POST":
        cliente_id = request.form["cliente_id"]
        contenido = request.form["contenido"]
        fecha = request.form["fecha"]
        
        if cliente_id == "" or contenido == "":
            return f"<p>Error: cliente y contenido son obligatorios.</p><a href='/notas/{id}/editar'>Volver</a>"
        
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

           
        
                
if __name__ == "__main__":
    modo_debug = os.getenv("FLASK_DEBUG", "False") == "True"
    app.run(debug=modo_debug)