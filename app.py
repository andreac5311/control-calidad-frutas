import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(
    page_title="Control de Calidad - Frutas y Hortalizas",
    page_icon="🍋",
    layout="wide"
)

DB_PATH = "data/calidad.db"

def cargar_datos():
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql("SELECT * FROM muestras", conn)
        conn.close()
        return df
    except:
        return pd.DataFrame()

df = cargar_datos()

st.title("🍋 Sistema de Control Estadístico de Calidad")
st.subheader("Frutas, Hortalizas y Plantas Medicinales — Universidad del Magdalena")
st.markdown("---")

if not df.empty:
    mediciones = df[["muestra1","muestra2","muestra3","muestra4","muestra5"]].values
    X_bar = np.mean(mediciones, axis=1)
    R = np.max(mediciones, axis=1) - np.min(mediciones, axis=1)
    R_bar = np.mean(R)
    X_bar_bar = np.mean(X_bar)
    A2 = 0.577
    UCL = X_bar_bar + A2 * R_bar
    LCL = X_bar_bar - A2 * R_bar
    fuera = sum(1 for x in X_bar if x > UCL or x < LCL)
    bajo_control = round((1 - fuera/len(X_bar))*100, 1)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📦 Muestras registradas", len(df)*5)
    col2.metric("🔬 Variables monitoreadas", df["variable"].nunique())
    col3.metric("✅ Bajo control", f"{bajo_control}%")
    col4.metric("🚨 Subgrupos fuera", fuera)
else:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📦 Muestras registradas", "0")
    col2.metric("🔬 Variables monitoreadas", "0")
    col3.metric("✅ Bajo control", "0%")
    col4.metric("🚨 Subgrupos fuera", "0")

st.markdown("---")

if not df.empty:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Muestras por producto")
        conteo = df["producto"].value_counts()
        fig1 = go.Figure(go.Bar(
            x=conteo.index, y=conteo.values,
            marker_color="steelblue"))
        fig1.update_layout(height=300, template="plotly_white",
            xaxis_title="Producto", yaxis_title="Subgrupos")
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.subheader("📈 Tendencia de medias X̄")
        mediciones = df[["muestra1","muestra2","muestra3","muestra4","muestra5"]].values
        X_bar = np.mean(mediciones, axis=1)
        fig2 = go.Figure(go.Scatter(
            y=X_bar, mode="lines+markers",
            line=dict(color="steelblue", width=2),
            marker=dict(size=6)))
        fig2.update_layout(height=300, template="plotly_white",
            xaxis_title="Subgrupo", yaxis_title="X̄")
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    st.subheader("📋 Resumen por variable")
    resumen = df.groupby(["producto","variable"]).agg(
        Subgrupos=("subgrupo","count"),
        Media=("muestra1","mean"),
        Analista=("analista","first")
    ).reset_index()
    st.dataframe(resumen, use_container_width=True)

else:
    st.info("👈 Ve a **📥 Ingreso de Datos** para comenzar a registrar muestras")

st.markdown("---")
st.markdown("**Universidad del Magdalena** | Control Estadístico de Procesos 2026-1")