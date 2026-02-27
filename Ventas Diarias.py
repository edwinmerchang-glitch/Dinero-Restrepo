import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import os
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="VentasPro Analytics", 
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- ESTILOS CSS MEJORADOS ----------
st.markdown("""
<style>
    /* Fondo elegante con patrón sutil */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        position: relative;
    }
    
    /* Patrón de fondo sutil */
    .stApp::before {
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: 
            radial-gradient(circle at 20% 50%, rgba(255,255,255,0.02) 0%, transparent 25%),
            radial-gradient(circle at 80% 80%, rgba(255,255,255,0.02) 0%, transparent 25%),
            repeating-linear-gradient(45deg, rgba(255,255,255,0.01) 0px, rgba(255,255,255,0.01) 1px, transparent 1px, transparent 10px);
        pointer-events: none;
        z-index: 0;
    }
    
    /* Sidebar elegante y moderno */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a2639 0%, #0f172a 100%);
        border-right: 1px solid rgba(255,255,255,0.1);
        box-shadow: 10px 0 30px rgba(0,0,0,0.3);
    }
    
    section[data-testid="stSidebar"] > div {
        background: transparent;
    }
    
    /* Títulos del sidebar */
    .sidebar-title {
        color: white;
        font-size: 1.2rem;
        font-weight: 600;
        margin: 1.5rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid rgba(255,255,255,0.1);
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Elementos del sidebar */
    .sidebar-section {
        background: rgba(255,255,255,0.03);
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
        border: 1px solid rgba(255,255,255,0.05);
        backdrop-filter: blur(10px);
    }
    
    /* Header principal */
    .main-header {
        background: linear-gradient(135deg, #667eea20 0%, #764ba220 100%);
        backdrop-filter: blur(10px);
        border-radius: 24px;
        padding: 2rem;
        margin: 1rem 0 2rem 0;
        border: 1px solid rgba(255,255,255,0.1);
        box-shadow: 0 20px 40px rgba(0,0,0,0.2);
    }
    
    /* Título principal */
    .main-title {
        font-size: 3.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #a8c0ff 0%, #3f2b96 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
        text-shadow: 0 10px 20px rgba(0,0,0,0.2);
    }
    
    /* Subtítulo */
    .main-subtitle {
        color: rgba(255,255,255,0.7);
        font-size: 1.2rem;
        font-weight: 300;
        margin-bottom: 1.5rem;
    }
    
    /* Badges modernos */
    .modern-badge {
        display: inline-block;
        padding: 0.4rem 1.2rem;
        border-radius: 30px;
        font-size: 0.85rem;
        font-weight: 500;
        margin: 0 0.3rem;
        background: rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1);
        color: white;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }
    
    .badge-purple {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
    }
    
    .badge-blue {
        background: linear-gradient(135deg, #2193b0 0%, #6dd5ed 100%);
        border: none;
    }
    
    .badge-green {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        border: none;
    }
    
    /* Tarjetas de métricas */
    .metric-card {
        background: rgba(255,255,255,0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 24px;
        padding: 1.5rem;
        transition: all 0.3s ease;
        height: 100%;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        background: rgba(255,255,255,0.08);
        border-color: rgba(255,255,255,0.2);
        box-shadow: 0 20px 40px rgba(0,0,0,0.2);
    }
    
    .metric-icon {
        font-size: 2rem;
        margin-bottom: 1rem;
        opacity: 0.8;
    }
    
    .metric-label {
        color: rgba(255,255,255,0.6);
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.5rem;
    }
    
    .metric-value {
        color: white;
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        line-height: 1.2;
    }
    
    .metric-comparison {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-top: 1rem;
        padding-top: 1rem;
        border-top: 1px solid rgba(255,255,255,0.1);
    }
    
    .metric-delta {
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    
    .delta-positive {
        background: rgba(72, 187, 120, 0.2);
        color: #48bb78;
        border: 1px solid rgba(72, 187, 120, 0.3);
    }
    
    .delta-negative {
        background: rgba(245, 101, 101, 0.2);
        color: #f56565;
        border: 1px solid rgba(245, 101, 101, 0.3);
    }
    
    .delta-neutral {
        background: rgba(160, 174, 192, 0.2);
        color: #a0aec0;
        border: 1px solid rgba(160, 174, 192, 0.3);
    }
    
    .metric-previous {
        color: rgba(255,255,255,0.4);
        font-size: 0.85rem;
    }
    
    /* Selectores y inputs */
    .stSelectbox > div > div {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        color: white;
    }
    
    .stSelectbox > div > div:hover {
        border-color: rgba(255,255,255,0.3);
    }
    
    .stDateInput > div > div {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        color: white;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 12px !important;
        color: white !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
        background: rgba(255,255,255,0.03);
        padding: 0.5rem;
        border-radius: 16px;
        border: 1px solid rgba(255,255,255,0.05);
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 12px;
        padding: 0.5rem 1.5rem;
        color: rgba(255,255,255,0.6);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
    }
    
    /* DataFrames */
    .dataframe-container {
        background: rgba(255,255,255,0.03);
        border-radius: 16px;
        padding: 1rem;
        border: 1px solid rgba(255,255,255,0.05);
    }
    
    /* Tooltips personalizados */
    .custom-tooltip {
        position: relative;
        display: inline-block;
        cursor: help;
        margin-left: 0.3rem;
        color: rgba(255,255,255,0.4);
    }
    
    .custom-tooltip:hover {
        color: rgba(255,255,255,0.8);
    }
    
    .custom-tooltip .tooltip-text {
        visibility: hidden;
        width: 200px;
        background: rgba(0,0,0,0.9);
        color: white;
        text-align: center;
        border-radius: 8px;
        padding: 0.5rem;
        position: absolute;
        z-index: 1000;
        bottom: 125%;
        left: 50%;
        margin-left: -100px;
        opacity: 0;
        transition: opacity 0.3s;
        font-size: 0.8rem;
        border: 1px solid rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
        pointer-events: none;
    }
    
    .custom-tooltip:hover .tooltip-text {
        visibility: visible;
        opacity: 1;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 2rem;
        margin-top: 3rem;
        color: rgba(255,255,255,0.3);
        font-size: 0.9rem;
        border-top: 1px solid rgba(255,255,255,0.05);
    }
</style>
""", unsafe_allow_html=True)

