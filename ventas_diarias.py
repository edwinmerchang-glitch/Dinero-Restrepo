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
st.markdown("### Análisis Comparativo Interanual (Mes a Mes)")

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

# ---------- LÓGICA: FILTRAR POR PERÍODO EQUIVALENTE ----------
# Determinamos el período a comparar (mes o rango personalizado)
if fecha_inicio.month == fecha_fin.month and fecha_inicio.year == fecha_fin.year:
    # Caso 1: El rango está dentro de un mismo mes -> Comparar mes completo
    mes_a_comparar = fecha_inicio.month
    # Obtener nombre del mes en español
    meses_es = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
        7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }
    periodo_desc = f"mes de {meses_es[mes_a_comparar]}"
    
    datos_base = df_filtrado[
        (df_filtrado["anio"] == año_base) & 
        (df_filtrado["fecha"].dt.month == mes_a_comparar)
    ]
    datos_comparar = df_filtrado[
        (df_filtrado["anio"] == año_comparar) & 
        (df_filtrado["fecha"].dt.month == mes_a_comparar)
    ]
    
else:
    # Caso 2: Rango personalizado (ej. 15 Ene - 15 Feb) -> Comparar mismo rango del año anterior
    periodo_desc = f"período {fecha_inicio.strftime('%d/%m')} - {fecha_fin.strftime('%d/%m')}"
    
    # Calculamos las fechas equivalentes en el año base
    # Nota: Esto asume que el año base tiene los mismos días del año.
    try:
        fecha_inicio_base = fecha_inicio.replace(year=año_base)
        fecha_fin_base = fecha_fin.replace(year=año_base)
    except ValueError as e:
        # Esto puede pasar si la fecha es 29 de febrero y el año base no es bisiesto.
        st.warning(f"La fecha {fecha_inicio.strftime('%d/%m')} no existe en {año_base}. Se usará el 28 de febrero como aproximación.")
        # Ajustamos al último día de febrero
        if fecha_inicio.month == 2 and fecha_inicio.day == 29:
            fecha_inicio_base = fecha_inicio.replace(year=año_base, month=2, day=28)
        else:
            fecha_inicio_base = fecha_inicio.replace(year=año_base)
        
        if fecha_fin.month == 2 and fecha_fin.day == 29:
            fecha_fin_base = fecha_fin.replace(year=año_base, month=2, day=28)
        else:
            fecha_fin_base = fecha_fin.replace(year=año_base)

    datos_base = df_filtrado[
        (df_filtrado["anio"] == año_base) & 
        (df_filtrado["fecha"] >= pd.Timestamp(fecha_inicio_base)) &
        (df_filtrado["fecha"] <= pd.Timestamp(fecha_fin_base))
    ]
    datos_comparar = df_filtrado[
        (df_filtrado["anio"] == año_comparar) & 
        (df_filtrado["fecha"] >= fecha_inicio) &
        (df_filtrado["fecha"] <= fecha_fin)
    ]

# ---------- KPIS CON TARJETAS MODERNAS (CORREGIDO) ----------
st.markdown(f'<div class="section-title">📈 Comparación General: {año_base} vs {año_comparar} ({periodo_desc})</div>', unsafe_allow_html=True)

if datos_base.empty and datos_comparar.empty:
    st.warning(f"No hay datos para el período seleccionado en {año_base} ni en {año_comparar}")
    st.stop()
elif datos_base.empty:
    st.info(f"Mostrando solo datos de {año_comparar} para {periodo_desc} (no hay datos en {año_base} para este período exacto)")
elif datos_comparar.empty:
    st.info(f"Mostrando solo datos de {año_base} para {periodo_desc} (no hay datos en {año_comparar} para este período exacto)")

