import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy import stats
import json

st.set_page_config(page_title="Detección de Outliers", page_icon="", layout="wide")
st.title("Detección Automática de Datos Atípicos")
st.markdown("---")
st.info("Identifica automáticamente datos atípicos usando múltiples métodos estadísticos.")

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

def detectar_zscore(datos, umbral=3.0):
    z_scores = np.abs(stats.zscore(datos))
    return np.where(z_scores > umbral)[0].tolist(), z_scores

def detectar_iqr(datos):
    Q1 = np.percentile(datos, 25)
    Q3 = np.percentile(datos, 75)
    IQR = Q3 - Q1
    limite_inf = Q1 - 1.5 * IQR
    limite_sup = Q3 + 1.5 * IQR
    outliers = np.where((datos < limite_inf) | (datos > limite_sup))[0].tolist()
    return outliers, Q1, Q3, IQR, limite_inf, limite_sup

def detectar_grubbs(datos, alpha=0.05):
    n = len(datos)
    media = np.mean(datos)
    std = np.std(datos, ddof=1)
    G = np.abs(datos - media) / std
    idx_max = np.argmax(G)
    G_max = G[idx_max]
    t_crit = stats.t.ppf(1 - alpha/(2*n), n-2)
    G_crit = ((n-1)/np.sqrt(n)) * np.sqrt(t_crit**2/(n-2+t_crit**2))
    es_outlier = G_max > G_crit
    return idx_max if es_outlier else None, G_max, G_crit

df = cargar_datos()

if df.empty:
    st.warning("No hay datos. Ve a Ingreso de Datos o Simulador primero.")
    st.stop()

col1, col2 = st.columns(2)
with col1:
    producto = st.selectbox("Producto", df["producto"].unique())
with col2:
    variable = st.selectbox("Variable", df[df["producto"]==producto]["variable"].unique())

df_f = df[(df["producto"]==producto) & (df["variable"]==variable)]
mediciones = df_f[["muestra1","muestra2","muestra3","muestra4","muestra5"]].values
todos = mediciones.flatten()
indices_todos = np.arange(len(todos))

st.markdown("---")
st.subheader("Configuración de métodos")
col1, col2, col3 = st.columns(3)
with col1:
    usar_zscore = st.checkbox("Z-Score", value=True)
    umbral_z = st.slider("Umbral Z-Score", 2.0, 4.0, 3.0, 0.1)
with col2:
    usar_iqr = st.checkbox("Rango Intercuartílico (IQR)", value=True)
with col3:
    usar_grubbs = st.checkbox("Test de Grubbs", value=True)
    alpha_grubbs = st.select_slider("Nivel α", options=[0.01, 0.05, 0.10], value=0.05)

st.markdown("---")

outliers_zscore = []
outliers_iqr = []
outlier_grubbs = None
z_scores = None

if usar_zscore:
    outliers_zscore, z_scores = detectar_zscore(todos, umbral_z)

if usar_iqr:
    outliers_iqr, Q1, Q3, IQR, lim_inf, lim_sup = detectar_iqr(todos)

if usar_grubbs:
    outlier_grubbs, G_max, G_crit = detectar_grubbs(todos, alpha_grubbs)

todos_outliers = list(set(outliers_zscore + outliers_iqr + 
    ([outlier_grubbs] if outlier_grubbs is not None else [])))

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total datos", len(todos))
col2.metric("Outliers Z-Score", len(outliers_zscore))
col3.metric("Outliers IQR", len(outliers_iqr))
col4.metric("Outliers totales", len(todos_outliers))

st.markdown("---")
st.subheader("Visualización de outliers")

tab1, tab2, tab3 = st.tabs(["Serie de datos", "Boxplot", "Histograma"])

