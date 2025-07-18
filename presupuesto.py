# -*- coding: utf-8 -*-
"""
Created on Wed Jul 16 19:01:20 2025
@author: Pablo Martinez
"""

import streamlit as st
import pandas as pd
import datetime
import numpy as np
import matplotlib.pyplot as plt
import io

st.set_page_config(layout="wide")
st.title("📊 Dashboard Presupuesto Proyectado")

# --- PARÁMETROS GENERALES ---
st.sidebar.header("⚙️ Parámetros Generales")
fecha_inicio = st.sidebar.date_input("📅 Fecha de inicio", datetime.date(2025, 7, 1))
fecha_inicio = pd.to_datetime(fecha_inicio)

periodos = 24
fechas = [fecha_inicio + pd.DateOffset(months=i) for i in range(periodos)]

# --- FILTRO DE PERIODO ---
st.sidebar.header("📅 Filtro de periodo a visualizar")
opcion_periodo = st.sidebar.radio(
    "Selecciona periodo:",
    ["Todo", "Año 2025", "Año 2026", "Próximo trimestre", "Próximo semestre", "Próximos 12 meses"],
    index=5
)


# --- ORQUESTACIÓN ---
st.sidebar.header("📦 Orquestación")

precio_orquestacion = st.sidebar.number_input("💰 Precio por orquestación (USD/container)", value=4.28)
crecimiento_anual = st.sidebar.slider("📈 Crecimiento anual basado en datos reales (%)", 20.0, 70.0, 55.0) / 100

# Datos reales mensuales: enero 2024 a junio 2025 (18 valores)
containers_reales = [
    7761, 5406, 6243, 6453, 5509, 5599, 8059, 8108, 7981, 9821, 10907, 13122,   # 2024
    10995, 8619, 10428, 8915, 10047, 8157                                       # 2025 hasta junio
]

# Crear mapa de mes (formato 'Jul', 'Aug', etc.) a valores históricos
meses_reales = pd.date_range(start="2024-01-01", periods=18, freq='MS')
containers_dict = {fecha.strftime('%b'): valor for fecha, valor in zip(meses_reales, containers_reales)}

# Fechas de proyección: desde julio 2025 en adelante
fecha_inicio = pd.to_datetime("2025-07-01")
periodos = 24
fechas = [fecha_inicio + pd.DateOffset(months=i) for i in range(periodos)]

# Proyección: usar mismo mes del año anterior como base
containers_proyectados = []
for fecha in fechas:
    mes_nombre = fecha.strftime('%b')  # 'Jul', 'Aug', etc.
    if mes_nombre in containers_dict:
        base = containers_dict[mes_nombre]
        proyectado = base * (1 + crecimiento_anual)
    else:
        # fallback en caso de error (por si el mes no está definido)
        base = 10000
        proyectado = base * (1 + crecimiento_anual)
    containers_proyectados.append(round(proyectado))

# Ingreso por orquestación
ingreso_orquestacion = [round(c * precio_orquestacion, 2) for c in containers_proyectados]

# Crear DataFrame
df_orquestacion = pd.DataFrame({
    "Fecha": fechas,
    "Containers": containers_proyectados,
    "Ingreso Orquestación": ingreso_orquestacion
})


# DataFrame final
df = pd.DataFrame({
    "Fecha": fechas,
    "Containers": containers_proyectados,
    "Ingreso Orquestación": ingreso_orquestacion
})


# --- FINANCIAMIENTO ---
# --- Valores base predeterminados (jul-2025 a dic-2026) ---
valores_base = [
    500000, 500000, 1000000, 1500000, 4500000, 4500000, 4500000, 6500000,
    8500000, 10500000, 12500000, 14500000, 16500000, 18000000,
    20000000, 20000000, 20000000, 20000000
]
valores_base += [0.0] * (periodos - len(valores_base))  # Rellenar si hay más meses

