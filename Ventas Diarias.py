import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import os

st.set_page_config(page_title="Comparador de Ventas", layout="wide")

# ---------- DB ----------
# Crear directorio data si no existe
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

st.title("📊 Comparador de Ventas Diarias — Comparación Interanual")

with st.expander("📤 Cargar Excel"):
    archivo = st.file_uploader("Sube archivo Excel", type=["xlsx"])
    anio = st.number_input("Selecciona el año:", 
                          min_value=2000, 
                          max_value=2100, 
                          value=datetime.now().year,
                          step=1)

    if archivo and st.button("Guardar datos"):
        try:
            df = pd.read_excel(archivo)

            # Verificar que el archivo tenga las columnas requeridas
            columnas_requeridas = ["Fecha", "Secciones", "Entradas", "Venta", 
                                  "Tickets", "Artículos", "Ticket promedio", 
                                  "Artículos por ticket", "Tasa de conversión"]
            
            columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
            
            if columnas_faltantes:
                st.error(f"El archivo debe contener las siguientes columnas: {', '.join(columnas_faltantes)}")
            else:
                # Renombrar columnas para que coincidan con la base de datos
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
                
                # Agregar columna de año
                df["anio"] = anio
                
                # Convertir tipos de datos
                df["fecha"] = pd.to_datetime(df["fecha"]).dt.date
                df["entradas"] = pd.to_numeric(df["entradas"], errors='coerce')
                df["venta"] = pd.to_numeric(df["venta"], errors='coerce')
                df["tickets"] = pd.to_numeric(df["tickets"], errors='coerce')
                df["articulos"] = pd.to_numeric(df["articulos"], errors='coerce')
                df["ticket_promedio"] = pd.to_numeric(df["ticket_promedio"], errors='coerce')
                df["articulos_por_ticket"] = pd.to_numeric(df["articulos_por_ticket"], errors='coerce')
                df["tasa_conversion"] = pd.to_numeric(df["tasa_conversion"], errors='coerce')
                
                conn = conectar()
                if conn is not None:
                    df.to_sql("ventas", conn, if_exists="append", index=False)
                    conn.close()
                    st.success(f"Datos del año {anio} cargados correctamente ({len(df)} registros)")
                    
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
    st.warning("Aún no hay datos cargados")
    st.stop()

# ---------- SELECCIÓN DE AÑOS A COMPARAR ----------
st.sidebar.header("Configuración de Comparación")

# Obtener años disponibles en la base de datos
años_disponibles = sorted(df["anio"].unique(), reverse=True)

if len(años_disponibles) == 0:
    st.warning("No hay años disponibles en la base de datos")
    st.stop()

# Selectores de años
col_selector1, col_selector2 = st.sidebar.columns(2)
with col_selector1:
    año_base = st.selectbox("Año base (anterior)", 
                           options=años_disponibles,
                           index=min(1, len(años_disponibles)-1) if len(años_disponibles) > 1 else 0)
with col_selector2:
    año_comparar = st.selectbox("Año a comparar (actual)", 
                               options=años_disponibles,
                               index=0)

# Verificar que sean años diferentes
if año_base == año_comparar and len(años_disponibles) > 1:
    st.sidebar.warning("Selecciona dos años diferentes para comparar")
    # Ajustar automáticamente
    if año_comparar == años_disponibles[0]:
        año_base = años_disponibles[1] if len(años_disponibles) > 1 else año_base

# ---------- FILTROS ADICIONALES ----------
st.sidebar.header("Filtros")

# Asegurar que la columna fecha sea datetime
df["fecha"] = pd.to_datetime(df["fecha"])

# Verificar que hay fechas válidas
if df.empty or df["fecha"].isna().all():
    st.warning("No hay datos con fechas válidas para filtrar")
    st.stop()

# Obtener fechas mínima y máxima
fecha_min = df["fecha"].min()
fecha_max = df["fecha"].max()

# Filtro de rango de fechas en el sidebar
st.sidebar.write("Seleccionar rango de fechas:")

if fecha_min.date() == fecha_max.date():
    # Si solo hay una fecha
    fecha_seleccionada = st.sidebar.date_input(
        "Fecha",
        value=fecha_min.date(),
        min_value=fecha_min.date(),
        max_value=fecha_max.date(),
        key="fecha_unica"
    )
    fecha_inicio = pd.Timestamp(fecha_seleccionada)
    fecha_fin = pd.Timestamp(fecha_seleccionada)
