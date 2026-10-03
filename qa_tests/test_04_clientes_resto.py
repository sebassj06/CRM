# -*- coding: utf-8 -*-
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright
from helpers import BASE_URL, attach_listeners, screenshot, ok, fail, info, print_summary

STATE_DIR = os.path.dirname(__file__)
STATE_ADMIN_A = os.path.join(STATE_DIR, "state_admin_a.json")
STATE_MIEMBRO_A = os.path.join(STATE_DIR, "state_miembro_a.json")
STATE_ADMIN_B = os.path.join(STATE_DIR, "state_admin_b.json")

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(storage_state=STATE_ADMIN_A, viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    b = {}
    attach_listeners(page, b)
    page.goto(f"{BASE_URL}/clientes")
    page.wait_for_load_state("networkidle")

    # --- Buscador: mayusculas/minusculas y acentos ---
    page.fill("#buscador-clientes", "QA_CLIENTE 1")
    page.wait_for_timeout(300)
    visibles = page.locator("#tabla-clientes tbody tr:visible").count()
    if visibles >= 1:
        ok("Buscador funciona con MAYUSCULAS")
    else:
        fail("Buscador no encontro resultado en mayusculas para 'QA_CLIENTE 1'")
    page.fill("#buscador-clientes", "")
    page.wait_for_timeout(200)

    # --- Acceso directo a /clientes/nuevo ---
    page.goto(f"{BASE_URL}/clientes/nuevo")
    page.wait_for_load_state("networkidle")
    if page.url.rstrip("/") == f"{BASE_URL}/clientes" and page.get_attribute("#modal-cliente", "open") is not None:
        ok("GET /clientes/nuevo redirige a /clientes y abre el modal automaticamente")
    else:
        fail("GET /clientes/nuevo no abrio el modal en /clientes", page.url)
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)

    # --- Acceso directo a /clientes/<id>/editar ---
    href = page.locator("a:has-text('QA_Cliente 1')").first.get_attribute("href")
    cliente_id = href.rstrip("/").split("/")[-1]
    page.goto(f"{BASE_URL}/clientes/{cliente_id}/editar")
    page.wait_for_load_state("networkidle")
    if page.url.rstrip("/") == f"{BASE_URL}/clientes" and page.get_attribute("#modal-cliente", "open") is not None:
        valor = page.input_value("#modal-nombre")
        ok("GET /clientes/<id>/editar redirige a /clientes y abre el modal con datos", valor)
    else:
        fail("GET /clientes/<id>/editar no abrio el modal correctamente", page.url)
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)

    with open(os.path.join(STATE_DIR, "ids_compartidos.json")) as f:
        ids = json.load(f)
    ids["cliente_a"] = cliente_id
    with open(os.path.join(STATE_DIR, "ids_compartidos.json"), "w") as f:
        json.dump(ids, f)

    # --- Exportar clientes ---
    with page.expect_download() as dl_info:
        page.click("a:has-text('Exportar')")
    download = dl_info.value
    ok("Exportar clientes dispara una descarga", download.suggested_filename)

    # --- Detalle de cliente: secciones proyectos/notas/IA ---
    page.goto(f"{BASE_URL}/clientes/{cliente_id}")
    page.wait_for_load_state("networkidle")
    if page.locator("text=Proyectos").count() > 0 and page.locator("text=Historial de notas").count() > 0:
        ok("Detalle de cliente muestra secciones de Proyectos y Notas")
    else:
        fail("Detalle de cliente no muestra las secciones esperadas")
    if page.locator("text=Resumen con IA").count() > 0:
        ok("Detalle de cliente muestra la seccion de Resumen con IA")
    else:
        fail("Detalle de cliente no muestra seccion de IA")

    # --- Editar desde el detalle (debe abrir modal ahi mismo, no navegar a /clientes) ---
    page.click(".boton-editar-cliente")
    page.wait_for_timeout(300)
    if page.get_attribute("#modal-cliente", "open") is not None and page.url.rstrip("/") == f"{BASE_URL}/clientes/{cliente_id}":
        ok("Editar desde el detalle de cliente abre el modal SIN navegar al listado")
    else:
        fail("Editar desde el detalle de cliente no se comporto como se esperaba", page.url)
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)

    screenshot(page, "cliente_detalle_admin_a.png")

    if b["console_errors"]:
        fail("Errores de consola (resto de pruebas de clientes)", "; ".join(set(b["console_errors"][:5])))

    ctx.close()

    # ============ MIEMBRO: no debe ver boton eliminar ============
    ctx_m = browser.new_context(storage_state=STATE_MIEMBRO_A, viewport={"width": 1280, "height": 900})
    page_m = ctx_m.new_page()
    page_m.goto(f"{BASE_URL}/clientes")
    page_m.wait_for_load_state("networkidle")
    eliminar_visible = page_m.locator("form.form-eliminar button").count()
    if eliminar_visible == 0:
        ok("Miembro NO ve boton de Eliminar en la lista de clientes")
    else:
        fail("Miembro SI ve boton de Eliminar en clientes (deberia estar oculto)", str(eliminar_visible))

    # Miembro intenta POST directo a eliminar (sin boton visible, pero probamos la ruta)
    resp = page_m.request.post(f"{BASE_URL}/clientes/{cliente_id}/eliminar", data={})
    info("POST directo a /clientes/<id>/eliminar como miembro -> status", str(resp.status))
    if resp.status in (302, 303):
        # Verificar que redirige a inicio con flash de error, no que borra
        pass
    page_m.goto(f"{BASE_URL}/clientes/{cliente_id}")
    page_m.wait_for_load_state("networkidle")
    if "QA_Cliente 1" in page_m.content() or cliente_id in page_m.url:
        ok("Cliente NO fue eliminado por el POST directo de un miembro (proteccion admin_requerido funciona)")
    else:
        fail("El cliente parece haber sido eliminado por un miembro via POST directo (CRITICO)")
    ctx_m.close()

    # ============ ADMIN B: aislamiento multi-tenant ============
    ctx_b = browser.new_context(storage_state=STATE_ADMIN_B, viewport={"width": 1280, "height": 900})
    page_b = ctx_b.new_page()
    page_b.goto(f"{BASE_URL}/clientes/{cliente_id}")
    page_b.wait_for_load_state("networkidle")
    contenido_b = page_b.content()
    if "QA_Cliente 1" in contenido_b or "qa_cliente1@test.com" in contenido_b:
        fail("CRITICO: Admin de Agencia B puede ver datos del cliente de Agencia A via URL directa", f"id={cliente_id}")
    else:
        ok("Admin de Agencia B NO puede ver el cliente de Agencia A via URL directa (aislamiento OK)")
    page_b.goto(f"{BASE_URL}/clientes")
    page_b.wait_for_load_state("networkidle")
    if "QA_Cliente 1" in page_b.content():
        fail("CRITICO: El cliente de la Agencia A aparece en la lista de clientes de la Agencia B")
    else:
        ok("La lista de clientes de Agencia B no incluye clientes de Agencia A")
    ctx_b.close()

    browser.close()

print_summary()
