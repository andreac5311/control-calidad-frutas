import streamlit as st
import sqlite3
import numpy as np
import pandas as pd

st.set_page_config(page_title="Simulador de Datos", page_icon="🎲", layout="wide")
st.title("🎲 Simulador de Datos de Prueba")
st.markdown("---")
st.info("💡 Genera datos simulados realistas para demostrar el sistema sin necesitar mediciones reales.")

DB_PATH = "data/calidad.db"

PRODUCTOS_CONFIG = {
    "Mango": {
        "variables": {
            "Peso (g)": {"media": 300, "std": 15, "LIE": 250, "LSE": 350},
            "Diámetro (cm)": {"media": 8.5, "std": 0.4, "LIE": 7.5, "LSE": 9.5},
            "Grados Brix": {"media": 14.0, "std": 1.2, "LIE": 11.0, "LSE": 17.0},
            "pH": {"media": 3.8, "std": 0.2, "LIE": 3.2, "LSE": 4.5},
        }
    },
    "Banano": {
        "variables": {
            "Peso (g)": {"media": 120, "std": 10, "LIE": 90, "LSE": 150},
            "Longitud (cm)": {"media": 18.0, "std": 1.5, "LIE": 14.0, "LSE": 22.0},
            "Grados Brix": {"media": 20.0, "std": 1.5, "LIE": 16.0, "LSE": 24.0},
            "pH": {"media": 4.5, "std": 0.3, "LIE": 3.8, "LSE": 5.2},
        }
    },
    "Aguacate": {
        "variables": {
            "Peso (g)": {"media": 250, "std": 20, "LIE": 200, "LSE": 320},
            "Diámetro (cm)": {"media": 7.0, "std": 0.5, "LIE": 6.0, "LSE": 8.5},
            "pH": {"media": 6.5, "std": 0.3, "LIE": 5.8, "LSE": 7.2},
            "Contenido grasa (%)": {"media": 15.0, "std": 2.0, "LIE": 10.0, "LSE": 20.0},
        }
    },
    "Sábila (Aloe vera)": {
        "variables": {
            "Peso gel (g)": {"media": 180, "std": 20, "LIE": 130, "LSE": 230},
            "pH": {"media": 4.2, "std": 0.3, "LIE": 3.5, "LSE": 5.0},
            "Contenido humedad (%)": {"media": 95.0, "std": 1.5, "LIE": 91.0, "LSE": 99.0},
        }
    },
    "Manzanilla": {
        "variables": {
            "Altura planta (cm)": {"media": 35, "std": 5, "LIE": 20, "LSE": 50},
            "Peso fresco (g)": {"media": 45, "std": 8, "LIE": 25, "LSE": 65},
            "Aceites esenciales (%)": {"media": 0.8, "std": 0.1, "LIE": 0.5, "LSE": 1.2},
        }
    },
    "Melón": {
        "variables": {
            "Peso (g)": {"media": 1500, "std": 150, "LIE": 1100, "LSE": 1900},
            "Diámetro (cm)": {"media": 15.0, "std": 1.0, "LIE": 12.0, "LSE": 18.0},
            "Grados Brix": {"media": 12.0, "std": 1.0, "LIE": 9.0, "LSE": 15.0},
            "pH": {"media": 6.2, "std": 0.3, "LIE": 5.5, "LSE": 7.0},
        }
    },
}

st.subheader("⚙️ Configuración de la simulación")

col1, col2, col3 = st.columns(3)
with col1:
    producto = st.selectbox("Producto", list(PRODUCTOS_CONFIG.keys()))
with col2:
    variable = st.selectbox("Variable", list(PRODUCTOS_CONFIG[producto]["variables"].keys()))
with col3:
    analista = st.text_input("Nombre del analista", "Simulador")

config = PRODUCTOS_CONFIG[producto]["variables"][variable]

col1, col2, col3 = st.columns(3)
with col1:
    n_subgrupos = st.number_input("Número de subgrupos", min_value=25, max_value=100, value=25)
with col2:
    nivel_variacion = st.select_slider(
        "Nivel de variación del proceso",
        options=["Muy bajo", "Bajo", "Normal", "Alto", "Muy alto"],
        value="Normal"
    )
with col3:
    incluir_fuera = st.checkbox("Incluir puntos fuera de control", value=True)

st.markdown("---")
st.subheader("📊 Parámetros del proceso")
col1, col2, col3, col4 = st.columns(4)
with col1:
    media_sim = st.number_input("Media del proceso", value=float(config["media"]))
with col2:
    multiplicador = {"Muy bajo": 0.3, "Bajo": 0.6, "Normal": 1.0, "Alto": 1.5, "Muy alto": 2.5}
    std_sim = config["std"] * multiplicador[nivel_variacion]
    st.metric("Desviación estándar", f"{std_sim:.3f}")
with col3:
    st.metric("LIE referencia", f"{config['LIE']}")
with col4:
    st.metric("LSE referencia", f"{config['LSE']}")

if st.button("🎲 Generar y guardar datos simulados", use_container_width=True):
    np.random.seed(None)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS muestras (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        producto TEXT, tipo TEXT, variable TEXT,
        unidad TEXT, analista TEXT, fecha TEXT,
        subgrupo INTEGER, muestra1 REAL, muestra2 REAL,
        muestra3 REAL, muestra4 REAL, muestra5 REAL
    )''')
    
    datos_generados = []
    for i in range(int(n_subgrupos)):
        if incluir_fuera and i in [int(n_subgrupos*0.3), int(n_subgrupos*0.7)]:
            muestras = np.random.normal(media_sim + 3.5*std_sim, std_sim*0.5, 5)
        else:
            muestras = np.random.normal(media_sim, std_sim, 5)
        
        datos_generados.append(muestras)
        c.execute("INSERT INTO muestras VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?,?)",
            (producto, "Variable continua", variable, "",
             analista, pd.Timestamp.now().strftime("%Y-%m-%d"), i+1, *muestras))
    
    conn.commit()
    conn.close()
    
    datos_arr = np.array(datos_generados)
    X_bar = np.mean(datos_arr, axis=1)
    
    st.success(f"✅ {n_subgrupos} subgrupos generados y guardados para {producto} - {variable}")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Media global", f"{np.mean(X_bar):.3f}")
    col2.metric("Desv. estándar", f"{np.std(X_bar, ddof=1):.3f}")
    col3.metric("Mínimo", f"{np.min(datos_arr):.3f}")
    col4.metric("Máximo", f"{np.max(datos_arr):.3f}")
    
    st.balloons()
    st.info("👈 Ve a 📊 Gráficos de Variables para ver los gráficos de control generados")

st.markdown("---")
st.subheader("🗑️ Gestión de datos")
col1, col2 = st.columns(2)
with col1:
    if st.button("🗑️ Borrar TODOS los datos", use_container_width=True, type="secondary"):
        conn = sqlite3.connect(DB_PATH)
        conn.execute("DELETE FROM muestras")
        conn.commit()
        conn.close()
        st.warning("⚠️ Todos los datos han sido eliminados")
        st.rerun()

with col2:
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql("SELECT * FROM muestras", conn)
        conn.close()
        st.metric("Total subgrupos en base de datos", len(df))
    except:
        st.metric("Total subgrupos en base de datos", 0)