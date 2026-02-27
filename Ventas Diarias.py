import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

st.set_page_config(page_title="Comparador de Ventas", layout="wide")

# ---------- DB ----------

DB_PATH = "data/ventas.db"

def conectar():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def crear_tabla():
    conn = conectar()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            producto TEXT,
            categoria TEXT,
            cantidad INTEGER,
            valor REAL,
            anio INTEGER
        )
    """)
    conn.commit()
    conn.close()

crear_tabla()

# ---------- CARGA ----------

st.title("📊 Comparador de Ventas — Año Anterior vs Año Actual")

with st.expander("📤 Cargar Excel"):
    archivo = st.file_uploader("Sube archivo Excel", type=["xlsx"])
    anio = st.selectbox("Selecciona el año:", [datetime.now().year - 1, datetime.now().year])

    if archivo and st.button("Guardar datos"):
        df = pd.read_excel(archivo)

        columnas = ["fecha", "producto", "categoria", "cantidad", "valor"]
        if not all(col in df.columns for col in columnas):
            st.error("El archivo debe contener las columnas: fecha, producto, categoria, cantidad, valor")
        else:
            df["anio"] = anio
            conn = conectar()
            df.to_sql("ventas", conn, if_exists="append", index=False)
            conn.close()
            st.success(f"Datos del año {anio} cargados correctamente")

# ---------- CONSULTAS ----------

def cargar_datos():
    conn = conectar()
    df = pd.read_sql("SELECT * FROM ventas", conn)
    conn.close()
    return df

df = cargar_datos()

if df.empty:
    st.warning("Aún no hay datos cargados")
    st.stop()

# ---------- KPIs ----------

st.subheader("📈 Comparación General")

col1, col2, col3 = st.columns(3)

anio_ant = datetime.now().year - 1
anio_act = datetime.now().year

total_ant = df[df["anio"] == anio_ant]["valor"].sum()
total_act = df[df["anio"] == anio_act]["valor"].sum()

variacion = ((total_act - total_ant) / total_ant * 100) if total_ant > 0 else 0

col1.metric("Ventas Año Anterior", f"${total_ant:,.0f}")
col2.metric("Ventas Año Actual", f"${total_act:,.0f}")
col3.metric("Variación", f"{variacion:.2f}%", delta=f"{variacion:.2f}%")

# ---------- GRAFICOS ----------

st.subheader("📊 Comparación Mensual")

df["fecha"] = pd.to_datetime(df["fecha"])
df["mes"] = df["fecha"].dt.month

tabla = df.groupby(["anio", "mes"])["valor"].sum().reset_index()

pivot = tabla.pivot(index="mes", columns="anio", values="valor").fillna(0)

st.line_chart(pivot)

# ---------- TABLA ----------

st.subheader("📋 Detalle Comparativo")

st.dataframe(pivot.style.format("{:,.0f}"))

# ---------- BORRAR ----------

with st.expander("⚠️ Administración"):
    if st.button("Borrar todos los datos"):
        conn = conectar()
        conn.execute("DELETE FROM ventas")
        conn.commit()
        conn.close()
        st.warning("Base de datos limpiada")
        st.experimental_rerun()