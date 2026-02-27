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

# Convertir fecha a datetime para filtros
df["fecha"] = pd.to_datetime(df["fecha"])

# Filtro de rango de fechas
fecha_min = df["fecha"].min().date()
fecha_max = df["fecha"].max().date()
fecha_inicio, fecha_fin = st.sidebar.date_input(
    "Rango de fechas",
    value=(fecha_min, fecha_max),
    min_value=fecha_min,
    max_value=fecha_max
)

# Filtro de secciones
secciones = df["secciones"].unique()
secciones_seleccionadas = st.sidebar.multiselect(
    "Secciones",
    options=secciones,
    default=secciones
)

# Aplicar filtros
df_filtrado = df[
    (df["fecha"].dt.date >= fecha_inicio) &
    (df["fecha"].dt.date <= fecha_fin) &
    (df["secciones"].isin(secciones_seleccionadas))
]

# ---------- KPIS GENERALES ----------
st.subheader(f"📈 Comparación: {año_base} vs {año_comparar}")

# Calcular métricas por año
metricas_base = df_filtrado[df_filtrado["anio"] == año_base].agg({
    "venta": "sum",
    "entradas": "sum",
    "tickets": "sum",
    "articulos": "sum"
})

metricas_comparar = df_filtrado[df_filtrado["anio"] == año_comparar].agg({
    "venta": "sum",
    "entradas": "sum",
    "tickets": "sum",
    "articulos": "sum"
})

# Verificar si hay datos para ambos años
if metricas_base["venta"] == 0 or metricas_comparar["venta"] == 0:
    st.info(f"⚠️ No hay datos completos para ambos años. Años con datos: {', '.join(map(str, años_disponibles))}")

# Calcular ticket promedio y artículos por ticket
ticket_prom_base = metricas_base["venta"] / metricas_base["tickets"] if metricas_base["tickets"] > 0 else 0
ticket_prom_comparar = metricas_comparar["venta"] / metricas_comparar["tickets"] if metricas_comparar["tickets"] > 0 else 0

# Mostrar KPIs
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
    tasa_base = df_filtrado[df_filtrado['anio'] == año_base]['tasa_conversion'].mean() if not df_filtrado[df_filtrado['anio'] == año_base].empty else 0
    tasa_comparar = df_filtrado[df_filtrado['anio'] == año_comparar]['tasa_conversion'].mean() if not df_filtrado[df_filtrado['anio'] == año_comparar].empty else 0
    delta_tasa = tasa_comparar - tasa_base if tasa_base > 0 else None
    st.metric(
        f"Tasa Conv. {año_comparar}",
        f"{tasa_comparar:.2f}%",
        delta=f"{delta_tasa:.2f} pp vs {año_base}" if delta_tasa is not None else "Sin datos base",
        delta_color="normal" if delta_tasa is not None else "off"
    )
    st.caption(f"{año_base}: {tasa_base:.2f}%")

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
        # Crear una columna de Mes (como string o número) para mejor visualización
        df_grafico['mes'] = df_grafico['fecha'].dt.month
        df_grafico['mes_nombre'] = df_grafico['fecha'].dt.strftime('%b') # 'Ene', 'Feb', etc.

        # Preparar datos para gráficos: Agrupar por MES y AÑO
        df_evolucion_mensual = df_grafico.groupby(['mes', 'mes_nombre', 'anio'])['venta'].sum().reset_index()

        if not df_evolucion_mensual.empty:
            # Crear una tabla pivote: Filas = Mes, Columnas = Año, Valores = Ventas
            pivot_ventas = df_evolucion_mensual.pivot(index='mes_nombre', columns='anio', values='venta').fillna(0)
            # Ordenar los meses correctamente
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