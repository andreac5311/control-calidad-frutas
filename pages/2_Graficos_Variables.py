import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy import stats
import json

st.set_page_config(page_title="Análisis de Variables Continuas", page_icon="", layout="wide")
st.title("Análisis Completo de Variables Continuas")
st.markdown("---")
st.info("Análisis estadístico completo con gráficos de control, reglas de Nelson, detección de outliers, capacidad del proceso y pruebas de normalidad.")

DB_PATH = "data/calidad.db"

def cargar_datos():
    try:
        conn = sqlite3.connect(DB_PATH)
        # Corregir filtro para incluir la tilde
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
            # Filtrar solo las columnas que existen y son de tipo variable continua
            df_filtrado = df[df['tipo'] == 'Variable continua'].copy()

            # Asegurarse de que existan las columnas de muestras
            columnas_muestras = ['muestra1', 'muestra2', 'muestra3', 'muestra4', 'muestra5']
            for col in columnas_muestras:
                if col not in df_filtrado.columns:
                    df_filtrado[col] = np.nan

            return df_filtrado[['producto', 'variable', 'subgrupo', 'muestra1', 'muestra2', 'muestra3', 'muestra4', 'muestra5']]
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
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
todos = mediciones.flatten()

# Datos comunes para todas las pestañas
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

# Funciones comunes
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

# Pestañas principales
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Gráficos de Control",
    "Reglas de Nelson",
    "Detección de Outliers",
    "Capacidad del Proceso",
    "Pruebas de Normalidad"
])

# PESTAÑA 1: GRÁFICOS DE CONTROL
with tab1:
    st.subheader("Gráficos de Control por Variables")
    st.markdown("Selecciona el tipo de gráfico para monitorear la variabilidad del proceso.")

    tipo_grafico = st.radio("Selecciona tipo de gráfico", ["X̄ - R", "X̄ - S"], horizontal=True)

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

        st.markdown("---")
        st.subheader("Interpretación de Resultados")
        if fuera1 == 0 and fuera2 == 0:
            st.success("""
            **Conclusión:** El proceso está bajo control estadístico.
            - No hay puntos fuera de los límites de control
            - La variabilidad del proceso es estable
            - **Recomendación:** Mantener las condiciones actuales del proceso
            """)
        else:
            st.warning("""
            **Conclusión:** El proceso muestra señales de falta de control.
            - Investigue las causas de los puntos fuera de control
            - Verifique si hubo cambios en el proceso o en las condiciones de medición
            - **Recomendación:** Use las Reglas de Nelson para identificar patrones
            """)

    else:  # X̄ - S
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
        st.subheader("Interpretación de Resultados")
        if fuera1 == 0 and fuera2 == 0:
            st.success("""
            **Conclusión:** El proceso está bajo control estadístico.
            - La media y la desviación estándar son estables
            - **Recomendación:** Continuar con el monitoreo regular
            """)
        else:
            st.warning("""
            **Conclusión:** Variabilidad del proceso no controlada.
            - Revise los puntos fuera de control en el gráfico S
            - **Recomendación:** Verifique la consistencia de las mediciones
            """)

    st.markdown("---")
    st.subheader("Tabla de Valores")
    tabla = pd.DataFrame({"Subgrupo": range(1, len(X_bar)+1), "X̄": X_bar, "R": R, "S": S})
    st.dataframe(tabla.style.format({"X̄": "{:.4f}", "R": "{:.4f}", "S": "{:.4f}"}), use_container_width=True)

# PESTAÑA 3: DETECCIÓN DE OUTLIERS
with tab3:
    st.subheader("Detección Automática de Datos Atípicos")
    st.info("Identifica automáticamente datos atípicos usando múltiples métodos estadísticos.")

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

    tab1_out, tab2_out, tab3_out = st.tabs(["Serie de datos", "Boxplot", "Histograma"])

    with tab1_out:
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

    with tab2_out:
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

    with tab3_out:
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
    st.subheader("Interpretación de Resultados")

    if len(todos_outliers) == 0:
        st.success("""
        **Conclusión:** No se detectaron datos atípicos.
        - Los datos muestran consistencia y calidad uniforme
        - **Recomendación:** Continuar con el monitoreo regular
        """)
    else:
        pct_outliers = len(todos_outliers) / len(todos) * 100
        if pct_outliers < 5:
            st.warning(f"""
            **Conclusión:** Se detectaron algunos outliers ({pct_outliers:.1f}%).
            - La mayoría de los datos son consistentes
            - **Recomendación:** Investigar las causas de los outliers detectados
            """)
        else:
            st.error(f"""
            **Conclusión:** Alto porcentaje de outliers ({pct_outliers:.1f}%).
            - Posible problema sistemático en el proceso
            - **Recomendación:** Revisar todo el proceso de medición y muestreo
            """)

        st.markdown("**Posibles causas de outliers en frutas/hortalizas:**")
        st.markdown("""
        - Errores de medición o calibración del equipo
        - Frutos con defectos o dañados
        - Variabilidad natural extrema
        - Errores en el registro de datos
        """)