with tab1:
    colores = ["red" if i in todos_outliers else "steelblue" for i in range(len(todos))]
    tamanios = [14 if i in todos_outliers else 7 for i in range(len(todos))]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=todos, mode="markers+lines",
        marker=dict(color=colores, size=tamanios),
        line=dict(color="lightgray", width=1),
        name="Datos"
    ))
    
    if usar_iqr:
        fig.add_hline(y=lim_sup, line=dict(color="orange", dash="dash"),
            annotation_text=f"Límite sup IQR={lim_sup:.3f}")
        fig.add_hline(y=lim_inf, line=dict(color="orange", dash="dash"),
            annotation_text=f"Límite inf IQR={lim_inf:.3f}")
    
    fig.add_hline(y=np.mean(todos), line=dict(color="green", width=2),
        annotation_text=f"Media={np.mean(todos):.3f}")
    
    if usar_zscore:
        fig.add_hline(y=np.mean(todos)+umbral_z*np.std(todos,ddof=1),
            line=dict(color="red", dash="dot"),
            annotation_text=f"Z=+{umbral_z}")
        fig.add_hline(y=np.mean(todos)-umbral_z*np.std(todos,ddof=1),
            line=dict(color="red", dash="dot"),
            annotation_text=f"Z=-{umbral_z}")
    
    fig.update_layout(
        title=f"Serie de datos — {variable} ({producto})",
        xaxis_title="Observación",
        yaxis_title=variable,
        height=420,
        template="plotly_white"
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    fig2 = go.Figure()
    fig2.add_trace(go.Box(
        y=todos,
        name=variable,
        marker=dict(color="steelblue", outliercolor="red",
            line=dict(outliercolor="red", outlierwidth=2)),
        boxpoints="outliers",
        jitter=0.3,
        pointpos=-1.8
    ))
    fig2.update_layout(
        title=f"Boxplot — {variable} ({producto})",
        yaxis_title=variable,
        height=420,
        template="plotly_white"
    )
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    fig3 = go.Figure()
    fig3.add_trace(go.Histogram(
        x=todos, nbinsx=20,
        marker=dict(color="steelblue", opacity=0.7),
        name="Datos"
    ))
    for i in todos_outliers:
        fig3.add_vline(x=todos[i], line=dict(color="red", dash="dash", width=1))
    fig3.update_layout(
        title=f"Histograma con outliers marcados — {variable} ({producto})",
        xaxis_title=variable,
        yaxis_title="Frecuencia",
        height=420,
        template="plotly_white"
    )
    st.plotly_chart(fig3, use_container_width=True)

st.markdown("---")
st.subheader("Detalle de outliers detectados")

if len(todos_outliers) == 0:
    st.success("No se detectaron datos atípicos con los métodos seleccionados.")
else:
    for i in sorted(todos_outliers):
        subgrupo = i // 5 + 1
        muestra = i % 5 + 1
        valor = todos[i]
        metodos = []
        if i in outliers_zscore:
            metodos.append(f"Z-Score={z_scores[i]:.3f}")
        if i in outliers_iqr:
            metodos.append("IQR")
        if outlier_grubbs == i:
            metodos.append(f"Grubbs (G={G_max:.3f})")

        st.error(f"""
        **Outlier detectado** — Valor: `{valor:.4f}`
        Subgrupo: **{subgrupo}** | Muestra: **{muestra}**
        Métodos que lo detectaron: **{', '.join(metodos)}**
        Desviación de la media: **{abs(valor - np.mean(todos)):.4f}**
        ({abs(valor - np.mean(todos))/np.std(todos,ddof=1):.2f} desviaciones estándar)
        """)

st.markdown("---")
st.subheader("Comparación de métodos")

data_comp = {
    "Método": ["Z-Score", "IQR", "Grubbs"],
    "Ventaja": [
        "Simple e intuitivo",
        "Robusto, no asume normalidad",
        "Test formal con nivel de significancia"
    ],
    "Limitación": [
        "Sensible a distribuciones no normales",
        "Puede perder outliers extremos",
        "Asume normalidad, solo detecta uno a la vez"
    ],
    "Cuándo usarlo": [
        "Datos normales, n grande",
        "Datos con sesgo, exploración inicial",
        "Confirmación estadística formal"
    ],
    "Outliers detectados": [
        len(outliers_zscore),
        len(outliers_iqr),
        1 if outlier_grubbs is not None else 0
    ]
}
st.dataframe(pd.DataFrame(data_comp), use_container_width=True)