import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy import stats
import json

st.set_page_config(page_title="Capacidad del Proceso", page_icon="", layout="wide")
st.title("Índices de Capacidad del Proceso")
st.markdown("---")

DB_PATH = "data/calidad.db"

def cargar_datos():
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql("SELECT * FROM muestras WHERE tipo='Variable continua'", conn)
        conn.close()

        # Convertir JSON a estructura de datos
        datos_procesados = []
        for _, row in df.iterrows():
            try:
                muestras_data = json.loads(row['muestras_json'])
                producto = row['producto']
                variable = row['variable']
                subgrupo = row['subgrupo']

                # Asegurarse de que tenemos exactamente 5 muestras (rellenar con NaN si es necesario)
                muestras = muestras_data['muestras']
                if len(muestras) < 5:
                    muestras = muestras + [np.nan] * (5 - len(muestras))
                elif len(muestras) > 5:
                    muestras = muestras[:5]

                datos_procesados.append({
                    'producto': producto,
                    'variable': variable,
                    'subgrupo': subgrupo,
                    'muestra1': muestras[0],
                    'muestra2': muestras[1],
                    'muestra3': muestras[2],
                    'muestra4': muestras[3],
                    'muestra5': muestras[4]
                })
            except:
                continue

        return pd.DataFrame(datos_procesados)
    except:
        return pd.DataFrame()

df = cargar_datos()

if df.empty:
    st.warning("No hay datos. Ve a Ingreso de Datos primero.")
    st.stop()

col1, col2 = st.columns(2)
with col1:
    producto = st.selectbox("Producto", df["producto"].unique())
with col2:
    variable = st.selectbox("Variable", df[df["producto"]==producto]["variable"].unique())

df_f = df[(df["producto"]==producto) & (df["variable"]==variable)]
mediciones = df_f[["muestra1","muestra2","muestra3","muestra4","muestra5"]].values
todos = mediciones.flatten()

st.markdown("---")
st.subheader("Especificaciones del proceso")
col1, col2, col3 = st.columns(3)
with col1:
    LSE = st.number_input("Límite Superior de Especificación (LSE)", value=float(np.mean(todos)+3*np.std(todos)))
with col2:
    LIE = st.number_input("Límite Inferior de Especificación (LIE)", value=float(np.mean(todos)-3*np.std(todos)))
with col3:
    objetivo = st.number_input("Valor objetivo", value=float(np.mean(todos)))

if st.button("Calcular índices de capacidad", use_container_width=True):
    media = np.mean(todos)
    sigma_total = np.std(todos, ddof=1)
    
    X_bar = np.mean(mediciones, axis=1)
    R = np.max(mediciones, axis=1) - np.min(mediciones, axis=1)
    R_bar = np.mean(R)
    d2 = 2.326
    sigma_dentro = R_bar / d2

    Cp = (LSE - LIE) / (6 * sigma_dentro)
    Cpk = min((LSE - media)/(3*sigma_dentro), (media - LIE)/(3*sigma_dentro))
    Pp = (LSE - LIE) / (6 * sigma_total)
    Ppk = min((LSE - media)/(3*sigma_total), (media - LIE)/(3*sigma_total))

    st.markdown("---")
    st.subheader("Resultados")
    
    col1, col2, col3, col4 = st.columns(4)
    
    def color_indice(valor):
        if valor >= 1.33: return "normal"
        elif valor >= 1.0: return "off"
        else: return "inverse"
    
    col1.metric("Cp", f"{Cp:.4f}", delta="Capaz" if Cp >= 1.33 else "Revisar" if Cp >= 1.0 else "No capaz")
    col2.metric("Cpk", f"{Cpk:.4f}", delta="Capaz" if Cpk >= 1.33 else "Revisar" if Cpk >= 1.0 else "No capaz")
    col3.metric("Pp", f"{Pp:.4f}", delta="Capaz" if Pp >= 1.33 else "Revisar" if Pp >= 1.0 else "No capaz")
    col4.metric("Ppk", f"{Ppk:.4f}", delta="Capaz" if Ppk >= 1.33 else "Revisar" if Ppk >= 1.0 else "No capaz")

    st.markdown("---")
    st.subheader("Histograma de capacidad")
    
    x_range = np.linspace(min(todos)-3*sigma_total, max(todos)+3*sigma_total, 200)
    curva = stats.norm.pdf(x_range, media, sigma_total)
    
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=todos, nbinsx=20, name="Datos",
        histnorm="probability density",
        marker=dict(color="steelblue", opacity=0.7)))
    fig.add_trace(go.Scatter(x=x_range, y=curva, mode="lines",
        line=dict(color="darkblue", width=2), name="Normal"))
    fig.add_vline(x=LSE, line=dict(color="red", dash="dash", width=2), annotation_text="LSE")
    fig.add_vline(x=LIE, line=dict(color="red", dash="dash", width=2), annotation_text="LIE")
    fig.add_vline(x=media, line=dict(color="green", width=2), annotation_text="Media")
    fig.add_vline(x=objetivo, line=dict(color="orange", dash="dot", width=2), annotation_text="Objetivo")
    fig.update_layout(title=f"Capacidad del proceso - {variable} ({producto})",
        xaxis_title=variable, yaxis_title="Densidad", height=450, template="plotly_white")
    
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Interpretación")
    
    interpretaciones = {
        "Cp": (Cp, "Potencial del proceso (variación natural vs especificaciones)"),
        "Cpk": (Cpk, "Capacidad real (considera descentramiento)"),
        "Pp": (Pp, "Desempeño del proceso (variación total)"),
        "Ppk": (Ppk, "Desempeño real (variación total + descentramiento)")
    }
    
    for indice, (valor, descripcion) in interpretaciones.items():
        if valor >= 1.33:
            st.success(f"**{indice} = {valor:.4f}** — {descripcion} → Proceso CAPAZ")
        elif valor >= 1.0:
            st.warning(f"**{indice} = {valor:.4f}** — {descripcion} → Proceso MARGINALMENTE capaz")
        else:
            st.error(f"**{indice} = {valor:.4f}** — {descripcion} → Proceso NO capaz")
