import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import json

st.set_page_config(page_title="Reglas de Nelson", page_icon="", layout="wide")
st.title("Detección Automática — Reglas de Nelson")
st.markdown("---")
st.info("Las reglas de Nelson detectan patrones anormales en el proceso, incluso cuando los puntos están dentro de los límites de control.")

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

def detectar_nelson(X_bar, media, sigma):
    alertas = {i: [] for i in range(1, 7)}
    n = len(X_bar)
    
    for i, x in enumerate(X_bar):
        if x > media + 3*sigma or x < media - 3*sigma:
            alertas[1].append(i)
    
    for i in range(8, n+1):
        ventana = X_bar[i-8:i]
        if all(v > media for v in ventana) or all(v < media for v in ventana):
            alertas[2].extend(range(i-8, i))
    
    for i in range(6, n+1):
        ventana = X_bar[i-6:i]
        if all(ventana[j] < ventana[j+1] for j in range(5)) or \
           all(ventana[j] > ventana[j+1] for j in range(5)):
            alertas[3].extend(range(i-6, i))
    
    for i in range(14, n+1):
        ventana = X_bar[i-14:i]
        alternan = all(
            (ventana[j] > ventana[j+1]) != (ventana[j+1] > ventana[j+2])
            for j in range(12)
        )
        if alternan:
            alertas[4].extend(range(i-14, i))
    
    for i in range(3, n+1):
        ventana = X_bar[i-3:i]
        count = sum(1 for v in ventana if v > media + 2*sigma or v < media - 2*sigma)
        if count >= 2:
            alertas[5].extend(range(i-3, i))
    
    for i in range(5, n+1):
        ventana = X_bar[i-5:i]
        count = sum(1 for v in ventana if v > media + sigma or v < media - sigma)
        if count >= 4:
            alertas[6].extend(range(i-5, i))
    
    for k in alertas:
        alertas[k] = list(set(alertas[k]))
    
    return alertas

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
X_bar = np.mean(mediciones, axis=1)
R = np.max(mediciones, axis=1) - np.min(mediciones, axis=1)
R_bar = np.mean(R)
d2 = 2.326
sigma = R_bar / d2
media = np.mean(X_bar)
A2 = 0.577
UCL = media + A2 * R_bar
LCL = media - A2 * R_bar

alertas = detectar_nelson(X_bar, media, sigma)
total_alertas = sum(len(v) for v in alertas.values())

st.markdown("---")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Subgrupos analizados", len(X_bar))
col2.metric("Media global", f"{media:.4f}")
col3.metric("Sigma estimado", f"{sigma:.4f}")
if total_alertas == 0:
    col4.metric("Alertas detectadas", "0 — Proceso OK")
else:
    col4.metric("Alertas detectadas", total_alertas)

st.markdown("---")
st.subheader("Gráfico con alertas marcadas")

colores = ["green"] * len(X_bar)
for regla, indices in alertas.items():
    for i in indices:
        if i < len(colores):
            colores[i] = "red"

fig = go.Figure()

fig.add_shape(type="rect", x0=-0.5, x1=len(X_bar)-0.5,
    y0=media+sigma, y1=media+2*sigma,
    fillcolor="yellow", opacity=0.1, line_width=0)
fig.add_shape(type="rect", x0=-0.5, x1=len(X_bar)-0.5,
    y0=media-2*sigma, y1=media-sigma,
    fillcolor="yellow", opacity=0.1, line_width=0)
fig.add_shape(type="rect", x0=-0.5, x1=len(X_bar)-0.5,
    y0=media+2*sigma, y1=UCL,
    fillcolor="orange", opacity=0.1, line_width=0)
fig.add_shape(type="rect", x0=-0.5, x1=len(X_bar)-0.5,
    y0=LCL, y1=media-2*sigma,
    fillcolor="orange", opacity=0.1, line_width=0)

fig.add_trace(go.Scatter(
    y=X_bar, mode="lines+markers",
    marker=dict(color=colores, size=10, symbol="circle"),
    line=dict(color="gray", width=1.5),
    name="X̄"
))

fig.add_hline(y=UCL, line=dict(color="red", dash="dash", width=2),
    annotation_text=f"UCL={UCL:.3f}", annotation_position="right")
fig.add_hline(y=media+2*sigma, line=dict(color="orange", dash="dot", width=1),
    annotation_text="μ+2σ", annotation_position="right")
fig.add_hline(y=media+sigma, line=dict(color="yellow", dash="dot", width=1),
    annotation_text="μ+1σ", annotation_position="right")
