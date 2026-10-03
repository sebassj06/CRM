# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright
from helpers import BASE_URL, ok, fail, info, print_summary

STATE_ADMIN_A = os.path.join(os.path.dirname(__file__), "state_admin_a.json")

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(storage_state=STATE_ADMIN_A, viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.goto(f"{BASE_URL}/usuarios")
    page.wait_for_load_state("networkidle")
    csrf = page.eval_on_selector("input[name=csrf_token]", "el => el.value")

    # ID de QA_admin_a (unico admin de la agencia A en este momento)
    import json
    resp = page.request.get(f"{BASE_URL}/usuarios")
    # Sacamos el id del propio usuario desde la sesion/cookie no es trivial; lo buscamos por nombre via la tabla usuarios
    from core.usuarios import obtener_usuario_por_nombre
    admin_id = obtener_usuario_por_nombre("QA_admin_a")[0]

    resp = page.request.post(f"{BASE_URL}/usuarios/{admin_id}/eliminar", form={"csrf_token": csrf})
    info("POST directo para eliminar al propio admin (unico admin) -> status", resp.status)
    page.goto(f"{BASE_URL}/usuarios")
    page.wait_for_load_state("networkidle")
    if page.locator("text=QA_admin_a").count() > 0:
        ok("El unico admin de la agencia NO pudo ser eliminado via POST directo (protegido)")
    else:
        fail("CRITICO: el unico admin de la agencia fue eliminado via POST directo (bypass de la UI)")

    ctx.close()
    browser.close()

print_summary()
