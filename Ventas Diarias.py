import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
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
st.markdown("### Análisis Comparativo Interanual")

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
    
    # Selectores de años con diseño mejorado
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
    
    # Filtros
    st.markdown("#### 🔍 Filtros")
    
    # Preparar fechas
    df["fecha"] = pd.to_datetime(df["fecha"])
    fecha_min = df["fecha"].min()
    fecha_max = df["fecha"].max()
    
    # Selector de rango de fechas
    if fecha_min.date() == fecha_max.date():
        fecha_seleccionada = st.date_input(
            "Fecha",
            value=fecha_min.date(),
            min_value=fecha_min.date(),
            max_value=fecha_max.date(),
            key="fecha_unica"
        )
        fecha_inicio = pd.Timestamp(fecha_seleccionada)
        fecha_fin = pd.Timestamp(fecha_seleccionada)
    else:
        col_fecha1, col_fecha2 = st.columns(2)
        with col_fecha1:
            fecha_inicio_sel = st.date_input(
                "Fecha inicial",
                value=fecha_min.date(),
                min_value=fecha_min.date(),
                max_value=fecha_max.date(),
                key="fecha_inicio"
            )
        with col_fecha2:
            fecha_fin_sel = st.date_input(
                "Fecha final",
                value=fecha_max.date(),
                min_value=fecha_min.date(),
                max_value=fecha_max.date(),
                key="fecha_fin"
            )
        
        fecha_inicio = pd.Timestamp(fecha_inicio_sel)
        fecha_fin = pd.Timestamp(fecha_fin_sel)
        
        if fecha_inicio > fecha_fin:
            st.error("La fecha inicial debe ser menor o igual a la fecha final")
            fecha_inicio, fecha_fin = fecha_fin, fecha_inicio
    
    # Filtro de secciones
    secciones = sorted(df["secciones"].unique())
    secciones_seleccionadas = st.multiselect(
        "Secciones",
        options=secciones,
        default=secciones,
        key="secciones_filter",
        help="Selecciona una o más secciones"
    )
    
    # Aplicar filtros
    df_filtrado = df[
        (df["fecha"] >= fecha_inicio) &
        (df["fecha"] <= fecha_fin) &
        (df["secciones"].isin(secciones_seleccionadas))
    ]
    
    # Resumen de filtros activos
    st.markdown("---")
    st.markdown("#### 📊 Filtros activos")
    st.markdown(f"""
    <div class="active-filters">
        <span class="filter-badge">📅 {fecha_inicio.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')}</span>
        <span class="filter-badge">🏷️ {len(secciones_seleccionadas)} secciones</span>
        <span class="filter-badge">📋 {len(df_filtrado):,} registros</span>
    </div>
    """, unsafe_allow_html=True)

# ---------- DATOS FILTRADOS POR AÑO ----------
datos_base = df_filtrado[df_filtrado["anio"] == año_base]
datos_comparar = df_filtrado[df_filtrado["anio"] == año_comparar]

# ---------- KPIS CON TARJETAS MODERNAS ----------
st.markdown(f'<div class="section-title">📈 Comparación General: {año_base} vs {año_comparar}</div>', unsafe_allow_html=True)

if datos_base.empty and datos_comparar.empty:
    st.warning("No hay datos para los años seleccionados en el rango de fechas")
    st.stop()
elif datos_base.empty:
    st.info(f"Mostrando solo datos de {año_comparar}")
    kpi_data = [(año_comparar, datos_comparar)]
elif datos_comparar.empty:
    st.info(f"Mostrando solo datos de {año_base}")
    kpi_data = [(año_base, datos_base)]
else:
    kpi_data = [(año_base, datos_base), (año_comparar, datos_comparar)]