# ---------- DB ----------
DB_DIR = "data"
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

DB_PATH = os.path.join(DB_DIR, "ventas.db")

def conectar():
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10)
        return conn
    except sqlite3.Error as e:
        st.error(f"🔴 Error de conexión: {e}")
        return None

def crear_tabla():
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
            st.error(f"🔴 Error al crear tabla: {e}")
        finally:
            conn.close()

crear_tabla()

# ---------- HEADER ELEGANTE ----------
st.markdown("""
    <div class='main-header'>
        <div style='display: flex; justify-content: space-between; align-items: center;'>
            <div>
                <div class='main-title'>VentasPro Analytics</div>
                <div class='main-subtitle'>Inteligencia de ventas en tiempo real</div>
                <div style='margin-top: 1rem;'>
                    <span class='modern-badge badge-purple'>✨ Análisis Predictivo</span>
                    <span class='modern-badge badge-blue'>📊 Comparativas Inteligentes</span>
                    <span class='modern-badge badge-green'>🎯 KPIs en Tiempo Real</span>
                </div>
            </div>
            <div style='text-align: right;'>
                <div style='color: rgba(255,255,255,0.6); font-size: 0.9rem;'>Última actualización</div>
                <div style='color: white; font-size: 1.2rem; font-weight: 600;'>{}</div>
            </div>
        </div>
    </div>
""".format(datetime.now().strftime("%d de %B, %Y")), unsafe_allow_html=True)

