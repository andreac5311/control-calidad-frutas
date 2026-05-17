import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io
import json
import numpy as np

st.set_page_config(page_title="Ingreso de Datos", page_icon="", layout="wide")
st.title("Ingreso de Datos")
st.markdown("---")

DB_PATH = "data/calidad.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS muestras (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        producto TEXT, tipo TEXT, variable TEXT,
        unidad TEXT, analista TEXT, fecha TEXT,
        subgrupo INTEGER, muestras_json TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

with st.form("ingreso"):
    st.subheader("Informacion de trazabilidad")
    col1, col2, col3 = st.columns(3)
    with col1:
        producto = st.selectbox("Producto", ["Mango","Banano","Aguacate","Melon","Cilantro","Sabila","Manzanilla","Menta","Otro"])
        tipo = st.selectbox("Tipo de control", ["Variable continua", "Atributo"])
    with col2:
        variable = st.selectbox("Variable a controlar", ["Peso (g)","Diametro (cm)","Grados Brix","pH","Firmeza","Contenido de humedad (%)","Otro"])
        unidad = st.text_input("Unidad de medida", "g")
    with col3:
        analista = st.text_input("Nombre del analista", "")
        fecha = st.date_input("Fecha de muestreo", datetime.today())

    st.markdown("---")
    st.subheader("Ingreso de muestras por subgrupo")
    col1, col2 = st.columns(2)
    with col1:
        n_subgrupos = st.number_input("Numero de subgrupos", min_value=25, max_value=100, value=25)
    with col2:
        n_muestras = st.number_input("Muestras por subgrupo", min_value=2, max_value=15, value=5)

    st.info(f"Ingresa {n_muestras} mediciones por subgrupo")

    datos = []
    for i in range(int(n_subgrupos)):
        cols = st.columns(n_muestras + 1)
        cols[0].markdown(f"**SG {i+1}**")
        fila = [cols[j+1].number_input(f"M{j+1}", key=f"sg{i}m{j}", label_visibility="collapsed") for j in range(n_muestras)]
        datos.append(fila)

    submitted = st.form_submit_button("Guardar datos", use_container_width=True)

    if submitted:
        conn = sqlite3.connect(DB_PATH)
        for i, fila in enumerate(datos):
            muestras_data = {
                "muestras": fila,
                "n_muestras": n_muestras,
                "media": float(np.mean(fila)) if fila else 0
            }
            conn.execute("INSERT INTO muestras VALUES (NULL,?,?,?,?,?,?,?,?)",
                (producto, tipo, variable, unidad, analista, str(fecha), i+1, json.dumps(muestras_data)))
        conn.commit()
        conn.close()
        st.success(f"Datos guardados correctamente: {n_subgrupos} subgrupos con {n_muestras} muestras cada uno")

st.markdown("---")
st.subheader("Datos registrados")
try:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM muestras", conn)
    conn.close()
    if len(df) > 0:
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("No hay datos registrados aun")
except:
    st.warning("No hay datos registrados aun")

st.markdown("---")
st.subheader("Importar datos desde Excel")
st.info("El archivo Excel debe tener columnas: muestra1, muestra2, muestra3, muestra4, muestra5")

