import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy import stats
import json

st.set_page_config(page_title="Normalidad y Pareto", page_icon="", layout="wide")
st.title("Pruebas de Normalidad y Diagrama de Pareto")
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

tab1, tab2 = st.tabs(["Pruebas de Normalidad", "Diagrama de Pareto"])

with tab1:
    if df.empty:
        st.warning("No hay datos. Ve a Ingreso de Datos primero.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            producto = st.selectbox("Producto", df["producto"].unique())
        with col2:
            variable = st.selectbox("Variable", df[df["producto"]==producto]["variable"].unique())

        df_f = df[(df["producto"]==producto) & (df["variable"]==variable)]
        datos = df_f[["muestra1","muestra2","muestra3","muestra4","muestra5"]].values.flatten()

        st.markdown("---")
        st.subheader("Estadísticas descriptivas")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Media", f"{np.mean(datos):.4f}")
        col2.metric("Desv. estándar", f"{np.std(datos, ddof=1):.4f}")
        col3.metric("Mínimo", f"{np.min(datos):.4f}")
        col4.metric("Máximo", f"{np.max(datos):.4f}")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Mediana", f"{np.median(datos):.4f}")
        col2.metric("Curtosis", f"{stats.kurtosis(datos):.4f}")
        col3.metric("Asimetría", f"{stats.skew(datos):.4f}")
        col4.metric("N datos", f"{len(datos)}")

        st.markdown("---")
        st.subheader("Pruebas de normalidad")

        stat_sw, p_sw = stats.shapiro(datos)
        stat_ks, p_ks = stats.kstest(datos, 'norm', args=(np.mean(datos), np.std(datos)))
        stat_da, p_da = stats.normaltest(datos)

        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Shapiro-Wilk**")
            st.metric("Estadístico W", f"{stat_sw:.4f}")
            st.metric("Valor p", f"{p_sw:.4f}")
            if p_sw > 0.05:
                st.success("Normal (p > 0.05)")
            else:
                st.error("No normal (p ≤ 0.05)")

        with col2:
            st.markdown("**Kolmogorov-Smirnov**")
            st.metric("Estadístico D", f"{stat_ks:.4f}")
            st.metric("Valor p", f"{p_ks:.4f}")
            if p_ks > 0.05:
                st.success("Normal (p > 0.05)")
            else:
                st.error("No normal (p ≤ 0.05)")

        with col3:
            st.markdown("**D'Agostino-Pearson**")
            st.metric("Estadístico", f"{stat_da:.4f}")
            st.metric("Valor p", f"{p_da:.4f}")
            if p_da > 0.05:
                st.success("Normal (p > 0.05)")
            else:
                st.error("No normal (p ≤ 0.05)")

        st.markdown("---")
        st.subheader("Gráfico Q-Q")
        
        (osm, osr), (slope, intercept, r) = stats.probplot(datos)
        linea_y = slope * np.array(osm) + intercept

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=osm, y=osr, mode="markers",
            marker=dict(color="steelblue", size=8), name="Datos"))
        fig.add_trace(go.Scatter(x=osm, y=linea_y, mode="lines",
            line=dict(color="red", width=2), name="Línea normal"))
        fig.update_layout(title=f"Gráfico Q-Q - {variable} ({producto})",
            xaxis_title="Cuantiles teóricos", yaxis_title="Cuantiles observados",
            height=400, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Histograma con curva normal")
        x_range = np.linspace(min(datos)-2*np.std(datos), max(datos)+2*np.std(datos), 200)
        curva = stats.norm.pdf(x_range, np.mean(datos), np.std(datos))
        fig2 = go.Figure()
        fig2.add_trace(go.Histogram(x=datos, nbinsx=15, histnorm="probability density",
            marker=dict(color="steelblue", opacity=0.7), name="Datos"))
        fig2.add_trace(go.Scatter(x=x_range, y=curva, mode="lines",
            line=dict(color="red", width=2), name="Curva normal"))
        fig2.update_layout(title="Histograma de frecuencias",
            xaxis_title=variable, yaxis_title="Densidad",
            height=400, template="plotly_white")
        st.plotly_chart(fig2, use_container_width=True)

with tab2:
    st.subheader("Diagrama de Pareto")
    st.info("Ingresa los defectos encontrados por categoría")

    producto_p = st.selectbox("Producto", ["Mango","Banano","Aguacate","Melón","Cilantro","Sábila","Manzanilla"], key="prod_pareto")
    
    defectos_lista = ["Manchas","Daños por plagas","Golpes","Frutos podridos","Defectos de color","Presencia de insectos","Material extraño"]
    
    frecuencias = {}
    st.markdown("**Ingresa la frecuencia de cada defecto:**")
    cols = st.columns(2)
    for i, defecto in enumerate(defectos_lista):
        with cols[i % 2]:
            frecuencias[defecto] = st.number_input(defecto, min_value=0, value=0, key=f"par_{i}")

    if st.button("Generar Pareto", use_container_width=True):
        df_pareto = pd.DataFrame(list(frecuencias.items()), columns=["Defecto","Frecuencia"])
        df_pareto = df_pareto[df_pareto["Frecuencia"] > 0].sort_values("Frecuencia", ascending=False)
        
        if df_pareto.empty:
            st.warning("Ingresa al menos un defecto con frecuencia mayor a 0")
        else:
            df_pareto["Acumulado"] = df_pareto["Frecuencia"].cumsum()
            df_pareto["Porcentaje"] = df_pareto["Frecuencia"] / df_pareto["Frecuencia"].sum() * 100
            df_pareto["Porcentaje acumulado"] = df_pareto["Acumulado"] / df_pareto["Frecuencia"].sum() * 100

            fig = go.Figure()
            fig.add_trace(go.Bar(x=df_pareto["Defecto"], y=df_pareto["Frecuencia"],
                marker_color="steelblue", name="Frecuencia"))
            fig.add_trace(go.Scatter(x=df_pareto["Defecto"], y=df_pareto["Porcentaje acumulado"],
                mode="lines+markers", marker=dict(color="red", size=8),
                line=dict(color="red", width=2), name="% Acumulado", yaxis="y2"))
            fig.add_hline(y=80, line=dict(color="orange", dash="dash"), yref="y2",
                annotation_text="80%")
            fig.update_layout(
                title=f"Diagrama de Pareto - Defectos en {producto_p}",
                xaxis_title="Tipo de defecto",
                yaxis=dict(title="Frecuencia"),
                yaxis2=dict(title="% Acumulado", overlaying="y", side="right", range=[0,110]),
                height=450, template="plotly_white",
                legend=dict(x=0.7, y=0.95))
            st.plotly_chart(fig, use_container_width=True)

            vital_80 = df_pareto[df_pareto["Porcentaje acumulado"] <= 80]["Defecto"].tolist()
            st.success(f"El 80% de defectos se concentra en: **{', '.join(vital_80) if vital_80 else df_pareto.iloc[0]['Defecto']}**")
            st.dataframe(df_pareto, use_container_width=True)