else:
    # Si hay múltiples fechas
    col_fecha1, col_fecha2 = st.sidebar.columns(2)
    
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
    
    # Validar que fecha_inicio <= fecha_fin
    if fecha_inicio > fecha_fin:
        st.sidebar.error("La fecha inicial debe ser menor o igual a la fecha final")
        fecha_inicio, fecha_fin = fecha_fin, fecha_inicio

# Filtro de secciones
secciones = sorted(df["secciones"].unique())
secciones_seleccionadas = st.sidebar.multiselect(
    "Secciones",
    options=secciones,
    default=secciones,
    key="secciones_filter"
)

# Aplicar filtros usando comparación directa con Timestamps
df_filtrado = df[
    (df["fecha"] >= fecha_inicio) &
    (df["fecha"] <= fecha_fin) &
    (df["secciones"].isin(secciones_seleccionadas))
]

# Mostrar información de los filtros aplicados
st.sidebar.info(f"Mostrando {len(df_filtrado)} registros de {len(df)} totales")

# ---------- VERIFICAR FILTROS APLICADOS ----------
st.sidebar.write("---")
st.sidebar.write(f"📊 **Resumen de filtros:**")
st.sidebar.write(f"- Rango: {fecha_inicio.strftime('%d/%m/%Y')} al {fecha_fin.strftime('%d/%m/%Y')}")
st.sidebar.write(f"- Secciones: {len(secciones_seleccionadas)} seleccionadas")
st.sidebar.write(f"- Registros mostrados: {len(df_filtrado)}")

# ---------- KPIS GENERALES ----------
st.subheader(f"📈 Comparación General: {año_base} vs {año_comparar}")

# Verificar que hay datos para los años seleccionados dentro del rango filtrado
datos_base_filtrados = df_filtrado[df_filtrado["anio"] == año_base]
datos_comparar_filtrados = df_filtrado[df_filtrado["anio"] == año_comparar]

if datos_base_filtrados.empty and datos_comparar_filtrados.empty:
    st.warning(f"No hay datos para los años {año_base} y {año_comparar} en el rango de fechas seleccionado")
    st.stop()
elif datos_base_filtrados.empty:
    st.warning(f"No hay datos para el año {año_base} en el rango de fechas seleccionado")
    # Mostrar solo datos del año a comparar
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(f"Ventas {año_comparar}", f"${datos_comparar_filtrados['venta'].sum():,.0f}")
    with col2:
        st.metric(f"Entradas {año_comparar}", f"{datos_comparar_filtrados['entradas'].sum():,.0f}")
    with col3:
        ticket_prom = datos_comparar_filtrados['venta'].sum() / datos_comparar_filtrados['tickets'].sum() if datos_comparar_filtrados['tickets'].sum() > 0 else 0
        st.metric(f"Ticket Prom. {año_comparar}", f"${ticket_prom:,.2f}")
    with col4:
        st.metric(f"Tasa Conv. {año_comparar}", f"{datos_comparar_filtrados['tasa_conversion'].mean():.2f}%")
    st.stop()
elif datos_comparar_filtrados.empty:
    st.warning(f"No hay datos para el año {año_comparar} en el rango de fechas seleccionado")
    # Mostrar solo datos del año base
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(f"Ventas {año_base}", f"${datos_base_filtrados['venta'].sum():,.0f}")
    with col2:
        st.metric(f"Entradas {año_base}", f"{datos_base_filtrados['entradas'].sum():,.0f}")
    with col3:
        ticket_prom = datos_base_filtrados['venta'].sum() / datos_base_filtrados['tickets'].sum() if datos_base_filtrados['tickets'].sum() > 0 else 0
        st.metric(f"Ticket Prom. {año_base}", f"${ticket_prom:,.2f}")
    with col4:
        st.metric(f"Tasa Conv. {año_base}", f"{datos_base_filtrados['tasa_conversion'].mean():.2f}%")
    st.stop()

