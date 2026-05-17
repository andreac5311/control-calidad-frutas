import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Gráficos de Atributos", page_icon="", layout="wide")
st.title("Gráficos de Control por Atributos")
st.markdown("---")

st.info("Ingresa los datos de atributos directamente aquí")

tipo_grafico = st.selectbox("Tipo de gráfico", ["p - Proporción de defectos", "np - Número de defectos", "c - Defectos por unidad", "u - Defectos por unidad variable"])

producto = st.selectbox("Producto", ["Mango","Banano","Aguacate","Melón","Cilantro","Sábila","Manzanilla"])
atributo = st.selectbox("Atributo a controlar", ["Presencia de manchas","Daños por plagas","Golpes o magulladuras","Frutos podridos","Defectos de color","Presencia de insectos"])
analista = st.text_input("Analista", "")
n_subgrupos = st.number_input("Número de subgrupos", min_value=25, max_value=100, value=25)

st.markdown("---")
st.subheader("Ingreso de datos por subgrupo")

if "p" in tipo_grafico or "np" in tipo_grafico:
    col1, col2 = st.columns(2)
    tamanio_n = col1.number_input("Tamaño de subgrupo (n)", min_value=1, value=50)
    
    defectos = []
    cols_header = st.columns(3)
    cols_header[0].markdown("**Subgrupo**")
    cols_header[1].markdown("**Defectos**")
    cols_header[2].markdown("**Proporción**")
    
    for i in range(int(n_subgrupos)):
        cols = st.columns(3)
        cols[0].write(f"SG {i+1}")
        d = cols[1].number_input(f"d{i+1}", min_value=0, max_value=int(tamanio_n), key=f"d{i}", label_visibility="collapsed")
        defectos.append(d)
        cols[2].write(f"{d/tamanio_n:.4f}")
    
    if st.button("Generar gráfico", use_container_width=True):
        defectos = np.array(defectos)
        proporciones = defectos / tamanio_n
        
        if "p" in tipo_grafico and "np" not in tipo_grafico:
            p_bar = np.mean(proporciones)
            UCL = p_bar + 3 * np.sqrt(p_bar*(1-p_bar)/tamanio_n)
            LCL = max(0, p_bar - 3 * np.sqrt(p_bar*(1-p_bar)/tamanio_n))
            valores = proporciones
            titulo = f"Gráfico p - {atributo} ({producto})"
            ylabel = "Proporción defectos"
            cl = p_bar
        else:
            np_bar = np.mean(defectos)
            p_bar = np_bar / tamanio_n
            UCL = np_bar + 3 * np.sqrt(np_bar*(1-p_bar))
            LCL = max(0, np_bar - 3 * np.sqrt(np_bar*(1-p_bar)))
            valores = defectos
            titulo = f"Gráfico np - {atributo} ({producto})"
            ylabel = "Número de defectos"
            cl = np_bar

        colores = ["red" if v > UCL or v < LCL else "green" for v in valores]
        fuera = colores.count("red")

        fig = go.Figure()
        fig.add_trace(go.Scatter(y=valores, mode="lines+markers",
            marker=dict(color=colores, size=10),
            line=dict(color="gray", width=1)))
        fig.add_hline(y=UCL, line=dict(color="red", dash="dash", width=2), annotation_text=f"UCL={UCL:.4f}")
        fig.add_hline(y=cl, line=dict(color="green", width=2), annotation_text=f"CL={cl:.4f}")
        fig.add_hline(y=LCL, line=dict(color="red", dash="dash", width=2), annotation_text=f"LCL={LCL:.4f}")
        fig.update_layout(title=titulo, xaxis_title="Subgrupo", yaxis_title=ylabel, height=450, template="plotly_white")
        
        st.plotly_chart(fig, use_container_width=True)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("UCL", f"{UCL:.4f}")
        col2.metric("CL", f"{cl:.4f}")
        col3.metric("LCL", f"{LCL:.4f}")
        
        if fuera > 0:
            st.error(f"{fuera} puntos FUERA de control")
        else:
            st.success("Proceso bajo control estadístico")

else:
    defectos_c = []
    if "u" in tipo_grafico:
        tamanos = []
    
    for i in range(int(n_subgrupos)):
        cols = st.columns(2)
        cols[0].write(f"SG {i+1}")
        d = cols[1].number_input(f"c{i+1}", min_value=0, key=f"c{i}", label_visibility="collapsed")
        defectos_c.append(d)

    if st.button("Generar gráfico", use_container_width=True):
        defectos_c = np.array(defectos_c)
        
        if "u" not in tipo_grafico:
            c_bar = np.mean(defectos_c)
            UCL = c_bar + 3 * np.sqrt(c_bar)
            LCL = max(0, c_bar - 3 * np.sqrt(c_bar))
            valores = defectos_c
            titulo = f"Gráfico c - {atributo} ({producto})"
            ylabel = "Número de defectos"
            cl = c_bar
        else:
            u_bar = np.mean(defectos_c)
            UCL = u_bar + 3 * np.sqrt(u_bar)
            LCL = max(0, u_bar - 3 * np.sqrt(u_bar))
            valores = defectos_c
            titulo = f"Gráfico u - {atributo} ({producto})"
            ylabel = "Defectos por unidad"
            cl = u_bar

        colores = ["red" if v > UCL or v < LCL else "green" for v in valores]
        fuera = colores.count("red")

        fig = go.Figure()
        fig.add_trace(go.Scatter(y=valores, mode="lines+markers",
            marker=dict(color=colores, size=10),
            line=dict(color="gray", width=1)))
        fig.add_hline(y=UCL, line=dict(color="red", dash="dash", width=2), annotation_text=f"UCL={UCL:.4f}")
        fig.add_hline(y=cl, line=dict(color="green", width=2), annotation_text=f"CL={cl:.4f}")
        fig.add_hline(y=LCL, line=dict(color="red", dash="dash", width=2), annotation_text=f"LCL={LCL:.4f}")
        fig.update_layout(title=titulo, xaxis_title="Subgrupo", yaxis_title=ylabel, height=450, template="plotly_white")
        
        st.plotly_chart(fig, use_container_width=True)

        col1, col2, col3 = st.columns(3)
        col1.metric("UCL", f"{UCL:.4f}")
        col2.metric("CL", f"{cl:.4f}")
        col3.metric("LCL", f"{LCL:.4f}")

        if fuera > 0:
            st.error(f"{fuera} puntos FUERA de control")
        else:
            st.success("Proceso bajo control estadístico")
