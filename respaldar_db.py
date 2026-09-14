import subprocess
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def respaldar_base_de_datos():
    carpeta_respaldos = "respaldos"
    os.makedirs(carpeta_respaldos, exist_ok=True)

    ahora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nombre_respaldo = f"crm_backup_{ahora}.sql"
    ruta_respaldo = os.path.join(carpeta_respaldos, nombre_respaldo)

    database_url = os.getenv("DATABASE_URL")

    with open(ruta_respaldo, "w") as archivo_salida:
        subprocess.run(["pg_dump", database_url], stdout=archivo_salida, check=True)

    print(f"Respaldo creado: {ruta_respaldo}")

if __name__ == "__main__":
    respaldar_base_de_datos()