import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import os
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import calendar

st.set_page_config(
    page_title="Comparador de Ventas Diarias", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS para mejor apariencia
st.markdown("""
<style>
    /* Estilos generales */
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* Tarjetas para métricas */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
        transition: transform 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    /* Tarjeta de presupuesto */
    .budget-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        color: white;
        margin: 1rem 0;
    }
    
    /* Títulos de secciones */
    .section-title {
        color: #1f77b4;
        font-size: 1.5rem;
        font-weight: 600;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #1f77b4;
    }
    
    /* Badges para filtros */
    .filter-badge {
        background-color: #e1f5fe;
        color: #01579b;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
        display: inline-block;
        margin: 0.2rem;
    }
    
    /* Contenedor de filtros activos */
    .active-filters {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

# ---------- DB ----------
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

def eliminar_tabla_existente():
    """Elimina la tabla si existe para recrearla con la nueva estructura"""
    conn = conectar()
    if conn is not None:
        try:
            c = conn.cursor()
            c.execute("DROP TABLE IF EXISTS ventas")
            conn.commit()
        except sqlite3.Error as e:
            st.error(f"Error al eliminar tabla: {e}")
        finally:
            conn.close()

def crear_tabla():
    """Crea la tabla con la nueva estructura"""
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
st.title("📊 Comparador de Ventas Diarias")
st.markdown("### Análisis Comparativo con Presupuesto +15%")

with st.expander("📤 Cargar Excel", expanded=False):
    col_upload1, col_upload2 = st.columns([2, 1])
    with col_upload1:
        archivo = st.file_uploader("Sube archivo Excel", type=["xlsx"])
    with col_upload2:
        anio = st.number_input("Año:", 
                              min_value=2000, 
                              max_value=2100, 
                              value=datetime.now().year,
                              step=1)

    if archivo and st.button("📥 Guardar datos", use_container_width=True):
        try:
            df = pd.read_excel(archivo)

            columnas_requeridas = ["Fecha", "Secciones", "Entradas", "Venta", 
                                  "Tickets", "Artículos", "Ticket promedio", 
                                  "Artículos por ticket", "Tasa de conversión"]
            
            columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
            
            if columnas_faltantes:
                st.error(f"El archivo debe contener: {', '.join(columnas_faltantes)}")
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
                    st.success(f"✅ Datos del año {anio} cargados correctamente ({len(df)} registros)")
                    st.balloons()
                    
        except Exception as e:
            st.error(f"Error al cargar el archivo: {e}")

# ---------- CONSULTAS ----------
def cargar_datos():
    """Carga todos los datos de la base de datos"""
    conn = conectar()
    if conn is not None:
        try:
            df = pd.read_sql("SELECT * FROM ventas", conn)
            # Convertir fecha a datetime
            df["fecha"] = pd.to_datetime(df["fecha"])
            return df
        except sqlite3.Error as e:
            st.error(f"Error al cargar datos: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
    return pd.DataFrame()

df = cargar_datos()

if df.empty:
    st.warning("⚠️ Aún no hay datos cargados")
    st.stop()

# ---------- SIDEBAR - CONFIGURACIÓN ----------
with st.sidebar:
    st.markdown("### ⚙️ Configuración")
    
    # Años disponibles
    años_disponibles = sorted(df["anio"].unique(), reverse=True)
    
    if len(años_disponibles) == 0:
        st.warning("No hay años disponibles")
        st.stop()
    
    # Selectores de años
    st.markdown("#### 📅 Años a comparar")
    col_anio1, col_anio2 = st.columns(2)
    with col_anio1:
        año_base = st.selectbox("Año base", 
                               options=años_disponibles,
                               index=min(1, len(años_disponibles)-1) if len(años_disponibles) > 1 else 0,
                               help="Año anterior para comparar")
    with col_anio2:
        año_comparar = st.selectbox("Año actual", 
                                   options=años_disponibles,
                                   index=0,
                                   help="Año más reciente para comparar")
    
    if año_base == año_comparar and len(años_disponibles) > 1:
        st.warning("Selecciona años diferentes")
        if año_comparar == años_disponibles[0]:
            año_base = años_disponibles[1] if len(años_disponibles) > 1 else año_base
    
    st.markdown("---")
    
    # Opción de filtros independientes
    st.markdown("#### 🔍 Modo de filtrado")
    filtros_independientes = st.checkbox(
        "📅 Filtros independientes por año",
        value=False,
        help="Activa esta opción para seleccionar diferentes períodos en cada año"
    )
    
    st.markdown("---")
    
    # Filtro de secciones (común para ambos años)
    st.markdown("#### 🏷️ Secciones")
    secciones = sorted(df["secciones"].unique())
    secciones_seleccionadas = st.multiselect(
        "Selecciona secciones",
        options=secciones,
        default=secciones,
        key="secciones_filter"
    )
    
    st.markdown("---")
    
    if filtros_independientes:
        # Filtros independientes para cada año
        st.markdown("#### 📅 Períodos por año")
        
        # Filtros para año base
        st.markdown(f"**{año_base}**")
        df_base_year = df[df["anio"] == año_base]
        if not df_base_year.empty:
            min_fecha_base = df_base_year["fecha"].min().date()
            max_fecha_base = df_base_year["fecha"].max().date()
            
            col_fecha_base1, col_fecha_base2 = st.columns(2)
            with col_fecha_base1:
                fecha_inicio_base = st.date_input(
                    "Fecha inicial",
                    value=min_fecha_base,
                    min_value=min_fecha_base,
                    max_value=max_fecha_base,
                    key="fecha_inicio_base"
                )
            with col_fecha_base2:
                fecha_fin_base = st.date_input(
                    "Fecha final",
                    value=max_fecha_base,
                    min_value=min_fecha_base,
                    max_value=max_fecha_base,
                    key="fecha_fin_base"
                )
            
            # Convertir a datetime para filtrado
            fecha_inicio_base_dt = pd.Timestamp(fecha_inicio_base)
            fecha_fin_base_dt = pd.Timestamp(fecha_fin_base)
            
            if fecha_inicio_base_dt > fecha_fin_base_dt:
                st.error("La fecha inicial debe ser menor o igual a la fecha final")
                fecha_inicio_base_dt, fecha_fin_base_dt = fecha_fin_base_dt, fecha_inicio_base_dt
                fecha_inicio_base, fecha_fin_base = fecha_fin_base, fecha_inicio_base
        else:
            st.warning(f"No hay datos para {año_base}")
            fecha_inicio_base_dt = None
            fecha_fin_base_dt = None
            fecha_inicio_base = None
            fecha_fin_base = None
        
        st.markdown("---")
        
        # Filtros para año comparar
        st.markdown(f"**{año_comparar}**")
        df_comp_year = df[df["anio"] == año_comparar]
        if not df_comp_year.empty:
            min_fecha_comp = df_comp_year["fecha"].min().date()
            max_fecha_comp = df_comp_year["fecha"].max().date()
            
            col_fecha_comp1, col_fecha_comp2 = st.columns(2)
            with col_fecha_comp1:
                fecha_inicio_comp = st.date_input(
                    "Fecha inicial",
                    value=min_fecha_comp,
                    min_value=min_fecha_comp,
                    max_value=max_fecha_comp,
                    key="fecha_inicio_comp"
                )
            with col_fecha_comp2:
                fecha_fin_comp = st.date_input(
                    "Fecha final",
                    value=max_fecha_comp,
                    min_value=min_fecha_comp,
                    max_value=max_fecha_comp,
                    key="fecha_fin_comp"
                )
            
            # Convertir a datetime para filtrado
            fecha_inicio_comp_dt = pd.Timestamp(fecha_inicio_comp)
            fecha_fin_comp_dt = pd.Timestamp(fecha_fin_comp)
            
            if fecha_inicio_comp_dt > fecha_fin_comp_dt:
                st.error("La fecha inicial debe ser menor o igual a la fecha final")
                fecha_inicio_comp_dt, fecha_fin_comp_dt = fecha_fin_comp_dt, fecha_inicio_comp_dt
                fecha_inicio_comp, fecha_fin_comp = fecha_fin_comp, fecha_inicio_comp
        else:
            st.warning(f"No hay datos para {año_comparar}")
            fecha_inicio_comp_dt = None
            fecha_fin_comp_dt = None
            fecha_inicio_comp = None
            fecha_fin_comp = None
    
    else:
        # Filtros comunes (mismo rango para ambos años)
        st.markdown("#### 📅 Período común")
        
        # Preparar fechas globales
        fecha_min = df["fecha"].min().date()
        fecha_max = df["fecha"].max().date()
        
        col_fecha1, col_fecha2 = st.columns(2)
        with col_fecha1:
            fecha_inicio_sel = st.date_input(
                "Fecha inicial",
                value=fecha_min,
                min_value=fecha_min,
                max_value=fecha_max,
                key="fecha_inicio_comun"
            )
        with col_fecha2:
            fecha_fin_sel = st.date_input(
                "Fecha final",
                value=fecha_max,
                min_value=fecha_min,
                max_value=fecha_max,
                key="fecha_fin_comun"
            )
        
        fecha_inicio = pd.Timestamp(fecha_inicio_sel)
        fecha_fin = pd.Timestamp(fecha_fin_sel)
        
        if fecha_inicio > fecha_fin:
            st.error("La fecha inicial debe ser menor o igual a la fecha final")
            fecha_inicio, fecha_fin = fecha_fin, fecha_inicio
        
        # Calcular fechas equivalentes en año base
        dias_en_rango = (fecha_fin - fecha_inicio).days + 1
        
        try:
            fecha_inicio_base = fecha_inicio.replace(year=año_base)
            fecha_fin_base = fecha_fin.replace(year=año_base)
        except ValueError:
            # Manejar 29 de febrero
            st.warning("Ajustando fechas para año no bisiesto")
            if fecha_inicio.month == 2 and fecha_inicio.day == 29:
                fecha_inicio_base = fecha_inicio.replace(year=año_base, month=2, day=28)
            else:
                fecha_inicio_base = fecha_inicio.replace(year=año_base)
            
            if fecha_fin.month == 2 and fecha_fin.day == 29:
                fecha_fin_base = fecha_fin.replace(year=año_base, month=2, day=28)
            else:
                fecha_fin_base = fecha_fin.replace(year=año_base)
    
    st.markdown("---")
    
    # Opciones de presupuesto
    st.markdown("#### 💰 Presupuesto")
    mostrar_presupuesto = st.checkbox("Mostrar presupuesto +15%", value=True)
    
    if mostrar_presupuesto:
        crecimiento_presupuesto = st.slider(
            "Crecimiento objetivo (%)",
            min_value=0,
            max_value=50,
            value=15,
            step=1,
            help="Porcentaje de crecimiento para calcular el presupuesto"
        )
    
    st.markdown("---")
    
    # Resumen de filtros
    st.markdown("#### 📊 Filtros activos")
    
    if filtros_independientes:
        filter_html = '<div class="active-filters">'
        if fecha_inicio_base and fecha_fin_base:
            filter_html += f'<span class="filter-badge">📅 {año_base}: {fecha_inicio_base.strftime("%d/%m/%Y")} - {fecha_fin_base.strftime("%d/%m/%Y")}</span>'
        
        if fecha_inicio_comp and fecha_fin_comp:
            filter_html += f'<span class="filter-badge">📅 {año_comparar}: {fecha_inicio_comp.strftime("%d/%m/%Y")} - {fecha_fin_comp.strftime("%d/%m/%Y")}</span>'
    else:
        filter_html = f'''
        <div class="active-filters">
            <span class="filter-badge">📅 {fecha_inicio.strftime("%d/%m/%Y")} - {fecha_fin.strftime("%d/%m/%Y")}</span>
            <span class="filter-badge">📋 {dias_en_rango} días</span>
        '''
    
    filter_html += f'<span class="filter-badge">🏷️ {len(secciones_seleccionadas)} secciones</span></div>'
    st.markdown(filter_html, unsafe_allow_html=True)

# ---------- APLICAR FILTROS ----------
if filtros_independientes:
    # Filtrar con períodos independientes
    if fecha_inicio_base_dt is not None and fecha_fin_base_dt is not None:
        datos_base = df[
            (df["anio"] == año_base) &
            (df["fecha"] >= fecha_inicio_base_dt) &
            (df["fecha"] <= fecha_fin_base_dt) &
            (df["secciones"].isin(secciones_seleccionadas))
        ]
        periodo_desc_base = f"{fecha_inicio_base.strftime('%d/%m/%Y')} - {fecha_fin_base.strftime('%d/%m/%Y')}"
    else:
        datos_base = pd.DataFrame()
        periodo_desc_base = "sin datos"
    
    if fecha_inicio_comp_dt is not None and fecha_fin_comp_dt is not None:
        datos_comparar = df[
            (df["anio"] == año_comparar) &
            (df["fecha"] >= fecha_inicio_comp_dt) &
            (df["fecha"] <= fecha_fin_comp_dt) &
            (df["secciones"].isin(secciones_seleccionadas))
        ]
        periodo_desc_comp = f"{fecha_inicio_comp.strftime('%d/%m/%Y')} - {fecha_fin_comp.strftime('%d/%m/%Y')}"
    else:
        datos_comparar = pd.DataFrame()
        periodo_desc_comp = "sin datos"
    
    periodo_desc = f"Períodos independientes: {año_base} ({periodo_desc_base}) vs {año_comparar} ({periodo_desc_comp})"
    
else:
    # Filtrar con mismo período
    datos_base = df[
        (df["anio"] == año_base) & 
        (df["fecha"] >= fecha_inicio_base) &
        (df["fecha"] <= fecha_fin_base) &
        (df["secciones"].isin(secciones_seleccionadas))
    ]
    
    datos_comparar = df[
        (df["anio"] == año_comparar) & 
        (df["fecha"] >= fecha_inicio) &
        (df["fecha"] <= fecha_fin) &
        (df["secciones"].isin(secciones_seleccionadas))
    ]
    
    if dias_en_rango == 1:
        periodo_desc = f"día {fecha_inicio.strftime('%d/%m/%Y')}"
    else:
        periodo_desc = f"período {fecha_inicio.strftime('%d/%m')} - {fecha_fin.strftime('%d/%m')}"

# ---------- KPIS CON PRESUPUESTO ----------
st.markdown(f'<div class="section-title">📈 Comparación General: {año_base} vs {año_comparar} ({periodo_desc})</div>', unsafe_allow_html=True)

if datos_base.empty and datos_comparar.empty:
    st.warning("No hay datos para los períodos seleccionados")
    st.stop()

# Mostrar información de registros
col_reg1, col_reg2 = st.columns(2)
with col_reg1:
    if not datos_base.empty:
        dias_base = datos_base['fecha'].dt.date.nunique()
        st.info(f"📅 **{año_base}:** {len(datos_base)} registros • {dias_base} días con datos")
    else:
        st.warning(f"⚠️ No hay datos para {año_base} en el período seleccionado")

with col_reg2:
    if not datos_comparar.empty:
        dias_comp = datos_comparar['fecha'].dt.date.nunique()
        st.info(f"📅 **{año_comparar}:** {len(datos_comparar)} registros • {dias_comp} días con datos")
    else:
        st.warning(f"⚠️ No hay datos para {año_comparar} en el período seleccionado")

# Calcular métricas si hay datos en ambos años
if not datos_base.empty and not datos_comparar.empty:
    ventas_base = datos_base["venta"].sum()
    ventas_comp = datos_comparar["venta"].sum()
    entradas_base = datos_base["entradas"].sum()
    entradas_comp = datos_comparar["entradas"].sum()
    
    tickets_base = datos_base["tickets"].sum()
    tickets_comp = datos_comparar["tickets"].sum()
    
    ticket_base = ventas_base / tickets_base if tickets_base > 0 else 0
    ticket_comp = ventas_comp / tickets_comp if tickets_comp > 0 else 0
    
    tasa_base = datos_base["tasa_conversion"].mean()
    tasa_comp = datos_comparar["tasa_conversion"].mean()
    
    # Calcular presupuesto con crecimiento
    if mostrar_presupuesto:
        presupuesto = ventas_base * (1 + crecimiento_presupuesto / 100)
        cumplimiento_presupuesto = (ventas_comp / presupuesto * 100) if presupuesto > 0 else 0
    
    # Crear KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        delta = ((ventas_comp - ventas_base)/ventas_base*100) if ventas_base > 0 else None
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #666; font-size: 0.9rem; margin: 0;">Ventas {año_comparar}</h3>
            <h2 style="color: #1f77b4; font-size: 2rem; margin: 0.5rem 0;">${ventas_comp:,.0f}</h2>
            <p style="color: {'#4caf50' if delta and delta > 0 else '#f44336' if delta and delta < 0 else '#666'}; margin: 0;">
                {f'▲ {delta:.1f}%' if delta and delta > 0 else f'▼ {abs(delta):.1f}%' if delta and delta < 0 else '0%'} vs {año_base}
            </p>
            <p style="color: #999; font-size: 0.8rem; margin: 0.5rem 0 0 0;">{año_base}: ${ventas_base:,.0f}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        delta = ((entradas_comp - entradas_base)/entradas_base*100) if entradas_base > 0 else None
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #666; font-size: 0.9rem; margin: 0;">Entradas {año_comparar}</h3>
            <h2 style="color: #1f77b4; font-size: 2rem; margin: 0.5rem 0;">{entradas_comp:,.0f}</h2>
            <p style="color: {'#4caf50' if delta and delta > 0 else '#f44336' if delta and delta < 0 else '#666'}; margin: 0;">
                {f'▲ {delta:.1f}%' if delta and delta > 0 else f'▼ {abs(delta):.1f}%' if delta and delta < 0 else '0%'} vs {año_base}
            </p>
            <p style="color: #999; font-size: 0.8rem; margin: 0.5rem 0 0 0;">{año_base}: {entradas_base:,.0f}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        delta = ((ticket_comp - ticket_base)/ticket_base*100) if ticket_base > 0 else None
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #666; font-size: 0.9rem; margin: 0;">Ticket Prom. {año_comparar}</h3>
            <h2 style="color: #1f77b4; font-size: 2rem; margin: 0.5rem 0;">${ticket_comp:,.2f}</h2>
            <p style="color: {'#4caf50' if delta and delta > 0 else '#f44336' if delta and delta < 0 else '#666'}; margin: 0;">
                {f'▲ {delta:.1f}%' if delta and delta > 0 else f'▼ {abs(delta):.1f}%' if delta and delta < 0 else '0%'} vs {año_base}
            </p>
            <p style="color: #999; font-size: 0.8rem; margin: 0.5rem 0 0 0;">{año_base}: ${ticket_base:,.2f}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        delta = tasa_comp - tasa_base
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #666; font-size: 0.9rem; margin: 0;">Tasa Conv. {año_comparar}</h3>
            <h2 style="color: #1f77b4; font-size: 2rem; margin: 0.5rem 0;">{tasa_comp:.2f}%</h2>
            <p style="color: {'#4caf50' if delta > 0 else '#f44336' if delta < 0 else '#666'}; margin: 0;">
                {f'▲ {delta:.2f} pp' if delta > 0 else f'▼ {abs(delta):.2f} pp' if delta < 0 else '0 pp'} vs {año_base}
            </p>
            <p style="color: #999; font-size: 0.8rem; margin: 0.5rem 0 0 0;">{año_base}: {tasa_base:.2f}%</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Tarjeta de presupuesto
    if mostrar_presupuesto:
        st.markdown("### 🎯 Presupuesto vs Real")
        
        col_budget1, col_budget2, col_budget3 = st.columns(3)
        
        with col_budget1:
            st.markdown(f"""
            <div class="budget-card">
                <h4 style="margin: 0; opacity: 0.9;">Presupuesto {año_comparar}</h4>
                <h2 style="margin: 0.5rem 0; font-size: 2.2rem;">${presupuesto:,.0f}</h2>
                <p style="margin: 0; opacity: 0.9;">+{crecimiento_presupuesto}% vs {año_base}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col_budget2:
            color_cumpl = "#4caf50" if cumplimiento_presupuesto >= 100 else "#f44336"
            st.markdown(f"""
            <div class="metric-card">
                <h4 style="color: #666; margin: 0;">Cumplimiento</h4>
                <h2 style="color: {color_cumpl}; margin: 0.5rem 0;">{cumplimiento_presupuesto:.1f}%</h2>
                <p style="color: #999;">vs presupuesto</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col_budget3:
            diferencia = ventas_comp - presupuesto
            st.markdown(f"""
            <div class="metric-card">
                <h4 style="color: #666; margin: 0;">Diferencia</h4>
                <h2 style="color: {'#4caf50' if diferencia >= 0 else '#f44336'}; margin: 0.5rem 0;">${diferencia:+,.0f}</h2>
                <p style="color: #999;">vs presupuesto</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Barra de progreso visual
        progreso = min(cumplimiento_presupuesto / 100, 2.0)  # Máximo 200%
        st.progress(progreso if progreso <= 1.0 else 1.0, 
                   text=f"Progreso: {cumplimiento_presupuesto:.1f}% del presupuesto")
        
        if cumplimiento_presupuesto > 100:
            st.success(f"🎉 ¡Superaste el presupuesto en {cumplimiento_presupuesto - 100:.1f}%!")
        elif cumplimiento_presupuesto < 100:
            st.warning(f"📉 Estás {100 - cumplimiento_presupuesto:.1f}% por debajo del presupuesto")

# ---------- GRÁFICOS EXISTENTES ----------
st.markdown(f'<div class="section-title">📊 Análisis Visual</div>', unsafe_allow_html=True)

if not datos_base.empty and not datos_comparar.empty:
    # Preparar datos para gráficos
    # Combinar datos de ambos años para los gráficos que necesitan vista anual
    df_plot = pd.concat([datos_base, datos_comparar])
    df_plot['mes'] = df_plot['fecha'].dt.month
    df_plot['año_str'] = df_plot['anio'].astype(str)
    
    # Diccionario de meses en español
    meses_es = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
        7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }
    df_plot['mes_nombre'] = df_plot['mes'].map(meses_es)
    
    # Gráfico 1: Evolución mensual comparativa
    df_mensual = df_plot.groupby(['mes', 'mes_nombre', 'anio'])['venta'].sum().reset_index()
    df_mensual = df_mensual.sort_values('mes')
    
    fig1 = go.Figure()
    
    for año in [año_base, año_comparar]:
        df_año = df_mensual[df_mensual['anio'] == año]
        if not df_año.empty:
            color = '#1f77b4' if año == año_base else '#ff7f0e'
            nombre = f"Año {año}"
            
            fig1.add_trace(go.Scatter(
                x=df_año['mes_nombre'],
                y=df_año['venta'],
                mode='lines+markers+text',
                name=nombre,
                line=dict(color=color, width=3),
                marker=dict(size=10, symbol='circle'),
                text=df_año['venta'].apply(lambda x: f'${x/1e6:.1f}M'),
                textposition='top center',
                textfont=dict(size=10, color=color),
                hovertemplate='<b>%{x}</b><br>' +
                             'Ventas: $%{y:,.0f}<br>' +
                             '<extra>%{fullData.name}</extra>'
            ))
    
    fig1.update_layout(
        title=dict(
            text='Evolución Mensual de Ventas',
            x=0.5,
            font=dict(size=20)
        ),
        xaxis=dict(
            title='Mes',
            tickangle=45,
            categoryorder='array',
            categoryarray=list(meses_es.values()),
            gridcolor='lightgray'
        ),
        yaxis=dict(
            title='Ventas ($)',
            gridcolor='lightgray',
            tickformat='$,.0f'
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        hovermode='x unified',
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='center',
            x=0.5
        ),
        margin=dict(b=100)
    )
    
    st.plotly_chart(fig1, use_container_width=True)
    
    # Gráfico 2: Barras comparativas por sección
    st.markdown("### 📊 Comparación por Sección")
    
    df_secciones = df_plot.groupby(['secciones', 'anio'])['venta'].sum().reset_index()
    
    fig2 = go.Figure()
    
    for año in [año_base, año_comparar]:
        df_año = df_secciones[df_secciones['anio'] == año]
        if not df_año.empty:
            color = '#1f77b4' if año == año_base else '#ff7f0e'
            nombre = f"Año {año}"
            
            fig2.add_trace(go.Bar(
                x=df_año['secciones'],
                y=df_año['venta'],
                name=nombre,
                marker_color=color,
                text=df_año['venta'].apply(lambda x: f'${x/1e6:.1f}M'),
                textposition='outside',
                textfont=dict(size=11),
                hovertemplate='<b>%{x}</b><br>' +
                             'Ventas: $%{y:,.0f}<br>' +
                             '<extra>%{fullData.name}</extra>'
            ))
    
    fig2.update_layout(
        title=dict(
            text='Ventas por Sección - Comparativa Anual',
            x=0.5,
            font=dict(size=18)
        ),
        xaxis=dict(
            title='Sección',
            tickangle=45,
            gridcolor='lightgray'
        ),
        yaxis=dict(
            title='Ventas ($)',
            gridcolor='lightgray',
            tickformat='$,.0f'
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        barmode='group',
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='center',
            x=0.5
        ),
        margin=dict(b=100)
    )
    
    st.plotly_chart(fig2, use_container_width=True)
    
    # Gráfico 3: Distribución de tickets y entradas
    st.markdown("### 📈 Análisis de Eficiencia")
    
    df_eficiencia = df_plot.groupby('anio').agg({
        'tickets': 'sum',
        'entradas': 'sum',
        'ticket_promedio': 'mean',
        'tasa_conversion': 'mean',
        'venta': 'sum'
    }).reset_index()
    
    fig3 = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Tickets vs Entradas', 'Ticket Promedio', 
                       'Tasa de Conversión', 'Distribución de Ventas'),
        specs=[
            [{'type': 'bar'}, {'type': 'bar'}],
            [{'type': 'bar'}, {'type': 'pie'}]
        ]
    )
    
    # Gráfico 1: Tickets vs Entradas
    for i, fila in df_eficiencia.iterrows():
        año = int(fila['anio'])
        color = '#1f77b4' if año == año_base else '#ff7f0e'
        
        fig3.add_trace(
            go.Bar(
                name=f'Tickets {año}',
                x=[str(año)],
                y=[fila['tickets']],
                marker_color=color,
                text=[f'{fila["tickets"]:,.0f}'],
                textposition='inside',
                showlegend=False
            ),
            row=1, col=1
        )
        
        fig3.add_trace(
            go.Bar(
                name=f'Entradas {año}',
                x=[str(año)],
                y=[fila['entradas']],
                marker_color=color,
                marker_pattern_shape="/" if año == año_comparar else "",
                text=[f'{fila["entradas"]:,.0f}'],
                textposition='inside',
                showlegend=False
            ),
            row=1, col=1
        )
    
    # Gráfico 2: Ticket Promedio
    fig3.add_trace(
        go.Bar(
            x=df_eficiencia['anio'].astype(str),
            y=df_eficiencia['ticket_promedio'],
            marker_color=['#1f77b4', '#ff7f0e'],
            text=df_eficiencia['ticket_promedio'].apply(lambda x: f'${x:,.2f}'),
            textposition='outside',
            showlegend=False
        ),
        row=1, col=2
    )
    
    # Gráfico 3: Tasa de Conversión
    fig3.add_trace(
        go.Bar(
            x=df_eficiencia['anio'].astype(str),
            y=df_eficiencia['tasa_conversion'],
            marker_color=['#1f77b4', '#ff7f0e'],
            text=df_eficiencia['tasa_conversion'].apply(lambda x: f'{x:.2f}%'),
            textposition='outside',
            showlegend=False
        ),
        row=2, col=1
    )
    
    # Gráfico 4: Distribución de ventas por año
    fig3.add_trace(
        go.Pie(
            labels=[f'Año {int(año)}' for año in df_eficiencia['anio']],
            values=df_eficiencia['venta'],
            marker_colors=['#1f77b4', '#ff7f0e'],
            textinfo='label+percent',
            textposition='inside',
            hole=0.3,
            showlegend=False
        ),
        row=2, col=2
    )
    
    fig3.update_layout(
        height=600,
        title_text="Métricas de Eficiencia",
        title_x=0.5,
        title_font=dict(size=18),
        plot_bgcolor='white',
        paper_bgcolor='white',
        showlegend=False,
        barmode='group'
    )
    
    fig3.update_xaxes(gridcolor='lightgray')
    fig3.update_yaxes(gridcolor='lightgray', tickformat='$,.2f', row=1, col=2)
    fig3.update_yaxes(gridcolor='lightgray', tickformat='.1f', row=2, col=1)
    
    st.plotly_chart(fig3, use_container_width=True)
    
    # Gráfico 4: Heatmap de rendimiento por mes y sección
    st.markdown("### 🔥 Mapa de Calor - Rendimiento por Mes y Sección")
    
    # Seleccionar año para el heatmap
    año_heatmap = st.radio(
        "Selecciona año para ver el detalle:",
        [año_base, año_comparar],
        horizontal=True
    )
    
    df_heat = df_plot[df_plot['anio'] == año_heatmap].copy()
    
    if not df_heat.empty:
        # Crear tabla pivote para el heatmap
        pivot_heat = df_heat.pivot_table(
            values='venta',
            index='secciones',
            columns='mes_nombre',
            aggfunc='sum',
            fill_value=0
        )
        
        # Reordenar meses
        meses_disponibles = [col for col in list(meses_es.values()) if col in pivot_heat.columns]
        pivot_heat = pivot_heat[meses_disponibles]
        
        if not pivot_heat.empty:
            fig4 = go.Figure(data=go.Heatmap(
                z=pivot_heat.values,
                x=pivot_heat.columns,
                y=pivot_heat.index,
                colorscale='Viridis',
                text=pivot_heat.values,
                texttemplate='$%{text:,.0f}',
                textfont={"size": 10},
                hovertemplate='<b>%{y}</b><br>' +
                             'Mes: %{x}<br>' +
                             'Ventas: $%{z:,.0f}<br>' +
                             '<extra></extra>'
            ))
            
            fig4.update_layout(
                title=f'Distribución de Ventas {año_heatmap}',
                xaxis=dict(
                    title='Mes',
                    tickangle=45
                ),
                yaxis=dict(
                    title='Sección'
                ),
                height=400,
                plot_bgcolor='white',
                paper_bgcolor='white'
            )
            
            st.plotly_chart(fig4, use_container_width=True)
    
    # Gráfico 5: Tendencia de ticket promedio
    st.markdown("### 📈 Evolución del Ticket Promedio")
    
    df_ticket = df_plot.groupby(['mes', 'mes_nombre', 'anio'])['ticket_promedio'].mean().reset_index()
    df_ticket = df_ticket.sort_values('mes')
    
    fig5 = go.Figure()
    
    for año in [año_base, año_comparar]:
        df_año = df_ticket[df_ticket['anio'] == año]
        if not df_año.empty:
            color = '#1f77b4' if año == año_base else '#ff7f0e'
            nombre = f"Año {año}"
            
            fig5.add_trace(go.Scatter(
                x=df_año['mes_nombre'],
                y=df_año['ticket_promedio'],
                mode='lines+markers',
                name=nombre,
                line=dict(color=color, width=3, dash='solid'),
                marker=dict(size=8),
                hovertemplate='<b>%{x}</b><br>' +
                             'Ticket Prom.: $%{y:,.2f}<br>' +
                             '<extra>%{fullData.name}</extra>'
            ))
    
    fig5.update_layout(
        title='Evolución del Ticket Promedio por Mes',
        xaxis=dict(
            title='Mes',
            tickangle=45,
            categoryorder='array',
            categoryarray=list(meses_es.values())
        ),
        yaxis=dict(
            title='Ticket Promedio ($)',
            tickformat='$,.2f',
            gridcolor='lightgray'
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        hovermode='x unified',
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='center',
            x=0.5
        )
    )
    
    st.plotly_chart(fig5, use_container_width=True)

