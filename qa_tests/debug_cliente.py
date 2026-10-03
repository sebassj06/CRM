import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from playwright.sync_api import sync_playwright
from helpers import BASE_URL

STATE_ADMIN_A = os.path.join(os.path.dirname(__file__), "state_admin_a.json")

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(storage_state=STATE_ADMIN_A, viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.on("console", lambda m: print("CONSOLE:", m.type, m.text))
    page.on("requestfinished", lambda r: print("REQ:", r.method, r.url) if "clientes" in r.url and r.method == "POST" else None)
    page.goto(f"{BASE_URL}/clientes")
    page.wait_for_load_state("networkidle")

    page.click(".boton-nuevo-cliente")
    page.wait_for_selector("#modal-cliente[open]")
    page.fill("#modal-nombre", "QA_Debug Nombre")
    page.fill("#modal-email", "esto-no-es-un-email")
    print("Valor nombre antes de submit:", page.input_value("#modal-nombre"))
    print("Valor email antes de submit:", page.input_value("#modal-email"))

    # Interceptar el request para ver el body real que se envia
    def on_request(req):
        if req.method == "POST" and "clientes/nuevo" in req.url:
            print("POST BODY:", req.post_data)
    page.on("request", on_request)

    page.click("#formulario-cliente input[type=submit]")
    page.wait_for_timeout(1500)
    print("Error visible:", page.is_visible("#modal-cliente-error"))
    print("Texto error:", page.inner_text("#modal-cliente-error") if page.is_visible("#modal-cliente-error") else None)

    # Ahora revisemos la lista completa de clientes y paginacion
    page.goto(f"{BASE_URL}/clientes")
    page.wait_for_load_state("networkidle")
    filas = page.locator("#tabla-clientes tbody tr").all_text_contents()
    print("Cantidad de filas en tabla:", len(filas))
    for f in filas:
        print("FILA:", f[:120])
    paginacion_visible = page.locator(".paginacion").count()
    print("Elementos de paginacion:", paginacion_visible)

    ctx.close()
    browser.close()