# ---------- CARGA DE DATOS (CORREGIDO) ----------
with st.expander("📤 **Cargar Nuevos Datos**", expanded=False):
    col1, col2 = st.columns([2, 1])
    
    with col1:
        archivo = st.file_uploader(
            "Selecciona un archivo Excel",  # Label no vacío
            type=["xlsx"],
            help="Formatos soportados: .xlsx"
        )
    
    with col2:
        anio = st.number_input(
            "📅 Año de los datos",
            min_value=2000,
            max_value=2100,
            value=datetime.now().year,
            step=1
        )
    
    if archivo:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🚀 Procesar y Guardar", use_container_width=True):
                with st.spinner("🔄 Procesando datos..."):
                    try:
                        df = pd.read_excel(archivo)
                        
                        columnas_requeridas = ["Fecha", "Secciones", "Entradas", "Venta", 
                                              "Tickets", "Artículos", "Ticket promedio", 
                                              "Artículos por ticket", "Tasa de conversión"]
                        
                        columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
                        
                        if columnas_faltantes:
                            st.error(f"❌ Columnas faltantes: {', '.join(columnas_faltantes)}")
                        else:
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
                            
                            # Convertir tipos de datos
                            for col in ["entradas", "venta", "tickets", "articulos", 
                                       "ticket_promedio", "articulos_por_ticket", "tasa_conversion"]:
                                df[col] = pd.to_numeric(df[col], errors='coerce')
                            
                            conn = conectar()
                            if conn is not None:
                                df.to_sql("ventas", conn, if_exists="append", index=False)
                                conn.close()
                                
                                st.balloons()
                                st.success(f"✅ ¡{len(df)} registros cargados exitosamente para {anio}!")
                                
                    except Exception as e:
                        st.error(f"❌ Error al procesar: {str(e)}")