# Calcular métricas por año con los datos filtrados
metricas_base = {
    "venta": datos_base_filtrados["venta"].sum(),
    "entradas": datos_base_filtrados["entradas"].sum(),
    "tickets": datos_base_filtrados["tickets"].sum(),
    "articulos": datos_base_filtrados["articulos"].sum()
}

metricas_comparar = {
    "venta": datos_comparar_filtrados["venta"].sum(),
    "entradas": datos_comparar_filtrados["entradas"].sum(),
    "tickets": datos_comparar_filtrados["tickets"].sum(),
    "articulos": datos_comparar_filtrados["articulos"].sum()
}

# Calcular ticket promedio y artículos por ticket
ticket_prom_base = metricas_base["venta"] / metricas_base["tickets"] if metricas_base["tickets"] > 0 else 0
ticket_prom_comparar = metricas_comparar["venta"] / metricas_comparar["tickets"] if metricas_comparar["tickets"] > 0 else 0

# Calcular tasas de conversión promedio
tasa_base = datos_base_filtrados["tasa_conversion"].mean() if not datos_base_filtrados.empty else 0
tasa_comparar = datos_comparar_filtrados["tasa_conversion"].mean() if not datos_comparar_filtrados.empty else 0

# Mostrar KPIs con los datos filtrados
col1, col2, col3, col4 = st.columns(4)

with col1:
    delta_ventas = ((metricas_comparar['venta'] - metricas_base['venta'])/metricas_base['venta']*100) if metricas_base['venta'] > 0 else None
    st.metric(
        f"Ventas {año_comparar}",
        f"${metricas_comparar['venta']:,.0f}",
        delta=f"{delta_ventas:.1f}% vs {año_base}" if delta_ventas is not None else "Sin datos base",
        delta_color="normal" if delta_ventas is not None else "off"
    )
    st.caption(f"{año_base}: ${metricas_base['venta']:,.0f}")

with col2:
    delta_entradas = ((metricas_comparar['entradas'] - metricas_base['entradas'])/metricas_base['entradas']*100) if metricas_base['entradas'] > 0 else None
    st.metric(
        f"Entradas {año_comparar}",
        f"{metricas_comparar['entradas']:,.0f}",
        delta=f"{delta_entradas:.1f}% vs {año_base}" if delta_entradas is not None else "Sin datos base",
        delta_color="normal" if delta_entradas is not None else "off"
    )
    st.caption(f"{año_base}: {metricas_base['entradas']:,.0f}")

with col3:
    delta_ticket = ((ticket_prom_comparar - ticket_prom_base)/ticket_prom_base*100) if ticket_prom_base > 0 else None
    st.metric(
        f"Ticket Prom. {año_comparar}",
        f"${ticket_prom_comparar:,.2f}",
        delta=f"{delta_ticket:.1f}% vs {año_base}" if delta_ticket is not None else "Sin datos base",
        delta_color="normal" if delta_ticket is not None else "off"
    )
    st.caption(f"{año_base}: ${ticket_prom_base:,.2f}")

with col4:
    delta_tasa = tasa_comparar - tasa_base if tasa_base > 0 else None
    st.metric(
        f"Tasa Conv. {año_comparar}",
        f"{tasa_comparar:.2f}%",
        delta=f"{delta_tasa:.2f} pp vs {año_base}" if delta_tasa is not None else "Sin datos base",
        delta_color="normal" if delta_tasa is not None else "off"
    )
    st.caption(f"{año_base}: {tasa_base:.2f}%")

# Mostrar información del período filtrado
st.info(f"📅 Mostrando datos del {fecha_inicio.strftime('%d/%m/%Y')} al {fecha_fin.strftime('%d/%m/%Y')} | Secciones: {', '.join(secciones_seleccionadas[:3])}{'...' if len(secciones_seleccionadas) > 3 else ''}")

# ---------- COMPARACIÓN DÍA A DÍA ----------
st.subheader(f"📅 Comparación Día a Día: {año_base} vs {año_comparar}")

# Crear selector de fecha para comparación día a día
st.write("Selecciona un día para comparar entre años:")

# Obtener todas las fechas únicas del año base y año comparar (usando los datos filtrados)
fechas_base = sorted(df_filtrado[df_filtrado["anio"] == año_base]["fecha"].dt.date.unique())
fechas_comparar = sorted(df_filtrado[df_filtrado["anio"] == año_comparar]["fecha"].dt.date.unique())

