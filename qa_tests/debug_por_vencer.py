# -*- coding: utf-8 -*-
import sys, os, datetime
sys.path.insert(0, os.path.dirname(__file__))
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright
from helpers import BASE_URL

STATE_ADMIN_A = os.path.join(os.path.dirname(__file__), "state_admin_a.json")
hoy = datetime.date.today()
en_2_dias = (hoy + datetime.timedelta(days=2)).isoformat()
print("Fecha de hoy (segun script de prueba):", hoy.isoformat())
print("Fecha en 2 dias:", en_2_dias)

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(storage_state=STATE_ADMIN_A, viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.goto(f"{BASE_URL}/proyectos")
    page.wait_for_load_state("networkidle")
    page.click(".boton-nuevo-proyecto")
    page.wait_for_selector("#modal-proyecto[open]")
    page.fill("#modal-titulo", "QA_Proyecto PorVencer2")
    page.select_option("#modal-cliente_id", label="QA_Cliente 1")
    page.fill("#modal-fecha_entrega", en_2_dias)
    page.select_option("#modal-estado", "Pendiente")
    print("Valor del campo fecha justo antes de enviar:", page.input_value("#modal-fecha_entrega"))
    page.click("#formulario-proyecto input[type=submit]")
    page.wait_for_url(f"{BASE_URL}/proyectos", timeout=5000)
    page.wait_for_load_state("networkidle")
    fila = page.locator("tr", has=page.locator("text=QA_Proyecto PorVencer2"))
    print("HTML de la fila creada:")
    print(fila.inner_html())
    ctx.close()
    browser.close()