else:
    if datos_base.empty and datos_comparar.empty:
        st.warning("No hay datos para los años seleccionados en el período equivalente.")
    elif datos_base.empty:
        st.info(f"Solo hay datos para {año_comparar} en el {periodo_desc}. Selecciona otro año base para comparar.")
    else:
        st.info(f"Solo hay datos para {año_base} en el {periodo_desc}. Selecciona otro año para comparar.")

# ---------- NUEVOS GRÁFICOS DE PRESUPUESTO ----------
if not datos_base.empty and not datos_comparar.empty and mostrar_presupuesto:
    st.markdown(f'<div class="section-title">📈 Evolución Comparativa con Presupuesto</div>', unsafe_allow_html=True)
    
    # Preparar datos para la gráfica de evolución acumulada
    # Agrupar por fecha para ambos años y calcular acumulado
    df_evolucion_base = datos_base.groupby('fecha')['venta'].sum().reset_index()
    df_evolucion_base = df_evolucion_base.sort_values('fecha')
    df_evolucion_base['venta_acum'] = df_evolucion_base['venta'].cumsum()
    df_evolucion_base['año'] = año_base
    df_evolucion_base['tipo'] = 'Real'
    
    df_evolucion_comp = datos_comparar.groupby('fecha')['venta'].sum().reset_index()
    df_evolucion_comp = df_evolucion_comp.sort_values('fecha')
    df_evolucion_comp['venta_acum'] = df_evolucion_comp['venta'].cumsum()
    df_evolucion_comp['año'] = año_comparar
    df_evolucion_comp['tipo'] = 'Real'
    
    # Calcular líneas de presupuesto
    # Para el año base (presupuesto base = ventas reales acumuladas)
    if len(df_evolucion_base) > 0:
        primer_dia_base = df_evolucion_base['fecha'].iloc[0]
        ultimo_dia_base = df_evolucion_base['fecha'].iloc[-1]
        dias_totales_base = (ultimo_dia_base - primer_dia_base).days + 1
        
        # Presupuesto diario para año base (promedio)
        presupuesto_diario_base = ventas_base / dias_totales_base if dias_totales_base > 0 else 0
        
        # Crear DataFrame para línea de presupuesto base
        df_presupuesto_base = pd.DataFrame({
            'fecha': df_evolucion_base['fecha'],
            'venta_acum': [presupuesto_diario_base * (i + 1) for i in range(len(df_evolucion_base))],
            'año': año_base,
            'tipo': 'Presupuesto'
        })
    
    # Para el año comparar (presupuesto = ventas base * (1 + crecimiento))
    if len(df_evolucion_comp) > 0:
        primer_dia_comp = df_evolucion_comp['fecha'].iloc[0]
        ultimo_dia_comp = df_evolucion_comp['fecha'].iloc[-1]
        dias_totales_comp = (ultimo_dia_comp - primer_dia_comp).days + 1
        
        # Presupuesto diario para año comparar
        presupuesto_diario_comp = presupuesto / dias_totales_comp if dias_totales_comp > 0 else 0
        
        # Crear DataFrame para línea de presupuesto comparar
        df_presupuesto_comp = pd.DataFrame({
            'fecha': df_evolucion_comp['fecha'],
            'venta_acum': [presupuesto_diario_comp * (i + 1) for i in range(len(df_evolucion_comp))],
            'año': año_comparar,
            'tipo': 'Presupuesto'
        })
    
    # Crear figura con Plotly
    fig_evolucion = go.Figure()
    
    # Línea real año base
    if not df_evolucion_base.empty:
        fig_evolucion.add_trace(go.Scatter(
            x=df_evolucion_base['fecha'],
            y=df_evolucion_base['venta_acum'],
            mode='lines+markers',
            name=f'Real {año_base}',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=6),
            hovertemplate='<b>%{x|%d/%m/%Y}</b><br>' +
                         f'Real {año_base}: $%{{y:,.0f}}<br>' +
                         '<extra></extra>'
        ))
    
    # Línea presupuesto año base
    if not df_presupuesto_base.empty:
        fig_evolucion.add_trace(go.Scatter(
            x=df_presupuesto_base['fecha'],
            y=df_presupuesto_base['venta_acum'],
            mode='lines',
            name=f'Presupuesto {año_base}',
            line=dict(color='rgba(31, 119, 180, 0.3)', width=2, dash='dash'),
            hovertemplate='<b>%{x|%d/%m/%Y}</b><br>' +
                         f'Presupuesto {año_base}: $%{{y:,.0f}}<br>' +
                         '<extra></extra>'
        ))
    
    # Línea real año comparar
    if not df_evolucion_comp.empty:
        fig_evolucion.add_trace(go.Scatter(
            x=df_evolucion_comp['fecha'],
            y=df_evolucion_comp['venta_acum'],
            mode='lines+markers',
            name=f'Real {año_comparar}',
            line=dict(color='#ff7f0e', width=3),
            marker=dict(size=6),
            hovertemplate='<b>%{x|%d/%m/%Y}</b><br>' +
                         f'Real {año_comparar}: $%{{y:,.0f}}<br>' +
                         '<extra></extra>'
        ))
    
    # Línea presupuesto año comparar
    if not df_presupuesto_comp.empty:
        fig_evolucion.add_trace(go.Scatter(
            x=df_presupuesto_comp['fecha'],
            y=df_presupuesto_comp['venta_acum'],
            mode='lines',
            name=f'Presupuesto {año_comparar}',
            line=dict(color='rgba(255, 127, 14, 0.3)', width=2, dash='dash'),
            hovertemplate='<b>%{x|%d/%m/%Y}</b><br>' +
                         f'Presupuesto {año_comparar}: $%{{y:,.0f}}<br>' +
                         '<extra></extra>'
        ))
    
    # Configurar layout
    fig_evolucion.update_layout(
        title=dict(
            text=f'Evolución Acumulada de Ventas vs Presupuesto (+{crecimiento_presupuesto}%)',
            x=0.5,
            font=dict(size=20)
        ),
        xaxis=dict(
            title='Fecha',
            tickformat='%d/%m/%Y',
            tickangle=45,
            gridcolor='lightgray'
        ),
        yaxis=dict(
            title='Ventas Acumuladas ($)',
            gridcolor='lightgray',
            tickformat='$,.0f'
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        hovermode='x unified',
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='center',
            x=0.5
        ),
        margin=dict(b=100)
    )
    
    # Añadir anotación con el objetivo
    fig_evolucion.add_annotation(
        x=0.02,
        y=0.98,
        xref='paper',
        yref='paper',
        text=f'Objetivo {año_comparar}: ${presupuesto:,.0f}',
        showarrow=False,
        font=dict(size=12, color='#666'),
        bgcolor='rgba(255,255,255,0.8)',
        bordercolor='#ccc',
        borderwidth=1,
        borderpad=4
    )
    
    st.plotly_chart(fig_evolucion, use_container_width=True)
    
    # Métricas de seguimiento
    col_comp1, col_comp2, col_comp3 = st.columns(3)
    
    with col_comp1:
        # Comparación con año base
        if not df_evolucion_comp.empty and not df_evolucion_base.empty:
            ultimo_valor_comp = df_evolucion_comp['venta_acum'].iloc[-1]
            ultimo_valor_base = df_evolucion_base['venta_acum'].iloc[-1]
            diff_base = ((ultimo_valor_comp - ultimo_valor_base) / ultimo_valor_base * 100) if ultimo_valor_base > 0 else 0
            
            st.metric(
                f"vs {año_base}",
                f"${ultimo_valor_comp:,.0f}",
                f"{diff_base:+.1f}%",
                delta_color="normal"
            )
    
    with col_comp2:
        # Comparación con presupuesto
        if not df_evolucion_comp.empty and not df_presupuesto_comp.empty:
            ultimo_real = df_evolucion_comp['venta_acum'].iloc[-1]
            ultimo_pres = df_presupuesto_comp['venta_acum'].iloc[-1]
            cumplimiento = (ultimo_real / ultimo_pres * 100) if ultimo_pres > 0 else 0
            
            st.metric(
                "Cumplimiento",
                f"{cumplimiento:.1f}%",
                f"${ultimo_real - ultimo_pres:+,.0f}",
                delta_color="off" if cumplimiento >= 100 else "inverse"
            )
    
    with col_comp3:
        # Proyección final
        if not df_evolucion_comp.empty and dias_totales_comp > 0:
            dias_transcurridos = len(df_evolucion_comp)
            ritmo_diario = ultimo_real / dias_transcurridos if dias_transcurridos > 0 else 0
            proyeccion = ritmo_diario * dias_totales_comp
            
            st.metric(
                "Proyección final",
                f"${proyeccion:,.0f}",
                f"{((proyeccion - presupuesto)/presupuesto*100):+.1f}% vs objetivo",
                delta_color="normal"
            )
    
    # Gráfico de barras comparativo
    st.markdown("### 📊 Comparación por Año")
    
    periodos = [str(año_base), str(año_comparar)]
    valores_reales = [ventas_base, ventas_comp]
    valores_presupuesto = [ventas_base, presupuesto]
    
    fig_barras = go.Figure()
    
    # Barras de real
    fig_barras.add_trace(go.Bar(
        name='Real',
        x=periodos,
        y=valores_reales,
        marker_color=['#1f77b4', '#ff7f0e'],
        text=[f'${v:,.0f}' for v in valores_reales],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>' +
                     'Real: $%{y:,.0f}<br>' +
                     '<extra></extra>'
    ))
    
    # Línea de presupuesto
    fig_barras.add_trace(go.Scatter(
        name='Presupuesto',
        x=periodos,
        y=valores_presupuesto,
        mode='markers+lines',
        marker=dict(
            symbol='diamond',
            size=15,
            color=['#1f77b4', '#ff7f0e'],
            line=dict(color='white', width=2)
        ),
        line=dict(
            color='rgba(0,0,0,0.3)',
            width=2,
            dash='dot'
        ),
        text=[f'${v:,.0f}' for v in valores_presupuesto],
        textposition='top center',
        hovertemplate='<b>%{x}</b><br>' +
                     'Presupuesto: $%{y:,.0f}<br>' +
                     '<extra></extra>'
    ))
    
    fig_barras.update_layout(
        title=dict(
            text='Ventas Reales vs Presupuesto',
            x=0.5,
            font=dict(size=18)
        ),
        xaxis=dict(
            title='Año',
            gridcolor='lightgray'
        ),
        yaxis=dict(
            title='Ventas ($)',
            gridcolor='lightgray',
            tickformat='$,.0f'
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        barmode='group',
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='center',
            x=0.5
        ),
        margin=dict(b=50)
    )
    
    st.plotly_chart(fig_barras, use_container_width=True)
    
    # Tabla resumen
    st.markdown("### 📋 Resumen Comparativo")
    
    # Calcular promedios diarios
    promedio_diario_base = ventas_base / dias_base if dias_base > 0 else 0
    promedio_diario_comp = ventas_comp / dias_comp if dias_comp > 0 else 0
    
    df_resumen = pd.DataFrame({
        'Métrica': ['Ventas Totales', 'Días con datos', 'Promedio diario', 'vs Presupuesto'],
        str(año_base): [
            f'${ventas_base:,.0f}',
            f'{dias_base} días',
            f'${promedio_diario_base:,.0f}',
            'Base'
        ],
        str(año_comparar): [
            f'${ventas_comp:,.0f}',
            f'{dias_comp} días',
            f'${promedio_diario_comp:,.0f}',
            f'{cumplimiento_presupuesto:.1f}%'
        ],
        'Variación': [
            f'{((ventas_comp-ventas_base)/ventas_base*100):+.1f}%' if ventas_base > 0 else 'N/A',
            f'{((dias_comp-dias_base)/dias_base*100):+.1f}%' if dias_base > 0 else 'N/A',
            f'{((promedio_diario_comp - promedio_diario_base)/promedio_diario_base*100):+.1f}%' if promedio_diario_base > 0 else 'N/A',
            f'{cumplimiento_presupuesto-100:+.1f}%'
        ]
    })
    
    st.dataframe(df_resumen, use_container_width=True, hide_index=True)