# --- Parámetros financiamiento ---
st.sidebar.header("💸 Financiamiento")
metodo_fin = st.sidebar.selectbox("Método de cálculo", [
    "% de carga con crecimiento",
    "Monto inicial + crecimiento",
    "Ingreso manual"
], index=2)  # <- index 2 selecciona por defecto "Ingreso manual"

mes_inicio_fin = st.sidebar.slider("🕒 Mes inicio financiamiento", 0, periodos - 1, 0)
margen_fin = st.sidebar.slider("💵 Margen ganado (%)", 0.0, 2.0, 0.3) / 100

if metodo_fin == "% de carga con crecimiento":
    pct_fin = st.sidebar.slider("📦 % carga financiada", 0.0, 100.0, 40.0) / 100
    crecimiento_pct = st.sidebar.slider("📈 Crecimiento mensual del %", 0.0, 10.0, 0.0) / 100
    pct_fin_series = [(pct_fin * ((1 + crecimiento_pct) ** i)) for i in range(periodos)]
    monto_fin = df["Containers"] * precio_contenedor * pd.Series(pct_fin_series)

elif metodo_fin == "Monto inicial + crecimiento":
    monto_inicial = st.sidebar.number_input("💵 Monto financiado inicial (USD)", value=10000000.0)
    crecimiento_monto = st.sidebar.slider("📈 Crecimiento mensual monto (%)", 0.0, 20.0, 0.0) / 100
    monto_fin = pd.Series([monto_inicial * ((1 + crecimiento_monto) ** i) for i in range(periodos)])

else:  # Ingreso manual
    monto_manual = []
    st.sidebar.markdown("✍️ Ingresa los montos por mes:")
    for i in range(periodos):
        default_val = valores_base[i]
        monto_mes = st.sidebar.number_input(
            f"Mes {i+1} ({fechas[i].strftime('%b %Y')})",
            value=default_val,
            key=f"manual_fin_{i}"
        )
        monto_manual.append(monto_mes)
    monto_fin = pd.Series(monto_manual)

# Debug opcional
# print(monto_fin / 1_000_000)

# Aplicar condiciones de inicio
ingreso_fin = monto_fin * margen_fin
df["Monto Financiado"] = [m if i >= mes_inicio_fin else 0 for i, m in enumerate(monto_fin)]
df["Ingreso Financiamiento"] = [i if j >= mes_inicio_fin else 0 for j, i in enumerate(ingreso_fin)]


# --- FX ---
st.sidebar.header("💱 FX")

mes_inicio_fx = st.sidebar.slider("🕒 Mes inicio FX", 0, periodos - 1, 0)
fx_base = st.sidebar.radio("📊 Base FX:", ["Valor inicial", "Monto financiado", "Valor orquestado", "Ambos"])

spread_fx_pct = st.sidebar.number_input("🪙 Spread promedio (% sobre USD)", value=0.5, step=0.01, format="%.2f")
spread_fx = spread_fx_pct / 100  # Lo usamos como decimal en los cálculos

crecimiento_fx = st.sidebar.slider("📈 Crecimiento mensual FX (%)", 0.0, 40.0, 30.0) / 100

precio_contenedor = st.sidebar.number_input("💲 Precio por container (USD)", value=30000)

vol_fx = []

# --- OPCIÓN 1: VALOR INICIAL ---
if fx_base == "Valor inicial":
    fx_inicial = st.sidebar.number_input("📍 Volumen FX inicial (USD)", value=1000_000)
    for i in range(periodos):
        if i < mes_inicio_fx:
            vol_fx.append(0)
        elif i == mes_inicio_fx:
            vol_fx.append(fx_inicial)
        else:
            vol_fx.append(vol_fx[-1] * (1 + crecimiento_fx))

# --- OPCIÓN 2: % MONTO FINANCIADO ---
elif fx_base == "Monto financiado":
    pct_fx = st.sidebar.slider("💸 % del monto financiado que pasa por FX", 0.0, 100.0, 80.0) / 100
    for i in range(periodos):
        if i < mes_inicio_fx:
            vol_fx.append(0)
        else:
            base = df["Monto Financiado"][i] * pct_fx
            vol_fx.append(base * ((1 + crecimiento_fx) ** (i - mes_inicio_fx)))

