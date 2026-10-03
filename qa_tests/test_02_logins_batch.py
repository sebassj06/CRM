"""Hace login para los 4 usuarios QA en 2 tandas de 2 (el rate limit de /login
es 5/min y cuenta tanto GET como POST sobre /login, asi que cada login real
consume 2 peticiones contra ese endpoint)."""
import sys, os, time
sys.path.insert(0, os.path.dirname(__file__))
from playwright.sync_api import sync_playwright
from helpers import BASE_URL, USERS, login, attach_listeners, ok, fail, info, print_summary

TANDAS = [["admin_a", "miembro_a"], ["admin_b", "miembro_b"]]

with sync_playwright() as p:
    browser = p.chromium.launch()
    for i, tanda in enumerate(TANDAS):
        for key in tanda:
            username = USERS[key]
            ctx = browser.new_context()
            page = ctx.new_page()
            b = {}
            attach_listeners(page, b)
            login(page, username)
            if page.url.rstrip("/") == BASE_URL:
                ok(f"Login correcto para {username} llega al dashboard")
            else:
                fail(f"Login correcto para {username}", f"termino en {page.url} contenido={page.content()[:200]}")
            if b["console_errors"]:
                fail(f"Errores de consola en dashboard ({username})", "; ".join(b["console_errors"][:3]))
            if b["bad_responses"]:
                fail(f"Respuestas HTTP 4xx/5xx en dashboard ({username})", "; ".join(b["bad_responses"][:5]))
            ctx.storage_state(path=os.path.join(os.path.dirname(__file__), f"state_{key}.json"))
            ctx.close()
        if i < len(TANDAS) - 1:
            info("Esperando a que se libere el rate limit de /login antes de la siguiente tanda...")
            import urllib.request
            for _ in range(40):
                try:
                    r = urllib.request.urlopen(f"{BASE_URL}/login")
                    if r.status == 200:
                        break
                except Exception:
                    pass
                time.sleep(3)
    browser.close()

print_summary()
