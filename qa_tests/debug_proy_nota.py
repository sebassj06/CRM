# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright
from helpers import BASE_URL

STATE_ADMIN_A = os.path.join(os.path.dirname(__file__), "state_admin_a.json")

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(storage_state=STATE_ADMIN_A, viewport={"width": 1280, "height": 900})
    page = ctx.new_page()

    page.goto(f"{BASE_URL}/proyectos")
    page.wait_for_load_state("networkidle")
    filas = page.locator("#tabla-proyectos tbody tr").all_text_contents()
    print("Filas de proyectos:")
    for f in filas:
        print("  ->", " | ".join(x.strip() for x in f.split("\n") if x.strip()))
    print("Cantidad total con etiqueta-por-vencer:", page.locator(".etiqueta-por-vencer").count())
    print("Paginacion presente:", page.locator(".paginacion").count())

    page.goto(f"{BASE_URL}/notas")
    page.wait_for_load_state("networkidle")
    filas_n = page.locator("#tabla-notas tbody tr").all_text_contents()
    print("\nCantidad de filas de notas:", len(filas_n))
    for f in filas_n:
        print("  NOTA ->", " | ".join(x.strip() for x in f.split("\n") if x.strip())[:150])
    print("Paginacion notas:", page.locator(".paginacion").count())
    print("Total registros (texto paginacion):", page.locator(".paginacion").inner_text() if page.locator(".paginacion").count() else "N/A")

    ctx.close()
    browser.close()