if not fechas_base or not fechas_comparar:
    st.warning(f"No hay fechas disponibles para comparar entre {año_base} y {año_comparar} en el rango seleccionado")
else:
    col_dia1, col_dia2, col_dia3 = st.columns([2, 2, 1])
    
    with col_dia1:
        fecha_base_seleccionada = st.selectbox(
            f"Día en {año_base}",
            options=fechas_base,
            format_func=lambda x: x.strftime("%d/%m/%Y"),
            key="fecha_base"
        )
    
    with col_dia2:
        fecha_comparar_seleccionada = st.selectbox(
            f"Día en {año_comparar}",
            options=fechas_comparar,
            format_func=lambda x: x.strftime("%d/%m/%Y"),
            key="fecha_comparar"
        )
    
    with col_dia3:
        st.write("")
        st.write("")
        buscar_btn = st.button("🔍 Buscar mismo día", use_container_width=True)
    
    # Botón para buscar fechas similares (mismo mes y día)
    if buscar_btn:
        encontrado = False
        for fecha_b in fechas_base:
            for fecha_c in fechas_comparar:
                if fecha_b.month == fecha_c.month and fecha_b.day == fecha_c.day:
                    fecha_base_seleccionada = fecha_b
                    fecha_comparar_seleccionada = fecha_c
                    st.success(f"✓ Encontrado: {fecha_base_seleccionada.strftime('%d/%m')} en ambos años")
                    encontrado = True
                    break
            if encontrado:
                break
        if not encontrado:
            st.warning("No se encontró el mismo mes/día en ambos años")
    
    # Obtener datos para las fechas seleccionadas
    datos_dia_base = df_filtrado[
        (df_filtrado["anio"] == año_base) & 
        (df_filtrado["fecha"].dt.date == fecha_base_seleccionada)
    ]
    
    datos_dia_comparar = df_filtrado[
        (df_filtrado["anio"] == año_comparar) & 
        (df_filtrado["fecha"].dt.date == fecha_comparar_seleccionada)
    ]
    
    if not datos_dia_base.empty and not datos_dia_comparar.empty:
        # Calcular totales por día
        total_base = {
            "venta": datos_dia_base["venta"].sum(),
            "entradas": datos_dia_base["entradas"].sum(),
            "tickets": datos_dia_base["tickets"].sum(),
            "articulos": datos_dia_base["articulos"].sum()
        }
        
        total_comparar = {
            "venta": datos_dia_comparar["venta"].sum(),
            "entradas": datos_dia_comparar["entradas"].sum(),
            "tickets": datos_dia_comparar["tickets"].sum(),
            "articulos": datos_dia_comparar["articulos"].sum()
        }
        
        # Calcular ticket promedio diario
        ticket_prom_base = total_base["venta"] / total_base["tickets"] if total_base["tickets"] > 0 else 0
        ticket_prom_comparar = total_comparar["venta"] / total_comparar["tickets"] if total_comparar["tickets"] > 0 else 0
        
        # Mostrar comparación día a día
        st.write("---")
        st.subheader(f"Comparación: {fecha_base_seleccionada.strftime('%d/%m/%Y')} vs {fecha_comparar_seleccionada.strftime('%d/%m/%Y')}")
        
        col_dia_metric1, col_dia_metric2, col_dia_metric3, col_dia_metric4 = st.columns(4)
        
        with col_dia_metric1:
            delta_ventas_dia = ((total_comparar['venta'] - total_base['venta'])/total_base['venta']*100) if total_base['venta'] > 0 else None
            st.metric(
                f"Ventas {fecha_comparar_seleccionada.strftime('%d/%m')}",
                f"${total_comparar['venta']:,.0f}",
                delta=f"{delta_ventas_dia:.1f}% vs {fecha_base_seleccionada.strftime('%d/%m')}" if delta_ventas_dia is not None else "Sin datos",
                delta_color="normal" if delta_ventas_dia is not None else "off"
            )
            st.caption(f"{fecha_base_seleccionada.strftime('%d/%m')}: ${total_base['venta']:,.0f}")
        
        with col_dia_metric2:
            delta_entradas_dia = ((total_comparar['entradas'] - total_base['entradas'])/total_base['entradas']*100) if total_base['entradas'] > 0 else None
            st.metric(
                f"Entradas {fecha_comparar_seleccionada.strftime('%d/%m')}",
                f"{total_comparar['entradas']:,.0f}",
                delta=f"{delta_entradas_dia:.1f}% vs {fecha_base_seleccionada.strftime('%d/%m')}" if delta_entradas_dia is not None else "Sin datos",
                delta_color="normal" if delta_entradas_dia is not None else "off"
            )
            st.caption(f"{fecha_base_seleccionada.strftime('%d/%m')}: {total_base['entradas']:,.0f}")
        
        with col_dia_metric3:
            delta_ticket_dia = ((ticket_prom_comparar - ticket_prom_base)/ticket_prom_base*100) if ticket_prom_base > 0 else None
            st.metric(
                f"Ticket Prom. {fecha_comparar_seleccionada.strftime('%d/%m')}",
                f"${ticket_prom_comparar:,.2f}",
                delta=f"{delta_ticket_dia:.1f}% vs {fecha_base_seleccionada.strftime('%d/%m')}" if delta_ticket_dia is not None else "Sin datos",
                delta_color="normal" if delta_ticket_dia is not None else "off"
            )
            st.caption(f"{fecha_base_seleccionada.strftime('%d/%m')}: ${ticket_prom_base:,.2f}")
        
        with col_dia_metric4:
            tasa_base_dia = datos_dia_base["tasa_conversion"].mean() if not datos_dia_base.empty else 0
            tasa_comparar_dia = datos_dia_comparar["tasa_conversion"].mean() if not datos_dia_comparar.empty else 0
            delta_tasa_dia = tasa_comparar_dia - tasa_base_dia if tasa_base_dia > 0 else None
            st.metric(
                f"Tasa Conv. {fecha_comparar_seleccionada.strftime('%d/%m')}",
                f"{tasa_comparar_dia:.2f}%",
                delta=f"{delta_tasa_dia:.2f} pp vs {fecha_base_seleccionada.strftime('%d/%m')}" if delta_tasa_dia is not None else "Sin datos",
                delta_color="normal" if delta_tasa_dia is not None else "off"
            )
            st.caption(f"{fecha_base_seleccionada.strftime('%d/%m')}: {tasa_base_dia:.2f}%")
        
        # Mostrar desglose por sección para el día seleccionado
        with st.expander(f"📊 Ver desglose por sección"):
            # Crear tabla comparativa por sección
            secciones_dia = sorted(set(datos_dia_base["secciones"].unique()) | set(datos_dia_comparar["secciones"].unique()))
            
            data_secciones = []
            for seccion in secciones_dia:
                datos_base_sec = datos_dia_base[datos_dia_base["secciones"] == seccion]
                datos_comparar_sec = datos_dia_comparar[datos_dia_comparar["secciones"] == seccion]
                
                fila = {
                    "Sección": seccion,
                    f"Venta {año_base}": f"${datos_base_sec['venta'].sum():,.0f}" if not datos_base_sec.empty else "Sin datos",
                    f"Venta {año_comparar}": f"${datos_comparar_sec['venta'].sum():,.0f}" if not datos_comparar_sec.empty else "Sin datos",
                    f"Entradas {año_base}": f"{datos_base_sec['entradas'].sum():,.0f}" if not datos_base_sec.empty else "Sin datos",
                    f"Entradas {año_comparar}": f"{datos_comparar_sec['entradas'].sum():,.0f}" if not datos_comparar_sec.empty else "Sin datos",
                }
                data_secciones.append(fila)
            
            if data_secciones:
                st.dataframe(pd.DataFrame(data_secciones), use_container_width=True)
    else:
        if datos_dia_base.empty:
            st.warning(f"No hay datos para {fecha_base_seleccionada.strftime('%d/%m/%Y')}")
        if datos_dia_comparar.empty:
            st.warning(f"No hay datos para {fecha_comparar_seleccionada.strftime('%d/%m/%Y')}")