# --- OPCIÓN 3: % VALOR ORQUESTADO ---
elif fx_base == "Valor orquestado":
    pct_fx_o = st.sidebar.slider("📦 % de la orquestación que pasa por FX", 0.0, 100.0, 5.0) / 100
    for i in range(periodos):
        if i < mes_inicio_fx:
            vol_fx.append(0)
        else:
            base = df["Containers"][i] * precio_contenedor * pct_fx_o
            vol_fx.append(base * ((1 + crecimiento_fx) ** (i - mes_inicio_fx)))

# --- OPCIÓN 4: AMBOS (financiamiento + orquestación) ---
else:
    pct_fx = st.sidebar.slider("💸 % del monto financiado que pasa por FX", 0.0, 100.0, 80.0) / 100
    pct_fx_o = st.sidebar.slider("📦 % de la orquestación que pasa por FX", 0.0, 100.0, 5.0) / 100
    for i in range(periodos):
        if i < mes_inicio_fx:
            vol_fx.append(0)
        else:
            base_f = df["Monto Financiado"][i] * pct_fx
            base_o = df["Containers"][i] * precio_contenedor * pct_fx_o
            base = base_f + base_o
            vol_fx.append(base * ((1 + crecimiento_fx) ** (i - mes_inicio_fx)))

# --- Ingreso por FX ---
ingreso_fx = [v * spread_fx for v in vol_fx]
df["Volumen FX"] = vol_fx
df["Ingreso FX"] = ingreso_fx


# --- SEGURO CRÉDITO ---
st.sidebar.header("🔐 Seguro de Crédito")
mes_inicio_sc = st.sidebar.slider("🕒 Mes inicio seguro crédito", 0, periodos - 1, 1)
pct_aseg_sc = st.sidebar.slider("🔒 % monto carga asegurado", 0.0, 10.0, 4.0) / 100
prima_sc = st.sidebar.slider("💰 Prima (% del monto asegurado)", 0.3, 0.6, 0.4) / 100
comision_sc = st.sidebar.slider("💵 Comisión ganada (%)", 0.0, 10.0, 5.0) / 100
crecimiento_sc = st.sidebar.slider("📈 Crecimiento anual Seguro Crédito (%)", 0.0, 100.0, 0.0) / 100

valor_carga = df["Containers"] * precio_contenedor
monto_base_sc = valor_carga * pct_aseg_sc
monto_asegurado_sc = [monto_base_sc[i] * (1 + crecimiento_sc) ** (i / 12) for i in range(periodos)]
# Inicializa la lista con ceros
ingreso_sc = [0.0] * periodos

# Calcula y distribuye en 12 meses
for i in range(mes_inicio_sc, periodos):
    ingreso_total = monto_asegurado_sc[i] * prima_sc * comision_sc
    cuota_mensual = ingreso_total / 12

    for j in range(i, min(i + 12, periodos)):
        ingreso_sc[j] += cuota_mensual

df["Ingreso Seguro Crédito"] = ingreso_sc

# --- SEGURO CARGA ---
st.sidebar.header("📦 Seguro de Carga")
mes_inicio_sca = st.sidebar.slider("🕒 Mes inicio seguro carga", 0, periodos - 1, 1)
pct_aseg_sca = st.sidebar.slider("📦 % carga asegurada", 0.0, 10.0, 5.0) / 100
prima_sca = st.sidebar.slider("💰 Prima (% del valor carga)", 0.05, 0.15, 0.10) / 100
comision_sca = st.sidebar.slider("💵 Comisión ganada (%)", 0.0, 10.0, 4.0) / 100
crecimiento_sca = st.sidebar.slider("📈 Crecimiento anual Seguro Carga (%)", 0.0, 100.0, 0.0) / 100