# Calcular métricas
if not datos_base.empty and not datos_comparar.empty:
    ventas_base = datos_base["venta"].sum()
    ventas_comp = datos_comparar["venta"].sum()
    entradas_base = datos_base["entradas"].sum()
    entradas_comp = datos_comparar["entradas"].sum()
    
    ticket_base = ventas_base / datos_base["tickets"].sum() if datos_base["tickets"].sum() > 0 else 0
    ticket_comp = ventas_comp / datos_comparar["tickets"].sum() if datos_comparar["tickets"].sum() > 0 else 0
    
    tasa_base = datos_base["tasa_conversion"].mean()
    tasa_comp = datos_comparar["tasa_conversion"].mean()
    
    # Crear tarjetas con estilo moderno
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
        delta = tasa_comp - tasa_base if tasa_base > 0 else None
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #666; font-size: 0.9rem; margin: 0;">Tasa Conv. {año_comparar}</h3>
            <h2 style="color: #1f77b4; font-size: 2rem; margin: 0.5rem 0;">{tasa_comp:.2f}%</h2>
            <p style="color: {'#4caf50' if delta and delta > 0 else '#f44336' if delta and delta < 0 else '#666'}; margin: 0;">
                {f'▲ {delta:.2f} pp' if delta and delta > 0 else f'▼ {abs(delta):.2f} pp' if delta and delta < 0 else '0 pp'} vs {año_base}
            </p>
            <p style="color: #999; font-size: 0.8rem; margin: 0.5rem 0 0 0;">{año_base}: {tasa_base:.2f}%</p>
        </div>
        """, unsafe_allow_html=True)

# ---------- GRÁFICOS ROBUSTOS CON PLOTLY ----------
st.markdown(f'<div class="section-title">📊 Análisis Visual</div>', unsafe_allow_html=True)

if not datos_base.empty and not datos_comparar.empty:
    # Preparar datos para gráficos
    df_plot = df_filtrado[df_filtrado["anio"].isin([año_base, año_comparar])].copy()
    df_plot['mes'] = df_plot['fecha'].dt.month
    df_plot['mes_nombre'] = df_plot['fecha'].dt.strftime('%b')
    df_plot['año_str'] = df_plot['anio'].astype(str)
    
    # Gráfico 1: Evolución mensual comparativa
    df_mensual = df_plot.groupby(['mes', 'mes_nombre', 'anio'])['venta'].sum().reset_index()
    
    fig1 = px.line(
        df_mensual,
        x='mes_nombre',
        y='venta',
        color='anio',
        title='Evolución Mensual de Ventas',
        labels={'mes_nombre': 'Mes', 'venta': 'Ventas ($)', 'anio': 'Año'},
        color_discrete_map={año_base: '#1f77b4', año_comparar: '#ff7f0e'},
        line_shape='spline',
        markers=True
    )
    
    fig1.update_traces(
        line=dict(width=3),
        marker=dict(size=8)
    )
    
    fig1.update_layout(
        hovermode='x unified',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Arial", size=12),
        title=dict(x=0.5, xanchor='center'),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    fig1.update_xaxes(
        categoryorder='array',
        categoryarray=['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 
                      'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'],
        gridcolor='lightgray'
    )
    
    fig1.update_yaxes(gridcolor='lightgray')
    
    st.plotly_chart(fig1, use_container_width=True)
    
    # Gráfico 2: Barras comparativas por sección
    st.markdown("### 📊 Comparación por Sección")
    
    df_secciones = df_plot.groupby(['secciones', 'anio'])['venta'].sum().reset_index()
    
    fig2 = px.bar(
        df_secciones,
        x='secciones',
        y='venta',
        color='anio',
        barmode='group',
        title='Ventas por Sección - Comparativa Anual',
        labels={'secciones': 'Sección', 'venta': 'Ventas ($)', 'anio': 'Año'},
        color_discrete_map={año_base: '#1f77b4', año_comparar: '#ff7f0e'},
        text_auto='.2s'
    )
    
    fig2.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Arial", size=12),
        title=dict(x=0.5, xanchor='center'),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    fig2.update_xaxes(gridcolor='lightgray')
    fig2.update_yaxes(gridcolor='lightgray')
    
    st.plotly_chart(fig2, use_container_width=True)
    
    # Gráfico 3: Distribución de tickets y entradas
    st.markdown("### 📈 Análisis de Eficiencia")
    
    df_eficiencia = df_plot.groupby('anio').agg({
        'tickets': 'sum',
        'entradas': 'sum',
        'ticket_promedio': 'mean'
    }).reset_index()
    
    fig3 = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Tickets vs Entradas', 'Ticket Promedio'),
        specs=[[{'type': 'bar'}, {'type': 'bar'}]]
    )
    
    # Gráfico de barras para tickets y entradas
    fig3.add_trace(
        go.Bar(name='Tickets', x=df_eficiencia['anio'], y=df_eficiencia['tickets'],
               marker_color='#1f77b4', text=df_eficiencia['tickets'].apply(lambda x: f'{x:,.0f}'),
               textposition='outside'),
        row=1, col=1
    )
    
    fig3.add_trace(
        go.Bar(name='Entradas', x=df_eficiencia['anio'], y=df_eficiencia['entradas'],
               marker_color='#ff7f0e', text=df_eficiencia['entradas'].apply(lambda x: f'{x:,.0f}'),
               textposition='outside'),
        row=1, col=1
    )
    
    # Gráfico de barras para ticket promedio
    fig3.add_trace(
        go.Bar(name='Ticket Promedio', x=df_eficiencia['anio'], y=df_eficiencia['ticket_promedio'],
               marker_color='#2ca02c', text=df_eficiencia['ticket_promedio'].apply(lambda x: f'${x:,.2f}'),
               textposition='outside'),
        row=1, col=2
    )
    
    fig3.update_layout(
        showlegend=True,
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=400,
        title_text="Métricas de Eficiencia",
        title_x=0.5
    )
    
    fig3.update_xaxes(gridcolor='lightgray')
    fig3.update_yaxes(gridcolor='lightgray')
    
    st.plotly_chart(fig3, use_container_width=True)

# ---------- COMPARACIÓN DÍA A DÍA ----------
st.markdown(f'<div class="section-title">📅 Comparación Día a Día</div>', unsafe_allow_html=True)

if not datos_base.empty and not datos_comparar.empty:
    # Selectores de fecha con diseño mejorado
    col_cal1, col_cal2, col_cal3 = st.columns([2, 2, 1])
    
    with col_cal1:
        st.markdown(f"**{año_base}**")
        fechas_base = sorted(datos_base["fecha"].dt.date.unique())
        fecha_base = st.date_input(
            "Selecciona fecha",
            value=fechas_base[0],
            min_value=min(fechas_base),
            max_value=max(fechas_base),
            key="fecha_base",
            format="DD/MM/YYYY"
        )
    
    with col_cal2:
        st.markdown(f"**{año_comparar}**")
        fechas_comp = sorted(datos_comparar["fecha"].dt.date.unique())
        fecha_comp = st.date_input(
            "Selecciona fecha",
            value=fechas_comp[0],
            min_value=min(fechas_comp),
            max_value=max(fechas_comp),
            key="fecha_comp",
            format="DD/MM/YYYY"
        )
    
    with col_cal3:
        st.markdown("**Acción**")
        if st.button("🔄 Mismo día", use_container_width=True):
            # Buscar mismo mes/día
            for f_base in fechas_base:
                for f_comp in fechas_comp:
                    if f_base.month == f_comp.month and f_base.day == f_comp.day:
                        fecha_base = f_base
                        fecha_comp = f_comp
                        st.success(f"✓ {f_base.day}/{f_base.month} encontrado")
                        break
                else:
                    continue
                break
    
    # Mostrar comparación del día
    if fecha_base and fecha_comp:
        datos_dia_base = datos_base[datos_base["fecha"].dt.date == fecha_base]
        datos_dia_comp = datos_comparar[datos_comparar["fecha"].dt.date == fecha_comp]
        
        if not datos_dia_base.empty and not datos_dia_comp.empty:
            # Tarjetas de comparación diaria
            col_d1, col_d2, col_d3, col_d4 = st.columns(4)
            
            venta_base = datos_dia_base["venta"].sum()
            venta_comp = datos_dia_comp["venta"].sum()
            delta_venta = ((venta_comp - venta_base)/venta_base*100) if venta_base > 0 else None
            
            with col_d1:
                st.markdown(f"""
                <div class="metric-card" style="padding: 1rem;">
                    <h4 style="color: #666; margin: 0;">Ventas del día</h4>
                    <h3 style="color: #1f77b4; margin: 0.5rem 0;">${venta_comp:,.0f}</h3>
                    <p style="color: {'#4caf50' if delta_venta and delta_venta > 0 else '#f44336' if delta_venta and delta_venta < 0 else '#666'};">
                        {f'▲ {delta_venta:.1f}%' if delta_venta and delta_venta > 0 else f'▼ {abs(delta_venta):.1f}%' if delta_venta and delta_venta < 0 else '0%'}
                    </p>
                    <p style="color: #999; font-size: 0.8rem;">{año_base}: ${venta_base:,.0f}</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Más métricas del día...
            with col_d2:
                entradas_base = datos_dia_base["entradas"].sum()
                entradas_comp = datos_dia_comp["entradas"].sum()
                delta_ent = ((entradas_comp - entradas_base)/entradas_base*100) if entradas_base > 0 else None
                
                st.markdown(f"""
                <div class="metric-card" style="padding: 1rem;">
                    <h4 style="color: #666; margin: 0;">Entradas del día</h4>
                    <h3 style="color: #1f77b4; margin: 0.5rem 0;">{entradas_comp:,.0f}</h3>
                    <p style="color: {'#4caf50' if delta_ent and delta_ent > 0 else '#f44336' if delta_ent and delta_ent < 0 else '#666'};">
                        {f'▲ {delta_ent:.1f}%' if delta_ent and delta_ent > 0 else f'▼ {abs(delta_ent):.1f}%' if delta_ent and delta_ent < 0 else '0%'}
                    </p>
                    <p style="color: #999; font-size: 0.8rem;">{año_base}: {entradas_base:,.0f}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col_d3:
                ticket_base = venta_base / datos_dia_base["tickets"].sum() if datos_dia_base["tickets"].sum() > 0 else 0
                ticket_comp = venta_comp / datos_dia_comp["tickets"].sum() if datos_dia_comp["tickets"].sum() > 0 else 0
                delta_ticket = ((ticket_comp - ticket_base)/ticket_base*100) if ticket_base > 0 else None
                
                st.markdown(f"""
                <div class="metric-card" style="padding: 1rem;">
                    <h4 style="color: #666; margin: 0;">Ticket Promedio</h4>
                    <h3 style="color: #1f77b4; margin: 0.5rem 0;">${ticket_comp:,.2f}</h3>
                    <p style="color: {'#4caf50' if delta_ticket and delta_ticket > 0 else '#f44336' if delta_ticket and delta_ticket < 0 else '#666'};">
                        {f'▲ {delta_ticket:.1f}%' if delta_ticket and delta_ticket > 0 else f'▼ {abs(delta_ticket):.1f}%' if delta_ticket and delta_ticket < 0 else '0%'}
                    </p>
                    <p style="color: #999; font-size: 0.8rem;">{año_base}: ${ticket_base:,.2f}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col_d4:
                tasa_base = datos_dia_base["tasa_conversion"].mean()
                tasa_comp = datos_dia_comp["tasa_conversion"].mean()
                delta_tasa = tasa_comp - tasa_base
                
                st.markdown(f"""
                <div class="metric-card" style="padding: 1rem;">
                    <h4 style="color: #666; margin: 0;">Tasa Conversión</h4>
                    <h3 style="color: #1f77b4; margin: 0.5rem 0;">{tasa_comp:.2f}%</h3>
                    <p style="color: {'#4caf50' if delta_tasa > 0 else '#f44336' if delta_tasa < 0 else '#666'};">
                        {f'▲ {delta_tasa:.2f} pp' if delta_tasa > 0 else f'▼ {abs(delta_tasa):.2f} pp' if delta_tasa < 0 else '0 pp'}
                    </p>
                    <p style="color: #999; font-size: 0.8rem;">{año_base}: {tasa_base:.2f}%</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Desglose por sección del día
            with st.expander("📋 Ver desglose por sección del día"):
                secciones_dia = sorted(set(datos_dia_base["secciones"].unique()) | 
                                     set(datos_dia_comp["secciones"].unique()))
                
                data_dia = []
                for sec in secciones_dia:
                    base_sec = datos_dia_base[datos_dia_base["secciones"] == sec]
                    comp_sec = datos_dia_comp[datos_dia_comp["secciones"] == sec]
                    
                    venta_b = base_sec["venta"].sum() if not base_sec.empty else 0
                    venta_c = comp_sec["venta"].sum() if not comp_sec.empty else 0
                    
                    data_dia.append({
                        "Sección": sec,
                        f"Venta {año_base}": f"${venta_b:,.0f}" if venta_b > 0 else "Sin datos",
                        f"Venta {año_comparar}": f"${venta_c:,.0f}" if venta_c > 0 else "Sin datos",
                        "Variación": f"{((venta_c - venta_b)/venta_b*100):.1f}%" if venta_b > 0 and venta_c > 0 else "N/A"
                    })
                
                st.dataframe(pd.DataFrame(data_dia), use_container_width=True)

# ---------- DATOS DETALLADOS ----------
with st.expander("📋 Ver datos detallados", expanded=False):
    tab1, tab2 = st.tabs(["Resumen Anual", "Registros Detallados"])
    
    with tab1:
        resumen = df_filtrado.groupby("anio").agg({
            "venta": "sum",
            "entradas": "sum",
            "tickets": "sum",
            "tasa_conversion": "mean"
        }).round(2)
        
        resumen.columns = ["Ventas Totales", "Entradas Totales", "Tickets Totales", "Tasa Conv. Prom."]
        resumen["Ventas Totales"] = resumen["Ventas Totales"].apply(lambda x: f"${x:,.0f}")
        resumen["Entradas Totales"] = resumen["Entradas Totales"].apply(lambda x: f"{x:,.0f}")
        resumen["Tickets Totales"] = resumen["Tickets Totales"].apply(lambda x: f"{x:,.0f}")
        resumen["Tasa Conv. Prom."] = resumen["Tasa Conv. Prom."].apply(lambda x: f"{x:.2f}%")
        
        st.dataframe(resumen, use_container_width=True)
    
    with tab2:
        st.dataframe(
            df_filtrado.sort_values(["anio", "fecha"], ascending=[False, False])
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