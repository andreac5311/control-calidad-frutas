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

        # Hoja 1: Portada con información general
        portada_data = {
            "Información del Análisis": [
                f"Producto: {producto}",
                f"Variable: {variable}",
                f"Analista: {df_filtrado['analista'].iloc[0] if len(df_filtrado) > 0 else 'No especificado'}",
                f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                f"Número de subgrupos: {len(df_filtrado)}",
                f"Total de mediciones: {len(df_filtrado) * 5}"
            ],
            "Resumen Ejecutivo": [
                "Este informe contiene el análisis completo de control de calidad",
                "para variables continuas, incluyendo gráficos de control,",
                "índices de capacidad y pruebas estadísticas.",
                "",
                "Generado automáticamente por el Sistema de Control de Calidad"
            ]
        }

        portada_df = pd.DataFrame(portada_data)
        portada_df.to_excel(writer, sheet_name="Portada", index=False)

        # Ajustar formato de la portada
        worksheet = writer.sheets["Portada"]
        worksheet.column_dimensions["A"].width = 30
        worksheet.column_dimensions["B"].width = 50

        # Hoja 2: Datos crudos
        df_filtrado.to_excel(writer, sheet_name="Datos crudos", index=False)

        # Hoja 3: Gráfico de control con estadísticas
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
            "X̄ (Media)": np.round(X_bar, 4),
            "R (Rango)": np.round(R, 4),
            "S (Desv. Est.)": np.round(S, 4),
            "UCL_X̄": np.round(UCL_X, 4),
            "LCL_X̄": np.round(LCL_X, 4),
            "UCL_R": np.round(UCL_R, 4),
            "LCL_R": np.round(LCL_R, 4),
            "Estado": ["FUERA DE CONTROL" if x > UCL_X or x < LCL_X else "Bajo control" for x in X_bar]
        })
        df_control.to_excel(writer, sheet_name="Grafico de control", index=False)

        # Hoja 4: Índices de capacidad
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

        # Interpretación automática de capacidad
        def interpretar_capacidad(valor):
            if valor >= 1.33:
                return "Proceso CAPAZ - Cumple con especificaciones"
            elif valor >= 1.0:
                return "Proceso MARGINAL - Requiere mejora"
            else:
                return "Proceso NO CAPAZ - Requiere acción correctiva"

        df_capacidad = pd.DataFrame({
            "Índice": ["Cp", "Cpk", "Pp", "Ppk"],
            "Valor": [round(Cp,4), round(Cpk,4), round(Pp,4), round(Ppk,4)],
            "Interpretación": [
                interpretar_capacidad(Cp),
                interpretar_capacidad(Cpk),
                interpretar_capacidad(Pp),
                interpretar_capacidad(Ppk)
            ],
            "Descripción": [
                "Capacidad potencial del proceso",
                "Capacidad real (considera descentramiento)",
                "Desempeño del proceso",
                "Desempeño real (variación total + descentramiento)"
            ]
        })
        df_capacidad.to_excel(writer, sheet_name="Indices de capacidad", index=False)

        # Hoja 5: Prueba de normalidad
        stat_ks, p_ks = stats.kstest(todos, 'norm', args=(np.mean(todos), np.std(todos)))
        stat_da, p_da = stats.normaltest(todos)

        pruebas_normal = sum([p_sw > 0.05, p_ks > 0.05, p_da > 0.05])
        asimetria = stats.skew(todos)
        curtosis_val = stats.kurtosis(todos)

        # Interpretación automática de normalidad
        if pruebas_normal >= 2 and abs(asimetria) < 0.5 and abs(curtosis_val) < 0.5:
            conclusion_normalidad = "Los datos siguen una distribución normal"
            recomendacion_normalidad = "Puede usar métodos paramétricos (t-tests, ANOVA, etc.)"
        elif pruebas_normal >= 1:
            conclusion_normalidad = "Normalidad marginal"
            recomendacion_normalidad = "Considere usar métodos no paramétricos o transformar los datos"
        else:
            conclusion_normalidad = "Los datos NO siguen una distribución normal"
            recomendacion_normalidad = "Use métodos estadísticos no paramétricos"

        df_normalidad = pd.DataFrame({
            "Prueba": ["Shapiro-Wilk", "Kolmogorov-Smirnov", "D'Agostino-Pearson"],
            "Estadístico": [round(stat_sw,4), round(stat_ks,4), round(stat_da,4)],
            "p-valor": [round(p_sw,4), round(p_ks,4), round(p_da,4)],
            "Resultado": [
                "Normal" if p_sw > 0.05 else "No normal",
                "Normal" if p_ks > 0.05 else "No normal",
                "Normal" if p_da > 0.05 else "No normal"
            ]
        })

        df_normalidad_stats = pd.DataFrame({
            "Estadística": ["Media", "Desv. Estándar", "Asimetría", "Curtosis"],
            "Valor": [
                round(np.mean(todos),4),
                round(sigma,4),
                round(asimetria,4),
                round(curtosis_val,4)
            ]
        })

        # Escribir en la hoja
        df_normalidad.to_excel(writer, sheet_name="Prueba de normalidad", index=False, startrow=0)
        df_normalidad_stats.to_excel(writer, sheet_name="Prueba de normalidad", index=False, startrow=6)

        # Añadir conclusión usando openpyxl directamente
        worksheet = writer.sheets["Prueba de normalidad"]
        worksheet["A10"] = "Conclusión:"
        worksheet["B10"] = conclusion_normalidad
        worksheet["A11"] = "Recomendación:"
        worksheet["B11"] = recomendacion_normalidad

        # Hoja 6: Conclusiones y recomendaciones
        # Contar puntos fuera de control
        fuera_control_count = len(df_control[df_control["Estado"] == "FUERA DE CONTROL"])

        # Generar conclusiones automáticas
        conclusiones = []

        if fuera_control_count == 0:
            conclusiones.append("✅ El proceso está bajo control estadístico")
            conclusiones.append("✅ No se detectaron puntos fuera de los límites de control")
            conclusiones.append("✅ La variabilidad del proceso es estable")
        else:
            conclusiones.append("⚠️ El proceso muestra señales de falta de control")
            conclusiones.append(f"⚠️ {fuera_control_count} puntos fuera de control en el gráfico X̄")
            conclusiones.append("⚠️ Se recomienda investigar las causas de los puntos fuera de control")

        # Conclusiones basadas en capacidad
        if Cpk >= 1.33 and Ppk >= 1.33:
            conclusiones.append("✅ Proceso altamente capaz - cumple con especificaciones")
            conclusiones.append("✅ La variabilidad es baja y el proceso está centrado")
        elif Cpk >= 1.0 and Ppk >= 1.0:
            conclusiones.append("⚠️ Proceso marginalmente capaz")
            conclusiones.append("⚠️ Requiere reducción de variabilidad")
        else:
            conclusiones.append("❌ Proceso no capaz")
            conclusiones.append("❌ Requiere acciones correctivas urgentes")

        # Conclusiones basadas en normalidad
        if pruebas_normal >= 2:
            conclusiones.append("✅ Los datos siguen distribución normal")
        else:
            conclusiones.append("⚠️ Los datos no siguen distribución normal")

        # Recomendaciones generales
        recomendaciones = [
            "📊 Continuar con el monitoreo regular del proceso",
            "🔧 Realizar mantenimiento preventivo de equipos",
            "📈 Implementar mejoras continuas en el proceso",
            "📝 Documentar cualquier cambio en el proceso",
            "👨‍🔬 Capacitar al personal en técnicas de muestreo"
        ]

        if fuera_control_count > 0:
            recomendaciones.insert(0, "🔍 Investigar causas de puntos fuera de control")
            recomendaciones.insert(1, "📉 Verificar si hubo cambios en el proceso o condiciones")

        if Cpk < 1.33:
            recomendaciones.insert(2, "🎯 Reducir variabilidad del proceso")
            recomendaciones.insert(3, "📏 Mejorar precisión de mediciones")

        df_conclusiones = pd.DataFrame({
            "Conclusiones": conclusiones,
            "Recomendaciones": recomendaciones
        })

        # Añadir información adicional
        info_adicional = pd.DataFrame({
            "Información": [
                f"Producto analizado: {producto}",
                f"Variable medida: {variable}",
                f"Total de subgrupos: {len(df_filtrado)}",
                f"Total de mediciones: {len(todos)}",
                f"Fecha del análisis: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                f"Analista: {df_filtrado['analista'].iloc[0] if len(df_filtrado) > 0 else 'No especificado'}"
            ]
        })

        # Escribir en la hoja
        info_adicional.to_excel(writer, sheet_name="Conclusiones", index=False, header=False)
        df_conclusiones.to_excel(writer, sheet_name="Conclusiones", index=False, startrow=8)

        # Ajustar formato de la hoja de conclusiones
        worksheet = writer.sheets["Conclusiones"]
        worksheet.column_dimensions["A"].width = 60
        worksheet.column_dimensions["B"].width = 60

    buffer.seek(0)
    nombre = f"reporte_calidad_{producto}_{variable}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"

    st.download_button(
        label="Descargar Excel Completo",
        data=buffer,
        file_name=nombre,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
    st.success("✅ Archivo Excel generado con 6 hojas completas: Portada, Datos crudos, Gráfico de control, Índices de capacidad, Prueba de normalidad y Conclusiones")

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