# ---------- ANÁLISIS POR SECCIÓN ----------
st.subheader(f"📊 Comparación por Sección: {año_base} vs {año_comparar}")

# Agrupar por sección y año
seccion_comparacion = df_filtrado.groupby(["secciones", "anio"]).agg({
    "venta": "sum",
    "entradas": "sum",
    "tickets": "sum"
}).reset_index()

# Crear tabla comparativa
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
            f"Venta {año_base}": f"${venta_base:,.0f}",
            f"Venta {año_comparar}": f"${venta_comparar:,.0f}",
            "Variación %": f"{variacion:.1f}%"
        })

if comparacion_secciones:
    st.dataframe(pd.DataFrame(comparacion_secciones), use_container_width=True)
else:
    st.info(f"No hay datos completos para ambos años en ninguna sección. Años disponibles: {', '.join(map(str, años_disponibles))}")

# ---------- GRÁFICOS ----------
st.subheader("📈 Evolución Temporal")

try:
    # Filtrar solo los años seleccionados para el gráfico
    df_grafico = df_filtrado[df_filtrado["anio"].isin([año_base, año_comparar])].copy()
    
    if not df_grafico.empty:
        # Crear columna de mes para agrupar
        df_grafico['mes'] = df_grafico['fecha'].dt.month
        df_grafico['mes_nombre'] = df_grafico['fecha'].dt.strftime('%b')
        
        # Agrupar por mes y año
        df_evolucion_mensual = df_grafico.groupby(['mes', 'mes_nombre', 'anio'])['venta'].sum().reset_index()
        
        if not df_evolucion_mensual.empty:
            # Crear tabla pivote
            pivot_ventas = df_evolucion_mensual.pivot(index='mes_nombre', columns='anio', values='venta').fillna(0)
            # Ordenar los meses
            orden_meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
            pivot_ventas = pivot_ventas.reindex(orden_meses)
            
            st.line_chart(pivot_ventas)
            st.caption("Evolución mensual de ventas. Cada línea representa un año.")
        else:
            st.info("No hay datos suficientes para generar el gráfico mensual")
    else:
        st.info("No hay datos suficientes para generar el gráfico")
        
