# -*- coding: utf-8 -*-
import sys, os, io
sys.path.insert(0, os.path.dirname(__file__))
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright
from helpers import BASE_URL

STATE_ADMIN_A = os.path.join(os.path.dirname(__file__), "state_admin_a.json")

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(storage_state=STATE_ADMIN_A, viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.goto(f"{BASE_URL}/clientes")
    page.wait_for_load_state("networkidle")

    # Caso: email que pasa la validacion nativa del navegador (tiene @ y texto a ambos lados)
    # pero NO pasa la regex del servidor (le falta el punto/TLD): "qa@test"
    page.click(".boton-nuevo-cliente")
    page.wait_for_selector("#modal-cliente[open]")
    page.fill("#modal-nombre", "QA_EmailSinPunto")
    page.fill("#modal-email", "qa@test")
    page.click("#formulario-cliente input[type=submit]")
    page.wait_for_timeout(1500)
    print("CASE qa@test -> error visible:", page.is_visible("#modal-cliente-error"))
    if page.is_visible("#modal-cliente-error"):
        print("CASE qa@test -> texto:", page.inner_text("#modal-cliente-error"))
    print("CASE qa@test -> modal sigue abierto:", page.get_attribute("#modal-cliente", "open") is not None)
    print("CASE qa@test -> url actual:", page.url)

    # Verificar si el navegador bloqueo el submit via validez nativa
    es_valido_nativo = page.eval_on_selector("#modal-email", "el => el.checkValidity()")
    print("CASE qa@test -> checkValidity() nativo del input email:", es_valido_nativo)

    page.keyboard.press("Escape")
    page.wait_for_timeout(300)

    # Caso: email totalmente malformado "esto-no-es-un-email" (sin @) - confirmar que el navegador lo bloquea
    page.click(".boton-nuevo-cliente")
    page.wait_for_selector("#modal-cliente[open]")
    page.fill("#modal-nombre", "QA_SinArroba")
    page.fill("#modal-email", "esto-no-es-un-email")
    es_valido_nativo2 = page.eval_on_selector("#modal-email", "el => el.checkValidity()")
    print("CASE sin-arroba -> checkValidity() nativo:", es_valido_nativo2)
    mensaje_validacion = page.eval_on_selector("#modal-email", "el => el.validationMessage")
    print("CASE sin-arroba -> validationMessage nativo del navegador:", mensaje_validacion)

    ctx.close()
    browser.close()
