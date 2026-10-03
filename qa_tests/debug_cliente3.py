import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from playwright.sync_api import sync_playwright
from helpers import BASE_URL

STATE_ADMIN_A = os.path.join(os.path.dirname(__file__), "state_admin_a.json")

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(storage_state=STATE_ADMIN_A, viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.goto(f"{BASE_URL}/clientes")
    page.wait_for_load_state("networkidle")

    page.click(".boton-nuevo-cliente")
    page.wait_for_selector("#modal-cliente[open]")
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)
    print("Tras Esc, abierto?:", page.get_attribute("#modal-cliente", "open") is not None)

    page.click(".boton-nuevo-cliente")
    page.wait_for_selector("#modal-cliente[open]")
    page.mouse.click(5, 5)
    page.wait_for_timeout(300)
    print("Tras click afuera, abierto?:", page.get_attribute("#modal-cliente", "open") is not None)

    page.click(".boton-nuevo-cliente")
    page.wait_for_selector("#modal-cliente[open]")
    page.click("#boton-cancelar-modal-cliente")
    page.wait_for_timeout(300)
    print("Tras Cancelar, abierto?:", page.get_attribute("#modal-cliente", "open") is not None)

    ctx.close()
    browser.close()