# ---------- CARGA DE DATOS ----------
def cargar_datos():
    conn = conectar()
    if conn is not None:
        try:
            df = pd.read_sql("SELECT * FROM ventas", conn)
            return df
        except sqlite3.Error as e:
            st.error(f"🔴 Error al cargar datos: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
    return pd.DataFrame()

df = cargar_datos()

if df.empty:
    st.markdown("""
        <div style='text-align: center; padding: 4rem; background: rgba(255,255,255,0.03); border-radius: 24px; margin: 2rem; border: 1px solid rgba(255,255,255,0.05);'>
            <div style='font-size: 4rem; margin-bottom: 1rem;'>📊</div>
            <h2 style='color: white; margin-bottom: 1rem;'>¡Bienvenido a VentasPro!</h2>
            <p style='color: rgba(255,255,255,0.6); font-size: 1.1rem; margin-bottom: 2rem;'>
                Comienza cargando tus datos de ventas usando el panel superior
            </p>
            <span class='modern-badge badge-purple'>✨ Sube tu primer archivo Excel</span>
        </div>
    """, unsafe_allow_html=True)
    st.stop()

# ---------- SIDEBAR MEJORADO ----------
with st.sidebar:
    st.markdown("""
        <div style='text-align: center; padding: 2rem 1rem;'>
            <div style='font-size: 2.5rem; margin-bottom: 0.5rem;'>📊</div>
            <div style='color: white; font-size: 1.5rem; font-weight: 700;'>VentasPro</div>
            <div style='color: rgba(255,255,255,0.5); font-size: 0.9rem;'>Panel de Control</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div class='sidebar-title'>📅 Comparación Interanual</div>", unsafe_allow_html=True)
    
    años_disponibles = sorted(df["anio"].unique(), reverse=True)
    
    if len(años_disponibles) > 0:
        col1, col2 = st.columns(2)
        with col1:
            año_base = st.selectbox(
                "Año base",
                options=años_disponibles,
                index=min(1, len(años_disponibles)-1) if len(años_disponibles) > 1 else 0,
                key="anio_base"
            )
        with col2:
            año_comparar = st.selectbox(
                "Año actual",
                options=años_disponibles,
                index=0,
                key="anio_comparar"
            )
    else:
        st.warning("No hay años disponibles")
        st.stop()
    
    st.markdown("<div class='sidebar-title'>🔍 Filtros Inteligentes</div>", unsafe_allow_html=True)
    
    df["fecha"] = pd.to_datetime(df["fecha"])
    fecha_min = df["fecha"].min().date()
    fecha_max = df["fecha"].max().date()
    
    col1, col2 = st.columns(2)
    with col1:
        fecha_inicio = st.date_input("Desde", fecha_min, key="fecha_inicio")
    with col2:
        fecha_fin = st.date_input("Hasta", fecha_max, key="fecha_fin")
    
    secciones = df["secciones"].unique()
    secciones_seleccionadas = st.multiselect(
        "Secciones",
        options=secciones,
        default=secciones[:3] if len(secciones) > 3 else secciones,
        key="secciones_filtro"
    )
    
    st.markdown("<div class='sidebar-title'>📊 Resumen Rápido</div>", unsafe_allow_html=True)
    
    df_filtrado = df[
        (df["fecha"].dt.date >= fecha_inicio) &
        (df["fecha"].dt.date <= fecha_fin) &
        (df["secciones"].isin(secciones_seleccionadas))
    ]
    
    st.markdown(f"""
        <div style='background: rgba(255,255,255,0.05); border-radius: 16px; padding: 1.5rem; text-align: center; border: 1px solid rgba(255,255,255,0.05);'>
            <div style='color: rgba(255,255,255,0.6); font-size: 0.9rem; margin-bottom: 0.5rem;'>Registros Filtrados</div>
            <div style='color: white; font-size: 2.5rem; font-weight: 700;'>{len(df_filtrado):,}</div>
            <div style='color: rgba(255,255,255,0.4); font-size: 0.8rem; margin-top: 0.5rem;'>Total en BD: {len(df):,}</div>
        </div>
    """, unsafe_allow_html=True)

# ---------- MÉTRICAS PRINCIPALES ----------
st.markdown("<h2 style='color: white; margin: 2rem 0 1.5rem 0; font-weight: 600;'>📈 Métricas Principales</h2>", unsafe_allow_html=True)

# Calcular métricas
metricas_base = df_filtrado[df_filtrado["anio"] == año_base].agg({
    "venta": "sum", "entradas": "sum", "tickets": "sum"
})

metricas_comparar = df_filtrado[df_filtrado["anio"] == año_comparar].agg({
    "venta": "sum", "entradas": "sum", "tickets": "sum"
})

ticket_prom_base = metricas_base["venta"] / metricas_base["tickets"] if metricas_base["tickets"] > 0 else 0
ticket_prom_comparar = metricas_comparar["venta"] / metricas_comparar["tickets"] if metricas_comparar["tickets"] > 0 else 0

tasa_base = df_filtrado[df_filtrado['anio'] == año_base]['tasa_conversion'].mean() if not df_filtrado[df_filtrado['anio'] == año_base].empty else 0
tasa_comparar = df_filtrado[df_filtrado['anio'] == año_comparar]['tasa_conversion'].mean() if not df_filtrado[df_filtrado['anio'] == año_comparar].empty else 0

# Mostrar métricas en grid de 2x2
col1, col2 = st.columns(2)
col3, col4 = st.columns(2)

with col1:
    delta_ventas = ((metricas_comparar['venta'] - metricas_base['venta'])/metricas_base['venta']*100) if metricas_base['venta'] > 0 else 0
    delta_class = "delta-positive" if delta_ventas > 0 else "delta-negative" if delta_ventas < 0 else "delta-neutral"
    delta_symbol = "▲" if delta_ventas > 0 else "▼" if delta_ventas < 0 else "•"
    
    st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-icon'>💰</div>
            <div class='metric-label'>VENTAS TOTALES</div>
            <div class='metric-value'>${metricas_comparar['venta']:,.0f}</div>
            <div class='metric-comparison'>
                <span class='metric-delta {delta_class}'>{delta_symbol} {abs(delta_ventas):.1f}% vs {año_base}</span>
            </div>
            <div class='metric-previous'>{año_base}: ${metricas_base['venta']:,.0f}</div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    delta_entradas = ((metricas_comparar['entradas'] - metricas_base['entradas'])/metricas_base['entradas']*100) if metricas_base['entradas'] > 0 else 0
    delta_class = "delta-positive" if delta_entradas > 0 else "delta-negative" if delta_entradas < 0 else "delta-neutral"
    delta_symbol = "▲" if delta_entradas > 0 else "▼" if delta_entradas < 0 else "•"
    
    st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-icon'>👥</div>
            <div class='metric-label'>ENTRADAS</div>
            <div class='metric-value'>{metricas_comparar['entradas']:,.0f}</div>
            <div class='metric-comparison'>
                <span class='metric-delta {delta_class}'>{delta_symbol} {abs(delta_entradas):.1f}% vs {año_base}</span>
            </div>
            <div class='metric-previous'>{año_base}: {metricas_base['entradas']:,.0f}</div>
        </div>
    """, unsafe_allow_html=True)

with col3:
    delta_ticket = ((ticket_prom_comparar - ticket_prom_base)/ticket_prom_base*100) if ticket_prom_base > 0 else 0
    delta_class = "delta-positive" if delta_ticket > 0 else "delta-negative" if delta_ticket < 0 else "delta-neutral"
    delta_symbol = "▲" if delta_ticket > 0 else "▼" if delta_ticket < 0 else "•"
    
    st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-icon'>🎫</div>
            <div class='metric-label'>TICKET PROMEDIO</div>
            <div class='metric-value'>${ticket_prom_comparar:,.2f}</div>
            <div class='metric-comparison'>
                <span class='metric-delta {delta_class}'>{delta_symbol} {abs(delta_ticket):.1f}% vs {año_base}</span>
            </div>
            <div class='metric-previous'>{año_base}: ${ticket_prom_base:,.2f}</div>
        </div>
    """, unsafe_allow_html=True)

with col4:
    delta_tasa = tasa_comparar - tasa_base
    delta_class = "delta-positive" if delta_tasa > 0 else "delta-negative" if delta_tasa < 0 else "delta-neutral"
    delta_symbol = "▲" if delta_tasa > 0 else "▼" if delta_tasa < 0 else "•"
    
    st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-icon'>📊</div>
            <div class='metric-label'>TASA DE CONVERSIÓN</div>
            <div class='metric-value'>{tasa_comparar:.2f}%</div>
            <div class='metric-comparison'>
                <span class='metric-delta {delta_class}'>{delta_symbol} {abs(delta_tasa):.2f} pp vs {año_base}</span>
            </div>
            <div class='metric-previous'>{año_base}: {tasa_base:.2f}%</div>
        </div>
    """, unsafe_allow_html=True)

