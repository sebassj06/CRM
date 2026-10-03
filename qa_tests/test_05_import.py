# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright
from helpers import BASE_URL, attach_listeners, screenshot, ok, fail, info, print_summary

STATE_DIR = os.path.dirname(__file__)
STATE_ADMIN_A = os.path.join(STATE_DIR, "state_admin_a.json")
ARCHIVOS = os.path.join(STATE_DIR, "archivos")


def importar(page, nombre_archivo):
    page.goto(f"{BASE_URL}/clientes/importar")
    page.wait_for_load_state("networkidle")
    page.set_input_files("#archivo_csv", os.path.join(ARCHIVOS, nombre_archivo))
    page.click("input[type=submit]")
    page.wait_for_load_state("networkidle")
    flash = page.locator(".flash").all_inner_texts()
    return page.url, flash


with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(storage_state=STATE_ADMIN_A, viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    b = {}
    attach_listeners(page, b)

    # 1. Import valido (headers minuscula, igual que la plantilla real)
    url, flash = importar(page, "valido_minuscula.csv")
    info("Import valido_minuscula.csv -> flash", flash)
    if any("2 clientes importados" in m or "importados: 2" in m for m in flash):
        ok("Importacion CSV valida (headers minuscula) importa las filas correctamente", flash)
    else:
        fail("Importacion CSV valida no reporto 2 importados como se esperaba", flash)

    # 2. Import con headers CAPITALIZADOS tal como dicen las instrucciones en pantalla
    url, flash = importar(page, "headers_capitalizados.csv")
    info("Import headers_capitalizados.csv -> flash", flash)
    if any("0 clientes importados" in m and "2 duplicados" not in m for m in flash) or any("2 filas inválidas" in m or "2 filas invalidas" in m for m in flash):
        fail(
            "BUG: siguiendo las instrucciones EXACTAS de la pantalla de importar (columnas 'Nombre', 'Email', etc. "
            "con mayuscula inicial), el importador falla y marca TODAS las filas como invalidas. El codigo busca "
            "las claves en minuscula ('nombre', 'email', ...) pero no normaliza el case de los encabezados reales "
            "del archivo. Ver core/importacion.py funcion importar_clientes_desde_archivo.",
            flash
        )
    else:
        ok("Import con headers capitalizados funciono correctamente (no se reprodujo el bug esperado)", flash)

    # 3. Archivo vacio (solo headers, sin filas)
    url, flash = importar(page, "vacio.csv")
    info("Import vacio.csv (solo headers) -> flash", flash)
    if any("0 clientes importados" in m for m in flash):
        ok("Import de archivo sin filas no rompe, reporta 0 importados")
    else:
        fail("Import de archivo vacio (solo headers) con comportamiento inesperado", flash)

    # 4. Archivo totalmente vacio (0 bytes)
    url, flash = importar(page, "totalmente_vacio.csv")
    info("Import totalmente_vacio.csv (0 bytes) -> url/flash", f"{url} {flash}")
    if flash:
        ok("Import de archivo de 0 bytes no causa un 500, muestra algun mensaje", flash)
    else:
        fail("Import de archivo de 0 bytes sin mensaje claro", url)

    # 5. CSV sin columna 'email'
    url, flash = importar(page, "sin_columna_email.csv")
    info("Import sin_columna_email.csv -> flash", flash)
    if any("0 clientes importados" in m for m in flash) and any("1 filas inválidas" in m or "1 filas invalidas" in m for m in flash):
        ok("Import sin columna 'email' marca la fila como invalida (no crashea)", flash)
    else:
        fail("Import sin columna email con comportamiento inesperado (revisar si crasheo)", flash)

    # 6. Duplicados + invalidos combinados
    url, flash = importar(page, "duplicados_e_invalidos.csv")
    info("Import duplicados_e_invalidos.csv -> flash", flash)
    ok("Import con mezcla de duplicados/invalidos no crashea (ver detalle)", flash)

    # Re-importar el mismo archivo para probar duplicado contra la BD (ya existe el de la primera fila)
    url, flash = importar(page, "duplicados_e_invalidos.csv")
    info("Re-import del mismo archivo (duplicados contra BD) -> flash", flash)
    if any("duplicad" in m.lower() for m in flash):
        ok("Reimportar detecta duplicados contra la base de datos")
    else:
        fail("Reimportar no reporto duplicados esperados", flash)

    # 7. Extension incorrecta
    url, flash = importar(page, "extension_incorrecta.txt")
    info("Import extension_incorrecta.txt -> flash", flash)
    if any("no soportado" in m.lower() or "csv" in m.lower() for m in flash):
        ok("Extension incorrecta (.txt) es rechazada con mensaje claro")
    else:
        fail("Extension incorrecta no fue rechazada correctamente", flash)

    # 8. XLSX valido
    url, flash = importar(page, "valido.xlsx")
    info("Import valido.xlsx -> flash", flash)
    if any("1 clientes importados" in m or "importados: 1" in m for m in flash):
        ok("Importacion de archivo .xlsx funciona correctamente")
    else:
        fail("Importacion .xlsx no funciono como se esperaba", flash)

    # 9. Archivo grande (500 filas)
    import time
    t0 = time.time()
    url, flash = importar(page, "grande_500.csv")
    duracion = time.time() - t0
    info(f"Import grande_500.csv (500 filas) tardo {duracion:.1f}s -> flash", flash)
    if any("500 clientes importados" in m or "importados: 500" in m for m in flash):
        ok(f"Importacion de archivo grande (500 filas) funciona (tardo {duracion:.1f}s)")
    else:
        fail("Importacion de archivo grande no reporto 500 importados", flash)

    if b["bad_responses"]:
        fail("Respuestas HTTP 4xx/5xx durante pruebas de importacion", "; ".join(set(b["bad_responses"])))

    ctx.close()
    browser.close()

print_summary()
