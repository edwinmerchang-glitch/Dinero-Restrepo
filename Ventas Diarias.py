import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import os

st.set_page_config(page_title="Comparador de Ventas", layout="wide")

# ---------- DB ----------
# Crear directorio data si no existe
DB_DIR = "data"
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

DB_PATH = os.path.join(DB_DIR, "ventas.db")

def conectar():
    """Establece conexión con la base de datos"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10)
        return conn
    except sqlite3.Error as e:
        st.error(f"Error de conexión a la base de datos: {e}")
        return None

def crear_tabla():
    """Crea la tabla si no existe"""
    conn = conectar()
    if conn is not None:
        try:
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS ventas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TEXT,
                    secciones TEXT,
                    entradas INTEGER,
                    venta REAL,
                    tickets INTEGER,
                    articulos INTEGER,
                    ticket_promedio REAL,
                    articulos_por_ticket REAL,
                    tasa_conversion REAL,
                    anio INTEGER
                )
            """)
            conn.commit()
        except sqlite3.Error as e:
            st.error(f"Error al crear la tabla: {e}")
        finally:
            conn.close()

# Crear tabla al iniciar
crear_tabla()

# ---------- CARGA ----------

st.title("📊 Comparador de Ventas Diarias — Año Anterior vs Año Actual")

with st.expander("📤 Cargar Excel"):
    archivo = st.file_uploader("Sube archivo Excel", type=["xlsx"])
    anio = st.selectbox("Selecciona el año:", [datetime.now().year - 2, datetime.now().year - 1, datetime.now().year])

    if archivo and st.button("Guardar datos"):
        try:
            df = pd.read_excel(archivo)

            # Verificar que el archivo tenga las columnas requeridas
            columnas_requeridas = ["Fecha", "Secciones", "Entradas", "Venta", 
                                  "Tickets", "Artículos", "Ticket promedio", 
                                  "Artículos por ticket", "Tasa de conversión"]
            
            columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
            
            if columnas_faltantes:
                st.error(f"El archivo debe contener las siguientes columnas: {', '.join(columnas_faltantes)}")
            else:
                # Renombrar columnas para que coincidan con la base de datos
                df = df.rename(columns={
                    "Fecha": "fecha",
                    "Secciones": "secciones",
                    "Entradas": "entradas",
                    "Venta": "venta",
                    "Tickets": "tickets",
                    "Artículos": "articulos",
                    "Ticket promedio": "ticket_promedio",
                    "Artículos por ticket": "articulos_por_ticket",
                    "Tasa de conversión": "tasa_conversion"
                })
                
                # Agregar columna de año
                df["anio"] = anio
                
                # Convertir tipos de datos
                df["fecha"] = pd.to_datetime(df["fecha"]).dt.date
                df["entradas"] = pd.to_numeric(df["entradas"], errors='coerce')
                df["venta"] = pd.to_numeric(df["venta"], errors='coerce')
                df["tickets"] = pd.to_numeric(df["tickets"], errors='coerce')
                df["articulos"] = pd.to_numeric(df["articulos"], errors='coerce')
                df["ticket_promedio"] = pd.to_numeric(df["ticket_promedio"], errors='coerce')
                df["articulos_por_ticket"] = pd.to_numeric(df["articulos_por_ticket"], errors='coerce')
                df["tasa_conversion"] = pd.to_numeric(df["tasa_conversion"], errors='coerce')
                
                conn = conectar()
                if conn is not None:
                    df.to_sql("ventas", conn, if_exists="append", index=False)
                    conn.close()
                    st.success(f"Datos del año {anio} cargados correctamente ({len(df)} registros)")
                    
        except Exception as e:
            st.error(f"Error al cargar el archivo: {e}")

# ---------- CONSULTAS ----------

def cargar_datos():
    """Carga todos los datos de la base de datos"""
    conn = conectar()
    if conn is not None:
        try:
            df = pd.read_sql("SELECT * FROM ventas", conn)
            return df
        except sqlite3.Error as e:
            st.error(f"Error al cargar datos: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
    return pd.DataFrame()

df = cargar_datos()

if df.empty:
    st.warning("Aún no hay datos cargados")
    st.stop()

# ---------- FILTROS ----------
st.sidebar.header("Filtros")

# Convertir fecha a datetime para filtros
df["fecha"] = pd.to_datetime(df["fecha"])

# Filtro de rango de fechas
fecha_min = df["fecha"].min().date()
fecha_max = df["fecha"].max().date()
fecha_inicio, fecha_fin = st.sidebar.date_input(
    "Rango de fechas",
    value=(fecha_min, fecha_max),
    min_value=fecha_min,
    max_value=fecha_max
)

# Filtro de secciones
secciones = df["secciones"].unique()
secciones_seleccionadas = st.sidebar.multiselect(
    "Secciones",
    options=secciones,
    default=secciones
)

# Aplicar filtros
df_filtrado = df[
    (df["fecha"].dt.date >= fecha_inicio) &
    (df["fecha"].dt.date <= fecha_fin) &
    (df["secciones"].isin(secciones_seleccionadas))
]

# ---------- KPIs GENERALES ----------
st.subheader("📈 Comparación General")

anio_ant = datetime.now().year - 1
anio_act = datetime.now().year

# Calcular métricas por año
metricas_ant = df_filtrado[df_filtrado["anio"] == anio_ant].agg({
    "venta": "sum",
    "entradas": "sum",
    "tickets": "sum",
    "articulos": "sum"
})

metricas_act = df_filtrado[df_filtrado["anio"] == anio_act].agg({
    "venta": "sum",
    "entradas": "sum",
    "tickets": "sum",
    "articulos": "sum"
})

# Calcular ticket promedio y artículos por ticket
ticket_prom_ant = metricas_ant["venta"] / metricas_ant["tickets"] if metricas_ant["tickets"] > 0 else 0
ticket_prom_act = metricas_act["venta"] / metricas_act["tickets"] if metricas_act["tickets"] > 0 else 0

articulos_por_ticket_ant = metricas_ant["articulos"] / metricas_ant["tickets"] if metricas_ant["tickets"] > 0 else 0
articulos_por_ticket_act = metricas_act["articulos"] / metricas_act["tickets"] if metricas_act["tickets"] > 0 else 0

# Mostrar KPIs
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Ventas Totales",
        f"${metricas_act['venta']:,.0f}",
        delta=f"{(metricas_act['venta'] - metricas_ant['venta'])/metricas_ant['venta']*100:.1f}%" if metricas_ant['venta'] > 0 else None
    )

