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

# ---------- ESTILO LIMPIO Y PROFESIONAL ----------
st.markdown("""
<style>
    /* Fondo blanco limpio */
    .stApp {
        background-color: #ffffff;
    }
    
    /* Estilo para tarjetas de métricas */
    .metric-card {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    
    .metric-title {
        color: #6c757d;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.5rem;
    }
    
    .metric-value {
        color: #212529;
        font-size: 2rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .metric-delta {
        font-size: 0.9rem;
        padding: 0.25rem 0;
    }
    
    .delta-positive {
        color: #28a745;
    }
    
    .delta-negative {
        color: #dc3545;
    }
    
    .metric-sub {
        color: #adb5bd;
        font-size: 0.85rem;
        margin-top: 0.5rem;
        padding-top: 0.5rem;
        border-top: 1px solid #e9ecef;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #212529 !important;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background-color: #f8f9fa;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: #f8f9fa !important;
        border: 1px solid #e9ecef !important;
        border-radius: 8px !important;
        color: #212529 !important;
    }
    
    /* Selectores */
    .stSelectbox > div > div {
        background-color: white;
        border: 1px solid #e9ecef;
        border-radius: 8px;
    }
    
    /* DataFrame */
    .dataframe {
        background-color: white;
        border: 1px solid #e9ecef;
        border-radius: 8px;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 2rem;
        margin-top: 3rem;
        color: #adb5bd;
        font-size: 0.9rem;
        border-top: 1px solid #e9ecef;
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

# ---------- HEADER ----------
st.title("📊 VentasPro Analytics")
st.markdown("---")

# ---------- CARGA DE DATOS ----------
with st.expander("📤 Cargar Datos", expanded=False):
    col1, col2 = st.columns([2, 1])
    
    with col1:
        archivo = st.file_uploader(
            "Seleccionar archivo Excel",
            type=["xlsx"],
            help="Formatos: .xlsx"
        )
    
    with col2:
        anio = st.number_input(
            "Año",
            min_value=2000,
            max_value=2100,
            value=datetime.now().year,
            step=1
        )
    
    if archivo and st.button("🚀 Procesar y Guardar", use_container_width=True):
        with st.spinner("Procesando..."):
            try:
                df = pd.read_excel(archivo)
                
                # Verificar columnas
                columnas_requeridas = ["Fecha", "Secciones", "Entradas", "Venta", 
                                      "Tickets", "Artículos", "Ticket promedio", 
                                      "Artículos por ticket", "Tasa de conversión"]
                
                columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
                
                if columnas_faltantes:
                    st.error(f"❌ Faltan: {', '.join(columnas_faltantes)}")
                else:
                    # Renombrar columnas
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
                    
                    st.success(f"✅ {len(df)} registros guardados para {anio}")
                    st.rerun()
                    
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# ---------- CARGAR DATOS ----------
@st.cache_data(ttl=60)
def cargar_datos():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM ventas", conn)
    conn.close()
    return df

df = cargar_datos()

if df.empty:
    st.info("👋 Bienvenido a VentasPro. Comienza cargando tu primer archivo Excel.")
    st.stop()

# ---------- SIDEBAR ----------
with st.sidebar:
    st.markdown("### 🎯 Filtros")
    st.markdown("---")
    
    # Años disponibles
    años_disponibles = sorted(df["anio"].unique(), reverse=True)
    
    if len(años_disponibles) >= 2:
        año_base = st.selectbox(
            "Año base",
            options=años_disponibles,
            index=min(1, len(años_disponibles)-1)
        )
        año_comparar = st.selectbox(
            "Año a comparar",
            options=años_disponibles,
            index=0
        )
    else:
        año_base = años_disponibles[0]
        año_comparar = años_disponibles[0]
        st.warning("Se necesitan datos de dos años para comparar")
    
    st.markdown("---")
    
    # Rango de fechas
    df["fecha"] = pd.to_datetime(df["fecha"])
    fecha_min = df["fecha"].min().date()
    fecha_max = df["fecha"].max().date()
    
    fecha_inicio = st.date_input("Fecha inicio", fecha_min)
    fecha_fin = st.date_input("Fecha fin", fecha_max)
    
    # Secciones
    secciones = df["secciones"].unique()
    secciones_seleccionadas = st.multiselect(
        "Secciones",
        options=secciones,
        default=secciones.tolist()
    )
    
    st.markdown("---")
    
    # Resumen
    mask = (
        (df["fecha"].dt.date >= fecha_inicio) &
        (df["fecha"].dt.date <= fecha_fin) &
        (df["secciones"].isin(secciones_seleccionadas))
    )
    df_filtrado = df[mask]
    
    st.metric("Registros filtrados", f"{len(df_filtrado):,}")
    st.caption(f"Total BD: {len(df):,}")

# ---------- MÉTRICAS PRINCIPALES ----------
st.subheader("📈 Métricas Principales")

# Calcular métricas por año
df_base = df_filtrado[df_filtrado["anio"] == año_base]
df_comp = df_filtrado[df_filtrado["anio"] == año_comparar]

# Ventas
ventas_base = df_base["venta"].sum()
ventas_comp = df_comp["venta"].sum()
delta_ventas = ((ventas_comp - ventas_base) / ventas_base * 100) if ventas_base > 0 else 0

# Entradas
entradas_base = df_base["entradas"].sum()
entradas_comp = df_comp["entradas"].sum()
delta_entradas = ((entradas_comp - entradas_base) / entradas_base * 100) if entradas_base > 0 else 0

# Ticket promedio
tickets_base = df_base["tickets"].sum()
tickets_comp = df_comp["tickets"].sum()
ticket_base = ventas_base / tickets_base if tickets_base > 0 else 0
ticket_comp = ventas_comp / tickets_comp if tickets_comp > 0 else 0
delta_ticket = ((ticket_comp - ticket_base) / ticket_base * 100) if ticket_base > 0 else 0

# Tasa conversión
tasa_base = df_base["tasa_conversion"].mean() if not df_base.empty else 0
tasa_comp = df_comp["tasa_conversion"].mean() if not df_comp.empty else 0
delta_tasa = tasa_comp - tasa_base

# Mostrar métricas en 4 columnas
col1, col2, col3, col4 = st.columns(4)

with col1:
    delta_class = "delta-positive" if delta_ventas > 0 else "delta-negative" if delta_ventas < 0 else ""
    st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-title'>💰 Ventas Totales</div>
            <div class='metric-value'>${ventas_comp:,.0f}</div>
            <div class='metric-delta {delta_class}'>
                {delta_ventas:+.1f}% vs {año_base}
            </div>
            <div class='metric-sub'>{año_base}: ${ventas_base:,.0f}</div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    delta_class = "delta-positive" if delta_entradas > 0 else "delta-negative" if delta_entradas < 0 else ""
    st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-title'>👥 Entradas</div>
            <div class='metric-value'>{entradas_comp:,.0f}</div>
            <div class='metric-delta {delta_class}'>
                {delta_entradas:+.1f}% vs {año_base}
            </div>
            <div class='metric-sub'>{año_base}: {entradas_base:,.0f}</div>
        </div>
    """, unsafe_allow_html=True)

