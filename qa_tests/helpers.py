"""Helpers compartidos para los scripts de QA con Playwright. Local only."""
import os
import re
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:5000"
PASSWORD = "QA_Pass123!"

USERS = {
    "admin_a": "QA_admin_a",
    "miembro_a": "QA_miembro_a",
    "admin_b": "QA_admin_b",
    "miembro_b": "QA_miembro_b",
}

CAPTURAS_DIR = os.path.join(os.path.dirname(__file__), "capturas")
os.makedirs(CAPTURAS_DIR, exist_ok=True)

RESULTS = []


def ok(label, detail=""):
    detail = str(detail)
    RESULTS.append(("PASS", label, detail))
    print(f"[PASS] {label} {('- ' + detail) if detail else ''}")


def fail(label, detail=""):
    detail = str(detail)
    RESULTS.append(("FAIL", label, detail))
    print(f"[FAIL] {label} {('- ' + detail) if detail else ''}")


def info(label, detail=""):
    detail = str(detail)
    print(f"[INFO] {label} {('- ' + detail) if detail else ''}")


def attach_listeners(page, bucket):
    """Acumula errores de consola y respuestas de red fallidas (4xx/5xx) en `bucket` (dict con listas)."""
    bucket.setdefault("console_errors", [])
    bucket.setdefault("bad_responses", [])
    bucket.setdefault("page_errors", [])

    def on_console(msg):
        if msg.type == "error":
            bucket["console_errors"].append(f"{page.url} :: {msg.text}")

    def on_response(resp):
        try:
            if resp.status >= 400:
                bucket["bad_responses"].append(f"{resp.status} {resp.url}")
        except Exception:
            pass

    def on_pageerror(exc):
        bucket["page_errors"].append(f"{page.url} :: {exc}")

    page.on("console", on_console)
    page.on("response", on_response)
    page.on("pageerror", on_pageerror)


def login(page, username, password=PASSWORD):
    page.goto(f"{BASE_URL}/login")
    page.fill("#nombre_usuario", username)
    page.fill("#contraseña", password)
    page.click("input[type=submit]")
    page.wait_for_load_state("networkidle")
    return page.url


def new_context(browser, viewport=None, dark=False, storage_state=None):
    viewport = viewport or {"width": 1280, "height": 900}
    ctx = browser.new_context(viewport=viewport, storage_state=storage_state)
    if dark:
        ctx.add_init_script("localStorage.setItem('tema', 'oscuro');")
    return ctx


def screenshot(page, name):
    path = os.path.join(CAPTURAS_DIR, name)
    page.screenshot(path=path, full_page=True)
    return path


def print_summary():
    passed = sum(1 for r in RESULTS if r[0] == "PASS")
    failed = sum(1 for r in RESULTS if r[0] == "FAIL")
    print(f"\n==== RESUMEN: {passed} PASS, {failed} FAIL ====")
    for status, label, detail in RESULTS:
        if status == "FAIL":
            print(f"  FAIL: {label} -- {detail}")