# PESTAÑA 4: CAPACIDAD DEL PROCESO
with tab4:
    st.subheader("Índices de Capacidad del Proceso")
    st.info("Evalúa si el proceso es capaz de cumplir con las especificaciones del cliente.")

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
        st.subheader("Interpretación de Resultados")

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

        st.markdown("---")
        st.subheader("Recomendaciones Específicas")

        if Cpk >= 1.33 and Ppk >= 1.33:
            st.success("""
            **Conclusión:** Proceso altamente capaz.
            - El proceso cumple con las especificaciones
            - La variabilidad es baja y el proceso está centrado
            - **Recomendación:** Mantener las condiciones actuales y monitorear periódicamente
            """)
        elif Cpk >= 1.0 and Ppk >= 1.0:
            st.warning("""
            **Conclusión:** Proceso marginalmente capaz.
            - El proceso cumple mínimamente con las especificaciones
            - **Recomendación:** Reducir la variabilidad del proceso
            - Considerar mejorar la precisión de las mediciones
            """)
        else:
            st.error("""
            **Conclusión:** Proceso no capaz.
            - El proceso no cumple con las especificaciones
            - **Recomendación:** Acciones correctivas urgentes necesarias
            """)
            if abs(media - objetivo) > (LSE - LIE)/6:
                st.markdown("- **Problema principal:** Descentramiento del proceso")
                st.markdown("- **Acción:** Ajustar el proceso para centrarlo en el valor objetivo")
            else:
                st.markdown("- **Problema principal:** Excesiva variabilidad")
                st.markdown("- **Acción:** Reducir la variabilidad del proceso (mejorar equipos, entrenamiento, condiciones)")

# PESTAÑA 2: REGLAS DE NELSON
with tab2:
    st.subheader("Detección Automática — Reglas de Nelson")
    st.info("Las reglas de Nelson detectan patrones anormales en el proceso, incluso cuando los puntos están dentro de los límites de control.")

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

    R_bar = np.mean(R)
    d2 = 2.326
    sigma = R_bar / d2
    media = np.mean(X_bar)
    A2 = 0.577
    UCL = media + A2 * R_bar
    LCL = media - A2 * R_bar

    alertas = detectar_nelson(X_bar, media, sigma)
    total_alertas = sum(len(v) for v in alertas.values())

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
    st.subheader("Interpretación de Resultados")

    if not hay_alertas:
        st.success("""
        **Conclusión:** Proceso estable sin patrones anormales.
        - No se detectaron violaciones a las reglas de Nelson
        - El proceso muestra variación aleatoria natural
        - **Recomendación:** Continuar con el monitoreo regular
        """)
    else:
        st.warning("""
        **Conclusión:** Se detectaron patrones no aleatorios en el proceso.
        - Cada regla violada indica un tipo específico de problema
        - **Recomendación:** Investigue las causas raíz de los patrones detectados
        """)

        for regla, (nombre, descripcion) in REGLAS_DESC.items():
            if len(alertas[regla]) > 0:
                with st.expander(f"🔍 Interpretación de {nombre}"):
                    if regla == 1:
                        st.markdown(f"""
                        **Causas probables en frutas/hortalizas:**
                        - Error de medición o calibración
                        - Lote de diferente procedencia o calidad
                        - Falla en el equipo de medición
                        - Cambio brusco en condiciones ambientales

                        **Acción recomendada:**
                        - Verifique el subgrupo {alertas[regla][0]+1}
                        - Revise el equipo de medición
                        - Investigue si hubo cambios en el proceso
                        """)
                    elif regla == 2:
                        st.markdown(f"""
                        **Causas probables:**
                        - Cambio gradual en la madurez del producto
                        - Cambio de proveedor o variedad
                        - Ajuste incorrecto del proceso

                        **Acción recomendada:**
                        - Revise los últimos {len(alertas[regla])} subgrupos
                        - Verifique si hubo cambios en materiales o condiciones
                        """)
                    elif regla == 3:
                        st.markdown(f"""
                        **Causas probables:**
                        - Desgaste de herramienta de medición
                        - Cambio progresivo de temperatura/humedad
                        - Proceso de maduración acelerada

                        **Acción recomendada:**
                        - Identifique la fuente del cambio progresivo
                        - Revise el historial de {len(alertas[regla])} subgrupos
                        """)
                    elif regla == 4:
                        st.markdown(f"""
                        **Causas probables:**
                        - Mezcla de dos lotes diferentes
                        - Dos operarios con técnicas distintas
                        - Dos máquinas o equipos alternando

                        **Acción recomendada:**
                        - Verifique si hay mezcla de fuentes de producción
                        - Revise el proceso de muestreo
                        """)
                    elif regla == 5:
                        st.markdown(f"""
                        **Causas probables:**
                        - Aumento en variación de materia prima
                        - Condiciones ambientales inestables

                        **Acción recomendada:**
                        - Revise fuentes de variabilidad en el proceso
                        - Verifique los subgrupos afectados
                        """)
                    elif regla == 6:
                        st.markdown(f"""
                        **Causas probables:**
                        - Muestreo inadecuado
                        - Datos redondeados artificialmente
                        - Instrumento con baja resolución

                        **Acción recomendada:**
                        - Revise el método de muestreo
                        - Verifique la precisión de los instrumentos
                        """)

