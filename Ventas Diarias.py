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

# ---------- ESTILOS CSS PERSONALIZADOS ----------
st.markdown("""
<style>
    /* Estilos generales */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Tarjetas modernas */
    .modern-card {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 1.5rem;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.2);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .modern-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 60px rgba(0,0,0,0.15);
    }
    
    /* Métricas con estilo */
    .metric-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 1.2rem;
        color: white;
        text-align: center;
        box-shadow: 0 5px 20px rgba(102, 126, 234, 0.3);
    }
    
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .metric-value {
        font-size: 1.8rem;
        font-weight: bold;
        margin-bottom: 0.3rem;
    }
    
    .metric-delta {
        font-size: 0.9rem;
        padding: 0.2rem 0.8rem;
        border-radius: 20px;
        background: rgba(255,255,255,0.2);
        display: inline-block;
    }
    
    /* Badges y etiquetas */
    .badge-success {
        background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
        color: #1a4731;
        padding: 0.3rem 1rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    
    .badge-warning {
        background: linear-gradient(135deg, #f6d365 0%, #fda085 100%);
        color: #7f4f24;
        padding: 0.3rem 1rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    
    /* Encabezados */
    h1, h2, h3 {
        color: white !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    
    /* Sidebar personalizado */
    .css-1d391kg {
        background: rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
    }
    
    /* Botones modernos */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        border: 1px solid rgba(255,255,255,0.2);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
    }
    
    /* DataFrames */
    .dataframe-container {
        background: white;
        border-radius: 15px;
        padding: 1rem;
        box-shadow: 0 5px 20px rgba(0,0,0,0.05);
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        background: rgba(255,255,255,0.1);
        color: white;
        border-radius: 10px;
        border: 1px solid rgba(255,255,255,0.2);
    }
    
    /* Tooltips personalizados */
    .tooltip {
        position: relative;
        display: inline-block;
        cursor: help;
    }
    
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 200px;
        background: rgba(0,0,0,0.8);
        color: white;
        text-align: center;
        border-radius: 10px;
        padding: 0.5rem;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        margin-left: -100px;
        opacity: 0;
        transition: opacity 0.3s;
        font-size: 0.8rem;
        backdrop-filter: blur(10px);
    }
    
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
    
    /* Animaciones */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.6s ease-out;
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

# ---------- HEADER MODERNO ----------
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("""
        <div style='text-align: center; padding: 2rem;'>
            <h1 style='font-size: 3rem; margin-bottom: 0;'>📊 VentasPro Analytics</h1>
            <p style='color: rgba(255,255,255,0.8); font-size: 1.2rem;'>
                Inteligencia de ventas en tiempo real
            </p>
            <div style='display: flex; justify-content: center; gap: 1rem; margin-top: 1rem;'>
                <span class='badge-success'>✨ Análisis Predictivo</span>
                <span class='badge-warning'>📈 Comparativas Inteligentes</span>
                <span class='badge-success'>🎯 KPIs en Tiempo Real</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

# ---------- CARGA DE DATOS MODERNA ----------
with st.expander("📤 **Cargar Nuevos Datos**", expanded=False):
    col1, col2 = st.columns([2, 1])
    
    with col1:
        archivo = st.file_uploader(
            "Arrastra tu archivo Excel aquí",
            type=["xlsx"],
            help="Formatos soportados: .xlsx"
        )
    
    with col2:
        anio = st.number_input(
            "📅 Año de los datos",
            min_value=2000,
            max_value=2100,
            value=datetime.now().year,
            step=1,
            help="Selecciona el año correspondiente a estos datos"
        )
    
    if archivo:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🚀 Procesar y Guardar Datos", use_container_width=True):
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
                            
                            conn = conectar()
                            if conn is not None:
                                df.to_sql("ventas", conn, if_exists="append", index=False)
                                conn.close()
                                
                                st.balloons()
                                st.success(f"""
                                    ✅ **¡Datos cargados exitosamente!**  
                                    📊 {len(df)} registros para el año {anio}
                                """)
                                
                    except Exception as e:
                        st.error(f"❌ Error: {e}")

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
        <div style='text-align: center; padding: 4rem; background: rgba(255,255,255,0.1); border-radius: 20px; margin: 2rem;'>
            <h2 style='color: white;'>👋 ¡Bienvenido a VentasPro!</h2>
            <p style='color: rgba(255,255,255,0.8); font-size: 1.2rem; margin: 2rem;'>
                Comienza cargando tus datos de ventas usando el panel superior
            </p>
            <span class='badge-success'>✨ Sube tu primer archivo Excel</span>
        </div>
    """, unsafe_allow_html=True)
    st.stop()

# ---------- SIDEBAR MODERNO ----------
with st.sidebar:
    st.markdown("""
        <div style='text-align: center; padding: 1rem;'>
            <h3 style='color: white;'>🎯 Panel de Control</h3>
            <div style='height: 2px; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.5), transparent); margin: 1rem 0;'></div>
        </div>
    """, unsafe_allow_html=True)
    
    # Selector de años con diseño moderno
    años_disponibles = sorted(df["anio"].unique(), reverse=True)
    
    st.markdown("### 📅 Comparación Interanual")
    
    col1, col2 = st.columns(2)
    with col1:
        año_base = st.selectbox(
            "Año base",
            options=años_disponibles,
            index=min(1, len(años_disponibles)-1) if len(años_disponibles) > 1 else 0,
            help="Año con el que quieres comparar"
        )
    with col2:
        año_comparar = st.selectbox(
            "Año actual",
            options=años_disponibles,
            index=0,
            help="Año que quieres analizar"
        )
    
    st.markdown("### 🔍 Filtros Inteligentes")
    
    # Filtros con diseño mejorado
    df["fecha"] = pd.to_datetime(df["fecha"])
    fecha_min = df["fecha"].min().date()
    fecha_max = df["fecha"].max().date()
    
    fecha_inicio, fecha_fin = st.date_input(
        "📆 Rango de fechas",
        value=(fecha_min, fecha_max),
        min_value=fecha_min,
        max_value=fecha_max,
        help="Selecciona el período a analizar"
    )
    
    secciones = df["secciones"].unique()
    secciones_seleccionadas = st.multiselect(
        "🏷️ Secciones",
        options=secciones,
        default=secciones,
        help="Filtra por secciones específicas"
    )
    
    # Resumen rápido
    st.markdown("### 📊 Resumen Rápido")
    total_registros = len(df[(df["fecha"].dt.date >= fecha_inicio) & 
                             (df["fecha"].dt.date <= fecha_fin) &
                             (df["secciones"].isin(secciones_seleccionadas))])
    
    st.markdown(f"""
        <div style='background: rgba(255,255,255,0.1); border-radius: 10px; padding: 1rem;'>
            <p style='color: white; margin: 0;'>📋 Registros filtrados</p>
            <h2 style='color: white; margin: 0;'>{total_registros:,}</h2>
        </div>
    """, unsafe_allow_html=True)

# Aplicar filtros
df_filtrado = df[
    (df["fecha"].dt.date >= fecha_inicio) &
    (df["fecha"].dt.date <= fecha_fin) &
    (df["secciones"].isin(secciones_seleccionadas))
]

# ---------- MÉTRICAS PRINCIPALES ----------
st.markdown("<h2 style='text-align: center; margin: 2rem 0;'>📈 Métricas Principales</h2>", unsafe_allow_html=True)

# Calcular métricas
metricas_base = df_filtrado[df_filtrado["anio"] == año_base].agg({
    "venta": "sum", "entradas": "sum", "tickets": "sum"
})

metricas_comparar = df_filtrado[df_filtrado["anio"] == año_comparar].agg({
    "venta": "sum", "entradas": "sum", "tickets": "sum"
})

ticket_prom_base = metricas_base["venta"] / metricas_base["tickets"] if metricas_base["tickets"] > 0 else 0
ticket_prom_comparar = metricas_comparar["venta"] / metricas_comparar["tickets"] if metricas_comparar["tickets"] > 0 else 0

# Mostrar métricas en tarjetas modernas
col1, col2, col3, col4 = st.columns(4)

with col1:
    delta_ventas = ((metricas_comparar['venta'] - metricas_base['venta'])/metricas_base['venta']*100) if metricas_base['venta'] > 0 else None
    delta_color = "inverse" if delta_ventas and delta_ventas < 0 else "normal"
    
    st.markdown(f"""
        <div class='modern-card fade-in'>
            <div class='metric-container'>
                <div class='metric-label'>💰 Ventas Totales</div>
                <div class='metric-value'>${metricas_comparar['venta']:,.0f}</div>
                <div class='metric-delta'>
                    {'▲' if delta_ventas and delta_ventas > 0 else '▼' if delta_ventas and delta_ventas < 0 else '•'} 
                    {abs(delta_ventas):.1f}% vs {año_base}
                </div>
                <div style='font-size: 0.8rem; margin-top: 0.5rem;'>{año_base}: ${metricas_base['venta']:,.0f}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    delta_entradas = ((metricas_comparar['entradas'] - metricas_base['entradas'])/metricas_base['entradas']*100) if metricas_base['entradas'] > 0 else None
    
    st.markdown(f"""
        <div class='modern-card fade-in'>
            <div class='metric-container'>
                <div class='metric-label'>👥 Entradas</div>
                <div class='metric-value'>{metricas_comparar['entradas']:,.0f}</div>
                <div class='metric-delta'>
                    {'▲' if delta_entradas and delta_entradas > 0 else '▼' if delta_entradas and delta_entradas < 0 else '•'} 
                    {abs(delta_entradas):.1f}% vs {año_base}
                </div>
                <div style='font-size: 0.8rem; margin-top: 0.5rem;'>{año_base}: {metricas_base['entradas']:,.0f}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

with col3:
    delta_ticket = ((ticket_prom_comparar - ticket_prom_base)/ticket_prom_base*100) if ticket_prom_base > 0 else None
    
    st.markdown(f"""
        <div class='modern-card fade-in'>
            <div class='metric-container'>
                <div class='metric-label'>🎫 Ticket Promedio</div>
                <div class='metric-value'>${ticket_prom_comparar:,.2f}</div>
                <div class='metric-delta'>
                    {'▲' if delta_ticket and delta_ticket > 0 else '▼' if delta_ticket and delta_ticket < 0 else '•'} 
                    {abs(delta_ticket):.1f}% vs {año_base}
                </div>
                <div style='font-size: 0.8rem; margin-top: 0.5rem;'>{año_base}: ${ticket_prom_base:,.2f}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

with col4:
    tasa_base = df_filtrado[df_filtrado['anio'] == año_base]['tasa_conversion'].mean() if not df_filtrado[df_filtrado['anio'] == año_base].empty else 0
    tasa_comparar = df_filtrado[df_filtrado['anio'] == año_comparar]['tasa_conversion'].mean() if not df_filtrado[df_filtrado['anio'] == año_comparar].empty else 0
    delta_tasa = tasa_comparar - tasa_base if tasa_base > 0 else None
    
    st.markdown(f"""
        <div class='modern-card fade-in'>
            <div class='metric-container'>
                <div class='metric-label'>📊 Tasa de Conversión</div>
                <div class='metric-value'>{tasa_comparar:.2f}%</div>
                <div class='metric-delta'>
                    {'▲' if delta_tasa and delta_tasa > 0 else '▼' if delta_tasa and delta_tasa < 0 else '•'} 
                    {abs(delta_tasa):.2f} pp vs {año_base}
                </div>
                <div style='font-size: 0.8rem; margin-top: 0.5rem;'>{año_base}: {tasa_base:.2f}%</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# ---------- GRÁFICOS INTERACTIVOS ----------
st.markdown("<h2 style='text-align: center; margin: 3rem 0 2rem 0;'>📊 Análisis Visual</h2>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📈 Evolución Temporal", "🏷️ Análisis por Sección", "📋 Datos Detallados"])

with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de líneas con Plotly
        df_grafico = df_filtrado[df_filtrado["anio"].isin([año_base, año_comparar])]
        df_evolucion = df_grafico.groupby([pd.Grouper(key="fecha", freq="M"), "anio"])["venta"].sum().reset_index()
        
        if not df_evolucion.empty:
            fig = px.line(
                df_evolucion, 
                x="fecha", 
                y="venta", 
                color="anio",
                title=f"Evolución de Ventas - {año_base} vs {año_comparar}",
                color_discrete_sequence=['#FF6B6B', '#4ECDC4']
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                title_font_color='white',
                xaxis_title="Fecha",
                yaxis_title="Ventas ($)"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Gráfico de barras comparativo
        comparativo_mensual = df_evolucion.pivot(index=df_evolucion['fecha'].dt.month, 
                                                columns='anio', 
                                                values='venta').reset_index()
        
        fig = px.bar(
            comparativo_mensual,
            x='fecha',
            y=[año_base, año_comparar],
            title="Comparativa Mensual",
            barmode='group',
            color_discrete_sequence=['#FF6B6B', '#4ECDC4']
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            title_font_color='white',
            xaxis_title="Mes",
            yaxis_title="Ventas ($)"
        )
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    # Análisis por sección con gráfico de torta
    seccion_actual = df_filtrado[df_filtrado["anio"] == año_comparar].groupby("secciones")["venta"].sum().reset_index()
    
    if not seccion_actual.empty:
        fig = px.pie(
            seccion_actual,
            values='venta',
            names='secciones',
            title=f"Distribución de Ventas por Sección - {año_comparar}",
            color_discrete_sequence=px.colors.sequential.RdBu
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            title_font_color='white'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Tabla comparativa por sección
    st.markdown("### 📊 Comparativa Detallada por Sección")
    
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
                f"Ventas {año_base}": f"${venta_base:,.0f}",
                f"Ventas {año_comparar}": f"${venta_comparar:,.0f}",
                "Variación": f"{variacion:+.1f}%",
                "Trend": "📈" if variacion > 0 else "📉" if variacion < 0 else "➡️"
            })
    
    if comparacion_secciones:
        df_comparacion = pd.DataFrame(comparacion_secciones)
        st.dataframe(
            df_comparacion.style.applymap(
                lambda x: 'color: #4ECDC4' if '+' in str(x) else 'color: #FF6B6B' if '-' in str(x) and str(x) != '➡️' else '',
                subset=['Variación']
            ),
            use_container_width=True
        )

with tab3:
    # Datos detallados con formato
    st.markdown("### 📋 Registros Detallados")
    
    df_detalle = df_filtrado.sort_values(["anio", "fecha"], ascending=[False, False]).copy()
    df_detalle["venta_fmt"] = df_detalle["venta"].apply(lambda x: f"${x:,.0f}")
    df_detalle["ticket_promedio_fmt"] = df_detalle["ticket_promedio"].apply(lambda x: f"${x:,.2f}")
    df_detalle["tasa_conversion_fmt"] = df_detalle["tasa_conversion"].apply(lambda x: f"{x:.2f}%")
    
    st.dataframe(
        df_detalle[["fecha", "secciones", "entradas", "venta_fmt", "tickets", 
                   "articulos", "ticket_promedio_fmt", "tasa_conversion_fmt", "anio"]],
        use_container_width=True,
        column_config={
            "fecha": "Fecha",
            "secciones": "Sección",
            "entradas": "Entradas",
            "venta_fmt": "Venta",
            "tickets": "Tickets",
            "articulos": "Artículos",
            "ticket_promedio_fmt": "Ticket Prom.",
            "tasa_conversion_fmt": "Tasa Conv.",
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
                <span class='badge-success'>✨ Versión 2.0</span>
            </div>
        """, unsafe_allow_html=True)

# ---------- FOOTER ----------
st.markdown("""
    <div style='text-align: center; margin-top: 3rem; padding: 1rem;'>
        <p style='color: rgba(255,255,255,0.5); font-size: 0.9rem;'>
            VentasPro Analytics © 2024 | Dashboard inteligente para análisis de ventas
        </p>
    </div>
""", unsafe_allow_html=True)