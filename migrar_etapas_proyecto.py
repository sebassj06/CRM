from core.database import obtener_conexion
from core.agencias import obtener_agencias
from core.etapas import sembrar_etapas_default


def migrar():
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS etapas (
            id SERIAL PRIMARY KEY,
            agencia_id INTEGER NOT NULL,
            nombre TEXT NOT NULL,
            orden INTEGER NOT NULL DEFAULT 0,
            es_final BOOLEAN NOT NULL DEFAULT false)
    """)

    conexion.commit()
    cursor.close()
    conexion.close()

    for agencia in obtener_agencias():
        sembrar_etapas_default(agencia[0])

    print("Migración completa: tabla 'etapas', sembrada con Pendiente/En progreso/Completado para las agencias existentes.")


if __name__ == "__main__":
    migrar()