with st.expander("Ver formato requerido del Excel"):
    ejemplo = pd.DataFrame({
        "muestra1": [300.1, 298.5, 301.2],
        "muestra2": [299.3, 302.1, 298.8],
        "muestra3": [301.5, 299.8, 300.4],
        "muestra4": [298.9, 301.3, 299.1],
        "muestra5": [300.7, 298.2, 301.8]
    })
    st.dataframe(ejemplo, use_container_width=True)

    buffer_ej = io.BytesIO()
    ejemplo.to_excel(buffer_ej, index=False, engine="openpyxl")
    buffer_ej.seek(0)
    st.download_button(
        "Descargar plantilla Excel",
        data=buffer_ej,
        file_name="plantilla_muestras.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

archivo = st.file_uploader("Sube tu archivo Excel", type=["xlsx", "xls"])

if archivo is not None:
    try:
        df_excel = pd.read_excel(archivo)
        st.success(f"Archivo cargado: {len(df_excel)} filas detectadas")
        st.dataframe(df_excel.head(), use_container_width=True)

        columnas_req = ["muestra1","muestra2","muestra3","muestra4","muestra5"]
        if all(col in df_excel.columns for col in columnas_req):

            col1, col2, col3 = st.columns(3)
            with col1:
                prod_imp = st.selectbox("Producto", ["Mango","Banano","Aguacate","Melon","Cilantro","Sabila","Manzanilla"], key="prod_imp")
            with col2:
                var_imp = st.selectbox("Variable", ["Peso (g)","Diametro (cm)","Grados Brix","pH","Firmeza"], key="var_imp")
            with col3:
                analista_imp = st.text_input("Analista", "Importado", key="anal_imp")

            # Verificar si ya existen datos para este producto y variable
            conn_check = sqlite3.connect(DB_PATH)
            df_existente = pd.read_sql("SELECT * FROM muestras WHERE producto=? AND variable=? AND tipo='Variable continua'",
                                      conn_check, params=(prod_imp, var_imp))
            conn_check.close()

            if not df_existente.empty:
                st.warning(f"⚠️ Ya existen {len(df_existente)} registros para el producto '{prod_imp}' y variable '{var_imp}'")

                col1, col2 = st.columns(2)
                with col1:
                    accion = st.radio("¿Qué deseas hacer?",
                                     ["Reemplazar datos existentes", "Agregar nuevos datos"],
                                     horizontal=True)
                with col2:
                    if st.button("Confirmar acción", use_container_width=True):
                        st.session_state["accion_importar"] = accion
                        st.session_state["producto_importar"] = prod_imp
                        st.session_state["variable_importar"] = var_imp
                        st.session_state["analista_importar"] = analista_imp
                        st.session_state["df_excel_importar"] = df_excel.to_dict()

            if "accion_importar" in st.session_state and st.session_state["producto_importar"] == prod_imp and st.session_state["variable_importar"] == var_imp:
                accion = st.session_state["accion_importar"]
                df_excel_dict = st.session_state["df_excel_importar"]
                df_excel = pd.DataFrame(df_excel_dict)

                conn = sqlite3.connect(DB_PATH)

                if accion == "Reemplazar datos existentes":
                    # Eliminar datos existentes primero
                    conn.execute("DELETE FROM muestras WHERE producto=? AND variable=? AND tipo='Variable continua'",
                                (prod_imp, var_imp))
                    st.info(f"Se eliminaron {len(df_existente)} registros existentes")

                # Insertar nuevos datos
                for i, row in df_excel.iterrows():
                    conn.execute(
                        "INSERT INTO muestras VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (prod_imp, "Variable continua", var_imp, "",
                         analista_imp, str(datetime.today().date()), i+1,
                         row["muestra1"], row["muestra2"],
                         row["muestra3"], row["muestra4"], row["muestra5"])
                    )
                conn.commit()
                conn.close()

                if accion == "Reemplazar datos existentes":
                    st.success(f"✅ {len(df_excel)} subgrupos importados exitosamente (datos anteriores reemplazados)")
                else:
                    st.success(f"✅ {len(df_excel)} subgrupos importados exitosamente (datos agregados)")

                # Limpiar estado
                del st.session_state["accion_importar"]
                del st.session_state["producto_importar"]
                del st.session_state["variable_importar"]
                del st.session_state["analista_importar"]
                del st.session_state["df_excel_importar"]

        else:
            st.error(f"El archivo debe tener las columnas: {columnas_req}")
            st.markdown("Descarga la plantilla de arriba para ver el formato correcto.")

    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        st.info("Asegurate de que el archivo es .xlsx y tiene el formato correcto")
