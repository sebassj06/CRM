# -*- coding: utf-8 -*-
"""Limpia los datos de negocio (clientes/proyectos/pagos/notas) creados durante
el QA en las agencias QA_Agencia A y QA_Agencia B. Deja intactas las agencias
y los usuarios QA_* como fixture reutilizable para futuras pruebas, salvo el
usuario QA_nuevo_miembro que ya se elimino durante las pruebas."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from core.database import obtener_conexion

AGENCIA_IDS = (2, 3)  # QA_Agencia A, QA_Agencia B

conexion = obtener_conexion()
cursor = conexion.cursor()

for tabla in ("notas", "pagos", "proyectos", "clientes"):
    cursor.execute(f"DELETE FROM {tabla} WHERE agencia_id = ANY(%s)", (list(AGENCIA_IDS),))
    print(f"Borrados {cursor.rowcount} registros de {tabla}")

# Revertir configuracion de agencia (gmail/telegram falsos que configuramos en las pruebas)
cursor.execute(
    "UPDATE agencias SET telegram_chat_id = NULL, gmail_user = NULL, gmail_app_password = NULL, moneda = 'USD' WHERE id = ANY(%s)",
    (list(AGENCIA_IDS),)
)
print(f"Configuracion de agencias QA restablecida ({cursor.rowcount} filas)")

conexion.commit()

cursor.execute("SELECT id, nombre FROM agencias WHERE id = ANY(%s)", (list(AGENCIA_IDS),))
print("Agencias QA que se mantienen:", cursor.fetchall())
cursor.execute("SELECT id, nombre_usuario, agencia_id, rol FROM usuarios WHERE agencia_id = ANY(%s) ORDER BY id", (list(AGENCIA_IDS),))
print("Usuarios QA que se mantienen:", cursor.fetchall())

conexion.close()
