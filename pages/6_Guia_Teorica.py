import streamlit as st

st.set_page_config(page_title="Guía Teórica", page_icon="", layout="wide")
st.title("Guía Teórica — Control Estadístico de Calidad")
st.markdown("---")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Gráficos de Variables",
    "Gráficos de Atributos",
    "Capacidad del Proceso",
    "Normalidad",
    "Pareto"
])

with tab1:
    st.header("Gráficos de Control por Variables")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("¿Qué son?")
        st.markdown("""
        Los gráficos de control por variables se usan cuando la característica 
        de calidad es **medible numéricamente** (peso, diámetro, pH, grados Brix).
        
        Monitorean dos aspectos del proceso:
        - **La media (X̄):** el valor central del proceso
        - **La variabilidad (R o S):** qué tan dispersos están los datos
        """)
        
        st.subheader("Gráfico X̄ - R")
        st.markdown("""
        Usado cuando el **tamaño de subgrupo es pequeño (n ≤ 10)**.
        
        **Fórmulas:**
        """)
        st.latex(r"\bar{X} = \frac{\sum x_i}{n}")
        st.latex(r"R = X_{max} - X_{min}")
        st.latex(r"UCL_{\bar{X}} = \bar{\bar{X}} + A_2 \bar{R}")
        st.latex(r"LCL_{\bar{X}} = \bar{\bar{X}} - A_2 \bar{R}")
        st.latex(r"UCL_R = D_4 \bar{R} \quad LCL_R = D_3 \bar{R}")
        
        st.info("Para n=5: A₂=0.577, D₃=0, D₄=2.115")

    with col2:
        st.subheader("Gráfico X̄ - S")
        st.markdown("""
        Usado cuando el **tamaño de subgrupo es grande (n > 10)** 
        o se requiere mayor precisión.
        
        **Fórmulas:**
        """)
        st.latex(r"S = \sqrt{\frac{\sum(x_i - \bar{x})^2}{n-1}}")
        st.latex(r"UCL_{\bar{X}} = \bar{\bar{X}} + A_3 \bar{S}")
        st.latex(r"LCL_{\bar{X}} = \bar{\bar{X}} - A_3 \bar{S}")
        st.latex(r"UCL_S = B_4 \bar{S} \quad LCL_S = B_3 \bar{S}")
        
        st.info("Para n=5: A₃=1.427, B₃=0, B₄=2.089")

    st.markdown("---")
    st.subheader("¿Cómo interpretar los gráficos?")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.success("PROCESO BAJO CONTROL")
        st.markdown("""
        - Todos los puntos dentro de UCL y LCL
        - Distribución aleatoria de puntos
        - No hay patrones ni tendencias
        - **Decisión:** Continuar el proceso normalmente
        """)
    with col2:
        st.warning("SEÑALES DE ALERTA")
        st.markdown("""
        - 2 de 3 puntos cerca de los límites
        - 8 puntos consecutivos del mismo lado
        - Tendencia de 6 puntos ascendentes o descendentes
        - **Decisión:** Investigar causa especial
        """)
    with col3:
        st.error("PROCESO FUERA DE CONTROL")
        st.markdown("""
        - Puntos fuera de UCL o LCL
        - Patrones no aleatorios evidentes
        - Ciclos repetitivos
        - **Decisión:** Detener y corregir el proceso
        """)

    st.markdown("---")
    st.subheader("Reglas de Nelson para detectar causas especiales")
    reglas = {
        "Regla 1": "1 punto más allá de 3σ (fuera de límites)",
        "Regla 2": "9 puntos consecutivos del mismo lado de la línea central",
        "Regla 3": "6 puntos consecutivos en tendencia creciente o decreciente",
        "Regla 4": "14 puntos alternando arriba y abajo",
        "Regla 5": "2 de 3 puntos más allá de 2σ del mismo lado",
        "Regla 6": "4 de 5 puntos más allá de 1σ del mismo lado",
    }
    for regla, descripcion in reglas.items():
        st.markdown(f"**{regla}:** {descripcion}")