# PESTAÑA 5: PRUEBAS DE NORMALIDAD
with tab5:
    st.subheader("Pruebas de Normalidad")
    st.info("Evalúa si los datos siguen una distribución normal, requisito para muchos análisis estadísticos.")

    st.markdown("---")
    st.subheader("Estadísticas descriptivas")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Media", f"{np.mean(todos):.4f}")
    col2.metric("Desv. estándar", f"{np.std(todos, ddof=1):.4f}")
    col3.metric("Mínimo", f"{np.min(todos):.4f}")
    col4.metric("Máximo", f"{np.max(todos):.4f}")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Mediana", f"{np.median(todos):.4f}")
    col2.metric("Curtosis", f"{stats.kurtosis(todos):.4f}")
    col3.metric("Asimetría", f"{stats.skew(todos):.4f}")
    col4.metric("N datos", f"{len(todos)}")

    st.markdown("---")
    st.subheader("Pruebas de normalidad")

    stat_sw, p_sw = stats.shapiro(todos)
    stat_ks, p_ks = stats.kstest(todos, 'norm', args=(np.mean(todos), np.std(todos)))
    stat_da, p_da = stats.normaltest(todos)

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

    (osm, osr), (slope, intercept, r) = stats.probplot(todos)
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
    x_range = np.linspace(min(todos)-2*np.std(todos), max(todos)+2*np.std(todos), 200)
    curva = stats.norm.pdf(x_range, np.mean(todos), np.std(todos))
    fig2 = go.Figure()
    fig2.add_trace(go.Histogram(x=todos, nbinsx=15, histnorm="probability density",
        marker=dict(color="steelblue", opacity=0.7), name="Datos"))
    fig2.add_trace(go.Scatter(x=x_range, y=curva, mode="lines",
        line=dict(color="red", width=2), name="Curva normal"))
    fig2.update_layout(title="Histograma de frecuencias",
        xaxis_title=variable, yaxis_title="Densidad",
        height=400, template="plotly_white")
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    st.subheader("Interpretación de Resultados")

    # Contar cuántas pruebas indican normalidad
    pruebas_normal = sum([p_sw > 0.05, p_ks > 0.05, p_da > 0.05])
    asimetria = stats.skew(todos)
    curtosis = stats.kurtosis(todos)

    if pruebas_normal >= 2 and abs(asimetria) < 0.5 and abs(curtosis) < 0.5:
        st.success("""
        **Conclusión:** Los datos siguen una distribución normal.
        - La mayoría de las pruebas estadísticas confirman normalidad
        - La asimetría y curtosis están dentro de rangos aceptables
        - **Recomendación:** Puede usar métodos paramétricos (t-tests, ANOVA, etc.)
        """)
    elif pruebas_normal >= 1:
        st.warning("""
        **Conclusión:** Normalidad marginal.
        - Algunas pruebas indican normalidad, otras no
        - **Recomendación:** Considere usar métodos no paramétricos o transformar los datos
        - Pruebe transformaciones como log(x) o sqrt(x) si los datos son positivos
        """)
    else:
        st.error("""
        **Conclusión:** Los datos no siguen una distribución normal.
        - La mayoría de las pruebas rechazan la normalidad
        - **Recomendación:** Use métodos estadísticos no paramétricos
        - Considere transformaciones de datos o modelos no normales
        """)

    if abs(asimetria) > 0.5:
        st.markdown(f"- **Asimetría detectada:** {'Derecha' if asimetria > 0 else 'Izquierda'} (valor: {asimetria:.3f})")
    if abs(curtosis) > 0.5:
        st.markdown(f"- **Curtosis detectada:** {'Leptocúrtica' if curtosis > 0 else 'Platicúrtica'} (valor: {curtosis:.3f})")

