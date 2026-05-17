import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(
    page_title="Control de Calidad - Frutas y Hortalizas",
    page_icon="",
    layout="wide"
)

# Custom CSS for better visual design
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stMetric {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .chart-container {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .footer {
        text-align: center;
        color: #666;
        font-size: 0.9rem;
        margin-top: 2rem;
        padding: 1rem;
        background-color: #f8f9fa;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

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

st.markdown('<div class="main-header">Sistema de Control Estadístico de Calidad</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Frutas, Hortalizas y Plantas Medicinales — Universidad del Magdalena</div>', unsafe_allow_html=True)
st.markdown("---")

# Create a more visual metrics section
st.markdown("### Indicadores Clave de Calidad")

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

    # Create a more visual metrics layout
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 Muestras registradas", f"{len(df)*5:,}")
    with col2:
        st.metric("🔬 Variables monitoreadas", df["variable"].nunique())
    with col3:
        st.metric("✅ Bajo control", f"{bajo_control}%")
    with col4:
        st.metric("🚨 Subgrupos fuera", fuera)
else:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 Muestras registradas", "0")
    with col2:
        st.metric("🔬 Variables monitoreadas", "0")
    with col3:
        st.metric("✅ Bajo control", "0%")
    with col4:
        st.metric("🚨 Subgrupos fuera", "0")

st.markdown("---")

if not df.empty:
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📊 Muestras por producto")
        conteo = df["producto"].value_counts()
        fig1 = go.Figure(go.Bar(
            x=conteo.index, y=conteo.values,
            marker_color="#1f77b4"))
        fig1.update_layout(
            height=350,
            template="plotly_white",
            xaxis_title="Producto",
            yaxis_title="Subgrupos",
            hovermode="x unified",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.markdown("#### 📈 Tendencia de medias X̄")
        mediciones = df[["muestra1","muestra2","muestra3","muestra4","muestra5"]].values
        X_bar = np.mean(mediciones, axis=1)
        fig2 = go.Figure(go.Scatter(
            y=X_bar, mode="lines+markers",
            line=dict(color="#1f77b4", width=2),
            marker=dict(size=8, color="#1f77b4", line=dict(width=1, color="white"))))
        fig2.update_layout(
            height=350,
            template="plotly_white",
            xaxis_title="Subgrupo",
            yaxis_title="X̄",
            hovermode="x unified",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    st.markdown("#### 📋 Resumen por variable")
    resumen = df.groupby(["producto","variable"]).agg(
        Subgrupos=("subgrupo","count"),
        Media=("muestra1","mean"),
        Analista=("analista","first")
    ).reset_index()
    st.dataframe(resumen, use_container_width=True)

else:
    st.info("📥 Ve a **Ingreso de Datos** para comenzar a registrar muestras")

st.markdown("---")
st.markdown('<div class="footer">**Universidad del Magdalena** | Control Estadístico de Procesos 2026-1</div>', unsafe_allow_html=True)
