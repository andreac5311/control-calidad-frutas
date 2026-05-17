import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
from scipy import stats
import json

st.set_page_config(page_title="Semáforo de Calidad", page_icon="", layout="wide")
st.title("Semáforo de Calidad del Proceso")
st.markdown("---")
st.info("Visualización rápida del estado de todos los procesos monitoreados.")

DB_PATH = "data/calidad.db"

def cargar_datos():
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql("SELECT * FROM muestras WHERE tipo='Variable continua'", conn)
        conn.close()

        if df.empty:
            return df

        # Verificar si los datos están en formato JSON o en columnas separadas
        if 'muestras_json' in df.columns:
            # Formato JSON (nuevo)
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
        else:
            # Formato de columnas separadas (antiguo)
            # Verificar que existan las columnas requeridas
            columnas_requeridas = ['producto', 'variable', 'subgrupo', 'muestra1', 'muestra2', 'muestra3', 'muestra4', 'muestra5']
            columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]

            if columnas_faltantes:
                st.warning(f"Columnas faltantes en la base de datos: {', '.join(columnas_faltantes)}")
                return pd.DataFrame()

            return df[columnas_requeridas].copy()
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return pd.DataFrame()

def evaluar_proceso(mediciones):
    X_bar = np.mean(mediciones, axis=1)
    R = np.max(mediciones, axis=1) - np.min(mediciones, axis=1)
    X_bar_bar = np.mean(X_bar)
    R_bar = np.mean(R)
    A2 = 0.577
    d2 = 2.326
    UCL = X_bar_bar + A2 * R_bar
    LCL = X_bar_bar - A2 * R_bar
    sigma = R_bar / d2
    fuera = sum(1 for x in X_bar if x > UCL or x < LCL)
    pct_fuera = fuera / len(X_bar) * 100
    stat_sw, p_sw = stats.shapiro(mediciones.flatten())
    todos = mediciones.flatten()
    LSE = X_bar_bar + 3*sigma*2
    LIE = X_bar_bar - 3*sigma*2
    Cpk = min((LSE - X_bar_bar)/(3*sigma), (X_bar_bar - LIE)/(3*sigma))
    
    if pct_fuera == 0 and Cpk >= 1.33:
        estado = "VERDE"
        mensaje = "Proceso bajo control — Capaz"
        emoji = "🟢"
    elif pct_fuera <= 10 or (Cpk >= 1.0 and Cpk < 1.33):
        estado = "AMARILLO"
        mensaje = "Proceso requiere atención"
        emoji = "🟡"
    else:
        estado = "ROJO"
        mensaje = "Proceso fuera de control"
        emoji = "🔴"
    
    return {
        "estado": estado,
        "mensaje": mensaje,
        "emoji": emoji,
        "pct_fuera": pct_fuera,
        "Cpk": Cpk,
        "media": X_bar_bar,
        "normal": p_sw > 0.05,
        "p_valor": p_sw,
        "n_subgrupos": len(X_bar)
    }

df = cargar_datos()

if df.empty:
    st.warning("No hay datos. Ve a Ingreso de Datos o Simulador primero.")
    st.stop()

st.subheader("Estado general del sistema")

verdes = amarillos = rojos = 0
resultados = []

grupos = df.groupby(["producto", "variable"])
for (producto, variable), grupo in grupos:
    mediciones = grupo[["muestra1","muestra2","muestra3","muestra4","muestra5"]].values
    if len(mediciones) >= 2:
        res = evaluar_proceso(mediciones)
        res["producto"] = producto
        res["variable"] = variable
        resultados.append(res)
        if res["estado"] == "VERDE": verdes += 1
        elif res["estado"] == "AMARILLO": amarillos += 1
        else: rojos += 1

total = len(resultados)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total procesos", total)
col2.metric("Bajo control", verdes)
col3.metric("Atención", amarillos)
col4.metric("Fuera de control", rojos)

if total > 0:
    pct_ok = round(verdes/total*100, 1)
    st.progress(verdes/total if total > 0 else 0)
    st.caption(f"{pct_ok}% de procesos bajo control")

st.markdown("---")
st.subheader("Estado por proceso")

for res in resultados:
    if res["estado"] == "VERDE":
        color = "🟢"
        bg = "background-color: #d4edda; border-left: 5px solid #28a745; padding: 15px; border-radius: 8px; margin: 8px 0;"
    elif res["estado"] == "AMARILLO":
        color = "🟡"
        bg = "background-color: #fff3cd; border-left: 5px solid #ffc107; padding: 15px; border-radius: 8px; margin: 8px 0;"
    else:
        color = "🔴"
        bg = "background-color: #f8d7da; border-left: 5px solid #dc3545; padding: 15px; border-radius: 8px; margin: 8px 0;"

        st.markdown(f"""
        <div style="{bg}">
            <strong>{color} {res['producto']} — {res['variable']}</strong><br>
            {res['mensaje']} &nbsp;|&nbsp;
            Cpk: <strong>{res['Cpk']:.3f}</strong> &nbsp;|&nbsp;
            Fuera de control: <strong>{res['pct_fuera']:.1f}%</strong> &nbsp;|&nbsp;
            Media: <strong>{res['media']:.3f}</strong> &nbsp;|&nbsp;
            Normalidad: <strong>{'Sí' if res['normal'] else 'No'}</strong> &nbsp;|&nbsp;
            Subgrupos: <strong>{res['n_subgrupos']}</strong>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")
st.subheader("Tabla resumen")
if resultados:
    df_res = pd.DataFrame(resultados)[["producto","variable","estado","mensaje","pct_fuera","Cpk","media","normal","n_subgrupos"]]
    df_res.columns = ["Producto","Variable","Estado","Diagnóstico","% Fuera control","Cpk","Media","Normal","Subgrupos"]
    df_res = df_res.round(3)
    st.dataframe(df_res, use_container_width=True)

st.markdown("---")
st.subheader("Guía de interpretación del semáforo")
col1, col2, col3 = st.columns(3)
with col1:
    st.success("""
    **VERDE — Bajo control**
    - 0% de puntos fuera de control
    - Cpk ≥ 1.33
    - Proceso estable y capaz
    - **Acción:** Mantener condiciones actuales
    """)
with col2:
    st.warning("""
    **AMARILLO — Atención**
    - Hasta 10% fuera de control
    - 1.0 ≤ Cpk < 1.33
    - Proceso marginalmente capaz
    - **Acción:** Investigar causas, monitorear más frecuente
    """)
with col3:
    st.error("""
    **ROJO — Fuera de control**
    - Más del 10% fuera de control
    - Cpk < 1.0
    - Proceso no capaz
    - **Acción:** Detener, investigar y corregir inmediatamente
    """)
