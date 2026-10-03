import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from playwright.sync_api import sync_playwright
from helpers import BASE_URL, PASSWORD, USERS, login, attach_listeners, screenshot, ok, fail, info, print_summary

with sync_playwright() as p:
    browser = p.chromium.launch()

    # --- 1. Login con credenciales incorrectas ---
    ctx = browser.new_context()
    page = ctx.new_page()
    bucket = {}
    attach_listeners(page, bucket)
    page.goto(f"{BASE_URL}/login")
    page.fill("#nombre_usuario", "QA_admin_a")
    page.fill("#contraseña", "clave-incorrecta")
    page.click("input[type=submit]")
    page.wait_for_load_state("networkidle")
    if "Usuario o contraseña incorrectos" in page.content():
        ok("Login credenciales incorrectas muestra mensaje de error")
    else:
        fail("Login credenciales incorrectas", f"url={page.url}, no aparecio el mensaje esperado")
    if page.url.rstrip("/") == f"{BASE_URL}/login":
        ok("Login incorrecto permanece en /login (no redirige)")
    else:
        fail("Login incorrecto redirige a otra URL", page.url)

    # --- 2. Campos vacios ---
    page.goto(f"{BASE_URL}/login")
    page.click("input[type=submit]")
    page.wait_for_load_state("networkidle")
    info("Login campos vacios -> status url", page.url)
    if "incorrectos" in page.content() or page.url.endswith("/login"):
        ok("Login con campos vacios no rompe (se queda en login o muestra error)")
    else:
        fail("Login con campos vacios", "comportamiento inesperado")

    # --- 3. Toggle de password en login ---
    page.goto(f"{BASE_URL}/login")
    page.fill("#contraseña", "algo123")
    tipo_antes = page.eval_on_selector("#contraseña", "el => el.type")
    page.click(".boton-ver-password")
    tipo_despues = page.eval_on_selector("#contraseña", "el => el.type")
    if tipo_antes == "password" and tipo_despues == "text":
        ok("Toggle mostrar/ocultar contraseña en login funciona")
    else:
        fail("Toggle de password en login", f"antes={tipo_antes} despues={tipo_despues}")

    # --- 4. Acceder a ruta protegida sin sesion ---
    ctx_anon = browser.new_context()
    page_anon = ctx_anon.new_page()
    resp = page_anon.goto(f"{BASE_URL}/clientes")
    page_anon.wait_for_load_state("networkidle")
    if page_anon.url.rstrip("/") == f"{BASE_URL}/login":
        ok("Acceso a /clientes sin sesion redirige a /login")
    else:
        fail("Acceso a /clientes sin sesion", f"termino en {page_anon.url}")

    for ruta_protegida in ["/usuarios", "/configuracion", "/proyectos", "/pagos", "/notas", "/perfil", "/buscar"]:
        page_anon.goto(f"{BASE_URL}{ruta_protegida}")
        page_anon.wait_for_load_state("networkidle")
        if page_anon.url.rstrip("/") == f"{BASE_URL}/login":
            ok(f"Ruta protegida {ruta_protegida} sin sesion redirige a login")
        else:
            fail(f"Ruta protegida {ruta_protegida} sin sesion", f"termino en {page_anon.url}")
    ctx_anon.close()

    # --- 5. Login correcto para cada usuario QA ---
    for key, username in USERS.items():
        ctx_u = browser.new_context()
        page_u = ctx_u.new_page()
        b = {}
        attach_listeners(page_u, b)
        login(page_u, username)
        if page_u.url.rstrip("/") == BASE_URL + "/" or page_u.url.rstrip("/") == BASE_URL:
            ok(f"Login correcto para {username} llega al dashboard")
        else:
            fail(f"Login correcto para {username}", f"termino en {page_u.url}")
        if b["console_errors"]:
            fail(f"Errores de consola en dashboard tras login ({username})", "; ".join(b["console_errors"][:3]))
        if b["bad_responses"]:
            fail(f"Respuestas HTTP 4xx/5xx en dashboard tras login ({username})", "; ".join(b["bad_responses"][:5]))
        # Guardar storage_state para otros scripts
        ctx_u.storage_state(path=os.path.join(os.path.dirname(__file__), f"state_{key}.json"))
        ctx_u.close()

    # --- 6. Logout y volver atras ---
    ctx_lo = browser.new_context()
    page_lo = ctx_lo.new_page()
    login(page_lo, USERS["admin_a"])
    page_lo.goto(f"{BASE_URL}/logout")
    page_lo.wait_for_load_state("networkidle")
    if page_lo.url.rstrip("/") == f"{BASE_URL}/login":
        ok("Logout redirige a /login")
    else:
        fail("Logout no redirige a /login", page_lo.url)
    page_lo.go_back()
    page_lo.wait_for_load_state("networkidle")
    info("Despues de logout, boton atras lleva a", page_lo.url)
    # Intentar acceder de nuevo a una ruta protegida tras logout
    page_lo.goto(f"{BASE_URL}/clientes")
    page_lo.wait_for_load_state("networkidle")
    if page_lo.url.rstrip("/") == f"{BASE_URL}/login":
        ok("Tras logout, /clientes vuelve a pedir login (sesion invalidada)")
    else:
        fail("Tras logout, /clientes NO redirige a login (sesion no invalidada?)", page_lo.url)
    ctx_lo.close()

    # --- 7. Pagina 404 ---
    ctx_404 = browser.new_context(storage_state=os.path.join(os.path.dirname(__file__), "state_admin_a.json"))
    page_404 = ctx_404.new_page()
    resp = page_404.goto(f"{BASE_URL}/esta-ruta-no-existe-qa")
    page_404.wait_for_load_state("networkidle")
    if resp.status == 404:
        ok("Ruta inexistente devuelve status 404")
    else:
        fail("Ruta inexistente no devuelve 404", f"status={resp.status}")
    if "Página no encontrada" in page_404.content() or "no encontrada" in page_404.content().lower():
        ok("Pagina 404 muestra mensaje amigable")
    else:
        fail("Pagina 404 sin mensaje amigable", page_404.content()[:200])
    screenshot(page_404, "404_page.png")

    # 404 con ID inexistente
    resp2 = page_404.goto(f"{BASE_URL}/clientes/999999")
    page_404.wait_for_load_state("networkidle")
    info("GET /clientes/999999 (id inexistente) -> status/url", f"{resp2.status} {page_404.url}")
    ctx_404.close()

    browser.close()

print_summary()