fig.add_hline(y=media, line=dict(color="green", width=2),
    annotation_text=f"CL={media:.3f}", annotation_position="right")
fig.add_hline(y=media-sigma, line=dict(color="yellow", dash="dot", width=1),
    annotation_text="μ-1σ", annotation_position="right")
fig.add_hline(y=media-2*sigma, line=dict(color="orange", dash="dot", width=1),
    annotation_text="μ-2σ", annotation_position="right")
fig.add_hline(y=LCL, line=dict(color="red", dash="dash", width=2),
    annotation_text=f"LCL={LCL:.3f}", annotation_position="right")

fig.update_layout(
    title=f"Gráfico X̄ con Reglas de Nelson — {variable} ({producto})",
    xaxis_title="Subgrupo",
    yaxis_title="X̄",
    height=500,
    template="plotly_white",
    showlegend=False
)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.subheader("Detalle de alertas detectadas")

REGLAS_DESC = {
    1: ("Regla 1", "1 punto más allá de 3σ (fuera de límites de control)"),
    2: ("Regla 2", "9 puntos consecutivos del mismo lado de la línea central"),
    3: ("Regla 3", "6 puntos consecutivos en tendencia creciente o decreciente"),
    4: ("Regla 4", "14 puntos alternando arriba y abajo"),
    5: ("Regla 5", "2 de 3 puntos más allá de 2σ del mismo lado"),
    6: ("Regla 6", "4 de 5 puntos más allá de 1σ del mismo lado"),
}

hay_alertas = False
for regla, indices in alertas.items():
    nombre, descripcion = REGLAS_DESC[regla]
    if len(indices) > 0:
        hay_alertas = True
        subgrupos = [i+1 for i in sorted(indices)]
        st.error(f"**{nombre}:** {descripcion}\n\nSubgrupos afectados: {subgrupos}")

if not hay_alertas:
    st.success("No se detectaron violaciones a las reglas de Nelson. El proceso está bajo control estadístico.")

st.markdown("---")
st.subheader("Referencia de las Reglas de Nelson")
for regla, (nombre, descripcion) in REGLAS_DESC.items():
    with st.expander(f"{nombre} — {descripcion}"):
        if regla == 1:
            st.markdown("""
            **¿Qué indica?** Una causa especial de variación de gran magnitud.
            Un punto fuera de los límites es estadísticamente improbable (0.27% de probabilidad).
            
            **Causas comunes en frutas/hortalizas:**
            - Error de medición
            - Lote de diferente procedencia
            - Falla en el equipo de medición
            - Cambio brusco en condiciones ambientales
            
            **Acción recomendada:** Investigar inmediatamente el subgrupo afectado.
            """)
        elif regla == 2:
            st.markdown("""
            **¿Qué indica?** El proceso se desplazó de su valor central.
            9 puntos del mismo lado tiene probabilidad de 0.4% si el proceso es aleatorio.
            
            **Causas comunes:**
            - Cambio gradual en la madurez del producto
            - Cambio de proveedor
            - Ajuste incorrecto del proceso
            
            **Acción recomendada:** Verificar si hubo cambio en materiales o condiciones.
            """)
        elif regla == 3:
            st.markdown("""
            **¿Qué indica?** Tendencia sistemática en el proceso — algo está cambiando progresivamente.
            
            **Causas comunes:**
            - Desgaste de herramienta de medición
            - Cambio progresivo de temperatura
            - Proceso de maduración acelerada
            
            **Acción recomendada:** Identificar la fuente del cambio progresivo.
            """)
        elif regla == 4:
            st.markdown("""
            **¿Qué indica?** Patrón sistemático no aleatorio — posible mezcla de dos procesos.
            
            **Causas comunes:**
            - Mezcla de dos lotes diferentes
            - Dos operarios con técnicas distintas
            - Dos máquinas o equipos alternando
            
            **Acción recomendada:** Verificar si hay mezcla de fuentes de producción.
            """)
        elif regla == 5:
            st.markdown("""
            **¿Qué indica?** La variabilidad del proceso aumentó aunque los puntos no salgan de control.
            
            **Causas comunes:**
            - Aumento en variación de materia prima
            - Condiciones ambientales inestables
            
            **Acción recomendada:** Revisar fuentes de variabilidad en el proceso.
            """)
        elif regla == 6:
            st.markdown("""
            **¿Qué indica?** El proceso perdió variabilidad natural — posible estratificación de datos.
            
            **Causas comunes:**
            - Muestreo inadecuado
            - Datos redondeados artificialmente
            - Instrumento con baja resolución
            
            **Acción recomendada:** Revisar el método de muestreo y los instrumentos.
            """)