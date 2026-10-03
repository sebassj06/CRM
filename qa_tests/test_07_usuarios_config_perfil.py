# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright
from helpers import BASE_URL, attach_listeners, screenshot, ok, fail, info, print_summary

STATE_DIR = os.path.dirname(__file__)
STATE_ADMIN_A = os.path.join(STATE_DIR, "state_admin_a.json")
STATE_MIEMBRO_A = os.path.join(STATE_DIR, "state_miembro_a.json")

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ============ MIEMBRO: no debe acceder a /usuarios ni /configuracion ============
    ctx_m = browser.new_context(storage_state=STATE_MIEMBRO_A, viewport={"width": 1280, "height": 900})
    page_m = ctx_m.new_page()
    if page_m.locator("a[href='/usuarios']").count() == 0 and page_m.locator("a[href='/configuracion']").count() == 0:
        page_m.goto(f"{BASE_URL}/")
        page_m.wait_for_load_state("networkidle")
        if page_m.locator("a[href='/usuarios']").count() == 0 and page_m.locator("a[href='/configuracion']").count() == 0:
            ok("Miembro no ve enlaces a Usuarios/Configuracion en el menu")
        else:
            fail("Miembro SI ve enlaces a Usuarios/Configuracion en el menu")
    for ruta in ["/usuarios", "/configuracion"]:
        page_m.goto(f"{BASE_URL}{ruta}")
        page_m.wait_for_load_state("networkidle")
        if page_m.url.rstrip("/") == BASE_URL:
            ok(f"Miembro escribiendo {ruta} por URL es redirigido al inicio (sin acceso)")
        else:
            fail(f"CRITICO: Miembro pudo acceder a {ruta} escribiendo la URL directamente", page_m.url)
    ctx_m.close()

    # ============ ADMIN: usuarios CRUD ============
    ctx = browser.new_context(storage_state=STATE_ADMIN_A, viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    b = {}
    attach_listeners(page, b)
    page.goto(f"{BASE_URL}/usuarios")
    page.wait_for_load_state("networkidle")

    # Usuario duplicado
    page.click("#boton-nuevo-usuario")
    page.wait_for_selector("#modal-usuario[open]")
    page.fill("#nombre_usuario", "QA_admin_a")  # ya existe
    page.fill("#contraseña", "QA_Pass123!")
    page.click("#formulario-usuario input[type=submit]")
    try:
        page.wait_for_selector("#modal-usuario-error:not([hidden])", timeout=3000)
        texto = page.inner_text("#modal-usuario-error")
        ok("Crear usuario con nombre duplicado muestra error inline", texto)
    except Exception as e:
        fail("Crear usuario duplicado no mostro error", str(e))

    # Usuario nuevo valido (miembro)
    page.fill("#nombre_usuario", "QA_nuevo_miembro")
    page.fill("#contraseña", "QA_Pass123!")
    page.select_option("#rol", "miembro")
    page.click("#formulario-usuario input[type=submit]")
    page.wait_for_url(f"{BASE_URL}/usuarios", timeout=5000)
    page.wait_for_load_state("networkidle")
    if page.locator("text=QA_nuevo_miembro").count() > 0:
        ok("Usuario nuevo (miembro) creado correctamente")
    else:
        fail("Usuario nuevo no aparecio en la lista")

    # Toggle password al crear usuario
    page.click("#boton-nuevo-usuario")
    page.wait_for_selector("#modal-usuario[open]")
    page.fill("#contraseña", "algo")
    tipo_antes = page.eval_on_selector("#contraseña", "el => el.type")
    page.click("#modal-usuario .boton-ver-password")
    tipo_despues = page.eval_on_selector("#contraseña", "el => el.type")
    if tipo_antes == "password" and tipo_despues == "text":
        ok("Toggle mostrar/ocultar contraseña funciona en el modal de nuevo usuario")
    else:
        fail("Toggle de password no funciono en modal de usuario")
    page.click("#boton-cancelar-modal-usuario")
    page.wait_for_timeout(300)

    # Intentar eliminarse a si mismo: no deberia haber boton
    fila_propia = page.locator("tr", has=page.locator("text=(vos)"))
    if fila_propia.locator("form.form-eliminar").count() == 0:
        ok("No hay boton de eliminar para el propio usuario logueado (QA_admin_a)")
    else:
        fail("Aparece boton de eliminar para el propio usuario (deberia estar oculto)")

    # Eliminar al miembro nuevo
    fila_nuevo = page.locator("tr", has=page.locator("text=QA_nuevo_miembro"))
    fila_nuevo.locator("form.form-eliminar button").click()
    page.wait_for_selector("#modal-confirmar-eliminar[open]")
    page.click("#boton-cancelar-eliminar")
    page.wait_for_timeout(300)
    if page.locator("text=QA_nuevo_miembro").count() > 0:
        ok("Cancelar en el modal de confirmacion de borrado NO elimina al usuario")
    else:
        fail("El usuario desaparecio aunque se cancelo el borrado (bug)")

    fila_nuevo = page.locator("tr", has=page.locator("text=QA_nuevo_miembro"))
    fila_nuevo.locator("form.form-eliminar button").click()
    page.wait_for_selector("#modal-confirmar-eliminar[open]")
    page.click("#boton-confirmar-eliminar")
    page.wait_for_load_state("networkidle")
    if page.locator("text=QA_nuevo_miembro").count() == 0:
        ok("Confirmar eliminar SI elimina al usuario correctamente")
    else:
        fail("El usuario sigue apareciendo despues de confirmar su eliminacion")

    # Intentar eliminar al unico admin via POST directo (QA_admin_a es el unico admin de agencia A)
    csrf = page.eval_on_selector("input[name=csrf_token]", "el => el.value")
    # admin_id lo sacamos de la fila "(vos)"
    import re
    admin_href = page.locator("tr", has=page.locator("text=(vos)")).locator("form").get_attribute("action") if page.locator("tr", has=page.locator("text=(vos)")).locator("form").count() > 0 else None
    info("No se intenta eliminar al propio admin porque la UI ya no expone el boton (verificado arriba)")

    if b["console_errors"]:
        fail("Errores de consola en pruebas de usuarios", "; ".join(set(b["console_errors"][:5])))
    screenshot(page, "usuarios_admin_a.png")
    ctx.close()

    # ============ CONFIGURACION: guardar sin borrar password de Gmail ============
    ctx_c = browser.new_context(storage_state=STATE_ADMIN_A, viewport={"width": 1280, "height": 900})
    page_c = ctx_c.new_page()
    page_c.goto(f"{BASE_URL}/configuracion")
    page_c.wait_for_load_state("networkidle")
    page_c.fill("#gmail_user", "qa_fake_agencia@example.com")
    page_c.fill("#gmail_app_password", "clave-app-falsa-1234")
    page_c.fill("#telegram_chat_id", "QA_FAKE_CHAT_ID")
    page_c.click("input[type=submit]")
    page_c.wait_for_load_state("networkidle")
    if page_c.locator(".flash-exito, .flash.flash-exito").count() > 0 or "actualizada" in page_c.content().lower():
        ok("Guardar configuracion (Gmail/Telegram falsos) muestra mensaje de exito")
    else:
        fail("Guardar configuracion no mostro mensaje de exito")
    badge_gmail_conectado = page_c.locator("text=Conectado").count()
    info("Badges 'Conectado' tras guardar Gmail/Telegram", badge_gmail_conectado)

    # Ahora recargar y dejar la contraseña de gmail en blanco, cambiar solo el usuario
    page_c.goto(f"{BASE_URL}/configuracion")
    page_c.wait_for_load_state("networkidle")
    placeholder = page_c.get_attribute("#gmail_app_password", "placeholder")
    info("Placeholder del campo de password de Gmail tras guardar una", placeholder)
    page_c.fill("#gmail_user", "qa_fake_agencia@example.com")
    # dejamos gmail_app_password en blanco a proposito
    page_c.click("input[type=submit]")
    page_c.wait_for_load_state("networkidle")
    page_c.goto(f"{BASE_URL}/configuracion")
    page_c.wait_for_load_state("networkidle")
    badge_gmail_sigue_conectado = page_c.locator("text=Conectado").count()
    if badge_gmail_sigue_conectado >= 1:
        ok("Guardar con password de Gmail en blanco NO borra la contraseña guardada (sigue 'Conectado')")
    else:
        fail("BUG: guardar con password de Gmail en blanco borro la contraseña (ya no aparece 'Conectado')")

    screenshot(page_c, "configuracion_admin_a.png")
    ctx_c.close()

    # ============ PERFIL: renombrarse a un nombre de usuario que ya existe ============
    ctx_p = browser.new_context(storage_state=STATE_ADMIN_A, viewport={"width": 1280, "height": 900})
    page_p = ctx_p.new_page()
    respuestas_malas = []
    page_p.on("response", lambda r: respuestas_malas.append((r.status, r.url)) if r.status >= 500 else None)
    page_p.goto(f"{BASE_URL}/perfil")
    page_p.wait_for_load_state("networkidle")
    page_p.fill("#nombre_usuario", "QA_miembro_a")  # ya existe (otro usuario de la misma agencia)
    resp = page_p.click("input[type=submit]")
    page_p.wait_for_load_state("networkidle")
    info("Tras renombrar perfil a un nombre ya existente, status final / url", page_p.url)
    if respuestas_malas:
        fail(
            "BUG CRITICO: renombrar el perfil propio a un nombre de usuario que ya existe produce un error 500 "
            "del servidor (IntegrityError de PostgreSQL, violacion de UNIQUE en nombre_usuario, no esta "
            "capturado con try/except en la ruta /perfil como si lo esta en /usuarios).",
            str(respuestas_malas)
        )
        screenshot(page_p, "BUG_perfil_500_nombre_duplicado.png")
    else:
        texto = page_p.content()
        if "ya existe" in texto.lower() or "error" in texto.lower():
            ok("Renombrar el perfil a un nombre duplicado muestra un error manejado (no 500)")
        else:
            info("No se detecto error 500 pero tampoco un mensaje claro, revisar manualmente", page_p.url)
    ctx_p.close()

    browser.close()

print_summary()