# Calcular métricas (solo si hay datos en ambos años)
if not datos_base.empty and not datos_comparar.empty:
    ventas_base = datos_base["venta"].sum()
    ventas_comp = datos_comparar["venta"].sum()
    entradas_base = datos_base["entradas"].sum()
    entradas_comp = datos_comparar["entradas"].sum()
    
    # Calcular ticket promedio correctamente (ventas totales / tickets totales)
    tickets_base = datos_base["tickets"].sum()
    tickets_comp = datos_comparar["tickets"].sum()
    
    ticket_base = ventas_base / tickets_base if tickets_base > 0 else 0
    ticket_comp = ventas_comp / tickets_comp if tickets_comp > 0 else 0
    
    tasa_base = datos_base["tasa_conversion"].mean()
    tasa_comp = datos_comparar["tasa_conversion"].mean()
    
    # Mostrar información adicional sobre el período
    col_info1, col_info2 = st.columns(2)
    with col_info1:
        st.info(f"📅 **{año_base}:** {len(datos_base)} registros • {datos_base['fecha'].dt.date.nunique()} días con datos")
    with col_info2:
        st.info(f"📅 **{año_comparar}:** {len(datos_comparar)} registros • {datos_comparar['fecha'].dt.date.nunique()} días con datos")
    
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

# ---------- GRÁFICOS CON PLOTLY ----------
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
    
    # Gráfico 4: Heatmap de rendimiento por mes y sección (CORREGIDO)
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
        
        # CORRECCIÓN: Solo reordenar las columnas que existen
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

# ---------- COMPARACIÓN DÍA A DÍA MEJORADA ----------
st.markdown(f'<div class="section-title">📅 Comparación Día a Día</div>', unsafe_allow_html=True)