# ---------- GRÁFICOS ----------
st.markdown("<h2 style='color: white; margin: 3rem 0 1.5rem 0; font-weight: 600;'>📊 Análisis Visual</h2>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📈 Evolución Temporal", "🏷️ Análisis por Sección", "📋 Datos Detallados"])

with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        df_grafico = df_filtrado[df_filtrado["anio"].isin([año_base, año_comparar])]
        if not df_grafico.empty:
            df_evolucion = df_grafico.groupby([pd.Grouper(key="fecha", freq="M"), "anio"])["venta"].sum().reset_index()
            
            if not df_evolucion.empty:
                fig = px.line(
                    df_evolucion, 
                    x="fecha", 
                    y="venta", 
                    color="anio",
                    title=f"Evolución de Ventas",
                    color_discrete_sequence=['#FF6B6B', '#4ECDC4']
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='white',
                    title_font_color='white',
                    xaxis_title="",
                    yaxis_title="Ventas ($)",
                    legend_title="Año",
                    hovermode='x unified'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay datos suficientes para el gráfico")
    
    with col2:
        if not df_evolucion.empty:
            fig = px.bar(
                df_evolucion,
                x="fecha",
                y="venta",
                color="anio",
                title="Comparativa Mensual",
                barmode='group',
                color_discrete_sequence=['#FF6B6B', '#4ECDC4']
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                title_font_color='white',
                xaxis_title="",
                yaxis_title="Ventas ($)",
                legend_title="Año"
            )
            st.plotly_chart(fig, use_container_width=True)

with tab2:
    seccion_actual = df_filtrado[df_filtrado["anio"] == año_comparar].groupby("secciones")["venta"].sum().reset_index()
    
    if not seccion_actual.empty:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            fig = px.pie(
                seccion_actual,
                values='venta',
                names='secciones',
                title=f"Distribución {año_comparar}",
                color_discrete_sequence=px.colors.sequential.Viridis
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                title_font_color='white'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            seccion_comparacion = df_filtrado.groupby(["secciones", "anio"])["venta"].sum().reset_index()
            secciones_unicas = seccion_comparacion["secciones"].unique()
            comparacion_secciones = []
            
            for seccion in secciones_unicas:
                datos_seccion = seccion_comparacion[seccion_comparacion["secciones"] == seccion]
                dato_base = datos_seccion[datos_seccion["anio"] == año_base]
                dato_comparar = datos_seccion[datos_seccion["anio"] == año_comparar]
                
                if not dato_base.empty and not dato_comparar.empty:
                    venta_base = dato_base["venta"].values[0]
                    venta_comparar = dato_comparar["venta"].values[0]
                    variacion = ((venta_comparar - venta_base) / venta_base * 100) if venta_base > 0 else 0
                    
                    comparacion_secciones.append({
                        "Sección": seccion,
                        str(año_base): f"${venta_base:,.0f}",
                        str(año_comparar): f"${venta_comparar:,.0f}",
                        "Variación": f"{variacion:+.1f}%"
                    })
            
            if comparacion_secciones:
                st.dataframe(
                    pd.DataFrame(comparacion_secciones),
                    use_container_width=True,
                    hide_index=True
                )

with tab3:
    if not df_filtrado.empty:
        df_detalle = df_filtrado.sort_values(["anio", "fecha"], ascending=[False, False]).copy()
        df_detalle["Venta"] = df_detalle["venta"].apply(lambda x: f"${x:,.0f}")
        df_detalle["Ticket Prom."] = df_detalle["ticket_promedio"].apply(lambda x: f"${x:,.2f}")
        df_detalle["Tasa Conv."] = df_detalle["tasa_conversion"].apply(lambda x: f"{x:.2f}%")
        
        st.dataframe(
            df_detalle[["fecha", "secciones", "entradas", "Venta", "tickets", 
                       "articulos", "Ticket Prom.", "Tasa Conv.", "anio"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "fecha": "Fecha",
                "secciones": "Sección",
                "entradas": "Entradas",
                "Venta": "Venta",
                "tickets": "Tickets",
                "articulos": "Artículos",
                "Ticket Prom.": "Ticket Prom.",
                "Tasa Conv.": "Tasa Conv.",
                "anio": "Año"
            }
        )

# ---------- ADMINISTRACIÓN ----------
with st.expander("⚙️ Administración del Sistema"):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🗑️ Limpiar Todos los Datos", use_container_width=True):
            conn = conectar()
            if conn is not None:
                conn.execute("DELETE FROM ventas")
                conn.commit()
                conn.close()
                st.warning("✅ Datos eliminados")
                st.rerun()
    
    with col2:
        if st.button("🔄 Reiniciar Base de Datos", use_container_width=True):
            conn = conectar()
            if conn is not None:
                conn.execute("DROP TABLE IF EXISTS ventas")
                conn.commit()
                conn.close()
                crear_tabla()
                st.success("✅ Base de datos reiniciada")
                st.rerun()
    
    with col3:
        st.markdown("""
            <div style='text-align: center;'>
                <span class='modern-badge badge-purple'>✨ Versión 2.0</span>
            </div>
        """, unsafe_allow_html=True)

# ---------- FOOTER ----------
st.markdown("""
    <div class='footer'>
        VentasPro Analytics © 2025 | Dashboard inteligente para análisis de ventas
    </div>
""", unsafe_allow_html=True)