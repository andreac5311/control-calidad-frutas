import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy import stats

st.set_page_config(page_title="Análisis de Atributos", page_icon="", layout="wide")
st.title("Análisis Completo de Atributos")
st.markdown("---")
st.info("Análisis estadístico completo para datos de atributos con gráficos de control, detección de outliers y diagramas de Pareto.")

# Pestañas principales
tab1, tab2, tab3 = st.tabs([
    "Gráficos de Control por Atributos",
    "Detección de Outliers",
    "Diagrama de Pareto"
])

# PESTAÑA 1: GRÁFICOS DE CONTROL POR ATRIBUTOS
with tab1:
    st.subheader("Gráficos de Control por Atributos")
    st.info("Monitorea la proporción o número de defectos en el proceso.")

    tipo_grafico = st.selectbox("Tipo de gráfico", [
        "p - Proporción de defectos",
        "np - Número de defectos",
        "c - Defectos por unidad",
        "u - Defectos por unidad variable"
    ], key="tipo_grafico_atributos")

    producto = st.selectbox("Producto", ["Mango","Banano","Aguacate","Melón","Cilantro","Sábila","Manzanilla"], key="producto_atributos")
    atributo = st.selectbox("Atributo a controlar", [
        "Presencia de manchas",
        "Daños por plagas",
        "Golpes o magulladuras",
        "Frutos podridos",
        "Defectos de color",
        "Presencia de insectos"
    ], key="atributo_atributos")
    analista = st.text_input("Analista", "", key="analista_atributos")
    n_subgrupos = st.number_input("Número de subgrupos", min_value=25, max_value=100, value=25, key="n_subgrupos_atributos")

    st.markdown("---")
    st.subheader("Ingreso de datos por subgrupo")

    if "p" in tipo_grafico or "np" in tipo_grafico:
        col1, col2 = st.columns(2)
        tamanio_n = col1.number_input("Tamaño de subgrupo (n)", min_value=1, value=50, key="tamanio_n_atributos")

        defectos = []
        cols_header = st.columns(3)
        cols_header[0].markdown("**Subgrupo**")
        cols_header[1].markdown("**Defectos**")
        cols_header[2].markdown("**Proporción**")

        for i in range(int(n_subgrupos)):
            cols = st.columns(3)
            cols[0].write(f"SG {i+1}")
            d = cols[1].number_input(f"d{i+1}", min_value=0, max_value=int(tamanio_n), key=f"d_atrib_{i}", label_visibility="collapsed")
            defectos.append(d)
            cols[2].write(f"{d/tamanio_n:.4f}")

        if st.button("Generar gráfico", use_container_width=True, key="btn_generar_grafico_atributos"):
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

            st.markdown("---")
            st.subheader("Interpretación de Resultados")

            if fuera == 0:
                st.success(f"""
                **Conclusión:** Proceso bajo control estadístico.
                - No hay puntos fuera de los límites de control
                - La proporción de defectos es estable
                - **Recomendación:** Mantener las condiciones actuales del proceso
                """)
            else:
                st.warning(f"""
                **Conclusión:** Proceso fuera de control.
                - {fuera} puntos fuera de los límites de control
                - **Recomendación:** Investigar las causas de los defectos en los subgrupos afectados
                """)

    else:
        defectos_c = []
        if "u" in tipo_grafico:
            tamanos = []

        for i in range(int(n_subgrupos)):
            cols = st.columns(2)
            cols[0].write(f"SG {i+1}")
            d = cols[1].number_input(f"c{i+1}", min_value=0, key=f"c_atrib_{i}", label_visibility="collapsed")
            defectos_c.append(d)

        if st.button("Generar gráfico", use_container_width=True, key="btn_generar_grafico_c_atributos"):
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

            st.markdown("---")
            st.subheader("Interpretación de Resultados")

            if fuera == 0:
                st.success(f"""
                **Conclusión:** Proceso bajo control estadístico.
                - No hay puntos fuera de los límites de control
                - El número de defectos es estable
                - **Recomendación:** Mantener las condiciones actuales del proceso
                """)
            else:
                st.warning(f"""
                **Conclusión:** Proceso fuera de control.
                - {fuera} puntos fuera de los límites de control
                - **Recomendación:** Investigar las causas de los defectos en los subgrupos afectados
                """)

