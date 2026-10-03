import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from playwright.sync_api import sync_playwright
from helpers import BASE_URL, attach_listeners, screenshot, ok, fail, info, print_summary

STATE_DIR = os.path.dirname(__file__)
STATE_ADMIN_A = os.path.join(STATE_DIR, "state_admin_a.json")
STATE_MIEMBRO_A = os.path.join(STATE_DIR, "state_miembro_a.json")
STATE_ADMIN_B = os.path.join(STATE_DIR, "state_admin_b.json")

creado_ids = {}

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ============ ADMIN A: CRUD + validaciones ============
    ctx = browser.new_context(storage_state=STATE_ADMIN_A, viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    b = {}
    attach_listeners(page, b)
    page.goto(f"{BASE_URL}/clientes")
    page.wait_for_load_state("networkidle")

    dialogs = []
    page.on("dialog", lambda d: (dialogs.append(d.message), d.accept()))

    # --- Abrir modal nuevo cliente ---
    page.click(".boton-nuevo-cliente")
    try:
        page.wait_for_selector("#modal-cliente[open]", timeout=2000)
        ok("Modal 'Nuevo cliente' se abre al hacer click")
    except Exception as e:
        fail("Modal 'Nuevo cliente' no se abrio", str(e))

    # --- Submit vacio: campos obligatorios ---
    page.click("#formulario-cliente input[type=submit]")
    try:
        page.wait_for_selector("#modal-cliente-error:not([hidden])", timeout=3000)
        texto_error = page.inner_text("#modal-cliente-error")
        ok("Validacion de campos obligatorios (nombre/email vacios)", texto_error)
    except Exception as e:
        fail("No aparecio error inline por campos vacios", str(e))
    if page.is_visible("#modal-cliente[open]"):
        ok("El modal sigue abierto tras el error de validacion (no te saca del modal)")
    else:
        fail("El modal se cerro tras el error de validacion (deberia quedarse abierto)")

    # --- Email invalido ---
    page.fill("#modal-nombre", "QA_Cliente EmailInvalido")
    page.fill("#modal-email", "esto-no-es-un-email")
    page.click("#formulario-cliente input[type=submit]")
    try:
        page.wait_for_selector("#modal-cliente-error:not([hidden])", timeout=3000)
        texto_error = page.inner_text("#modal-cliente-error")
        if "email" in texto_error.lower() or "formato" in texto_error.lower():
            ok("Validacion de email invalido (sin @)", texto_error)
        else:
            fail("Mensaje de error no menciona el email", texto_error)
    except Exception as e:
        fail("No aparecio error por email invalido", str(e))

    # --- Crear cliente valido ---
    page.fill("#modal-nombre", "QA_Cliente 1")
    page.fill("#modal-email", "qa_cliente1@test.com")
    page.fill("#modal-empresa", "QA Empresa")
    page.click("#formulario-cliente input[type=submit]")
    try:
        page.wait_for_url(f"{BASE_URL}/clientes", timeout=5000)
        page.wait_for_load_state("networkidle")
        if page.locator("text=QA_Cliente 1").first.is_visible():
            ok("Cliente valido creado y aparece en la lista")
        else:
            fail("Cliente creado pero no aparece en la lista")
    except Exception as e:
        fail("Error al crear cliente valido", str(e))

    # --- Email duplicado ---
    page.click(".boton-nuevo-cliente")
    page.wait_for_selector("#modal-cliente[open]")
    page.fill("#modal-nombre", "QA_Cliente Duplicado")
    page.fill("#modal-email", "qa_cliente1@test.com")
    page.click("#formulario-cliente input[type=submit]")
    try:
        page.wait_for_selector("#modal-cliente-error:not([hidden])", timeout=3000)
        texto_error = page.inner_text("#modal-cliente-error")
        if "ya existe" in texto_error.lower() or "duplicad" in texto_error.lower():
            ok("Email duplicado detectado con error inline en el modal", texto_error)
        else:
            fail("Error de duplicado con texto inesperado", texto_error)
    except Exception as e:
        fail("No se detecto email duplicado al crear cliente", str(e))
    page.keyboard.press("Escape")

    # --- Cerrar modal con Esc ---
    page.click(".boton-nuevo-cliente")
    page.wait_for_selector("#modal-cliente[open]")
    page.keyboard.press("Escape")
    try:
        page.wait_for_selector("#modal-cliente:not([open])", timeout=2000)
        ok("Esc cierra el modal de cliente")
    except Exception as e:
        fail("Esc no cerro el modal de cliente", str(e))

    # --- Cerrar modal con click afuera ---
    page.click(".boton-nuevo-cliente")
    page.wait_for_selector("#modal-cliente[open]")
    page.mouse.click(5, 5)
    try:
        page.wait_for_selector("#modal-cliente:not([open])", timeout=2000)
        ok("Click afuera del modal (backdrop) lo cierra")
    except Exception as e:
        fail("Click afuera no cerro el modal", str(e))

    # --- Cancelar ---
    page.click(".boton-nuevo-cliente")
    page.wait_for_selector("#modal-cliente[open]")
    page.fill("#modal-nombre", "no deberia guardarse")
    page.click("#boton-cancelar-modal-cliente")
    try:
        page.wait_for_selector("#modal-cliente:not([open])", timeout=2000)
        ok("Boton Cancelar cierra el modal")
    except Exception as e:
        fail("Cancelar no cerro el modal", str(e))
    page.reload()
    page.wait_for_load_state("networkidle")
    if page.locator("text=no deberia guardarse").count() == 0:
        ok("Cancelar no guardo datos (no aparece el cliente cancelado)")
    else:
        fail("Cancelar SI guardo datos (bug)")

    # --- XSS / caracteres especiales / texto largo ---
    page.click(".boton-nuevo-cliente")
    page.wait_for_selector("#modal-cliente[open]")
    nombre_xss = "<script>window.__qa_xss_ejecutado = true;</script>QA_XSS_ñáé 😀"
    page.fill("#modal-nombre", nombre_xss)
    page.fill("#modal-email", "qa_xss@test.com")
    page.fill("#modal-notas", "Notas con comillas \"dobles\" y 'simples' y <b>html</b>")
    page.click("#formulario-cliente input[type=submit]")
    page.wait_for_url(f"{BASE_URL}/clientes", timeout=5000)
    page.wait_for_load_state("networkidle")
    ejecutado = page.evaluate("window.__qa_xss_ejecutado === true")
    if ejecutado:
        fail("XSS SE EJECUTO al crear cliente con <script> en el nombre", "CRITICO: posible XSS almacenado")
    else:
        ok("El <script> en el nombre del cliente NO se ejecuto (se escapa correctamente)")
    if page.locator(f"text={nombre_xss}").count() > 0 or "QA_XSS_" in page.content():
        ok("Texto con caracteres especiales/acentos/emoji se guarda y muestra como texto")
    else:
        info("No se encontro el texto XSS literal en la lista (revisar manualmente)")

    # --- Buscador ---
    page.fill("#buscador-clientes", "qa_cliente 1")
    page.wait_for_timeout(300)
    filas_visibles = page.locator("#tabla-clientes tbody tr:visible").count()
    if filas_visibles >= 1:
        ok("Buscador encuentra resultados en minusculas/con espacio", f"{filas_visibles} filas")
    else:
        fail("Buscador no encontro 'QA_Cliente 1' en minusculas")
    page.fill("#buscador-clientes", "ZZZNOEXISTEZZZ")
    page.wait_for_timeout(300)
    if page.is_visible("#estado-sin-resultados"):
        ok("Buscador muestra estado 'sin resultados' para busqueda sin coincidencias")
    else:
        fail("Buscador no muestra estado vacio para busqueda sin coincidencias")
    page.fill("#buscador-clientes", "")
    page.wait_for_timeout(200)

    # --- Editar cliente desde la lista (boton icono) ---
    fila_qa1 = page.locator("tr", has=page.locator("text=QA_Cliente 1")).first
    fila_qa1.locator(".boton-editar-cliente").click()
    try:
        page.wait_for_selector("#modal-cliente[open]", timeout=2000)
        titulo = page.inner_text("#modal-cliente-titulo")
        if "Editar" in titulo:
            ok("Modal de edicion abre con titulo correcto y datos precargados", titulo)
        valor_nombre = page.input_value("#modal-nombre")
        if valor_nombre == "QA_Cliente 1":
            ok("Modal de edicion precarga el nombre correcto")
        else:
            fail("Modal de edicion no precargo el nombre correcto", valor_nombre)
    except Exception as e:
        fail("No se pudo abrir modal de edicion desde la lista", str(e))

    # --- Telefono: pais Argentina (10 digitos), ingresar solo 5 ---
    page.select_option("#modal-telefono-prefijo", "+54")
    page.fill("#modal-telefono-numero", "12345")
    page.click("#formulario-cliente input[type=submit]")
    try:
        page.wait_for_selector("#modal-cliente-error:not([hidden])", timeout=2000)
        texto_error = page.inner_text("#modal-cliente-error")
        if "numeros" in texto_error.lower() or "número" in texto_error.lower() or "10" in texto_error:
            ok("Validacion de cantidad de digitos de telefono segun pais (Argentina, incompleto)", texto_error)
        else:
            fail("Error de telefono con texto inesperado", texto_error)
    except Exception as e:
        fail("No se valido la cantidad de digitos del telefono", str(e))

    page.fill("#modal-telefono-numero", "1123456789")
    page.click("#formulario-cliente input[type=submit]")
    try:
        page.wait_for_url(f"{BASE_URL}/clientes", timeout=5000)
        ok("Telefono con la cantidad correcta de digitos se guarda sin error")
    except Exception as e:
        fail("Fallo al guardar telefono con digitos correctos", str(e))
    page.wait_for_load_state("networkidle")

    # Guardar el id del cliente QA_Cliente 1 para pruebas de aislamiento multi-tenant
    href = page.locator("a:has-text('QA_Cliente 1')").first.get_attribute("href")
    if href:
        creado_ids["cliente_a"] = href.rstrip("/").split("/")[-1]
        info("ID de QA_Cliente 1 (agencia A)", creado_ids["cliente_a"])

    if b["console_errors"]:
        fail("Errores de consola durante pruebas de clientes (admin A)", "; ".join(set(b["console_errors"][:5])))
    if b["bad_responses"]:
        bad = [x for x in b["bad_responses"] if "400" not in x]  # 400 esperado por validaciones
        if bad:
            fail("Respuestas HTTP inesperadas durante pruebas de clientes", "; ".join(set(bad[:5])))

    screenshot(page, "clientes_admin_a_desktop_light.png")
    ctx.close()

    with open(os.path.join(STATE_DIR, "ids_compartidos.json"), "w") as f:
        json.dump(creado_ids, f)

    browser.close()

print_summary()