# ---------- COMPARACIÓN DÍA A DÍA ----------
st.markdown(f'<div class="section-title">📅 Comparación Día a Día</div>', unsafe_allow_html=True)

if not datos_base.empty and not datos_comparar.empty:
    
    st.info("""
    **🔍 Compara un día específico de cada año**
    
    Selecciona una fecha de cada año para ver cómo se comparan las métricas. 
    Puedes buscar el mismo día (mismo mes y día) en ambos años con el botón "🔄 Mismo día".
    """)
    
    # Selectores de fecha
    col_cal1, col_cal2, col_cal3 = st.columns([2, 2, 1])
    
    with col_cal1:
        st.markdown(f"### **{año_base}**")
        fechas_base = sorted(datos_base["fecha"].dt.date.unique())
        
        fecha_base = st.selectbox(
            "Selecciona fecha",
            options=fechas_base,
            format_func=lambda x: x.strftime("%A %d de %B, %Y") if hasattr(x, 'strftime') else str(x),
            key="fecha_base_select"
        )
    
    with col_cal2:
        st.markdown(f"### **{año_comparar}**")
        fechas_comp = sorted(datos_comparar["fecha"].dt.date.unique())
        
        fecha_comp = st.selectbox(
            "Selecciona fecha",
            options=fechas_comp,
            format_func=lambda x: x.strftime("%A %d de %B, %Y") if hasattr(x, 'strftime') else str(x),
            key="fecha_comp_select"
        )
    
    with col_cal3:
        st.markdown("### **Acciones**")
        
        if st.button("🔄 Mismo día", use_container_width=True, type="primary"):
            # Buscar mismo mes/día
            fecha_encontrada = False
            for f_base in fechas_base:
                for f_comp in fechas_comp:
                    if f_base.month == f_comp.month and f_base.day == f_comp.day:
                        fecha_base = f_base
                        fecha_comp = f_comp
                        fecha_encontrada = True
                        st.success(f"✓ {f_base.strftime('%d de %B')} encontrado en ambos años")
                        st.rerun()
                        break
                if fecha_encontrada:
                    break
            
            if not fecha_encontrada:
                st.warning("No se encontró el mismo día en ambos años")
    
    # Mostrar comparación si hay fechas seleccionadas
    if fecha_base and fecha_comp:
        datos_dia_base = datos_base[datos_base["fecha"].dt.date == fecha_base]
        datos_dia_comp = datos_comparar[datos_comparar["fecha"].dt.date == fecha_comp]
        
        if not datos_dia_base.empty and not datos_dia_comp.empty:
            st.markdown("---")
            st.markdown(f"## 📊 Comparación: {fecha_base.strftime('%d/%m/%Y')} vs {fecha_comp.strftime('%d/%m/%Y')}")
            
            # Calcular métricas del día
            venta_base = datos_dia_base["venta"].sum()
            venta_comp = datos_dia_comp["venta"].sum()
            entradas_base = datos_dia_base["entradas"].sum()
            entradas_comp = datos_dia_comp["entradas"].sum()
            tickets_base = datos_dia_base["tickets"].sum()
            tickets_comp = datos_dia_comp["tickets"].sum()
            
            ticket_prom_base = venta_base / tickets_base if tickets_base > 0 else 0
            ticket_prom_comp = venta_comp / tickets_comp if tickets_comp > 0 else 0
            
            tasa_base = datos_dia_base["tasa_conversion"].mean()
            tasa_comp = datos_dia_comp["tasa_conversion"].mean()
            
            # Mostrar KPIs del día
            col_d1, col_d2, col_d3, col_d4 = st.columns(4)
            
            delta_venta = ((venta_comp - venta_base)/venta_base*100) if venta_base > 0 else None
            with col_d1:
                st.metric(
                    f"Ventas {año_comparar}",
                    f"${venta_comp:,.0f}",
                    f"{delta_venta:+.1f}%" if delta_venta else None
                )
            
            delta_ent = ((entradas_comp - entradas_base)/entradas_base*100) if entradas_base > 0 else None
            with col_d2:
                st.metric(
                    f"Entradas {año_comparar}",
                    f"{entradas_comp:,.0f}",
                    f"{delta_ent:+.1f}%" if delta_ent else None
                )
            
            delta_ticket = ((ticket_prom_comp - ticket_prom_base)/ticket_prom_base*100) if ticket_prom_base > 0 else None
            with col_d3:
                st.metric(
                    f"Ticket Prom. {año_comparar}",
                    f"${ticket_prom_comp:,.2f}",
                    f"{delta_ticket:+.1f}%" if delta_ticket else None
                )
            
            delta_tasa = tasa_comp - tasa_base
            with col_d4:
                st.metric(
                    f"Tasa Conv. {año_comparar}",
                    f"{tasa_comp:.2f}%",
                    f"{delta_tasa:+.2f} pp"
                )

