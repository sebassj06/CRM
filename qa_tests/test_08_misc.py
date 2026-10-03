# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright
from helpers import BASE_URL, attach_listeners, screenshot, ok, fail, info, print_summary

STATE_DIR = os.path.dirname(__file__)
STATE_ADMIN_A = os.path.join(STATE_DIR, "state_admin_a.json")

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(storage_state=STATE_ADMIN_A, viewport={"width": 1280, "height": 900})
    page = ctx.new_page()

    # --- CSRF: POST sin token ---
    resp = page.request.post(f"{BASE_URL}/clientes/nuevo", form={"nombre": "QA_SinCSRF", "email": "qa_sincsrf@test.com"})
    info("POST /clientes/nuevo sin csrf_token -> status", resp.status)
    if resp.status in (400, 403):
        ok("POST sin token CSRF es rechazado correctamente")
    else:
        fail("POST sin token CSRF NO fue rechazado (posible vulnerabilidad CSRF)", resp.status)
    page.goto(f"{BASE_URL}/clientes")
    page.wait_for_load_state("networkidle")
    if page.locator("text=QA_SinCSRF").count() == 0:
        ok("El cliente sin CSRF token no se creo")
    else:
        fail("CRITICO: el cliente se creo a pesar de no tener token CSRF valido")

    # --- Doble click rapido en guardar (doble submit) ---
    page.click(".boton-nuevo-cliente")
    page.wait_for_selector("#modal-cliente[open]")
    page.fill("#modal-nombre", "QA_DobleClick")
    page.fill("#modal-email", "qa_dobleclick@test.com")
    boton = page.locator("#formulario-cliente input[type=submit]")
    boton.click()
    try:
        boton.click(timeout=500)
    except Exception:
        pass
    page.wait_for_timeout(1500)
    page.goto(f"{BASE_URL}/clientes")
    page.wait_for_load_state("networkidle")
    cantidad = page.locator("text=QA_DobleClick").count()
    if cantidad <= 1:
        ok(f"Doble click en Guardar no duplica el registro (encontrados: {cantidad})")
    else:
        fail(f"BUG: doble click en Guardar creo {cantidad} clientes duplicados")

    # --- Teclado: Tab/Enter/Esc en el modal ---
    page.click(".boton-nuevo-cliente")
    page.wait_for_selector("#modal-cliente[open]")
    foco_inicial = page.evaluate("document.activeElement.id")
    info("Elemento con foco al abrir el modal", foco_inicial)
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)
    if page.get_attribute("#modal-cliente", "open") is None:
        ok("Esc cierra el modal tambien cuando se navega solo con teclado")

    # --- Mobile + dark mode screenshots ---
    ctx.close()

    for viewport_name, viewport in [("desktop", {"width": 1280, "height": 900}), ("mobile", {"width": 375, "height": 812})]:
        for tema in ["claro", "oscuro"]:
            ctx2 = browser.new_context(storage_state=STATE_ADMIN_A, viewport=viewport)
            if tema == "oscuro":
                ctx2.add_init_script("localStorage.setItem('tema', 'oscuro');")
            page2 = ctx2.new_page()
            b2 = {}
            attach_listeners(page2, b2)
            page2.goto(f"{BASE_URL}/")
            page2.wait_for_load_state("networkidle")
            screenshot(page2, f"dashboard_{viewport_name}_{tema}.png")
            if viewport_name == "mobile":
                boton_menu_visible = page2.is_visible("#boton-menu")
                if boton_menu_visible:
                    page2.click("#boton-menu")
                    page2.wait_for_timeout(300)
                    sidebar_abierto = "abierto" in (page2.get_attribute(".sidebar", "class") or "")
                    if sidebar_abierto:
                        ok(f"Menu hamburguesa abre el sidebar en mobile ({tema})")
                    else:
                        fail(f"Menu hamburguesa no abrio el sidebar en mobile ({tema})")
                    screenshot(page2, f"dashboard_mobile_menu_abierto_{tema}.png")
                else:
                    fail(f"Boton de menu hamburguesa no visible en mobile ({tema})")
            # zoom 1.5 check
            page2.evaluate("document.body.style.zoom = 1.5")
            page2.wait_for_timeout(200)
            screenshot(page2, f"dashboard_{viewport_name}_{tema}_zoom150.png")
            if b2["console_errors"]:
                fail(f"Errores de consola en dashboard ({viewport_name}/{tema})", "; ".join(set(b2["console_errors"][:3])))
            ctx2.close()

    # Clientes en mobile dark con modal abierto (chequeo visual de que entra en pantalla)
    ctx3 = browser.new_context(storage_state=STATE_ADMIN_A, viewport={"width": 375, "height": 812})
    ctx3.add_init_script("localStorage.setItem('tema', 'oscuro');")
    page3 = ctx3.new_page()
    page3.goto(f"{BASE_URL}/clientes")
    page3.wait_for_load_state("networkidle")
    page3.click(".boton-nuevo-cliente")
    page3.wait_for_selector("#modal-cliente[open]")
    screenshot(page3, "modal_cliente_mobile_oscuro.png")
    box = page3.eval_on_selector("#modal-cliente", "el => { const r = el.getBoundingClientRect(); return {width: r.width, left: r.left, right: r.right}; }")
    info("Dimensiones del modal en mobile (375px)", box)
    if box["right"] <= 376 and box["left"] >= -1:
        ok("El modal de cliente entra dentro del ancho de pantalla mobile (375px)")
    else:
        fail("El modal de cliente se desborda del ancho de pantalla mobile", box)
    ctx3.close()

    browser.close()

print_summary()
