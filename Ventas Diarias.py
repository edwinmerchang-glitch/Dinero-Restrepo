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
    df_plot['año_str'] = df_plot['anio'].astype(str)
    
    # Diccionario de meses en español
    meses_es = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
        7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }
    df_plot['mes_nombre'] = df_plot['mes'].map(meses_es)
    
    # Gráfico 1: Evolución mensual comparativa (mejorado)
    df_mensual = df_plot.groupby(['mes', 'mes_nombre', 'anio'])['venta'].sum().reset_index()
    df_mensual = df_mensual.sort_values('mes')
    
    # Crear gráfico de líneas mejorado
    fig1 = go.Figure()
    
    for año in [año_base, año_comparar]:
        df_año = df_mensual[df_mensual['anio'] == año]
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
    
    # Gráfico 2: Barras comparativas por sección (mejorado)
    st.markdown("### 📊 Comparación por Sección")
    
    df_secciones = df_plot.groupby(['secciones', 'anio'])['venta'].sum().reset_index()
    
    fig2 = go.Figure()
    
    for año in [año_base, año_comparar]:
        df_año = df_secciones[df_secciones['anio'] == año]
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
    
    # Gráfico 3: Distribución de tickets y entradas (mejorado)
    st.markdown("### 📈 Análisis de Eficiencia")
    
    df_eficiencia = df_plot.groupby('anio').agg({
        'tickets': 'sum',
        'entradas': 'sum',
        'ticket_promedio': 'mean',
        'tasa_conversion': 'mean',
        'venta': 'sum'  # Agregamos venta total para el pie chart
    }).reset_index()
    
    # Crear subplots con 2 gráficos
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
        
        # Barra para Tickets
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
        
        # Barra para Entradas (superpuesta)
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
    
    # Gráfico 4: Distribución de ventas por año (pie chart)
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
        barmode='group'  # Para que las barras no se superpongan
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
        pivot_heat = pivot_heat[list(meses_es.values())]
        
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
        st.warning("No hay datos para los años seleccionados en el rango de fechas")
    elif datos_base.empty:
        st.info(f"Solo hay datos para {año_comparar}. Selecciona otro año base para comparar.")
    else:
        st.info(f"Solo hay datos para {año_base}. Selecciona otro año para comparar.")

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
            
            # Tarjetas de comparación diaria
            col_d1, col_d2, col_d3, col_d4 = st.columns(4)
            
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
            
            delta_ent = ((entradas_comp - entradas_base)/entradas_base*100) if entradas_base > 0 else None
            with col_d2:
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
            
            delta_ticket = ((ticket_prom_comp - ticket_prom_base)/ticket_prom_base*100) if ticket_prom_base > 0 else None
            with col_d3:
                st.markdown(f"""
                <div class="metric-card" style="padding: 1rem;">
                    <h4 style="color: #666; margin: 0;">Ticket Promedio</h4>
                    <h3 style="color: #1f77b4; margin: 0.5rem 0;">${ticket_prom_comp:,.2f}</h3>
                    <p style="color: {'#4caf50' if delta_ticket and delta_ticket > 0 else '#f44336' if delta_ticket and delta_ticket < 0 else '#666'};">
                        {f'▲ {delta_ticket:.1f}%' if delta_ticket and delta_ticket > 0 else f'▼ {abs(delta_ticket):.1f}%' if delta_ticket and delta_ticket < 0 else '0%'}
                    </p>
                    <p style="color: #999; font-size: 0.8rem;">{año_base}: ${ticket_prom_base:,.2f}</p>
                </div>
                """, unsafe_allow_html=True)
            
            delta_tasa = tasa_comp - tasa_base
            with col_d4:
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
            
            # ----- GRÁFICOS PARA COMPARACIÓN DÍA A DÍA -----
            st.markdown("### 📊 Análisis Visual del Día")
            
            # Crear pestañas para diferentes visualizaciones
            tab_dia1, tab_dia2, tab_dia3 = st.tabs(["📊 Comparativa", "🥧 Distribución", "📈 Tendencia Horaria (simulada)"])
            
            with tab_dia1:
                # Gráfico de barras comparativo por sección
                secciones_dia = sorted(set(datos_dia_base["secciones"].unique()) | 
                                     set(datos_dia_comp["secciones"].unique()))
                
                # Preparar datos para el gráfico
                data_barras = []
                for sec in secciones_dia:
                    base_sec = datos_dia_base[datos_dia_base["secciones"] == sec]
                    comp_sec = datos_dia_comp[datos_dia_comp["secciones"] == sec]
                    
                    venta_b = base_sec["venta"].sum() if not base_sec.empty else 0
                    venta_c = comp_sec["venta"].sum() if not comp_sec.empty else 0
                    
                    data_barras.append({
                        "Sección": sec,
                        f"{año_base}": venta_b,
                        f"{año_comparar}": venta_c
                    })
                
                df_barras = pd.DataFrame(data_barras)
                
                if not df_barras.empty:
                    fig_dia1 = go.Figure()
                    
                    fig_dia1.add_trace(go.Bar(
                        name=str(año_base),
                        x=df_barras['Sección'],
                        y=df_barras[str(año_base)],
                        marker_color='#1f77b4',
                        text=df_barras[str(año_base)].apply(lambda x: f'${x:,.0f}'),
                        textposition='outside',
                        hovertemplate='<b>%{x}</b><br>' +
                                     f'{año_base}: $%{{y:,.0f}}<br>' +
                                     '<extra></extra>'
                    ))
                    
                    fig_dia1.add_trace(go.Bar(
                        name=str(año_comparar),
                        x=df_barras['Sección'],
                        y=df_barras[str(año_comparar)],
                        marker_color='#ff7f0e',
                        text=df_barras[str(año_comparar)].apply(lambda x: f'${x:,.0f}'),
                        textposition='outside',
                        hovertemplate='<b>%{x}</b><br>' +
                                     f'{año_comparar}: $%{{y:,.0f}}<br>' +
                                     '<extra></extra>'
                    ))
                    
                    fig_dia1.update_layout(
                        title=f'Comparación por Sección - {fecha_base.strftime("%d/%m/%Y")} vs {fecha_comp.strftime("%d/%m/%Y")}',
                        xaxis=dict(title='Sección', tickangle=45),
                        yaxis=dict(title='Ventas ($)', tickformat='$,.0f'),
                        barmode='group',
                        plot_bgcolor='white',
                        paper_bgcolor='white',
                        height=400,
                        legend=dict(
                            orientation='h',
                            yanchor='bottom',
                            y=1.02,
                            xanchor='center',
                            x=0.5
                        )
                    )
                    
                    st.plotly_chart(fig_dia1, use_container_width=True)
            
            with tab_dia2:
                # Gráficos de pastel para distribución por sección
                col_pie1, col_pie2 = st.columns(2)
                
                with col_pie1:
                    # Pastel para año base
                    df_pie_base = datos_dia_base.groupby('secciones')['venta'].sum().reset_index()
                    fig_pie_base = go.Figure(data=[go.Pie(
                        labels=df_pie_base['secciones'],
                        values=df_pie_base['venta'],
                        hole=0.4,
                        marker_colors=px.colors.qualitative.Set3[:len(df_pie_base)],
                        textinfo='label+percent',
                        textposition='inside'
                    )])
                    
                    fig_pie_base.update_layout(
                        title=f'Distribución {año_base}',
                        height=300,
                        showlegend=False
                    )
                    
                    st.plotly_chart(fig_pie_base, use_container_width=True)
                
                with col_pie2:
                    # Pastel para año comparar
                    df_pie_comp = datos_dia_comp.groupby('secciones')['venta'].sum().reset_index()
                    fig_pie_comp = go.Figure(data=[go.Pie(
                        labels=df_pie_comp['secciones'],
                        values=df_pie_comp['venta'],
                        hole=0.4,
                        marker_colors=px.colors.qualitative.Set3[:len(df_pie_comp)],
                        textinfo='label+percent',
                        textposition='inside'
                    )])
                    
                    fig_pie_comp.update_layout(
                        title=f'Distribución {año_comparar}',
                        height=300,
                        showlegend=False
                    )
                    
                    st.plotly_chart(fig_pie_comp, use_container_width=True)
                
                # Métricas adicionales en columnas
                col_metric1, col_metric2, col_metric3 = st.columns(3)
                
                with col_metric1:
                    # Sección con mayor venta en año base
                    top_base = datos_dia_base.loc[datos_dia_base['venta'].idxmax()] if not datos_dia_base.empty else None
                    if top_base is not None:
                        st.metric(
                            "🏆 Mejor sección (Base)",
                            top_base['secciones'],
                            f"${top_base['venta']:,.0f}"
                        )
                
                with col_metric2:
                    # Sección con mayor venta en año comparar
                    top_comp = datos_dia_comp.loc[datos_dia_comp['venta'].idxmax()] if not datos_dia_comp.empty else None
                    if top_comp is not None:
                        st.metric(
                            "🏆 Mejor sección (Actual)",
                            top_comp['secciones'],
                            f"${top_comp['venta']:,.0f}"
                        )
                
                with col_metric3:
                    # Comparación de secciones con mayor crecimiento
                    crecimiento_secciones = []
                    for sec in secciones_dia:
                        venta_b = datos_dia_base[datos_dia_base['secciones'] == sec]['venta'].sum() if not datos_dia_base[datos_dia_base['secciones'] == sec].empty else 0
                        venta_c = datos_dia_comp[datos_dia_comp['secciones'] == sec]['venta'].sum() if not datos_dia_comp[datos_dia_comp['secciones'] == sec].empty else 0
                        if venta_b > 0:
                            crecimiento = ((venta_c - venta_b)/venta_b*100)
                            crecimiento_secciones.append((sec, crecimiento))
                    
                    if crecimiento_secciones:
                        mejor_crecimiento = max(crecimiento_secciones, key=lambda x: x[1])
                        st.metric(
                            "🚀 Mayor crecimiento",
                            mejor_crecimiento[0],
                            f"{mejor_crecimiento[1]:.1f}%"
                        )
            
            with tab_dia3:
                # Gráfico de tendencia horaria (simulada - asumiendo distribución uniforme)
                st.info("📊 Visualización de tendencia estimada (basada en distribución de tickets)")
                
                # Simular distribución horaria basada en tickets por sección
                horas = list(range(9, 21))  # 9 AM a 8 PM
                
                # Distribución simulada (campana alrededor del mediodía)
                distribucion = [0.02, 0.03, 0.05, 0.08, 0.12, 0.15, 0.15, 0.12, 0.10, 0.08, 0.06, 0.04]
                
                ventas_hora_base = [venta_base * d for d in distribucion]
                ventas_hora_comp = [venta_comp * d for d in distribucion]
                
                fig_horas = go.Figure()
                
                fig_horas.add_trace(go.Scatter(
                    x=[f"{h}:00" for h in horas],
                    y=ventas_hora_base,
                    mode='lines+markers',
                    name=str(año_base),
                    line=dict(color='#1f77b4', width=3),
                    marker=dict(size=8),
                    fill='tozeroy',
                    fillcolor='rgba(31, 119, 180, 0.1)'
                ))
                
                fig_horas.add_trace(go.Scatter(
                    x=[f"{h}:00" for h in horas],
                    y=ventas_hora_comp,
                    mode='lines+markers',
                    name=str(año_comparar),
                    line=dict(color='#ff7f0e', width=3),
                    marker=dict(size=8),
                    fill='tozeroy',
                    fillcolor='rgba(255, 127, 14, 0.1)'
                ))
                
                fig_horas.update_layout(
                    title='Distribución Horaria Estimada de Ventas',
                    xaxis=dict(title='Hora', tickangle=45),
                    yaxis=dict(title='Ventas ($)', tickformat='$,.0f'),
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    height=400,
                    hovermode='x unified',
                    legend=dict(
                        orientation='h',
                        yanchor='bottom',
                        y=1.02,
                        xanchor='center',
                        x=0.5
                    )
                )
                
                st.plotly_chart(fig_horas, use_container_width=True)
                
                st.caption("⚠️ *Esta es una simulación basada en la distribución de tickets. Para datos reales, se necesitaría información horaria en el Excel.*")
            
            # Desglose por sección del día (tabla detallada)
            with st.expander("📋 Ver desglose detallado por sección"):
                data_dia = []
                for sec in secciones_dia:
                    base_sec = datos_dia_base[datos_dia_base["secciones"] == sec]
                    comp_sec = datos_dia_comp[datos_dia_comp["secciones"] == sec]
                    
                    venta_b = base_sec["venta"].sum() if not base_sec.empty else 0
                    venta_c = comp_sec["venta"].sum() if not comp_sec.empty else 0
                    tickets_b = base_sec["tickets"].sum() if not base_sec.empty else 0
                    tickets_c = comp_sec["tickets"].sum() if not comp_sec.empty else 0
                    entradas_b = base_sec["entradas"].sum() if not base_sec.empty else 0
                    entradas_c = comp_sec["entradas"].sum() if not comp_sec.empty else 0
                    
                    ticket_prom_b = venta_b / tickets_b if tickets_b > 0 else 0
                    ticket_prom_c = venta_c / tickets_c if tickets_c > 0 else 0
                    
                    data_dia.append({
                        "Sección": sec,
                        f"Venta {año_base}": f"${venta_b:,.0f}" if venta_b > 0 else "Sin datos",
                        f"Venta {año_comparar}": f"${venta_c:,.0f}" if venta_c > 0 else "Sin datos",
                        f"Var. Venta": f"{((venta_c - venta_b)/venta_b*100):.1f}%" if venta_b > 0 and venta_c > 0 else "N/A",
                        f"Ticket Prom {año_base}": f"${ticket_prom_b:,.2f}" if ticket_prom_b > 0 else "N/A",
                        f"Ticket Prom {año_comparar}": f"${ticket_prom_c:,.2f}" if ticket_prom_c > 0 else "N/A",
                        f"Entradas {año_base}": f"{entradas_b:,.0f}" if entradas_b > 0 else "Sin datos",
                        f"Entradas {año_comparar}": f"{entradas_c:,.0f}" if entradas_c > 0 else "Sin datos"
                    })
                
                df_dia_detalle = pd.DataFrame(data_dia)
                st.dataframe(df_dia_detalle, use_container_width=True)

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