except Exception as e:
    st.warning(f"No se puede generar el gráfico: {e}")

# ---------- DATOS DETALLADOS ----------
with st.expander("📋 Ver datos detallados"):
    # Mostrar estadísticas por año
    st.subheader("Resumen por año")
    resumen_anual = df_filtrado.groupby("anio").agg({
        "venta": "sum",
        "entradas": "sum",
        "tickets": "sum",
        "tasa_conversion": "mean"
    }).round(2)
    
    resumen_anual.columns = ["Ventas Totales", "Entradas Totales", "Tickets Totales", "Tasa Conv. Promedio"]
    resumen_anual["Ventas Totales"] = resumen_anual["Ventas Totales"].apply(lambda x: f"${x:,.0f}")
    resumen_anual["Entradas Totales"] = resumen_anual["Entradas Totales"].apply(lambda x: f"{x:,.0f}")
    resumen_anual["Tickets Totales"] = resumen_anual["Tickets Totales"].apply(lambda x: f"{x:,.0f}")
    resumen_anual["Tasa Conv. Promedio"] = resumen_anual["Tasa Conv. Promedio"].apply(lambda x: f"{x:.2f}%")
    
    st.dataframe(resumen_anual, use_container_width=True)
    
    # Datos detallados
    st.subheader("Registros detallados")
    st.dataframe(
        df_filtrado.sort_values(["anio", "fecha"], ascending=[False, False])
        .style.format({
            "venta": "${:,.0f}",
            "ticket_promedio": "${:,.2f}",
            "tasa_conversion": "{:.2f}%"
        })
    )

# ---------- OPCIÓN PARA REINICIAR BASE DE DATOS ----------
with st.expander("⚠️ Administración"):
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Borrar todos los datos"):
            conn = conectar()
            if conn is not None:
                try:
                    conn.execute("DELETE FROM ventas")
                    conn.commit()
                    st.warning("Base de datos limpiada")
                    st.rerun()
                except sqlite3.Error as e:
                    st.error(f"Error al borrar datos: {e}")
                finally:
                    conn.close()
    
    with col2:
        if st.button("🔄 Reiniciar estructura de BD"):
            eliminar_tabla_existente()
            crear_tabla()
            st.success("Estructura de base de datos reiniciada")
            st.rerun()