# -*- coding: utf-8 -*-
import sys, os, json, datetime
sys.path.insert(0, os.path.dirname(__file__))
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright
from helpers import BASE_URL, attach_listeners, screenshot, ok, fail, info, print_summary

STATE_DIR = os.path.dirname(__file__)
STATE_ADMIN_A = os.path.join(STATE_DIR, "state_admin_a.json")
STATE_MIEMBRO_A = os.path.join(STATE_DIR, "state_miembro_a.json")
STATE_ADMIN_B = os.path.join(STATE_DIR, "state_admin_b.json")

hoy = datetime.date.today()
ayer = (hoy - datetime.timedelta(days=1)).isoformat()
en_2_dias = (hoy + datetime.timedelta(days=2)).isoformat()
en_30_dias = (hoy + datetime.timedelta(days=30)).isoformat()

ids = {}

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(storage_state=STATE_ADMIN_A, viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    b = {}
    attach_listeners(page, b)

    # ============ PROYECTOS ============
    page.goto(f"{BASE_URL}/proyectos")
    page.wait_for_load_state("networkidle")

    # Fecha pasada -> error
    page.click(".boton-nuevo-proyecto")
    page.wait_for_selector("#modal-proyecto[open]")
    page.fill("#modal-titulo", "QA_Proyecto FechaPasada")
    page.select_option("#modal-cliente_id", label="QA_Cliente 1")
    # Forzamos la fecha pasada via JS porque el input date tiene min=hoy (el navegador bloquearia escribirla)
    page.eval_on_selector("#modal-fecha_entrega", "(el, v) => { el.removeAttribute('min'); el.value = v; }", ayer)
    page.click("#formulario-proyecto input[type=submit]")
    try:
        page.wait_for_selector("#modal-proyecto-error:not([hidden])", timeout=3000)
        texto = page.inner_text("#modal-proyecto-error")
        ok("Proyecto con fecha de entrega pasada muestra error inline", texto)
    except Exception as e:
        fail("Proyecto con fecha pasada no mostro error (se habra creado igual?)", str(e))
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)

    # Proyecto valido, "por vencer" (en 2 dias)
    page.click(".boton-nuevo-proyecto")
    page.wait_for_selector("#modal-proyecto[open]")
    page.fill("#modal-titulo", "QA_Proyecto PorVencer")
    page.select_option("#modal-cliente_id", label="QA_Cliente 1")
    page.fill("#modal-fecha_entrega", en_2_dias)
    page.select_option("#modal-estado", "Pendiente")
    page.click("#formulario-proyecto input[type=submit]")
    page.wait_for_url(f"{BASE_URL}/proyectos", timeout=5000)
    page.wait_for_load_state("networkidle")
    if page.locator(".etiqueta-por-vencer").count() > 0:
        ok("Proyecto con entrega en 2 dias muestra la etiqueta 'Por vencer'")
    else:
        fail("Proyecto con entrega en 2 dias NO muestra la etiqueta 'Por vencer'")
    href = page.locator("a:has-text('QA_Proyecto PorVencer')").first.get_attribute("href")
    ids["proyecto_a"] = href.rstrip("/").split("/")[-1]

    # Verificar campanita de notificaciones
    page.click("#boton-notificaciones")
    page.wait_for_timeout(300)
    if page.locator(".dropdown-notificaciones").inner_text().find("QA_Proyecto PorVencer") != -1:
        ok("El proyecto por vencer aparece en la campana de notificaciones")
    else:
        fail("El proyecto por vencer NO aparece en la campana de notificaciones")
    page.keyboard.press("Escape")

    # Marcar completado desde la lista
    fila = page.locator("tr", has=page.locator(f"a[href='/proyectos/{ids['proyecto_a']}']"))
    fila.locator("button[data-tooltip='Marcar completado']").click()
    page.wait_for_load_state("networkidle")
    fila2 = page.locator("tr", has=page.locator(f"a[href='/proyectos/{ids['proyecto_a']}']"))
    estado_badge = fila2.locator(".badge").inner_text()
    if "Completado" in estado_badge:
        ok("Marcar completado desde la lista cambia el estado a Completado")
    else:
        fail("Marcar completado no actualizo el estado", estado_badge)
    if fila2.locator(".etiqueta-por-vencer").count() == 0:
        ok("Proyecto completado ya no muestra la etiqueta 'Por vencer'")
    else:
        fail("Proyecto completado SIGUE mostrando 'Por vencer' (bug)")

    # Otro proyecto normal (para pagos)
    page.click(".boton-nuevo-proyecto")
    page.wait_for_selector("#modal-proyecto[open]")
    page.fill("#modal-titulo", "QA_Proyecto Normal")
    page.select_option("#modal-cliente_id", label="QA_Cliente 1")
    page.fill("#modal-fecha_entrega", en_30_dias)
    page.click("#formulario-proyecto input[type=submit]")
    page.wait_for_url(f"{BASE_URL}/proyectos", timeout=5000)
    page.wait_for_load_state("networkidle")
    href2 = page.locator("a:has-text('QA_Proyecto Normal')").first.get_attribute("href")
    ids["proyecto_normal_a"] = href2.rstrip("/").split("/")[-1]

    # Editar proyecto: campos obligatorios vacios
    fila3 = page.locator("tr", has=page.locator(f"a[href='/proyectos/{ids['proyecto_normal_a']}']"))
    fila3.locator(".boton-editar-proyecto").click()
    page.wait_for_selector("#modal-proyecto[open]")
    page.fill("#modal-titulo", "")
    page.click("#formulario-proyecto input[type=submit]")
    try:
        page.wait_for_selector("#modal-proyecto-error:not([hidden])", timeout=3000)
        ok("Editar proyecto con titulo vacio muestra error de validacion")
    except Exception as e:
        fail("Editar proyecto con titulo vacio no mostro error", str(e))
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)

    # ============ PAGOS ============
    page.goto(f"{BASE_URL}/pagos")
    page.wait_for_load_state("networkidle")

    # Monto con decimales
    page.click(".boton-nuevo-pago")
    page.wait_for_selector("#modal-pago[open]")
    page.select_option("#modal-proyecto_id", label="QA_Proyecto Normal")
    page.fill("#modal-monto", "1234.56")
    page.fill("#modal-fecha-pago", hoy.isoformat())
    page.select_option("#modal-estado-pago", "cobrado")
    page.click("#formulario-pago input[type=submit]")
    page.wait_for_url(f"{BASE_URL}/pagos", timeout=5000)
    page.wait_for_load_state("networkidle")
    if page.locator("text=1,234.56").count() > 0 or page.locator("text=$1,234.56").count() > 0:
        ok("Pago con monto decimal (1234.56) se guarda y formatea correctamente")
    else:
        info("No se encontro el formato exacto esperado para 1234.56, revisar formato de moneda manualmente")

    # Pago pendiente
    page.click(".boton-nuevo-pago")
    page.wait_for_selector("#modal-pago[open]")
    page.select_option("#modal-proyecto_id", label="QA_Proyecto Normal")
    page.fill("#modal-monto", "500")
    page.fill("#modal-fecha-pago", hoy.isoformat())
    page.select_option("#modal-estado-pago", "pendiente")
    page.click("#formulario-pago input[type=submit]")
    page.wait_for_url(f"{BASE_URL}/pagos", timeout=5000)
    page.wait_for_load_state("networkidle")
    if page.locator(".badge-pendiente:has-text('Pendiente')").count() > 0:
        ok("Pago marcado como 'pendiente' muestra el badge correspondiente")
    else:
        fail("Pago pendiente no muestra el badge 'Pendiente'")

    href_pago = page.locator("tr", has=page.locator("text=QA_Proyecto Normal")).first.locator("a").first.get_attribute("href")
    ids["pago_pendiente_a"] = href_pago.rstrip("/").split("/")[-1]

    # Marcar cobrado
    fila_pago = page.locator("tr", has=page.locator(f"a[href='{href_pago}']"))
    if fila_pago.locator("button[data-tooltip='Marcar cobrado']").count() > 0:
        fila_pago.locator("button[data-tooltip='Marcar cobrado']").click()
        page.wait_for_load_state("networkidle")
        fila_pago2 = page.locator("tr", has=page.locator(f"a[href='{href_pago}']"))
        if "Cobrado" in fila_pago2.locator(".badge").inner_text():
            ok("Marcar cobrado cambia el estado del pago correctamente")
        else:
            fail("Marcar cobrado no actualizo el badge")

    # Recibo PDF
    page.goto(f"{BASE_URL}{href_pago}")
    page.wait_for_load_state("networkidle")
    with page.expect_download() as dl_info:
        page.click("a:has-text('Descargar recibo')")
    download = dl_info.value
    ok("Descargar recibo en PDF dispara una descarga", download.suggested_filename)

    # --- Monto negativo / cero via API directa (bypass validacion nativa del navegador) ---
    proyecto_normal_id = ids["proyecto_normal_a"]
    csrf_token = page.eval_on_selector("input[name=csrf_token]", "el => el.value")
    cookies = ctx.cookies()
    import urllib.request, urllib.parse
    resp_neg = page.request.post(
        f"{BASE_URL}/pagos/nuevo",
        form={"proyecto_id": proyecto_normal_id, "monto": "-100", "fecha": hoy.isoformat(), "estado": "cobrado", "csrf_token": csrf_token},
        headers={"X-Requested-With": "XMLHttpRequest"}
    )
    info("POST directo /pagos/nuevo con monto=-100 -> status", resp_neg.status)
    if resp_neg.status == 200:
        cuerpo = resp_neg.json()
        if cuerpo.get("exito"):
            fail("El servidor ACEPTA montos negativos para pagos (sin validacion de monto > 0)", "core/pagos.py / app.py nuevo_pago no valida monto negativo")
        else:
            ok("El servidor rechaza montos negativos", cuerpo)
    else:
        info("Respuesta inesperada para monto negativo", resp_neg.status)

    resp_cero = page.request.post(
        f"{BASE_URL}/pagos/nuevo",
        form={"proyecto_id": proyecto_normal_id, "monto": "0", "fecha": hoy.isoformat(), "estado": "cobrado", "csrf_token": csrf_token},
        headers={"X-Requested-With": "XMLHttpRequest"}
    )
    info("POST directo /pagos/nuevo con monto=0 -> status", resp_cero.status)

    # ============ NOTAS ============
    page.goto(f"{BASE_URL}/notas")
    page.wait_for_load_state("networkidle")
    page.click(".boton-nueva-nota")
    page.wait_for_selector("#modal-nota[open]")
    if page.is_visible("#boton-generar-ia-nota"):
        ok("Boton 'Generar con IA' esta presente en el modal de nueva nota (no se hace click para evitar llamar a la API real)")
    page.select_option("#modal-cliente_id-nota", label="QA_Cliente 1")
    page.fill("#modal-fecha-nota", hoy.isoformat())
    texto_largo = "QA_Nota " + ("Lorem ipsum dolor sit amet. " * 50)
    page.fill("#modal-contenido", texto_largo)
    page.click("#formulario-nota input[type=submit]")
    page.wait_for_url(f"{BASE_URL}/notas", timeout=5000)
    page.wait_for_load_state("networkidle")
    if page.locator("text=QA_Nota").count() > 0:
        ok("Nota con texto largo (1400+ caracteres) se crea correctamente")
    else:
        fail("Nota con texto largo no aparecio en la lista")

    if b["console_errors"]:
        fail("Errores de consola durante pruebas de proyectos/pagos/notas", "; ".join(set(b["console_errors"][:5])))

    screenshot(page, "notas_admin_a.png")
    ctx.close()

    with open(os.path.join(STATE_DIR, "ids_compartidos.json")) as f:
        prev = json.load(f)
    prev.update(ids)
    with open(os.path.join(STATE_DIR, "ids_compartidos.json"), "w") as f:
        json.dump(prev, f)

    # ============ MIEMBRO A: restricciones ============
    ctx_m = browser.new_context(storage_state=STATE_MIEMBRO_A, viewport={"width": 1280, "height": 900})
    page_m = ctx_m.new_page()
    for ruta in ["/proyectos", "/pagos", "/notas"]:
        page_m.goto(f"{BASE_URL}{ruta}")
        page_m.wait_for_load_state("networkidle")
        n = page_m.locator("form.form-eliminar button").count()
        if n == 0:
            ok(f"Miembro no ve boton Eliminar en {ruta}")
        else:
            fail(f"Miembro SI ve boton Eliminar en {ruta}", str(n))
    # Miembro SI deberia poder marcar completado/cobrado (login_requerido, no admin_requerido)
    page_m.goto(f"{BASE_URL}/proyectos/{ids['proyecto_normal_a']}")
    page_m.wait_for_load_state("networkidle")
    if page_m.locator("button:has-text('Marcar completado')").count() > 0:
        ok("Miembro SI puede ver el boton 'Marcar completado' (accion permitida para miembros)")
    else:
        info("Miembro no ve boton marcar completado (puede que el proyecto ya este completado)")
    ctx_m.close()

    # ============ ADMIN B: aislamiento ============
    ctx_b = browser.new_context(storage_state=STATE_ADMIN_B, viewport={"width": 1280, "height": 900})
    page_b = ctx_b.new_page()
    for entidad, id_ in [("proyectos", ids["proyecto_a"]), ("pagos", ids.get("pago_pendiente_a"))]:
        if not id_:
            continue
        page_b.goto(f"{BASE_URL}/{entidad}/{id_}")
        page_b.wait_for_load_state("networkidle")
        contenido = page_b.content()
        if "no encontrad" in contenido.lower():
            ok(f"Admin B no puede ver {entidad}/{id_} de la agencia A (aislamiento OK)")
        else:
            fail(f"CRITICO: Admin B puede ver {entidad}/{id_} de la agencia A", page_b.url)
    ctx_b.close()

    browser.close()

print_summary()