monto_asegurado_sca = [valor_carga[i] * pct_aseg_sca * (1 + crecimiento_sca) ** (i / 12) for i in range(periodos)]
ingreso_sca = [m * prima_sca * comision_sca if i >= mes_inicio_sca else 0 for i, m in enumerate(monto_asegurado_sca)]
df["Ingreso Seguro Carga"] = ingreso_sca


# --- PAGOS NAVIERAS ---
st.sidebar.header("🚢 Pagos a Navieras")
mes_inicio_nav = st.sidebar.slider("🕒 Mes inicio pagos navieras", 0, periodos - 1, 2)
pct_part_nav = st.sidebar.slider("📊 % participación sobre pagos posibles", 0.0, 30.0, 5.0) / 100
flete_prom = st.sidebar.number_input("🚢 Flete promedio (USD)", value=50000.0)
ingreso_fijo_nav = st.sidebar.number_input("💵 Ingreso fijo por pago", value=25.0)
comision_nav = st.sidebar.slider("💰 Comisión sobre monto pagado (%)", 0.0, 1.5, 0.75) / 100

# Cálculo base
monto_fletes = valor_carga * 0.10
n_pagos_max = monto_fletes / flete_prom
n_pagos_real = n_pagos_max * pct_part_nav

# Separar ingreso fijo y variable
ingreso_nav_fijo = [n * ingreso_fijo_nav if i >= mes_inicio_nav else 0 for i, n in enumerate(n_pagos_real)]
ingreso_nav_var = [m * pct_part_nav * comision_nav if i >= mes_inicio_nav else 0 for i, m in enumerate(monto_fletes)]

# Guardar en DataFrame
df["Ingreso Navieras Fijo"] = ingreso_nav_fijo
df["Ingreso Navieras Variable"] = ingreso_nav_var
df["Ingreso Navieras"] = df["Ingreso Navieras Fijo"] + df["Ingreso Navieras Variable"]


# --- PAGO PROVEEDORES ---
st.sidebar.header("🏗️ Pago a Proveedores")
mes_inicio_prov = st.sidebar.slider("🕒 Mes inicio pago a proveedores", 0, periodos - 1, 3)
pct_prov = st.sidebar.slider("📦 % de carga orquestada que paga proveedores", 0.0, 20.0, 0.6) / 100

monto_proveedor_base = []
ingreso_proveedores = []

for i in range(periodos):
    if i < mes_inicio_prov:
        monto_proveedor_base.append(0)
        ingreso_proveedores.append(0)
    else:
        base = df["Containers"][i] * precio_contenedor * pct_prov
        monto_proveedor_base.append(base)
        ingreso_proveedores.append(base * spread_fx)

df["Monto Pago Proveedores"] = monto_proveedor_base
df["Ingreso Pago Proveedores"] = ingreso_proveedores

# --- PAGO INLAND ---
st.sidebar.header("🚚 Pago Inland")
mes_inicio_inland = st.sidebar.slider("🕒 Mes inicio pago inland", 0, periodos - 1, 3)
pct_part_inland = st.sidebar.slider("📦 % de containers con pago inland", 0.0, 20.0, 10.0) / 100
flete_inland = st.sidebar.number_input("💲 Flete promedio inland (USD)", value=1500.0)
comision_inland = st.sidebar.slider("💰 Comisión sobre inland (%)", 0.0, 2.0, 0.75) / 100

containers_inland = df["Containers"] * pct_part_inland
monto_inland = containers_inland * flete_inland
ingreso_inland = monto_inland * comision_inland
df["Monto Pago Inland"] = monto_inland
df["Ingreso Pago Inland"] = [i if j >= mes_inicio_inland else 0 for j, i in enumerate(ingreso_inland)]



# Asegurar tipos compatibles
fecha_inicio = pd.to_datetime(fecha_inicio)
df["Fecha"] = pd.to_datetime(df["Fecha"])

# Filtro por opción seleccionada
if opcion_periodo == "Todo":
    df_filtrado = df.copy()

elif opcion_periodo == "Año 2025":
    df_filtrado = df[df["Fecha"].dt.year == 2025]