with col2:
    st.metric(
        "Entradas",
        f"{metricas_act['entradas']:,.0f}",
        delta=f"{(metricas_act['entradas'] - metricas_ant['entradas'])/metricas_ant['entradas']*100:.1f}%" if metricas_ant['entradas'] > 0 else None
    )

with col3:
    st.metric(
        "Ticket Promedio",
        f"${ticket_prom_act:,.2f}",
        delta=f"{(ticket_prom_act - ticket_prom_ant)/ticket_prom_ant*100:.1f}%" if ticket_prom_ant > 0 else None
    )

with col4:
    st.metric(
        "Tasa de Conversión",
        f"{df_filtrado[df_filtrado['anio'] == anio_act]['tasa_conversion'].mean():.2f}%",
        delta=f"{(df_filtrado[df_filtrado['anio'] == anio_act]['tasa_conversion'].mean() - df_filtrado[df_filtrado['anio'] == anio_ant]['tasa_conversion'].mean()):.2f}%" if not df_filtrado[df_filtrado['anio'] == anio_ant].empty else None
    )

# ---------- ANÁLISIS POR SECCIÓN ----------
st.subheader("📊 Comparación por Sección")

# Agrupar por sección y año
seccion_comparacion = df_filtrado.groupby(["secciones", "anio"]).agg({
    "venta": "sum",
    "entradas": "sum",
    "tickets": "sum"
}).reset_index()

# Crear tabla comparativa
secciones_unicas = seccion_comparacion["secciones"].unique()
comparacion_secciones = []

for seccion in secciones_unicas:
    datos_seccion = seccion_comparacion[seccion_comparacion["secciones"] == seccion]
    dato_ant = datos_seccion[datos_seccion["anio"] == anio_ant]
    dato_act = datos_seccion[datos_seccion["anio"] == anio_act]
    
    if not dato_ant.empty and not dato_act.empty:
        venta_ant = dato_ant["venta"].values[0]
        venta_act = dato_act["venta"].values[0]
        variacion = ((venta_act - venta_ant) / venta_ant * 100) if venta_ant > 0 else 0
        
        comparacion_secciones.append({
            "Sección": seccion,
            f"Venta {anio_ant}": f"${venta_ant:,.0f}",
            f"Venta {anio_act}": f"${venta_act:,.0f}",
            "Variación %": f"{variacion:.1f}%"
        })

if comparacion_secciones:
    st.dataframe(pd.DataFrame(comparacion_secciones), use_container_width=True)

# ---------- GRÁFICOS ----------
st.subheader("📈 Evolución Temporal")

# Preparar datos para gráficos
df_evolucion = df_filtrado.groupby([pd.Grouper(key="fecha", freq="M"), "anio"])["venta"].sum().reset_index()
df_evolucion["mes_año"] = df_evolucion["fecha"].dt.strftime("%Y-%m")

# Gráfico de líneas para ventas
pivot_ventas = df_evolucion.pivot(index="fecha", columns="anio", values="venta").fillna(0)
st.line_chart(pivot_ventas)

# ---------- DATOS DETALLADOS ----------
with st.expander("📋 Ver datos detallados"):
    st.dataframe(
        df_filtrado.sort_values("fecha", ascending=False)
        .style.format({
            "venta": "${:,.0f}",
            "ticket_promedio": "${:,.2f}",
            "tasa_conversion": "{:.2f}%"
        })
    )

# ---------- BORRAR ----------
with st.expander("⚠️ Administración"):
    if st.button("Borrar todos los datos"):
        conn = conectar()
        if conn is not None:
            try:
                conn.execute("DELETE FROM ventas")
                conn.commit()
                st.warning("Base de datos limpiada")
                st.rerun()
            except sqlite3.Error as e:
                st.error(f"Error al borrar datos: {e}")
            finally:
                conn.close()