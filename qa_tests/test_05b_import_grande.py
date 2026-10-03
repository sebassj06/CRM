# -*- coding: utf-8 -*-
import sys, os, time
sys.path.insert(0, os.path.dirname(__file__))
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright
from helpers import BASE_URL, ok, fail, info, print_summary

STATE_ADMIN_A = os.path.join(os.path.dirname(__file__), "state_admin_a.json")
ARCHIVOS = os.path.join(os.path.dirname(__file__), "archivos")

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(storage_state=STATE_ADMIN_A, viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.set_default_timeout(120000)
    page.goto(f"{BASE_URL}/clientes/importar")
    page.wait_for_load_state("networkidle")
    page.set_input_files("#archivo_csv", os.path.join(ARCHIVOS, "grande_500.csv"))
    t0 = time.time()
    with page.expect_navigation(timeout=120000):
        page.click("input[type=submit]")
    duracion = time.time() - t0
    flash = page.locator(".flash").all_inner_texts()
    info(f"Import de 500 filas tardo {duracion:.1f} segundos", flash)
    if duracion > 10:
        fail(f"Importar 500 clientes tarda demasiado ({duracion:.1f}s) - posible cuello de botella de performance (una conexion a BD nueva por fila)", flash)
    else:
        ok(f"Importar 500 filas es razonablemente rapido ({duracion:.1f}s)")
    ctx.close()
    browser.close()

print_summary()
