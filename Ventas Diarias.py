import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import os
import plotly.express as px

st.set_page_config(
    page_title="VentasPro Analytics", 
    page_icon="📊",
    layout="wide"
)

# ---------- ESTILOS BÁSICOS ----------
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    }
    h1, h2, h3 {
        color: white !important;
    }
    .metric-card {
        background: rgba(255,255,255,0.1);
        border-radius: 15px;
        padding: 1.5rem;
        color: white;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ---------- DB ----------
DB_DIR = "data"
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

DB_PATH = os.path.join(DB_DIR, "ventas.db")

def init_db():
    """Inicializa la base de datos"""
    conn = sqlite3.connect(DB_PATH)
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
    conn.close()

# Inicializar DB
init_db()

# ---------- TÍTULO ----------
st.title("📊 VentasPro Analytics")
st.markdown("---")

# ---------- CARGA DE DATOS ----------
with st.expander("📤 Cargar Datos"):
    col1, col2 = st.columns(2)
    
    with col1:
        archivo = st.file_uploader("Archivo Excel", type=["xlsx"])
    
    with col2:
        anio = st.number_input("Año", min_value=2000, max_value=2100, value=2025)
    
    if archivo and st.button("Guardar"):
        try:
            df = pd.read_excel(archivo)
            
            # Verificar columnas
            columnas_requeridas = ["Fecha", "Secciones", "Entradas", "Venta", 
                                  "Tickets", "Artículos", "Ticket promedio", 
                                  "Artículos por ticket", "Tasa de conversión"]
            
            if all(col in df.columns for col in columnas_requeridas):
                # Renombrar
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
                
                df["anio"] = anio
                df["fecha"] = pd.to_datetime(df["fecha"]).dt.date
                
                # Guardar
                conn = sqlite3.connect(DB_PATH)
                df.to_sql("ventas", conn, if_exists="append", index=False)
                conn.close()
                
                st.success(f"✅ {len(df)} registros guardados")
                st.rerun()
            else:
                st.error("Columnas incorrectas")
        except Exception as e:
            st.error(f"Error: {e}")

# ---------- CARGAR DATOS ----------
@st.cache_data(ttl=60)
def cargar_datos():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM ventas", conn)
    conn.close()
    return df

df = cargar_datos()

if df.empty:
    st.info("👋 Carga tu primer archivo Excel para comenzar")
    st.stop()

# ---------- SIDEBAR ----------
with st.sidebar:
    st.header("Filtros")
    
    # Años disponibles
    años = sorted(df["anio"].unique())
    
    if len(años) >= 2:
        año1 = st.selectbox("Año 1", años, index=0)
        año2 = st.selectbox("Año 2", años, index=min(1, len(años)-1))
    else:
        año1 = años[0]
        año2 = años[0]
        st.warning("Se necesitan 2 años para comparar")
    
    # Fechas
    df["fecha"] = pd.to_datetime(df["fecha"])
    fecha_min = df["fecha"].min().date()
    fecha_max = df["fecha"].max().date()
    
    fecha_ini = st.date_input("Desde", fecha_min)
    fecha_fin = st.date_input("Hasta", fecha_max)
    
    # Secciones
    secciones = st.multiselect(
        "Secciones",
        options=df["secciones"].unique(),
        default=df["secciones"].unique().tolist()
    )

# ---------- FILTRAR ----------
mask = (
    (df["fecha"].dt.date >= fecha_ini) &
    (df["fecha"].dt.date <= fecha_fin) &
    (df["secciones"].isin(secciones))
)
df_filtrado = df[mask]

# ---------- MÉTRICAS ----------
st.subheader("📈 Métricas Principales")

# Calcular métricas para cada año
df_año1 = df_filtrado[df_filtrado["anio"] == año1]
df_año2 = df_filtrado[df_filtrado["anio"] == año2]

# Ventas
ventas1 = df_año1["venta"].sum()
ventas2 = df_año2["venta"].sum()
delta_ventas = ((ventas2 - ventas1) / ventas1 * 100) if ventas1 > 0 else 0

# Entradas
entradas1 = df_año1["entradas"].sum()
entradas2 = df_año2["entradas"].sum()
delta_entradas = ((entradas2 - entradas1) / entradas1 * 100) if entradas1 > 0 else 0

# Ticket promedio
ticket1 = ventas1 / df_año1["tickets"].sum() if df_año1["tickets"].sum() > 0 else 0
ticket2 = ventas2 / df_año2["tickets"].sum() if df_año2["tickets"].sum() > 0 else 0
delta_ticket = ((ticket2 - ticket1) / ticket1 * 100) if ticket1 > 0 else 0

# Tasa conversión
tasa1 = df_año1["tasa_conversion"].mean() if not df_año1.empty else 0
tasa2 = df_año2["tasa_conversion"].mean() if not df_año2.empty else 0
delta_tasa = tasa2 - tasa1

# Mostrar en columnas
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        f"Ventas {año2}",
        f"${ventas2:,.0f}",
        f"{delta_ventas:+.1f}% vs {año1}"
    )

with col2:
    st.metric(
        f"Entradas {año2}",
        f"{entradas2:,.0f}",
        f"{delta_entradas:+.1f}% vs {año1}"
    )

with col3:
    st.metric(
        f"Ticket Prom. {año2}",
        f"${ticket2:,.2f}",
        f"{delta_ticket:+.1f}% vs {año1}"
    )

with col4:
    st.metric(
        f"Tasa Conv. {año2}",
        f"{tasa2:.2f}%",
        f"{delta_tasa:+.2f} pp vs {año1}"
    )

# ---------- GRÁFICOS ----------
st.subheader("📊 Análisis Visual")

tab1, tab2, tab3 = st.tabs(["Evolución", "Por Sección", "Detalle"])

with tab1:
    # Datos para gráfico
    df_graf = df_filtrado[df_filtrado["anio"].isin([año1, año2])].copy()
    df_graf["mes"] = df_graf["fecha"].dt.month
    df_mensual = df_graf.groupby(["anio", "mes"])["venta"].sum().reset_index()
    
    if not df_mensual.empty:
        pivot = df_mensual.pivot(index="mes", columns="anio", values="venta").fillna(0)
        st.line_chart(pivot)

with tab2:
    # Comparación por sección
    df_seccion = df_graf.groupby(["secciones", "anio"])["venta"].sum().reset_index()
    
    if not df_seccion.empty:
        secciones_lista = []
        for seccion in df_seccion["secciones"].unique():
            datos = df_seccion[df_seccion["secciones"] == seccion]
            val1 = datos[datos["anio"] == año1]["venta"].values
            val2 = datos[datos["anio"] == año2]["venta"].values
            
            if len(val1) > 0 and len(val2) > 0:
                secciones_lista.append({
                    "Sección": seccion,
                    str(año1): f"${val1[0]:,.0f}",
                    str(año2): f"${val2[0]:,.0f}",
                    "Var": f"{((val2[0]-val1[0])/val1[0]*100):+.1f}%" if val1[0] > 0 else "N/A"
                })
        
        if secciones_lista:
            st.dataframe(pd.DataFrame(secciones_lista), use_container_width=True)

with tab3:
    # Datos detallados
    st.dataframe(
        df_filtrado.sort_values(["anio", "fecha"], ascending=False),
        use_container_width=True
    )

# ---------- PIE DE PÁGINA ----------
st.markdown("---")
st.caption("VentasPro Analytics © 2025")