elif opcion_periodo == "Año 2026":
    df_filtrado = df[df["Fecha"].dt.year == 2026]

elif opcion_periodo == "Próximo trimestre":
    df_filtrado = df[(df["Fecha"] >= fecha_inicio) & (df["Fecha"] < fecha_inicio + pd.DateOffset(months=3))]

elif opcion_periodo == "Próximo semestre":
    df_filtrado = df[(df["Fecha"] >= fecha_inicio) & (df["Fecha"] < fecha_inicio + pd.DateOffset(months=6))]

elif opcion_periodo == "Próximos 12 meses":
    df_filtrado = df[(df["Fecha"] >= fecha_inicio) & (df["Fecha"] < fecha_inicio + pd.DateOffset(months=12))]



# --- CÁLCULOS Y COLUMNAS PERSONALIZADAS ---

# Recalculo de valores base
df_filtrado["Monto Asegurado SC"] = valor_carga * pct_aseg_sc
df_filtrado["Monto Asegurado SCA"] = valor_carga * pct_aseg_sca
df_filtrado["Monto Pagado Navieras"] = valor_carga * 0.10 * pct_part_nav

df_filtrado["Containers Orquestados"] = df_filtrado["Containers"]
df_filtrado["Monto Financiado Total"] = df_filtrado["Monto Financiado"]
df_filtrado["Volumen FX Total"] = df_filtrado["Volumen FX"]

# Agregar columnas de navieras y proveedores
df_filtrado["Ingreso Navieras Fijo"] = df["Ingreso Navieras Fijo"]
df_filtrado["Ingreso Navieras Variable"] = df["Ingreso Navieras Variable"]
df_filtrado["Ingreso Navieras"] = df["Ingreso Navieras"]
df_filtrado["Monto Pago Proveedores"] = df["Monto Pago Proveedores"]
df_filtrado["Ingreso Pago Proveedores"] = df["Ingreso Pago Proveedores"]
df_filtrado["Monto Pago Inland"] = df["Monto Pago Inland"]
df_filtrado["Ingreso Pago Inland"] = df["Ingreso Pago Inland"]

# Total ingresos
df_filtrado["Total Ingresos"] = df_filtrado[[
    "Ingreso Orquestación", "Ingreso Financiamiento", "Ingreso FX",
    "Ingreso Seguro Crédito", "Ingreso Seguro Carga",
    "Ingreso Navieras", "Ingreso Pago Proveedores", "Ingreso Pago Inland"
]].sum(axis=1)


# --- KPIs ---
st.subheader("📌 KPIs del periodo seleccionado")

# Volumen operado
st.markdown("### 📦 Volumenes Orquestados")
col1, col2, col3 = st.columns(3)
col1.metric("Total Containers", f"{df_filtrado['Containers'].sum():,.0f}")
col2.metric("Carga Valorizada", f"USD ${df_filtrado['Containers'].sum() * precio_contenedor:,.0f}")
col3.empty()  # para mantener alineación

# Montos totales por línea
st.markdown("### 💰 Montos Totales por Línea")
col4, col5, col6 = st.columns(3)
col4.metric("Monto Financiado", f"USD ${df_filtrado['Monto Financiado'].sum():,.0f}")
col5.metric("Monto Asegurado Crédito", f"USD ${df_filtrado['Monto Asegurado SC'].sum():,.0f}")

col6.metric("Monto Asegurado Carga", f"USD {df_filtrado['Monto Asegurado SCA'].sum():,.0f}")

col7, col8, col9 = st.columns(3)
col7.metric("Volumen FX", f"USD ${df_filtrado['Volumen FX'].sum():,.0f}")
col8.metric("Monto Pagado Navieras", f"USD ${df_filtrado['Monto Pagado Navieras'].sum():,.0f}")
col9.metric("Monto Pago Proveedores", f"USD ${df_filtrado['Monto Pago Proveedores'].sum():,.0f}")

