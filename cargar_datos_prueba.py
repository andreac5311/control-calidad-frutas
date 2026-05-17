import sqlite3
import numpy as np

DB_PATH = "data/calidad.db"

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS muestras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto TEXT, tipo TEXT, variable TEXT,
    unidad TEXT, analista TEXT, fecha TEXT,
    subgrupo INTEGER, muestra1 REAL, muestra2 REAL,
    muestra3 REAL, muestra4 REAL, muestra5 REAL
)''')

np.random.seed(42)
for i in range(25):
    muestras = np.random.normal(300, 10, 5)
    c.execute("INSERT INTO muestras VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?,?)",
        ("Mango", "Variable continua", "Peso (g)", "g", 
         "Andrea", "2026-05-16", i+1, *muestras))

conn.commit()
conn.close()
print("Datos de prueba cargados exitosamente")