with tab2:
    st.header("Gráficos de Control por Atributos")
    st.markdown("""
    Se usan cuando la característica de calidad es **cualitativa** 
    (conforme/no conforme, presencia/ausencia de defecto).
    """)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Gráfico p — Proporción de defectuosos")
        st.markdown("Monitorea la **proporción** de unidades defectuosas.")
        st.latex(r"p = \frac{np}{n}")
        st.latex(r"UCL_p = \bar{p} + 3\sqrt{\frac{\bar{p}(1-\bar{p})}{n}}")
        st.latex(r"LCL_p = \bar{p} - 3\sqrt{\frac{\bar{p}(1-\bar{p})}{n}}")
        st.info("Usar cuando: se reporta % de defectuosos en cada lote")

        st.markdown("---")
        st.subheader("Gráfico np — Número de defectuosos")
        st.markdown("Monitorea el **número** de unidades defectuosas.")
        st.latex(r"UCL_{np} = n\bar{p} + 3\sqrt{n\bar{p}(1-\bar{p})}")
        st.latex(r"LCL_{np} = n\bar{p} - 3\sqrt{n\bar{p}(1-\bar{p})}")
        st.info("Usar cuando: el tamaño de muestra es constante")

    with col2:
        st.subheader("Gráfico c — Número de defectos")
        st.markdown("Monitorea el **número de defectos** por unidad.")
        st.latex(r"UCL_c = \bar{c} + 3\sqrt{\bar{c}}")
        st.latex(r"LCL_c = \bar{c} - 3\sqrt{\bar{c}}")
        st.info("Usar cuando: se cuentan defectos en una unidad (ej: manchas en un fruto)")

        st.markdown("---")
        st.subheader("Gráfico u — Defectos por unidad variable")
        st.markdown("Monitorea defectos cuando el **tamaño de muestra varía**.")
        st.latex(r"u = \frac{c}{n}")
        st.latex(r"UCL_u = \bar{u} + 3\sqrt{\frac{\bar{u}}{n}}")
        st.latex(r"LCL_u = \bar{u} - 3\sqrt{\frac{\bar{u}}{n}}")
        st.info("Usar cuando: el área de oportunidad varía entre muestras")

    st.markdown("---")
    st.subheader("¿Cuándo usar cada gráfico?")
    data = {
        "Gráfico": ["p", "np", "c", "u"],
        "Tipo de dato": ["Proporción", "Conteo", "Conteo", "Tasa"],
        "Tamaño muestra": ["Variable o fijo", "Fijo", "Fijo", "Variable"],
        "Ejemplo en frutas": [
            "% mangos con manchas por lote",
            "# mangos defectuosos en 100",
            "# manchas en un mango",
            "# defectos por kg de fruta"
        ]
    }
    st.dataframe(data, use_container_width=True)

with tab3:
    st.header("Índices de Capacidad del Proceso")
    st.markdown("""
    Miden qué tan bien el proceso cumple con las especificaciones del cliente.
    Comparan la **variabilidad natural** del proceso con los **límites de especificación**.
    """)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Cp — Índice de capacidad potencial")
        st.markdown("Compara el ancho de las especificaciones con la variación del proceso.")
        st.latex(r"C_p = \frac{LSE - LIE}{6\sigma}")
        st.markdown("**No considera** si el proceso está centrado.")

        st.markdown("---")
        st.subheader("Cpk — Índice de capacidad real")
        st.markdown("Considera el **descentramiento** del proceso.")
        st.latex(r"C_{pk} = \min\left(\frac{LSE - \bar{X}}{3\sigma}, \frac{\bar{X} - LIE}{3\sigma}\right)")

    with col2:
        st.subheader("Pp — Índice de desempeño potencial")
        st.markdown("Usa la **desviación estándar total** (incluye variación entre subgrupos).")
        st.latex(r"P_p = \frac{LSE - LIE}{6s}")

        st.markdown("---")
        st.subheader("Ppk — Índice de desempeño real")
        st.markdown("Desempeño real considerando descentramiento y variación total.")
        st.latex(r"P_{pk} = \min\left(\frac{LSE - \bar{X}}{3s}, \frac{\bar{X} - LIE}{3s}\right)")

    st.markdown("---")
    st.subheader("Escala de interpretación")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.error("Índice < 1.00")
        st.markdown("Proceso **NO capaz**. Produce defectos fuera de especificación.")
    with col2:
        st.warning("1.00 ≤ Índice < 1.33")
        st.markdown("Proceso **marginalmente capaz**. Requiere monitoreo continuo.")
    with col3:
        st.success("1.33 ≤ Índice < 1.67")
        st.markdown("Proceso **capaz**. Cumple especificaciones con margen.")
    with col4:
        st.success("Índice ≥ 1.67")
        st.markdown("Proceso **altamente capaz**. Excelente control de calidad.")

    st.markdown("---")
    st.subheader("Diferencia clave: Cp vs Cpk")
    st.info("""
    - **Cp = Cpk:** El proceso está perfectamente centrado ✅
    - **Cp > Cpk:** El proceso está descentrado, aunque tenga potencial ⚠️
    - **Cp alto, Cpk bajo:** Hay variación baja pero el proceso no está en el objetivo ⚠️
    """)