# PESTAÑA 2: DETECCIÓN DE OUTLIERS PARA ATRIBUTOS
with tab2:
    st.subheader("Detección de Outliers en Datos de Atributos")
    st.info("Identifica subgrupos con comportamiento atípico en los datos de atributos.")

    st.markdown("---")
    st.subheader("Ingreso de datos para análisis de outliers")

    tipo_datos = st.radio("Tipo de datos", ["Proporción de defectos", "Número de defectos"], horizontal=True, key="tipo_datos_outliers")
    n_subgrupos_out = st.number_input("Número de subgrupos", min_value=25, max_value=100, value=25, key="n_subgrupos_outliers")

    if tipo_datos == "Proporción de defectos":
        tamanio_n_out = st.number_input("Tamaño de subgrupo (n)", min_value=1, value=50, key="tamanio_n_outliers")

        datos_out = []
        for i in range(int(n_subgrupos_out)):
            cols = st.columns(2)
            cols[0].write(f"SG {i+1}")
            d = cols[1].number_input(f"def{i+1}", min_value=0, max_value=int(tamanio_n_out), key=f"out_prop_{i}", label_visibility="collapsed")
            datos_out.append(d / tamanio_n_out)

    else:
        datos_out = []
        for i in range(int(n_subgrupos_out)):
            cols = st.columns(2)
            cols[0].write(f"SG {i+1}")
            d = cols[1].number_input(f"def{i+1}", min_value=0, key=f"out_num_{i}", label_visibility="collapsed")
            datos_out.append(d)

    if st.button("Analizar outliers", use_container_width=True, key="btn_analizar_outliers"):
        datos_out_array = np.array(datos_out)

        # Detección de outliers usando Z-Score
        z_scores = np.abs(stats.zscore(datos_out_array))
        umbral_z = 3.0
        outliers_z = np.where(z_scores > umbral_z)[0].tolist()

        # Detección de outliers usando IQR
        Q1 = np.percentile(datos_out_array, 25)
        Q3 = np.percentile(datos_out_array, 75)
        IQR = Q3 - Q1
        limite_inf = Q1 - 1.5 * IQR
        limite_sup = Q3 + 1.5 * IQR
        outliers_iqr = np.where((datos_out_array < limite_inf) | (datos_out_array > limite_sup))[0].tolist()

        todos_outliers = list(set(outliers_z + outliers_iqr))

        st.markdown("---")
        st.subheader("Resultados del análisis")

        col1, col2, col3 = st.columns(3)
        col1.metric("Total subgrupos", len(datos_out_array))
        col2.metric("Outliers Z-Score", len(outliers_z))
        col3.metric("Outliers IQR", len(outliers_iqr))

        # Visualización
        colores = ["red" if i in todos_outliers else "steelblue" for i in range(len(datos_out_array))]
        tamanios = [14 if i in todos_outliers else 7 for i in range(len(datos_out_array))]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            y=datos_out_array, mode="markers+lines",
            marker=dict(color=colores, size=tamanios),
            line=dict(color="lightgray", width=1),
            name="Datos"
        ))

        fig.add_hline(y=np.mean(datos_out_array), line=dict(color="green", width=2),
            annotation_text=f"Media={np.mean(datos_out_array):.4f}")

        fig.add_hline(y=np.mean(datos_out_array)+umbral_z*np.std(datos_out_array),
            line=dict(color="red", dash="dot"), annotation_text=f"Z=+{umbral_z}")

        fig.add_hline(y=np.mean(datos_out_array)-umbral_z*np.std(datos_out_array),
            line=dict(color="red", dash="dot"), annotation_text=f"Z=-{umbral_z}")

        fig.update_layout(
            title=f"Detección de outliers - {tipo_datos}",
            xaxis_title="Subgrupo",
            yaxis_title=tipo_datos,
            height=400,
            template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.subheader("Detalle de outliers detectados")

        if len(todos_outliers) == 0:
            st.success("No se detectaron subgrupos atípicos.")
        else:
            for i in sorted(todos_outliers):
                valor = datos_out_array[i]
                metodos = []
                if i in outliers_z:
                    metodos.append(f"Z-Score={z_scores[i]:.3f}")
                if i in outliers_iqr:
                    metodos.append("IQR")

                st.error(f"""
                **Outlier detectado** — Subgrupo: **{i+1}** | Valor: **{valor:.4f}**
                Métodos que lo detectaron: **{', '.join(metodos)}**
                Desviación de la media: **{abs(valor - np.mean(datos_out_array)):.4f}**
                """)

        st.markdown("---")
        st.subheader("Interpretación de Resultados")

        if len(todos_outliers) == 0:
            st.success(f"""
            **Conclusión:** No se detectaron subgrupos atípicos.
            - Todos los subgrupos muestran comportamiento consistente
            - **Recomendación:** Continuar con el monitoreo regular
            """)
        else:
            pct_outliers = len(todos_outliers) / len(datos_out_array) * 100
            st.warning(f"""
            **Conclusión:** Se detectaron {len(todos_outliers)} subgrupos atípicos ({pct_outliers:.1f}%).
            - Estos subgrupos muestran comportamiento diferente al resto
            - **Recomendación:** Investigar las causas de estos subgrupos atípicos
            """)

            st.markdown("**Posibles causas de outliers en datos de atributos:**")
            st.markdown("""
            - Errores en la inspección o conteo de defectos
            - Lotes con calidad significativamente diferente
            - Cambios en los criterios de inspección
            - Problemas temporales en el proceso de producción
            """)

# PESTAÑA 3: DIAGRAMA DE PARETO
with tab3:
    st.subheader("Diagrama de Pareto para Análisis de Defectos")
    st.info("Identifica los defectos más frecuentes para priorizar acciones de mejora (Regla 80/20).")

    producto_pareto = st.selectbox("Producto", ["Mango","Banano","Aguacate","Melón","Cilantro","Sábila","Manzanilla"], key="prod_pareto")

    defectos_lista = [
        "Manchas",
        "Daños por plagas",
        "Golpes",
        "Frutos podridos",
        "Defectos de color",
        "Presencia de insectos",
        "Material extraño"
    ]

    frecuencias = {}
    st.markdown("**Ingresa la frecuencia de cada defecto:**")
    cols = st.columns(2)
    for i, defecto in enumerate(defectos_lista):
        with cols[i % 2]:
            frecuencias[defecto] = st.number_input(defecto, min_value=0, value=0, key=f"par_{i}")

    if st.button("Generar Diagrama de Pareto", use_container_width=True, key="btn_generar_pareto"):
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
                title=f"Diagrama de Pareto - Defectos en {producto_pareto}",
                xaxis_title="Tipo de defecto",
                yaxis=dict(title="Frecuencia"),
                yaxis2=dict(title="% Acumulado", overlaying="y", side="right", range=[0,110]),
                height=450, template="plotly_white",
                legend=dict(x=0.7, y=0.95)
            )
            st.plotly_chart(fig, use_container_width=True)

            vital_80 = df_pareto[df_pareto["Porcentaje acumulado"] <= 80]["Defecto"].tolist()
            st.success(f"El 80% de defectos se concentra en: **{', '.join(vital_80) if vital_80 else df_pareto.iloc[0]['Defecto']}**")

            st.dataframe(df_pareto, use_container_width=True)

            st.markdown("---")
            st.subheader("Interpretación de Resultados")

            if len(vital_80) <= 2:
                st.success(f"""
                **Conclusión:** Enfoque claro para la mejora.
                - Solo {len(vital_80)} tipos de defectos representan el 80% del problema
                - **Recomendación:** Priorizar acciones correctivas en: **{', '.join(vital_80)}**
                - Esto tendrá el mayor impacto en la reducción total de defectos
                """)
            else:
                st.warning(f"""
                **Conclusión:** Varios defectos contribuyen significativamente.
                - {len(vital_80)} tipos de defectos representan el 80% del problema
                - **Recomendación:** Analizar causas raíz de los defectos más frecuentes
                - Considerar un plan de mejora por etapas
                """)

            st.markdown("**Acción recomendada según el principio de Pareto:**")
            st.markdown(f"""
            1. **Enfocarse en los vitales pocos:** {', '.join(vital_80)}
            2. **Analizar causas raíz** de estos defectos específicos
            3. **Implementar mejoras** dirigidas a los defectos prioritarios
            4. **Monitorear resultados** y ajustar según sea necesario
            """)