with col3:
    delta_class = "delta-positive" if delta_ticket > 0 else "delta-negative" if delta_ticket < 0 else ""
    st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-title'>🎫 Ticket Promedio</div>
            <div class='metric-value'>${ticket_comp:,.2f}</div>
            <div class='metric-delta {delta_class}'>
                {delta_ticket:+.1f}% vs {año_base}
            </div>
            <div class='metric-sub'>{año_base}: ${ticket_base:,.2f}</div>
        </div>
    """, unsafe_allow_html=True)

with col4:
    delta_class = "delta-positive" if delta_tasa > 0 else "delta-negative" if delta_tasa < 0 else ""
    st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-title'>📊 Tasa Conversión</div>
            <div class='metric-value'>{tasa_comp:.2f}%</div>
            <div class='metric-delta {delta_class}'>
                {delta_tasa:+.2f} pp vs {año_base}
            </div>
            <div class='metric-sub'>{año_base}: {tasa_base:.2f}%</div>
        </div>
    """, unsafe_allow_html=True)

# ---------- ANÁLISIS VISUAL ----------
st.subheader("📊 Análisis Visual")

tab1, tab2, tab3 = st.tabs(["📈 Evolución", "🏷️ Por Sección", "📋 Detalle"])

with tab1:
    # Gráfico de evolución
    df_graf = df_filtrado[df_filtrado["anio"].isin([año_base, año_comparar])].copy()
    
    if not df_graf.empty:
        df_graf["mes"] = df_graf["fecha"].dt.month
        df_mensual = df_graf.groupby(["anio", "mes"])["venta"].sum().reset_index()
        
        pivot = df_mensual.pivot(index="mes", columns="anio", values="venta").fillna(0)
        st.line_chart(pivot)
    else:
        st.info("No hay datos para mostrar")

with tab2:
    # Análisis por sección
    df_seccion = df_graf.groupby(["secciones", "anio"])["venta"].sum().reset_index()
    
    if not df_seccion.empty:
        datos_seccion = []
        for seccion in df_seccion["secciones"].unique():
            datos = df_seccion[df_seccion["secciones"] == seccion]
            val_base = datos[datos["anio"] == año_base]["venta"].values
            val_comp = datos[datos["anio"] == año_comparar]["venta"].values
            
            if len(val_base) > 0 and len(val_comp) > 0:
                var = ((val_comp[0] - val_base[0]) / val_base[0] * 100) if val_base[0] > 0 else 0
                datos_seccion.append({
                    "Sección": seccion,
                    f"Ventas {año_base}": f"${val_base[0]:,.0f}",
                    f"Ventas {año_comparar}": f"${val_comp[0]:,.0f}",
                    "Variación": f"{var:+.1f}%"
                })
        
        if datos_seccion:
            st.dataframe(pd.DataFrame(datos_seccion), use_container_width=True, hide_index=True)

with tab3:
    # Datos detallados
    if not df_filtrado.empty:
        st.dataframe(
            df_filtrado.sort_values(["anio", "fecha"], ascending=False),
            use_container_width=True,
            hide_index=True
        )

# ---------- PIE DE PÁGINA ----------
st.markdown("---")
st.markdown("""
    <div class='footer'>
        VentasPro Analytics © 2025 | Dashboard profesional para análisis de ventas
    </div>
""", unsafe_allow_html=True)