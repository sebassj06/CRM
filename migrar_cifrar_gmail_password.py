from core.database import obtener_conexion
from core.cifrado import cifrar, descifrar


def migrar():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT id, gmail_app_password FROM agencias WHERE gmail_app_password IS NOT NULL")
    filas = cursor.fetchall()

    cifradas = 0
    ya_cifradas = 0
    for agencia_id, valor_actual in filas:
        # Si descifrar(valor_actual) devuelve algo distinto del valor guardado,
        # es porque YA es un token Fernet válido (ya se cifró antes) — no hay
        # que tocarlo. Si devuelve lo mismo, es porque descifrar() no pudo
        # interpretarlo como token y lo devolvió tal cual: es texto plano
        # viejo, hay que cifrarlo ahora.
        if descifrar(valor_actual) == valor_actual:
            cursor.execute(
                "UPDATE agencias SET gmail_app_password = %s WHERE id = %s",
                (cifrar(valor_actual), agencia_id)
            )
            cifradas += 1
        else:
            ya_cifradas += 1

    conexion.commit()
    cursor.close()
    conexion.close()
    print(f"Migración completa: {cifradas} contraseña(s) cifrada(s), {ya_cifradas} ya estaban cifradas.")


if __name__ == "__main__":
    migrar()
