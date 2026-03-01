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
            min_fecha_base = df_base_year["fecha"].min()
            max_fecha_base = df_base_year["fecha"].max()
            
            col_fecha_base1, col_fecha_base2 = st.columns(2)
            with col_fecha_base1:
                fecha_inicio_base = st.date_input(
                    "Fecha inicial",
                    value=min_fecha_base.date(),
                    min_value=min_fecha_base.date(),
                    max_value=max_fecha_base.date(),
                    key="fecha_inicio_base"
                )
            with col_fecha_base2:
                fecha_fin_base = st.date_input(
                    "Fecha final",
                    value=max_fecha_base.date(),
                    min_value=min_fecha_base.date(),
                    max_value=max_fecha_base.date(),
                    key="fecha_fin_base"
                )
            
            fecha_inicio_base = pd.Timestamp(fecha_inicio_base)
            fecha_fin_base = pd.Timestamp(fecha_fin_base)
            
            if fecha_inicio_base > fecha_fin_base:
                st.error("La fecha inicial debe ser menor o igual a la fecha final")
                fecha_inicio_base, fecha_fin_base = fecha_fin_base, fecha_inicio_base
        else:
            st.warning(f"No hay datos para {año_base}")
            fecha_inicio_base = None
            fecha_fin_base = None
        
        st.markdown("---")
        
        # Filtros para año comparar
        st.markdown(f"**{año_comparar}**")
        df_comp_year = df[df["anio"] == año_comparar]
        if not df_comp_year.empty:
            min_fecha_comp = df_comp_year["fecha"].min()
            max_fecha_comp = df_comp_year["fecha"].max()
            
            col_fecha_comp1, col_fecha_comp2 = st.columns(2)
            with col_fecha_comp1:
                fecha_inicio_comp = st.date_input(
                    "Fecha inicial",
                    value=min_fecha_comp.date(),
                    min_value=min_fecha_comp.date(),
                    max_value=max_fecha_comp.date(),
                    key="fecha_inicio_comp"
                )
            with col_fecha_comp2:
                fecha_fin_comp = st.date_input(
                    "Fecha final",
                    value=max_fecha_comp.date(),
                    min_value=min_fecha_comp.date(),
                    max_value=max_fecha_comp.date(),
                    key="fecha_fin_comp"
                )
            
            fecha_inicio_comp = pd.Timestamp(fecha_inicio_comp)
            fecha_fin_comp = pd.Timestamp(fecha_fin_comp)
            
            if fecha_inicio_comp > fecha_fin_comp:
                st.error("La fecha inicial debe ser menor o igual a la fecha final")
                fecha_inicio_comp, fecha_fin_comp = fecha_fin_comp, fecha_inicio_comp
        else:
            st.warning(f"No hay datos para {año_comparar}")
            fecha_inicio_comp = None
            fecha_fin_comp = None
    
    else:
        # Filtros comunes (mismo rango para ambos años)
        st.markdown("#### 📅 Período común")
        
        # Preparar fechas globales
        df["fecha"] = pd.to_datetime(df["fecha"])
        fecha_min = df["fecha"].min()
        fecha_max = df["fecha"].max()
        
        col_fecha1, col_fecha2 = st.columns(2)
        with col_fecha1:
            fecha_inicio_sel = st.date_input(
                "Fecha inicial",
                value=fecha_min.date(),
                min_value=fecha_min.date(),
                max_value=fecha_max.date(),
                key="fecha_inicio_comun"
            )
        with col_fecha2:
            fecha_fin_sel = st.date_input(
                "Fecha final",
                value=fecha_max.date(),
                min_value=fecha_min.date(),
                max_value=fecha_max.date(),
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
        if fecha_inicio_base and fecha_fin_base:
            st.markdown(f"""
            <div class="active-filters">
                <span class="filter-badge">📅 {año_base}: {fecha_inicio_base.strftime('%d/%m/%Y')} - {fecha_fin_base.strftime('%d/%m/%Y')}</span>
            """, unsafe_allow_html=True)
        
        if fecha_inicio_comp and fecha_fin_comp:
            st.markdown(f"""
                <span class="filter-badge">📅 {año_comparar}: {fecha_inicio_comp.strftime('%d/%m/%Y')} - {fecha_fin_comp.strftime('%d/%m/%Y')}</span>
            """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="active-filters">
            <span class="filter-badge">📅 {fecha_inicio.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')}</span>
            <span class="filter-badge">📋 {dias_en_rango} días</span>
        """, unsafe_allow_html=True)
    
    st.markdown(f"""
        <span class="filter-badge">🏷️ {len(secciones_seleccionadas)} secciones</span>
    </div>
    """, unsafe_allow_html=True)

# ---------- APLICAR FILTROS ----------
if filtros_independientes:
    # Filtrar con períodos independientes
    if fecha_inicio_base and fecha_fin_base:
        datos_base = df[
            (df["anio"] == año_base) &
            (df["fecha"] >= fecha_inicio_base) &
            (df["fecha"] <= fecha_fin_base) &
            (df["secciones"].isin(secciones_seleccionadas))
        ]
        periodo_desc_base = f"{fecha_inicio_base.strftime('%d/%m/%Y')} - {fecha_fin_base.strftime('%d/%m/%Y')}"
    else:
        datos_base = pd.DataFrame()
        periodo_desc_base = "sin datos"
    
    if fecha_inicio_comp and fecha_fin_comp:
        datos_comparar = df[
            (df["anio"] == año_comparar) &
            (df["fecha"] >= fecha_inicio_comp) &
            (df["fecha"] <= fecha_fin_comp) &
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

# ---------- RESTO DEL CÓDIGO (GRÁFICOS, ETC) ----------
# Aquí va todo el código de gráficos que ya tenías antes...
# (Mantén todo el código de gráficos y visualizaciones que ya funcionaba)

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