col10, col11, col12 = st.columns(3)
col10.metric("Monto Pago Inland", f"USD ${df_filtrado['Monto Pago Inland'].sum():,.0f}")
col11.empty()
col12.empty()



# Ingresos por línea de negocio
st.markdown("### 📈 Ingresos por Línea de Negocio")
col13, col14, col15 = st.columns(3)
col13.metric("Ingreso Orquestación", f"USD ${df_filtrado['Ingreso Orquestación'].sum():,.0f}")
col14.metric("Ingreso Financiamiento", f"USD ${df_filtrado['Ingreso Financiamiento'].sum():,.0f}")
col15.metric("Ingreso FX", f"USD ${df_filtrado['Ingreso FX'].sum():,.0f}")

col16, col17, col18 = st.columns(3)
col16.metric("Ingreso Seguro Crédito", f"USD ${df_filtrado['Ingreso Seguro Crédito'].sum():,.0f}")
col17.metric("Ingreso Seguro Carga", f"USD ${df_filtrado['Ingreso Seguro Carga'].sum():,.0f}")
col18.metric("Ingreso Navieras", f"USD ${df_filtrado['Ingreso Navieras'].sum():,.0f}")

col19, col20, col21 = st.columns(3)
col19.metric("Ingreso Pago Proveedores", f"USD ${df_filtrado['Ingreso Pago Proveedores'].sum():,.0f}")
col20.metric("Ingreso Pago Inland", f"USD ${df_filtrado['Ingreso Pago Inland'].sum():,.0f}")
col21.metric("🔚 Total Ingresos", f"USD ${df_filtrado['Total Ingresos'].sum():,.0f}")

# --- RESUMEN TRANSPUESTO CON MONTOS BASE Y MEJORAS VISUALES ---
df_filtrado["Total Ingresos"] = df_filtrado[[
    "Ingreso Orquestación", "Ingreso Financiamiento", "Ingreso FX",
    "Ingreso Seguro Crédito", "Ingreso Seguro Carga",
    "Ingreso Navieras", "Ingreso Pago Proveedores", "Ingreso Pago Inland"
]].sum(axis=1)




# Crear resumen transpuesto desde df_filtrado
df_resumen = df_filtrado.set_index("Fecha")[[ 
    "Containers Orquestados", "Ingreso Orquestación",
    "Monto Financiado Total", "Ingreso Financiamiento",
    "Volumen FX Total", "Ingreso FX",
    "Monto Asegurado SC", "Ingreso Seguro Crédito",
    "Monto Asegurado SCA", "Ingreso Seguro Carga",
    "Monto Pagado Navieras", "Ingreso Navieras Fijo", "Ingreso Navieras Variable", "Ingreso Navieras",
    "Monto Pago Proveedores", "Ingreso Pago Proveedores",
    "Monto Pago Inland", "Ingreso Pago Inland",
    "Total Ingresos"
]].transpose()

df_resumen.index.name = "Línea de Negocio"
df_resumen.columns = [col.strftime('%b-%y') for col in df_resumen.columns]

# Crear estructura con encabezados por sección
df_resumen_final = pd.DataFrame()

secciones = {
    "🔷 ORQUESTACIÓN": ["Containers Orquestados", "Ingreso Orquestación"],
    "🔷 FINANCIAMIENTO": ["Monto Financiado Total", "Ingreso Financiamiento"],
    "🔷 FX": ["Volumen FX Total", "Ingreso FX"],
    "🔷 SEGURO CRÉDITO": ["Monto Asegurado SC", "Ingreso Seguro Crédito"],
    "🔷 SEGURO CARGA": ["Monto Asegurado SCA", "Ingreso Seguro Carga"],
    "🔷 NAVIERAS": ["Monto Pagado Navieras", "Ingreso Navieras Fijo", "Ingreso Navieras Variable", "Ingreso Navieras"],
    "🔷 PROVEEDORES": ["Monto Pago Proveedores", "Ingreso Pago Proveedores", "Monto Pago Inland", "Ingreso Pago Inland"]
}

