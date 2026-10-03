# -*- coding: utf-8 -*-
"""Genera archivos CSV/XLSX de prueba para QA de importacion de clientes."""
import csv
import os
import openpyxl

DIR = os.path.join(os.path.dirname(__file__), "archivos")
os.makedirs(DIR, exist_ok=True)

# 1. CSV valido con headers EN MINUSCULA (igual que la plantilla real que genera el sistema)
with open(os.path.join(DIR, "valido_minuscula.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["nombre", "email", "telefono", "empresa", "notas", "cliente_desde"])
    w.writerow(["QA_Import Minuscula 1", "qa_import_min1@test.com", "", "Empresa QA", "nota", ""])
    w.writerow(["QA_Import Minuscula 2", "qa_import_min2@test.com", "", "", "", ""])

# 2. CSV con headers CAPITALIZADOS, tal cual como dicen las instrucciones en pantalla
#    (Nombre, Email, Telefono, Empresa, Notas, cliente_desde)
with open(os.path.join(DIR, "headers_capitalizados.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["Nombre", "Email", "Telefono", "Empresa", "Notas", "cliente_desde"])
    w.writerow(["QA_Import Capital 1", "qa_import_cap1@test.com", "", "Empresa QA", "nota", ""])
    w.writerow(["QA_Import Capital 2", "qa_import_cap2@test.com", "", "", "", ""])

# 3. CSV vacio (solo headers, sin filas)
with open(os.path.join(DIR, "vacio.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["nombre", "email", "telefono", "empresa", "notas", "cliente_desde"])

# 4. CSV totalmente vacio (0 bytes)
open(os.path.join(DIR, "totalmente_vacio.csv"), "w").close()

# 5. CSV con columna 'email' faltante
with open(os.path.join(DIR, "sin_columna_email.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["nombre", "telefono", "empresa", "notas"])
    w.writerow(["QA_Import SinEmail", "", "", ""])

# 6. CSV con emails duplicados dentro del mismo archivo + fila invalida (sin nombre) + email mal formado
with open(os.path.join(DIR, "duplicados_e_invalidos.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["nombre", "email", "telefono", "empresa", "notas", "cliente_desde"])
    w.writerow(["QA_Import Dup", "qa_import_dup@test.com", "", "", "", ""])
    w.writerow(["QA_Import Dup Otra vez", "qa_import_dup@test.com", "", "", "", ""])  # email duplicado (misma fila repetida en el archivo)
    w.writerow(["", "qa_import_sinnombre@test.com", "", "", "", ""])  # sin nombre -> invalido
    w.writerow(["QA_Import EmailMalo", "esto-no-es-email", "", "", "", ""])  # email mal formado -> invalido

# 7. Extension incorrecta (.txt con contenido csv)
with open(os.path.join(DIR, "extension_incorrecta.txt"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["nombre", "email", "telefono", "empresa", "notas", "cliente_desde"])
    w.writerow(["QA_Import TxtExt", "qa_import_txtext@test.com", "", "", "", ""])

# 8. Archivo grande (500 filas validas)
with open(os.path.join(DIR, "grande_500.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["nombre", "email", "telefono", "empresa", "notas", "cliente_desde"])
    for i in range(500):
        w.writerow([f"QA_Import Grande {i}", f"qa_import_grande_{i}@test.com", "", "", "", ""])

# 9. XLSX valido (headers en minuscula)
libro = openpyxl.Workbook()
hoja = libro.active
hoja.append(["nombre", "email", "telefono", "empresa", "notas", "cliente_desde"])
hoja.append(["QA_Import Excel 1", "qa_import_excel1@test.com", "", "", "", ""])
libro.save(os.path.join(DIR, "valido.xlsx"))

print("Archivos generados en", DIR)
print(os.listdir(DIR))
