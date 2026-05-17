import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy import stats

st.set_page_config(page_title="Gráficos de Variables", page_icon="", layout="wide")
st.title("Gráficos de Control por Variables")
st.markdown("---")

DB_PATH = "data/calidad.db"

def cargar_datos():
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql("SELECT * FROM muestras WHERE tipo='Variable continua'", conn)
        conn.close()
        return df
    except:
        return pd.DataFrame()

df = cargar_datos()

if df.empty:
    st.warning("No hay datos de variables continuas. Ve a Ingreso de Datos primero.")
    st.stop()

col1, col2 = st.columns(2)
with col1:
    producto = st.selectbox("Producto", df["producto"].unique())
with col2:
    variable = st.selectbox("Variable", df[df["producto"]==producto]["variable"].unique())

df_filtrado = df[(df["producto"]==producto) & (df["variable"]==variable)].copy()
mediciones = df_filtrado[["muestra1","muestra2","muestra3","muestra4","muestra5"]].values

X_bar = np.mean(mediciones, axis=1)
R = np.max(mediciones, axis=1) - np.min(mediciones, axis=1)
S = np.std(mediciones, axis=1, ddof=1)
n = 5

d2, d3, A2, D3, D4 = 2.326, 0.864, 0.577, 0, 2.115
B3, B4, A3 = 0, 2.089, 1.427

X_bar_bar = np.mean(X_bar)
R_bar = np.mean(R)
S_bar = np.mean(S)

UCL_X_R = X_bar_bar + A2 * R_bar
LCL_X_R = X_bar_bar - A2 * R_bar
UCL_R = D4 * R_bar
LCL_R = D3 * R_bar

UCL_X_S = X_bar_bar + A3 * S_bar
LCL_X_S = X_bar_bar - A3 * S_bar
UCL_S = B4 * S_bar
LCL_S = B3 * S_bar

def color_puntos(valores, ucl, lcl, media):
    colores = []
    for v in valores:
        if v > ucl or v < lcl:
            colores.append("red")
        else:
            colores.append("green")
    return colores

def grafico_control(valores, ucl, lcl, media, titulo, ylabel):
    colores = color_puntos(valores, ucl, lcl, media)
    fuera = sum(1 for c in colores if c == "red")
    fig = go.Figure()
    fig.add_trace(go.Scatter(y=valores, mode="lines+markers",
        marker=dict(color=colores, size=10),
        line=dict(color="gray", width=1), name=ylabel))
    fig.add_hline(y=ucl, line=dict(color="red", dash="dash", width=2), annotation_text=f"UCL={ucl:.3f}")
    fig.add_hline(y=media, line=dict(color="green", width=2), annotation_text=f"CL={media:.3f}")
    fig.add_hline(y=lcl, line=dict(color="red", dash="dash", width=2), annotation_text=f"LCL={lcl:.3f}")
    fig.update_layout(title=titulo, xaxis_title="Subgrupo", yaxis_title=ylabel,
        height=400, template="plotly_white")
    return fig, fuera

tipo_grafico = st.radio("Selecciona tipo de gráfico", ["X̄ - R", "X̄ - S"], horizontal=True)
st.markdown("---")

if tipo_grafico == "X̄ - R":
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("X̄ (Media global)", f"{X_bar_bar:.4f}")
    col2.metric("R̄ (Rango medio)", f"{R_bar:.4f}")
    col3.metric("UCL (X̄)", f"{UCL_X_R:.4f}")
    col4.metric("LCL (X̄)", f"{LCL_X_R:.4f}")

    fig1, fuera1 = grafico_control(X_bar, UCL_X_R, LCL_X_R, X_bar_bar, f"Gráfico X̄ - {variable} ({producto})", "X̄")
    fig2, fuera2 = grafico_control(R, UCL_R, LCL_R, R_bar, f"Gráfico R - {variable} ({producto})", "R")
    
    st.plotly_chart(fig1, use_container_width=True)
    if fuera1 > 0:
        st.error(f"{fuera1} puntos FUERA de control en gráfico X̄")
    else:
        st.success("Proceso bajo control estadístico en gráfico X̄")
    
    st.plotly_chart(fig2, use_container_width=True)
    if fuera2 > 0:
        st.error(f"{fuera2} puntos FUERA de control en gráfico R")
    else:
        st.success("Proceso bajo control estadístico en gráfico R")

else:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("X̄ (Media global)", f"{X_bar_bar:.4f}")
    col2.metric("S̄ (Desv. media)", f"{S_bar:.4f}")
    col3.metric("UCL (X̄)", f"{UCL_X_S:.4f}")
    col4.metric("LCL (X̄)", f"{LCL_X_S:.4f}")

    fig1, fuera1 = grafico_control(X_bar, UCL_X_S, LCL_X_S, X_bar_bar, f"Gráfico X̄ - {variable} ({producto})", "X̄")
    fig2, fuera2 = grafico_control(S, UCL_S, LCL_S, S_bar, f"Gráfico S - {variable} ({producto})", "S")
    
    st.plotly_chart(fig1, use_container_width=True)
    if fuera1 > 0:
        st.error(f"{fuera1} puntos FUERA de control en gráfico X̄")
    else:
        st.success("Proceso bajo control estadístico en gráfico X̄")
    
    st.plotly_chart(fig2, use_container_width=True)
    if fuera2 > 0:
        st.error(f"{fuera2} puntos FUERA de control en gráfico S")
    else:
        st.success("Proceso bajo control estadístico en gráfico S")

st.markdown("---")
st.subheader("Tabla de valores")
tabla = pd.DataFrame({"Subgrupo": range(1, len(X_bar)+1), "X̄": X_bar, "R": R, "S": S})
st.dataframe(tabla.style.format({"X̄": "{:.4f}", "R": "{:.4f}", "S": "{:.4f}"}), use_container_width=True)