with tab4:
    st.header("Pruebas de Normalidad")
    st.markdown("""
    Antes de aplicar gráficos de control por variables, es importante verificar 
    que los datos siguen una **distribución normal**, ya que los límites de control 
    se calculan asumiendo normalidad.
    """)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("Shapiro-Wilk")
        st.markdown("""
        - **Uso:** Muestras pequeñas (n < 50)
        - **H₀:** Los datos siguen distribución normal
        - **Decisión:** Si p > 0.05 → Normal ✅
        - **Recomendado** para datos de control de calidad
        """)
    with col2:
        st.subheader("Kolmogorov-Smirnov")
        st.markdown("""
        - **Uso:** Muestras grandes (n ≥ 50)
        - **H₀:** Los datos siguen distribución normal
        - **Decisión:** Si p > 0.05 → Normal ✅
        - Compara distribución empírica vs teórica
        """)
    with col3:
        st.subheader("D'Agostino-Pearson")
        st.markdown("""
        - **Uso:** Cualquier tamaño de muestra
        - **H₀:** Los datos siguen distribución normal
        - **Decisión:** Si p > 0.05 → Normal ✅
        - Basado en asimetría y curtosis
        """)

    st.markdown("---")
    st.subheader("Gráfico Q-Q (Quantile-Quantile)")
    st.markdown("""
    Herramienta visual para evaluar normalidad:
    - **Puntos sobre la línea roja:** Los datos son normales ✅
    - **Puntos alejados de la línea:** Los datos se desvían de la normalidad ❌
    - **Colas curvadas hacia arriba:** Distribución con cola derecha pesada
    - **Colas curvadas hacia abajo:** Distribución con cola izquierda pesada
    """)

    st.subheader("¿Qué hacer si los datos NO son normales?")
    st.warning("""
    - Aplicar transformaciones: logarítmica, raíz cuadrada, Box-Cox
    - Usar gráficos de control no paramétricos
    - Aumentar el tamaño de muestra
    - Investigar causas de la no normalidad (datos atípicos, mezcla de procesos)
    """)

with tab5:
    st.header("Diagrama de Pareto")
    st.markdown("""
    Herramienta gráfica basada en el **Principio de Pareto (80/20)**:
    el 80% de los problemas son causados por el 20% de las causas.
    """)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("¿Cómo se construye?")
        st.markdown("""
        1. **Identificar** y clasificar los tipos de defectos
        2. **Contar** la frecuencia de cada defecto
        3. **Ordenar** de mayor a menor frecuencia
        4. **Calcular** porcentajes acumulados
        5. **Graficar** barras + línea acumulada
        6. **Identificar** el 80% de los defectos
        """)

    with col2:
        st.subheader("¿Cómo se interpreta?")
        st.markdown("""
        - Las barras más altas = defectos más frecuentes
        - La línea roja = porcentaje acumulado
        - **Zona vital (0-80%):** Pocos defectos que causan la mayoría de problemas
        - **Zona trivial (80-100%):** Muchos defectos que tienen poco impacto
        - **Acción:** Atacar primero los defectos en la zona vital
        """)

    st.markdown("---")
    st.subheader("Aplicación en frutas y hortalizas")
    st.info("""
    **Ejemplo — Mango:**
    Si el Pareto muestra que "manchas" y "golpes" representan el 80% de los defectos,
    el esfuerzo de mejora debe enfocarse en:
    - Mejorar el manejo post-cosecha (golpes)
    - Controlar condiciones de almacenamiento (manchas)
    - En lugar de atacar todos los defectos simultáneamente
    """)

    st.subheader("Diferencia con histograma")
    data = {
        "Característica": ["Propósito", "Eje X", "Eje Y", "Ordenamiento", "Uso principal"],
        "Pareto": [
            "Priorizar problemas",
            "Categorías de defectos",
            "Frecuencia + % acumulado",
            "Mayor a menor frecuencia",
            "Toma de decisiones"
        ],
        "Histograma": [
            "Ver distribución de datos",
            "Valores de la variable",
            "Frecuencia",
            "Orden natural de valores",
            "Análisis de variabilidad"
        ]
    }
    st.dataframe(data, use_container_width=True)