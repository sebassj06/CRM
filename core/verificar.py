import sqlite3

conexion = sqlite3.connect("crm.db")
cursor = conexion.cursor()

cursor.execute ("SELECT * FROM proyectos")
resultados = cursor.fetchall()

print(resultados)

conexion.close()