for nombre, filas in secciones.items():
    encabezado = pd.DataFrame([[""] * df_resumen.shape[1]], columns=df_resumen.columns)
    encabezado.index = [nombre]
    sub_df = df_resumen.loc[filas]
    sub_df.index = [f"  {i}" for i in filas]
    df_resumen_final = pd.concat([df_resumen_final, encabezado, sub_df])

# ✅ Agregar Total Ingresos UNA SOLA VEZ
if "Total Ingresos" in df_resumen_final.index:
    total_final_index = "Total Ingresos Final"
else:
    total_final_index = "Total Ingresos"

total_final = df_resumen.loc[["Total Ingresos"]]
total_final.index = [total_final_index]
df_resumen_final = pd.concat([df_resumen_final, total_final])

# Mostrar tabla final
st.subheader("📋 Resumen transpuesto por línea de negocio")

def safe_format(val, row_name=None):
    try:
        if isinstance(val, (int, float)):
            if row_name and "Containers Orquestados" in row_name.strip():
                return f"{val:,.0f}"  # solo separador de miles
            else:
                return f"USD ${val:,.0f}"  # con USD
        return val
    except:
        return val


# Función para colorear por sección
def style_table(df):
    styles = []
    for idx in df.index:
        if any(idx.strip().startswith(seccion) for seccion in secciones.keys()):
            styles.append(["background-color: #D6EAF8; font-weight: bold"] * df.shape[1])
        elif idx.strip() == "Total Ingresos" or idx.strip() == "Total Ingresos Final":
            styles.append(["background-color: #A9DFBF; font-weight: bold"] * df.shape[1])
        else:
            styles.append(["background-color: #f9f9f9"] * df.shape[1])
    return pd.DataFrame(styles, index=df.index, columns=df.columns)

# Mostrar tabla estilizada correctamente formateada
df_resumen_final.index.name = "Concepto"
df_resumen_final = df_resumen_final.reset_index()
df_resumen_final = df_resumen_final.set_index("Concepto")

# Formateo personalizado solo para Containers Orquestados
def formatear_valores(val, fila):
    if fila.strip() == "Containers Orquestados" and isinstance(val, (int, float)):
        return f"{val:,.0f}"  # sin USD
    elif isinstance(val, (int, float)):
        return f"USD ${val:,.0f}"
    else:
        return val

# Aplicar formato
df_format = df_resumen_final.copy()
for fila in df_format.index:
    df_format.loc[fila] = df_format.loc[fila].apply(lambda val: formatear_valores(val, fila))

# Mostrar tabla estilizada
st.dataframe(
    df_format.style
        .apply(style_table, axis=None)
        .set_properties(**{"border": "1px solid #DDD", "font-size": "12px"})
)


# --- EXPORTAR A EXCEL ---
excel_buffer = io.BytesIO()
with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
    df_resumen.to_excel(writer, sheet_name='Resumen')

st.download_button(
    label="⬇️ Descargar resumen en Excel",
    data=excel_buffer.getvalue(),
    file_name="resumen_presupuesto.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# Gráfico
st.subheader("📈 Ingresos por línea de negocio")

fig, ax = plt.subplots(figsize=(12, 5))

# Formateo del eje x como 'Jun-25'
df_plot = df_filtrado.copy()
df_plot["Fechas"] = df_plot["Fecha"].dt.strftime("%b-%y")
df_plot.set_index("Fechas", inplace=True)
df_plot = df_plot[[ 
    "Ingreso Orquestación", "Ingreso Financiamiento", "Ingreso FX",
    "Ingreso Seguro Crédito", "Ingreso Seguro Carga",
    "Ingreso Navieras", "Ingreso Pago Proveedores", "Ingreso Pago Inland"
]]

df_plot.plot(kind="bar", stacked=True, ax=ax)
ax.set_ylabel("USD")
ax.set_title("Ingresos mensuales por línea de negocio")
ax.tick_params(axis='x', rotation=45)

st.pyplot(fig)

