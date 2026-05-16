import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="Ingreso de Datos", page_icon="📥", layout="wide")
st.title("📥 Ingreso de Datos")
st.markdown("---")

DB_PATH = "data/calidad.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS muestras (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        producto TEXT, tipo TEXT, variable TEXT,
        unidad TEXT, analista TEXT, fecha TEXT,
        subgrupo INTEGER, muestra1 REAL, muestra2 REAL,
        muestra3 REAL, muestra4 REAL, muestra5 REAL
    )''')
    conn.commit()
    conn.close()

init_db()

with st.form("ingreso"):
    st.subheader("🔬 Información de trazabilidad")
    col1, col2, col3 = st.columns(3)
    with col1:
        producto = st.selectbox("Producto", ["Mango","Banano","Aguacate","Melón","Cilantro","Sábila","Manzanilla","Menta","Otro"])
        tipo = st.selectbox("Tipo de control", ["Variable continua", "Atributo"])
    with col2:
        variable = st.selectbox("Variable a controlar", ["Peso (g)","Diámetro (cm)","Grados Brix","pH","Firmeza","Contenido de humedad (%)","Otro"])
        unidad = st.text_input("Unidad de medida", "g")
    with col3:
        analista = st.text_input("Nombre del analista", "")
        fecha = st.date_input("Fecha de muestreo", datetime.today())

    st.markdown("---")
    st.subheader("📊 Ingreso de muestras por subgrupo")
    n_subgrupos = st.number_input("Número de subgrupos", min_value=25, max_value=100, value=25)
    
    st.info("💡 Ingresa 5 mediciones por subgrupo")
    
    datos = []
    for i in range(int(n_subgrupos)):
        cols = st.columns(6)
        cols[0].markdown(f"**SG {i+1}**")
        fila = [cols[j+1].number_input(f"M{j+1}", key=f"sg{i}m{j}", label_visibility="collapsed") for j in range(5)]
        datos.append(fila)

    submitted = st.form_submit_button("💾 Guardar datos", use_container_width=True)
    
    if submitted:
        conn = sqlite3.connect(DB_PATH)
        for i, fila in enumerate(datos):
            conn.execute("INSERT INTO muestras VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?,?)",
                (producto, tipo, variable, unidad, analista, str(fecha), i+1, *fila))
        conn.commit()
        conn.close()
        st.success(f"✅ {n_subgrupos} subgrupos guardados correctamente")
        st.balloons()

st.markdown("---")
st.subheader("📋 Datos registrados")
try:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM muestras", conn)
    conn.close()
    if len(df) > 0:
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("No hay datos registrados aún")
except:
    st.warning("No hay datos registrados aún")