# ---------- DATOS DETALLADOS ----------
with st.expander("📋 Ver datos detallados", expanded=False):
    tab1, tab2 = st.tabs(["Resumen por Período", "Registros Detallados"])
    
    with tab1:
        # Crear resumen para los períodos seleccionados
        resumen_data = []
        
        if not datos_base.empty:
            resumen_data.append({
                "Año": año_base,
                "Período": periodo_desc,
                "Ventas Totales": f"${datos_base['venta'].sum():,.0f}",
                "Entradas Totales": f"{datos_base['entradas'].sum():,.0f}",
                "Tickets Totales": f"{datos_base['tickets'].sum():,.0f}",
                "Ticket Prom.": f"${datos_base['venta'].sum()/datos_base['tickets'].sum():,.2f}" if datos_base['tickets'].sum() > 0 else "N/A",
                "Tasa Conv.": f"{datos_base['tasa_conversion'].mean():.2f}%"
            })
        
        if not datos_comparar.empty:
            resumen_data.append({
                "Año": año_comparar,
                "Período": periodo_desc,
                "Ventas Totales": f"${datos_comparar['venta'].sum():,.0f}",
                "Entradas Totales": f"{datos_comparar['entradas'].sum():,.0f}",
                "Tickets Totales": f"{datos_comparar['tickets'].sum():,.0f}",
                "Ticket Prom.": f"${datos_comparar['venta'].sum()/datos_comparar['tickets'].sum():,.2f}" if datos_comparar['tickets'].sum() > 0 else "N/A",
                "Tasa Conv.": f"{datos_comparar['tasa_conversion'].mean():.2f}%"
            })
        
        resumen_df = pd.DataFrame(resumen_data)
        st.dataframe(resumen_df, use_container_width=True)
    
    with tab2:
        # Mostrar todos los registros del período seleccionado
        df_detalle = pd.concat([datos_base, datos_comparar]) if not datos_base.empty or not datos_comparar.empty else pd.DataFrame()
        if not df_detalle.empty:
            st.dataframe(
                df_detalle.sort_values(["anio", "fecha"], ascending=[False, False])
                .style.format({
                    "venta": "${:,.0f}",
                    "ticket_promedio": "${:,.2f}",
                    "tasa_conversion": "{:.2f}%"
                }),
                use_container_width=True
            )

# ---------- ADMINISTRACIÓN ----------
with st.expander("⚙️ Administración", expanded=False):
    col_admin1, col_admin2 = st.columns(2)
    
    with col_admin1:
        if st.button("🗑️ Borrar todos los datos", use_container_width=True):
            conn = conectar()
            if conn is not None:
                try:
                    conn.execute("DELETE FROM ventas")
                    conn.commit()
                    st.warning("Base de datos limpiada")
                    st.rerun()
                except sqlite3.Error as e:
                    st.error(f"Error: {e}")
                finally:
                    conn.close()
    
    with col_admin2:
        if st.button("🔄 Reiniciar estructura", use_container_width=True):
            eliminar_tabla_existente()
            crear_tabla()
            st.success("Estructura reiniciada")
            st.rerun()