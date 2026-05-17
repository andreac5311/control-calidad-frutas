import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
from scipy import stats
import io
from datetime import datetime
import json

st.set_page_config(page_title="Exportar Resultados", page_icon="", layout="wide")
st.title("Exportar Resultados")
st.markdown("---")

DB_PATH = "data/calidad.db"

def cargar_datos():
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql("SELECT * FROM muestras", conn)
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
    st.warning("No hay datos registrados aún. Ve a Ingreso de Datos primero.")
    st.stop()

st.subheader("Selecciona qué exportar")

col1, col2 = st.columns(2)
with col1:
    producto = st.selectbox("Producto", ["Todos"] + list(df["producto"].unique()))
with col2:
    variable = st.selectbox("Variable", ["Todas"] + list(df["variable"].unique()))

df_filtrado = df.copy()
if producto != "Todos":
    df_filtrado = df_filtrado[df_filtrado["producto"] == producto]
if variable != "Todas":
    df_filtrado = df_filtrado[df_filtrado["variable"] == variable]

st.info(f"{len(df_filtrado)} subgrupos seleccionados")

st.markdown("---")
st.subheader("Exportar a Excel")
st.markdown("Genera un archivo Excel con múltiples hojas: datos crudos, estadísticas y resultados de control.")

if st.button("Generar archivo Excel", use_container_width=True):
    buffer = io.BytesIO()
    
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        
        df_filtrado.to_excel(writer, sheet_name="Datos crudos", index=False)
        
        mediciones = df_filtrado[["muestra1","muestra2","muestra3","muestra4","muestra5"]].values
        X_bar = np.mean(mediciones, axis=1)
        R = np.max(mediciones, axis=1) - np.min(mediciones, axis=1)
        S = np.std(mediciones, axis=1, ddof=1)
        
        A2, D3, D4 = 0.577, 0, 2.115
        X_bar_bar = np.mean(X_bar)
        R_bar = np.mean(R)
        S_bar = np.mean(S)
        
        UCL_X = X_bar_bar + A2 * R_bar
        LCL_X = X_bar_bar - A2 * R_bar
        UCL_R = D4 * R_bar
        LCL_R = D3 * R_bar
        
        df_control = pd.DataFrame({
            "Subgrupo": df_filtrado["subgrupo"].values,
            "Producto": df_filtrado["producto"].values,
            "Variable": df_filtrado["variable"].values,
            "X_barra": np.round(X_bar, 4),
            "Rango_R": np.round(R, 4),
            "Desv_S": np.round(S, 4),
            "UCL_Xbarra": np.round(UCL_X, 4),
            "LCL_Xbarra": np.round(LCL_X, 4),
            "UCL_R": np.round(UCL_R, 4),
            "LCL_R": np.round(LCL_R, 4),
            "Estado": ["FUERA DE CONTROL" if x > UCL_X or x < LCL_X else "Bajo control" for x in X_bar]
        })
        df_control.to_excel(writer, sheet_name="Graficos de control", index=False)
        
        todos = mediciones.flatten()
        stat_sw, p_sw = stats.shapiro(todos)
        sigma = np.std(todos, ddof=1)
        d2 = 2.326
        sigma_dentro = R_bar / d2
        
        LSE = np.mean(todos) + 3*sigma
        LIE = np.mean(todos) - 3*sigma
        Cp = (LSE - LIE) / (6 * sigma_dentro)
        Cpk = min((LSE - np.mean(todos))/(3*sigma_dentro), 
                  (np.mean(todos) - LIE)/(3*sigma_dentro))
        Pp = (LSE - LIE) / (6 * sigma)
        Ppk = min((LSE - np.mean(todos))/(3*sigma), 
                  (np.mean(todos) - LIE)/(3*sigma))
        
        df_stats = pd.DataFrame({
            "Estadística": [
                "N total de datos", "Media global", "Desviación estándar",
                "Mínimo", "Máximo", "Mediana",
                "Asimetría", "Curtosis",
                "Shapiro-Wilk W", "Shapiro-Wilk p-valor",
                "Normalidad", "X_barra_barra", "R_barra",
                "UCL X-barra", "LCL X-barra", "UCL R", "LCL R",
                "Cp", "Cpk", "Pp", "Ppk",
                "Fecha de reporte"
            ],
            "Valor": [
                len(todos), round(np.mean(todos),4), round(sigma,4),
                round(np.min(todos),4), round(np.max(todos),4), round(np.median(todos),4),
                round(stats.skew(todos),4), round(stats.kurtosis(todos),4),
                round(stat_sw,4), round(p_sw,4),
                "Normal" if p_sw > 0.05 else "No normal",
                round(X_bar_bar,4), round(R_bar,4),
                round(UCL_X,4), round(LCL_X,4), round(UCL_R,4), round(LCL_R,4),
                round(Cp,4), round(Cpk,4), round(Pp,4), round(Ppk,4),
                datetime.now().strftime("%Y-%m-%d %H:%M")
            ]
        })
        df_stats.to_excel(writer, sheet_name="Resumen estadistico", index=False)
        
        fuera_control = df_control[df_control["Estado"] == "FUERA DE CONTROL"]
        if len(fuera_control) > 0:
            fuera_control.to_excel(writer, sheet_name="Alertas fuera de control", index=False)
    
    buffer.seek(0)
    nombre = f"reporte_calidad_{producto}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    
    st.download_button(
        label="Descargar Excel",
        data=buffer,
        file_name=nombre,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
    st.success("Archivo Excel generado con 4 hojas: datos, control, estadísticas y alertas")

st.markdown("---")
st.subheader("Exportar datos crudos a CSV")

csv = df_filtrado.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Descargar CSV",
        data=csv,
        file_name=f"datos_calidad_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        use_container_width=True
    )

st.markdown("---")
st.subheader("Vista previa de datos")
st.dataframe(df_filtrado, use_container_width=True)