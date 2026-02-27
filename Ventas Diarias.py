import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import os
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import locale
import calendar

# Intentar configurar locale en español
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'Spanish_Spain.1252')
    except:
        pass  # Si no funciona, usaremos los nombres en español manualmente

st.set_page_config(
    page_title="VentasPro Analytics", 
    page_icon="📊",
    layout="wide"
)

# Diccionario de meses en español
MESES_ES = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
    5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
    9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
}

# Diccionario de días en español
DIAS_ES = {
    0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves',
    4: 'Viernes', 5: 'Sábado', 6: 'Domingo'
}

DIAS_ES_ABR = {
    0: 'Lun', 1: 'Mar', 2: 'Mié', 3: 'Jue',
    4: 'Vie', 5: 'Sáb', 6: 'Dom'
}

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
    
    /* Calendario en español */
    .stDateInput label {
        font-weight: 500;
    }
    
    /* Personalizar el calendario desplegable */
    div[data-baseweb="calendar"] {
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    div[data-baseweb="calendar"] span[aria-label*="day"] {
        text-transform: capitalize;
    }
    
    /* Mes y año en el calendario */
    div[data-baseweb="calendar"] div[role="presentation"] {
        text-transform: capitalize;
    }
    
    /* Estilo para tarjetas de gráficos */
    .chart-card {
        background-color: white;
        border: 1px solid #e9ecef;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        margin-bottom: 1rem;
    }
    
    .chart-title {
        color: #495057;
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #e9ecef;
    }
    
    /* Estilo para comparador de días */
    .day-comparator {
        background-color: #e7f5ff;
        border: 1px solid #74c0fc;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .day-comparator-title {
        color: #1864ab;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Función para formatear fechas en español
def formato_fecha_es(fecha):
    """Formatea una fecha en español"""
    if isinstance(fecha, str):
        fecha = pd.to_datetime(fecha)
    return f"{fecha.day} de {MESES_ES[fecha.month]} de {fecha.year}"

# Función para obtener el nombre del día en español
def dia_semana_es(fecha):
    """Devuelve el nombre del día de la semana en español"""
    if isinstance(fecha, str):
        fecha = pd.to_datetime(fecha)
    return DIAS_ES[fecha.weekday()]

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
    
    # Tipo de comparación
    st.markdown("#### 🔍 Tipo de Comparación")
    tipo_comparacion = st.radio(
        "Seleccionar modo",
        ["📅 Rango de fechas", "📆 Mismo día de la semana", "🎯 Fecha específica"],
        help="Elige cómo quieres comparar los períodos"
    )
    
    st.markdown("---")
    
    df["fecha"] = pd.to_datetime(df["fecha"])
    fecha_min = df["fecha"].min().date()
    fecha_max = df["fecha"].max().date()
    
    if tipo_comparacion == "📅 Rango de fechas":
        st.markdown("#### 📅 Rango de fechas")
        
        col1, col2 = st.columns(2)
        with col1:
            fecha_inicio = st.date_input(
                "Desde",
                fecha_min,
                min_value=fecha_min,
                max_value=fecha_max,
                key="fecha_inicio_rango"
            )
        with col2:
            fecha_fin = st.date_input(
                "Hasta",
                fecha_max,
                min_value=fecha_min,
                max_value=fecha_max,
                key="fecha_fin_rango"
            )
        
        # Aplicar el mismo rango a ambos años
        fecha_inicio_base = fecha_inicio
        fecha_fin_base = fecha_fin
        fecha_inicio_comp = fecha_inicio
        fecha_fin_comp = fecha_fin
        
        st.caption(f"📆 {formato_fecha_es(fecha_inicio)} → {formato_fecha_es(fecha_fin)}")
    
    elif tipo_comparacion == "📆 Mismo día de la semana":
        st.markdown("#### 📆 Comparar mismo día de la semana")
        
        # Seleccionar semana de referencia
        semanas_disponibles = sorted(df[df["anio"] == año_comparar]["fecha"].dt.isocalendar().week.unique())
        
        col1, col2 = st.columns(2)
        with col1:
            semana_ref = st.selectbox(
                "Semana de referencia",
                options=semanas_disponibles,
                help="Número de semana del año"
            )
        with col2:
            dia_ref = st.selectbox(
                "Día de la semana",
                options=list(DIAS_ES.values()),
                index=4,  # Viernes por defecto
                help="Día a comparar"
            )
        
        # Convertir día seleccionado a número (0-6)
        dia_num = list(DIAS_ES.keys())[list(DIAS_ES.values()).index(dia_ref)]
        
        # Encontrar fechas para ambos años
        df_comp_semana = df[(df["anio"] == año_comparar) & 
                           (df["fecha"].dt.isocalendar().week == semana_ref) &
                           (df["fecha"].dt.weekday == dia_num)]
        
        df_base_semana = df[(df["anio"] == año_base) & 
                           (df["fecha"].dt.isocalendar().week == semana_ref) &
                           (df["fecha"].dt.weekday == dia_num)]
        
        if not df_comp_semana.empty and not df_base_semana.empty:
            fecha_inicio_comp = df_comp_semana["fecha"].iloc[0].date()
            fecha_fin_comp = fecha_inicio_comp
            fecha_inicio_base = df_base_semana["fecha"].iloc[0].date()
            fecha_fin_base = fecha_inicio_base
            
            st.markdown(f"""
                <div class='day-comparator'>
                    <div class='day-comparator-title'>📆 Comparación seleccionada:</div>
                    <div>{año_base}: {formato_fecha_es(fecha_inicio_base)} ({dia_ref})</div>
                    <div>{año_comparar}: {formato_fecha_es(fecha_inicio_comp)} ({dia_ref})</div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("No hay datos para la combinación seleccionada")
            fecha_inicio_base = fecha_min
            fecha_fin_base = fecha_max
            fecha_inicio_comp = fecha_min
            fecha_fin_comp = fecha_max
    
    else:  # Fecha específica
        st.markdown("#### 🎯 Fecha específica")
        
        fecha_especifica = st.date_input(
            "Seleccionar fecha",
            fecha_min,
            min_value=fecha_min,
            max_value=fecha_max
        )
        
        # Encontrar la misma fecha en ambos años
        fecha_comp = fecha_especifica.replace(year=año_comparar)
        fecha_base = fecha_especifica.replace(year=año_base)
        
        fecha_inicio_base = fecha_base
        fecha_fin_base = fecha_base
        fecha_inicio_comp = fecha_comp
        fecha_fin_comp = fecha_comp
        
        st.caption(f"📆 {año_base}: {formato_fecha_es(fecha_base)}")
        st.caption(f"📆 {año_comparar}: {formato_fecha_es(fecha_comp)}")
    
    st.markdown("---")
    
    # Secciones
    secciones = df["secciones"].unique()
    secciones_seleccionadas = st.multiselect(
        "🏷️ Secciones",
        options=secciones,
        default=secciones.tolist()
    )
    
    st.markdown("---")
    
    # Resumen con filtros separados por año
    if tipo_comparacion == "📅 Rango de fechas":
        mask_base = (
            (df["fecha"].dt.date >= fecha_inicio_base) &
            (df["fecha"].dt.date <= fecha_fin_base) &
            (df["anio"] == año_base) &
            (df["secciones"].isin(secciones_seleccionadas))
        )
        mask_comp = (
            (df["fecha"].dt.date >= fecha_inicio_comp) &
            (df["fecha"].dt.date <= fecha_fin_comp) &
            (df["anio"] == año_comparar) &
            (df["secciones"].isin(secciones_seleccionadas))
        )
    else:
        mask_base = (
            (df["fecha"].dt.date == fecha_inicio_base) &
            (df["anio"] == año_base) &
            (df["secciones"].isin(secciones_seleccionadas))
        )
        mask_comp = (
            (df["fecha"].dt.date == fecha_inicio_comp) &
            (df["anio"] == año_comparar) &
            (df["secciones"].isin(secciones_seleccionadas))
        )
    
    df_base = df[mask_base]
    df_comp = df[mask_comp]
    df_filtrado = pd.concat([df_base, df_comp])
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(f"📋 Registros {año_base}", f"{len(df_base):,}")
    with col2:
        st.metric(f"📋 Registros {año_comparar}", f"{len(df_comp):,}")
    
    st.caption(f"Total BD: {len(df):,} registros")

# ---------- MÉTRICAS PRINCIPALES ----------
st.subheader("📈 Métricas Principales")

# Ventas
ventas_base = df_base["venta"].sum()
ventas_comp = df_comp["venta"].sum()
delta_ventas = ((ventas_comp - ventas_base) / ventas_base * 100) if ventas_base > 0 else 0

# Entradas
entradas_base = df_base["entradas"].sum()
entradas_comp = df_comp["entradas"].sum()
delta_entradas = ((entradas_comp - entradas_base) / entradas_base * 100) if entradas_base > 0 else 0

# Tickets
tickets_base = df_base["tickets"].sum()
tickets_comp = df_comp["tickets"].sum()
delta_tickets = ((tickets_comp - tickets_base) / tickets_base * 100) if tickets_base > 0 else 0

# Artículos
articulos_base = df_base["articulos"].sum()
articulos_comp = df_comp["articulos"].sum()
delta_articulos = ((articulos_comp - articulos_base) / articulos_base * 100) if articulos_base > 0 else 0

# Ticket promedio
ticket_prom_base = ventas_base / tickets_base if tickets_base > 0 else 0
ticket_prom_comp = ventas_comp / tickets_comp if tickets_comp > 0 else 0
delta_ticket_prom = ((ticket_prom_comp - ticket_prom_base) / ticket_prom_base * 100) if ticket_prom_base > 0 else 0

# Artículos por ticket
articulos_x_ticket_base = articulos_base / tickets_base if tickets_base > 0 else 0
articulos_x_ticket_comp = articulos_comp / tickets_comp if tickets_comp > 0 else 0
delta_articulos_x_ticket = ((articulos_x_ticket_comp - articulos_x_ticket_base) / articulos_x_ticket_base * 100) if articulos_x_ticket_base > 0 else 0

# Tasa conversión
tasa_base = df_base["tasa_conversion"].mean() if not df_base.empty else 0
tasa_comp = df_comp["tasa_conversion"].mean() if not df_comp.empty else 0
delta_tasa = tasa_comp - tasa_base

# Mostrar métricas en 4 columnas (primera fila)
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
    delta_class = "delta-positive" if delta_tickets > 0 else "delta-negative" if delta_tickets < 0 else ""
    st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-title'>🎟️ Tickets</div>
            <div class='metric-value'>{tickets_comp:,.0f}</div>
            <div class='metric-delta {delta_class}'>
                {delta_tickets:+.1f}% vs {año_base}
            </div>
            <div class='metric-sub'>{año_base}: {tickets_base:,.0f}</div>
        </div>
    """, unsafe_allow_html=True)

with col4:
    delta_class = "delta-positive" if delta_articulos > 0 else "delta-negative" if delta_articulos < 0 else ""
    st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-title'>📦 Artículos</div>
            <div class='metric-value'>{articulos_comp:,.0f}</div>
            <div class='metric-delta {delta_class}'>
                {delta_articulos:+.1f}% vs {año_base}
            </div>
            <div class='metric-sub'>{año_base}: {articulos_base:,.0f}</div>
        </div>
    """, unsafe_allow_html=True)

# Segunda fila de métricas
col1, col2, col3, col4 = st.columns(4)

with col1:
    delta_class = "delta-positive" if delta_ticket_prom > 0 else "delta-negative" if delta_ticket_prom < 0 else ""
    st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-title'>🎫 Ticket Promedio</div>
            <div class='metric-value'>${ticket_prom_comp:,.2f}</div>
            <div class='metric-delta {delta_class}'>
                {delta_ticket_prom:+.1f}% vs {año_base}
            </div>
            <div class='metric-sub'>{año_base}: ${ticket_prom_base:,.2f}</div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    delta_class = "delta-positive" if delta_articulos_x_ticket > 0 else "delta-negative" if delta_articulos_x_ticket < 0 else ""
    st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-title'>📊 Artículos/Ticket</div>
            <div class='metric-value'>{articulos_x_ticket_comp:.2f}</div>
            <div class='metric-delta {delta_class}'>
                {delta_articulos_x_ticket:+.1f}% vs {año_base}
            </div>
            <div class='metric-sub'>{año_base}: {articulos_x_ticket_base:.2f}</div>
        </div>
    """, unsafe_allow_html=True)

with col3:
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

# ---------- ANÁLISIS POR SECCIÓN ----------
st.subheader("📋 Análisis por Sección")

if not df_base.empty and not df_comp.empty:
    secciones_unicas = set(df_base["secciones"].unique()) | set(df_comp["secciones"].unique())
    datos_seccion = []
    
    for seccion in secciones_unicas:
        datos_base = df_base[df_base["secciones"] == seccion]
        datos_comp = df_comp[df_comp["secciones"] == seccion]
        
        if not datos_base.empty and not datos_comp.empty:
            venta_base = datos_base["venta"].sum()
            venta_comp = datos_comp["venta"].sum()
            var_venta = ((venta_comp - venta_base) / venta_base * 100) if venta_base > 0 else 0
            
            entradas_base = datos_base["entradas"].sum()
            entradas_comp = datos_comp["entradas"].sum()
            
            tickets_base = datos_base["tickets"].sum()
            tickets_comp = datos_comp["tickets"].sum()
            
            ticket_prom_base = venta_base / tickets_base if tickets_base > 0 else 0
            ticket_prom_comp = venta_comp / tickets_comp if tickets_comp > 0 else 0
            
            tasa_base = datos_base["tasa_conversion"].mean()
            tasa_comp = datos_comp["tasa_conversion"].mean()
            
            datos_seccion.append({
                "Sección": seccion,
                f"Ventas {año_base}": f"${venta_base:,.0f}",
                f"Ventas {año_comparar}": f"${venta_comp:,.0f}",
                "Var %": f"{var_venta:+.1f}%",
                f"Ticket Prom {año_comparar}": f"${ticket_prom_comp:,.2f}",
                "Var Ticket": f"{((ticket_prom_comp - ticket_prom_base) / ticket_prom_base * 100):+.1f}%" if ticket_prom_base > 0 else "N/A",
                f"Tasa {año_comparar}": f"{tasa_comp:.2f}%",
                "Delta Tasa": f"{(tasa_comp - tasa_base):+.2f} pp"
            })
    
    if datos_seccion:
        st.dataframe(pd.DataFrame(datos_seccion), use_container_width=True, hide_index=True)

# ---------- RESUMEN DEL PERÍODO ----------
with st.expander("📅 Detalle del período seleccionado"):
    st.markdown(f"""
    **Tipo de comparación:** {tipo_comparacion}
    
    **{año_base}:**
    - Período: {formato_fecha_es(fecha_inicio_base)} → {formato_fecha_es(fecha_fin_base)}
    - Días incluidos: {(fecha_fin_base - fecha_inicio_base).days + 1} días
    - Registros: {len(df_base):,}
    
    **{año_comparar}:**
    - Período: {formato_fecha_es(fecha_inicio_comp)} → {formato_fecha_es(fecha_fin_comp)}
    - Días incluidos: {(fecha_fin_comp - fecha_inicio_comp).days + 1} días
    - Registros: {len(df_comp):,}
    
    **Secciones incluidas:** {', '.join(secciones_seleccionadas)}
    """)

# ---------- PIE DE PÁGINA ----------
st.markdown("---")
st.markdown("""
    <div class='footer'>
        VentasPro Analytics © 2025 | Dashboard profesional para análisis de ventas
    </div>
""", unsafe_allow_html=True)