if not datos_base.empty and not datos_comparar.empty:
    
    # Explicación de la funcionalidad
    st.info("""
    **🔍 Compara un día específico de cada año**
    
    Selecciona una fecha de cada año para ver cómo se comparan las métricas. 
    Puedes buscar el mismo día (mismo mes y día) en ambos años con el botón "🔄 Mismo día".
    """)
    
    # Crear pestañas para diferentes modos de comparación
    tab_dia1, tab_dia2, tab_dia3 = st.tabs(["📅 Comparador de Fechas", "📊 Calendario", "📈 Día más vendido"])
    
    with tab_dia1:
        # Selectores de fecha con diseño mejorado
        col_cal1, col_cal2, col_cal3 = st.columns([2, 2, 1])
        
        with col_cal1:
            st.markdown(f"### **{año_base}**")
            fechas_base = sorted(datos_base["fecha"].dt.date.unique())
            
            # Selector con formato mejorado
            fecha_base = st.selectbox(
                "Selecciona fecha",
                options=fechas_base,
                format_func=lambda x: x.strftime("%A %d de %B, %Y") if hasattr(x, 'strftime') else str(x),
                key="fecha_base_select"
            )
            
            # Mostrar día de la semana
            if fecha_base:
                dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
                dia_semana = dias_semana[fecha_base.weekday()]
                st.caption(f"📆 {dia_semana}")
        
        with col_cal2:
            st.markdown(f"### **{año_comparar}**")
            fechas_comp = sorted(datos_comparar["fecha"].dt.date.unique())
            
            fecha_comp = st.selectbox(
                "Selecciona fecha",
                options=fechas_comp,
                format_func=lambda x: x.strftime("%A %d de %B, %Y") if hasattr(x, 'strftime') else str(x),
                key="fecha_comp_select"
            )
            
            # Mostrar día de la semana
            if fecha_comp:
                dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
                dia_semana = dias_semana[fecha_comp.weekday()]
                st.caption(f"📆 {dia_semana}")
        
        with col_cal3:
            st.markdown("### **Acciones**")
            
            # Botón para buscar mismo día
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
            
            # Botón para fechas más recientes
            if st.button("📅 Últimos datos", use_container_width=True):
                fecha_base = fechas_base[-1] if fechas_base else None
                fecha_comp = fechas_comp[-1] if fechas_comp else None
                st.rerun()
    
    with tab_dia2:
        # Vista de calendario simplificada
        st.markdown("### 📆 Calendario comparativo")
        
        col_cal_left, col_cal_right = st.columns(2)
        
        with col_cal_left:
            st.markdown(f"**{año_base}**")
            # Crear un DataFrame con resumen por día para el año base
            df_base_dias = datos_base.groupby(datos_base['fecha'].dt.date).agg({
                'venta': 'sum',
                'entradas': 'sum',
                'tickets': 'sum'
            }).reset_index()
            df_base_dias.columns = ['fecha', 'venta', 'entradas', 'tickets']
            df_base_dias['venta_mm'] = df_base_dias['venta'] / 1_000_000
            
            # Mostrar tabla con últimos 10 días
            st.dataframe(
                df_base_dias.sort_values('fecha', ascending=False).head(10)
                .style.format({
                    'fecha': lambda x: x.strftime('%d/%m/%Y'),
                    'venta': '${:,.0f}',
                    'venta_mm': '${:.1f}M',
                    'entradas': '{:,.0f}',
                    'tickets': '{:,.0f}'
                }),
                use_container_width=True,
                height=300
            )
        
        with col_cal_right:
            st.markdown(f"**{año_comparar}**")
            # Crear un DataFrame con resumen por día para el año comparar
            df_comp_dias = datos_comparar.groupby(datos_comparar['fecha'].dt.date).agg({
                'venta': 'sum',
                'entradas': 'sum',
                'tickets': 'sum'
            }).reset_index()
            df_comp_dias.columns = ['fecha', 'venta', 'entradas', 'tickets']
            df_comp_dias['venta_mm'] = df_comp_dias['venta'] / 1_000_000
            
            # Mostrar tabla con últimos 10 días
            st.dataframe(
                df_comp_dias.sort_values('fecha', ascending=False).head(10)
                .style.format({
                    'fecha': lambda x: x.strftime('%d/%m/%Y'),
                    'venta': '${:,.0f}',
                    'venta_mm': '${:.1f}M',
                    'entradas': '{:,.0f}',
                    'tickets': '{:,.0f}'
                }),
                use_container_width=True,
                height=300
            )
    
    with tab_dia3:
        # Análisis de días destacados
        st.markdown("### 🏆 Días destacados")
        
        col_top1, col_top2, col_top3 = st.columns(3)
        
        with col_top1:
            # Día con más ventas en año base
            if not datos_base.empty:
                top_venta_base = datos_base.loc[datos_base['venta'].idxmax()]
                st.metric(
                    f"💰 Más ventas {año_base}",
                    f"${top_venta_base['venta']:,.0f}",
                    top_venta_base['fecha'].strftime('%d/%m/%Y')
                )
        
        with col_top2:
            # Día con más entradas en año base
            if not datos_base.empty:
                top_entradas_base = datos_base.loc[datos_base['entradas'].idxmax()]
                st.metric(
                    f"👥 Más entradas {año_base}",
                    f"{top_entradas_base['entradas']:,.0f}",
                    top_entradas_base['fecha'].strftime('%d/%m/%Y')
                )
        
        with col_top3:
            # Día con mejor ticket promedio en año base
            if not datos_base.empty:
                top_ticket_base = datos_base.loc[datos_base['ticket_promedio'].idxmax()]
                st.metric(
                    f"💳 Mejor ticket {año_base}",
                    f"${top_ticket_base['ticket_promedio']:,.2f}",
                    top_ticket_base['fecha'].strftime('%d/%m/%Y')
                )
        
        st.markdown("---")
        
        col_top4, col_top5, col_top6 = st.columns(3)
        
        with col_top4:
            # Día con más ventas en año comparar
            if not datos_comparar.empty:
                top_venta_comp = datos_comparar.loc[datos_comparar['venta'].idxmax()]
                st.metric(
                    f"💰 Más ventas {año_comparar}",
                    f"${top_venta_comp['venta']:,.0f}",
                    top_venta_comp['fecha'].strftime('%d/%m/%Y')
                )
        
        with col_top5:
            # Día con más entradas en año comparar
            if not datos_comparar.empty:
                top_entradas_comp = datos_comparar.loc[datos_comparar['entradas'].idxmax()]
                st.metric(
                    f"👥 Más entradas {año_comparar}",
                    f"{top_entradas_comp['entradas']:,.0f}",
                    top_entradas_comp['fecha'].strftime('%d/%m/%Y')
                )
        
        with col_top6:
            # Día con mejor ticket promedio en año comparar
            if not datos_comparar.empty:
                top_ticket_comp = datos_comparar.loc[datos_comparar['ticket_promedio'].idxmax()]
                st.metric(
                    f"💳 Mejor ticket {año_comparar}",
                    f"${top_ticket_comp['ticket_promedio']:,.2f}",
                    top_ticket_comp['fecha'].strftime('%d/%m/%Y')
                )
    
    # Mostrar la comparación detallada si hay fechas seleccionadas
    if 'fecha_base' in locals() and 'fecha_comp' in locals() and fecha_base and fecha_comp:
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
            
            # Tarjetas de comparación diaria con estilo mejorado
            col_d1, col_d2, col_d3, col_d4 = st.columns(4)
            
            delta_venta = ((venta_comp - venta_base)/venta_base*100) if venta_base > 0 else None
            with col_d1:
                st.markdown(f"""
                <div class="metric-card" style="padding: 1rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                    <h4 style="color: rgba(255,255,255,0.9); margin: 0;">Ventas del día</h4>
                    <h3 style="color: white; margin: 0.5rem 0; font-size: 1.8rem;">${venta_comp:,.0f}</h3>
                    <p style="color: {'#a5d6a7' if delta_venta and delta_venta > 0 else '#ef9a9a' if delta_venta and delta_venta < 0 else 'rgba(255,255,255,0.7)'}; margin: 0; font-weight: bold;">
                        {f'▲ {delta_venta:.1f}%' if delta_venta and delta_venta > 0 else f'▼ {abs(delta_venta):.1f}%' if delta_venta and delta_venta < 0 else '0%'}
                    </p>
                    <p style="color: rgba(255,255,255,0.7); font-size: 0.8rem; margin: 0.5rem 0 0 0;">{año_base}: ${venta_base:,.0f}</p>
                </div>
                """, unsafe_allow_html=True)
            
            delta_ent = ((entradas_comp - entradas_base)/entradas_base*100) if entradas_base > 0 else None
            with col_d2:
                st.markdown(f"""
                <div class="metric-card" style="padding: 1rem; background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); color: white;">
                    <h4 style="color: rgba(255,255,255,0.9); margin: 0;">Entradas del día</h4>
                    <h3 style="color: white; margin: 0.5rem 0; font-size: 1.8rem;">{entradas_comp:,.0f}</h3>
                    <p style="color: {'#a5d6a7' if delta_ent and delta_ent > 0 else '#ef9a9a' if delta_ent and delta_ent < 0 else 'rgba(255,255,255,0.7)'}; margin: 0; font-weight: bold;">
                        {f'▲ {delta_ent:.1f}%' if delta_ent and delta_ent > 0 else f'▼ {abs(delta_ent):.1f}%' if delta_ent and delta_ent < 0 else '0%'}
                    </p>
                    <p style="color: rgba(255,255,255,0.7); font-size: 0.8rem; margin: 0.5rem 0 0 0;">{año_base}: {entradas_base:,.0f}</p>
                </div>
                """, unsafe_allow_html=True)
            
            delta_ticket = ((ticket_prom_comp - ticket_prom_base)/ticket_prom_base*100) if ticket_prom_base > 0 else None
            with col_d3:
                st.markdown(f"""
                <div class="metric-card" style="padding: 1rem; background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); color: white;">
                    <h4 style="color: rgba(255,255,255,0.9); margin: 0;">Ticket Promedio</h4>
                    <h3 style="color: white; margin: 0.5rem 0; font-size: 1.8rem;">${ticket_prom_comp:,.2f}</h3>
                    <p style="color: {'#a5d6a7' if delta_ticket and delta_ticket > 0 else '#ef9a9a' if delta_ticket and delta_ticket < 0 else 'rgba(255,255,255,0.7)'}; margin: 0; font-weight: bold;">
                        {f'▲ {delta_ticket:.1f}%' if delta_ticket and delta_ticket > 0 else f'▼ {abs(delta_ticket):.1f}%' if delta_ticket and delta_ticket < 0 else '0%'}
                    </p>
                    <p style="color: rgba(255,255,255,0.7); font-size: 0.8rem; margin: 0.5rem 0 0 0;">{año_base}: ${ticket_prom_base:,.2f}</p>
                </div>
                """, unsafe_allow_html=True)
            
            delta_tasa = tasa_comp - tasa_base
            with col_d4:
                st.markdown(f"""
                <div class="metric-card" style="padding: 1rem; background: linear-gradient(135deg, #5f2c82 0%, #49a09d 100%); color: white;">
                    <h4 style="color: rgba(255,255,255,0.9); margin: 0;">Tasa Conversión</h4>
                    <h3 style="color: white; margin: 0.5rem 0; font-size: 1.8rem;">{tasa_comp:.2f}%</h3>
                    <p style="color: {'#a5d6a7' if delta_tasa > 0 else '#ef9a9a' if delta_tasa < 0 else 'rgba(255,255,255,0.7)'}; margin: 0; font-weight: bold;">
                        {f'▲ {delta_tasa:.2f} pp' if delta_tasa > 0 else f'▼ {abs(delta_tasa):.2f} pp' if delta_tasa < 0 else '0 pp'}
                    </p>
                    <p style="color: rgba(255,255,255,0.7); font-size: 0.8rem; margin: 0.5rem 0 0 0;">{año_base}: {tasa_base:.2f}%</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Comparación por hora (simulada)
            with st.expander("📊 Ver análisis detallado por hora (simulado)", expanded=False):
                st.info("""
                **📈 Distribución horaria estimada**
                
                Esta visualización estima cómo se distribuyen las ventas a lo largo del día basándose en el total de tickets.
                Para tener datos reales por hora, el Excel debería incluir una columna con la hora de cada venta.
                """)
                
                # Simular distribución horaria
                horas = list(range(9, 21))
                distribucion = [0.02, 0.03, 0.05, 0.08, 0.12, 0.15, 0.15, 0.12, 0.10, 0.08, 0.06, 0.04]
                
                ventas_hora_base = [venta_base * d for d in distribucion]
                ventas_hora_comp = [venta_comp * d for d in distribucion]
                
                fig_horas = go.Figure()
                
                fig_horas.add_trace(go.Bar(
                    name=str(año_base),
                    x=[f"{h}:00" for h in horas],
                    y=ventas_hora_base,
                    marker_color='#1f77b4',
                    text=[f'${v/1000:.0f}K' for v in ventas_hora_base],
                    textposition='inside',
                    opacity=0.8
                ))
                
                fig_horas.add_trace(go.Bar(
                    name=str(año_comparar),
                    x=[f"{h}:00" for h in horas],
                    y=ventas_hora_comp,
                    marker_color='#ff7f0e',
                    text=[f'${v/1000:.0f}K' for v in ventas_hora_comp],
                    textposition='inside',
                    opacity=0.8
                ))
                
                fig_horas.update_layout(
                    title='Distribución Horaria Estimada',
                    xaxis=dict(title='Hora'),
                    yaxis=dict(title='Ventas ($)', tickformat='$,.0f'),
                    barmode='group',
                    plot_bgcolor='white',
                    height=400,
                    legend=dict(
                        orientation='h',
                        yanchor='bottom',
                        y=1.02,
                        xanchor='center',
                        x=0.5
                    )
                )
                
                st.plotly_chart(fig_horas, use_container_width=True)
            
            # Desglose por sección
            with st.expander("📋 Ver desglose por sección", expanded=True):
                secciones_dia = sorted(set(datos_dia_base["secciones"].unique()) | 
                                     set(datos_dia_comp["secciones"].unique()))
                
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
                    
                    var_venta = ((venta_c - venta_b)/venta_b*100) if venta_b > 0 and venta_c > 0 else None
                    
                    data_dia.append({
                        "Sección": sec,
                        f"Venta {año_base}": f"${venta_b:,.0f}" if venta_b > 0 else "-",
                        f"Venta {año_comparar}": f"${venta_c:,.0f}" if venta_c > 0 else "-",
                        "Variación": f"{var_venta:+.1f}%" if var_venta is not None else "-",
                        f"Ticket {año_base}": f"${ticket_prom_b:,.2f}" if ticket_prom_b > 0 else "-",
                        f"Ticket {año_comparar}": f"${ticket_prom_c:,.2f}" if ticket_prom_c > 0 else "-",
                        f"Entradas {año_base}": f"{entradas_b:,.0f}" if entradas_b > 0 else "-",
                        f"Entradas {año_comparar}": f"{entradas_c:,.0f}" if entradas_c > 0 else "-"
                    })
                
                df_dia_detalle = pd.DataFrame(data_dia)
                
                # Aplicar formato condicional a la columna de variación
                def color_variacion(val):
                    if isinstance(val, str) and '%' in val:
                        try:
                            num = float(val.replace('%', '').replace('+', ''))
                            if num > 0:
                                return 'color: #4caf50; font-weight: bold'
                            elif num < 0:
                                return 'color: #f44336; font-weight: bold'
                        except:
                            pass
                    return ''
                
                st.dataframe(
                    df_dia_detalle.style.applymap(color_variacion, subset=['Variación']),
                    use_container_width=True,
                    height=400
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