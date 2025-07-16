# -*- coding: utf-8 -*-
"""
Created on Wed Jul 16 08:54:45 2025

@author: Pablo Martinez
"""
# PRESUPUESTO PROYECTADO - DASHBOARD STREAMLIT
import streamlit as st
import pandas as pd
import datetime
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("📊 Dashboard Presupuesto Proyectado")

# --- PARÁMETROS GENERALES ---
st.sidebar.header("⚙️ Parámetros Generales")
fecha_inicio = st.sidebar.date_input("📅 Fecha de inicio", datetime.date(2025, 1, 1))
periodos = 24
fechas = [fecha_inicio + pd.DateOffset(months=i) for i in range(periodos)]

# --- FILTRO DE PERIODO ---
st.sidebar.header("📅 Filtro de periodo a visualizar")
opcion_periodo = st.sidebar.radio("Selecciona periodo:", ["Todo", "Año 2025", "Próximo trimestre", "Primer semestre"])

# --- ORQUESTACIÓN ---
st.sidebar.header("📦 Orquestación")
unidad_base = st.sidebar.radio("Unidad base:", ["Container", "TEU"])
if unidad_base == "Container":
    containers_inicial = st.sidebar.number_input("Containers iniciales", value=20000)
    teus_inicial = containers_inicial * 2
else:
    teus_inicial = st.sidebar.number_input("TEUs iniciales", value=40000)
    containers_inicial = teus_inicial / 2

precio_orquestacion = st.sidebar.number_input("💰 Precio por orquestación (USD/container)", value=5.0)
crecimiento_orquestacion = st.sidebar.slider("📈 Crecimiento mensual carga (%)", 0.0, 10.0, 3.0) / 100
containers_proyectados = [containers_inicial * ((1 + crecimiento_orquestacion) ** i) for i in range(periodos)]
ingreso_orquestacion = [round(c * precio_orquestacion, 2) for c in containers_proyectados]

# DataFrame base
df = pd.DataFrame({
    "Fecha": fechas,
    "Containers": containers_proyectados,
    "Ingreso Orquestación": ingreso_orquestacion
})

# --- FINANCIAMIENTO ---
st.sidebar.header("💸 Financiamiento")
mes_inicio_fin = st.sidebar.slider("🕒 Mes inicio financiamiento", 0, 24, 2)
pct_fin = st.sidebar.slider("📦 % carga financiada", 0.0, 100.0, 40.0) / 100
margen_fin = st.sidebar.slider("💵 Margen ganado (%)", 0.0, 10.0, 0.3) / 100
monto_fin = df["Containers"] * precio_orquestacion * pct_fin
ingreso_fin = monto_fin * margen_fin
df["Monto Financiado"] = [m if i >= mes_inicio_fin else 0 for i, m in enumerate(monto_fin)]
df["Ingreso Financiamiento"] = [i if j >= mes_inicio_fin else 0 for j, i in enumerate(ingreso_fin)]

# --- FX ---
st.sidebar.header("💱 FX")
mes_inicio_fx = st.sidebar.slider("🕒 Mes inicio FX", 0, 24, 3)
fx_base = st.sidebar.radio("Base FX:", ["Monto financiado", "Valor orquestado", "Ambos"])
spread_fx = st.sidebar.number_input("🪙 Spread promedio (USD/USD)", value=0.05)

if fx_base == "Monto financiado":
    pct_fx = st.sidebar.slider("💸 % financiamiento que pasa por FX", 0.0, 100.0, 80.0) / 100
    vol_fx = df["Monto Financiado"] * pct_fx
elif fx_base == "Valor orquestado":
    pct_fx_o = st.sidebar.slider("📦 % orquestación que pasa por FX", 0.0, 100.0, 5.0) / 100
    vol_fx = df["Containers"] * precio_orquestacion * pct_fx_o
else:
    pct_fx = st.sidebar.slider("💸 % financiamiento que pasa por FX", 0.0, 100.0, 80.0) / 100
    pct_fx_o = st.sidebar.slider("📦 % orquestación que pasa por FX", 0.0, 100.0, 5.0) / 100
    vol_fx = df["Monto Financiado"] * pct_fx + df["Containers"] * precio_orquestacion * pct_fx_o

ingreso_fx = vol_fx * spread_fx
df["Volumen FX"] = vol_fx
df["Ingreso FX"] = [i if j >= mes_inicio_fx else 0 for j, i in enumerate(ingreso_fx)]

# --- SEGURO CRÉDITO ---
st.sidebar.header("🔐 Seguro de Crédito")
mes_inicio_sc = st.sidebar.slider("🕒 Mes inicio seguro crédito", 0, 24, 4)
pct_aseg_sc = st.sidebar.slider("🔒 % monto financiado asegurado", 0.0, 100.0, 80.0) / 100
prima_sc = st.sidebar.slider("💰 Prima (% del monto asegurado)", 0.3, 0.5, 0.4) / 100
comision_sc = st.sidebar.slider("💵 Comisión ganada (%)", 0.0, 10.0, 5.0) / 100

monto_asegurado_sc = df["Monto Financiado"] * pct_aseg_sc
ingreso_sc = monto_asegurado_sc * prima_sc * comision_sc
df["Ingreso Seguro Crédito"] = [i if j >= mes_inicio_sc else 0 for j, i in enumerate(ingreso_sc)]

# --- SEGURO CARGA ---
st.sidebar.header("📦 Seguro de Carga")
mes_inicio_sca = st.sidebar.slider("🕒 Mes inicio seguro carga", 0, 24, 6)
pct_aseg_sca = st.sidebar.slider("📦 % carga asegurada", 0.0, 100.0, 60.0) / 100
prima_sca = st.sidebar.slider("💰 Prima (% del valor carga)", 0.05, 0.15, 0.10) / 100
comision_sca = st.sidebar.slider("💵 Comisión ganada (%)", 0.0, 10.0, 4.0) / 100

valor_carga = df["Containers"] * precio_orquestacion
monto_asegurado_sca = valor_carga * pct_aseg_sca
ingreso_sca = monto_asegurado_sca * prima_sca * comision_sca
df["Ingreso Seguro Carga"] = [i if j >= mes_inicio_sca else 0 for j, i in enumerate(ingreso_sca)]

# --- PAGOS NAVIERAS ---
st.sidebar.header("🚢 Pagos a Navieras")
mes_inicio_nav = st.sidebar.slider("🕒 Mes inicio pagos navieras", 0, 24, 6)
pct_part_nav = st.sidebar.slider("📊 % participación sobre pagos posibles", 0.0, 100.0, 30.0) / 100
flete_prom = st.sidebar.number_input("🚢 Flete promedio (USD)", value=100000.0)
ingreso_fijo_nav = st.sidebar.number_input("💵 Ingreso fijo por pago", value=20.0)
comision_nav = st.sidebar.slider("💰 Comisión sobre monto pagado (%)", 0.0, 5.0, 1.0) / 100

monto_fletes = valor_carga * 0.10
n_pagos_max = monto_fletes / flete_prom
n_pagos_real = n_pagos_max * pct_part_nav
ingreso_nav_fijo = n_pagos_real * ingreso_fijo_nav
ingreso_nav_var = monto_fletes * pct_part_nav * comision_nav
ingreso_nav_total = ingreso_nav_fijo + ingreso_nav_var
df["Ingreso Navieras"] = [i if j >= mes_inicio_nav else 0 for j, i in enumerate(ingreso_nav_total)]

# --- OTROS PAGOS ---
st.sidebar.header("📂 Otros Pagos")
mes_inicio_otros = st.sidebar.slider("🕒 Mes inicio otros pagos", 0, 24, 8)
pct_part_otros = st.sidebar.slider("📊 % participación sobre tope", 0.0, 100.0, 50.0) / 100
tope_otros = 0.05
pago_prom_otros = st.sidebar.number_input("🧾 Monto promedio pago", value=50000.0)
ingreso_fijo_otros = st.sidebar.number_input("💵 Ingreso fijo por transacción", value=15.0)
comision_otros = st.sidebar.slider("💰 Comisión sobre monto (%)", 0.0, 10.0, 2.0) / 100

monto_otros_max = valor_carga * tope_otros
n_pagos_otros = monto_otros_max / pago_prom_otros * pct_part_otros
ingreso_otros = n_pagos_otros * ingreso_fijo_otros + monto_otros_max * pct_part_otros * comision_otros
df["Ingreso Otros"] = [i if j >= mes_inicio_otros else 0 for j, i in enumerate(ingreso_otros)]

# --- FILTRO DE PERIODO ---
if opcion_periodo == "Todo":
    df_filtrado = df.copy()
elif opcion_periodo == "Año 2025":
    df_filtrado = df[df["Fecha"].dt.year == 2025]
elif opcion_periodo == "Próximo trimestre":
    df_filtrado = df.iloc[:3]
elif opcion_periodo == "Primer semestre":
    df_filtrado = df.iloc[:6]
else:
    df_filtrado = df.copy()

# --- KPIs ---
st.subheader("📌 KPIs del periodo seleccionado")
col1, col2, col3 = st.columns(3)
col1.metric("Total Containers", f"{df_filtrado['Containers'].sum():,.0f}")
col2.metric("Ingreso Orquestación", f"${df_filtrado['Ingreso Orquestación'].sum():,.0f}")
col3.metric("Monto Financiado", f"${df_filtrado['Monto Financiado'].sum():,.0f}")

col4, col5, col6 = st.columns(3)
col4.metric("Ingreso Financiamiento", f"${df_filtrado['Ingreso Financiamiento'].sum():,.0f}")
col5.metric("Ingreso FX", f"${df_filtrado['Ingreso FX'].sum():,.0f}")
col6.metric("Ingreso Seguro Crédito", f"${df_filtrado['Ingreso Seguro Crédito'].sum():,.0f}")

col7, col8, col9 = st.columns(3)
col7.metric("Ingreso Seguro Carga", f"${df_filtrado['Ingreso Seguro Carga'].sum():,.0f}")
col8.metric("Ingreso Navieras", f"${df_filtrado['Ingreso Navieras'].sum():,.0f}")
col9.metric("Ingreso Otros", f"${df_filtrado['Ingreso Otros'].sum():,.0f}")

# ... (todo el código anterior se mantiene igual hasta la línea del DataFrame df_filtrado)

# --- TABLA RESUMEN (TRANSPUESTA) ---
df_filtrado["Total Ingresos"] = df_filtrado[[
    "Ingreso Orquestación", "Ingreso Financiamiento", "Ingreso FX",
    "Ingreso Seguro Crédito", "Ingreso Seguro Carga",
    "Ingreso Navieras", "Ingreso Otros"
]].sum(axis=1)

st.subheader("📋 Resumen transpuesto por línea de negocio")
df_resumen = df_filtrado.set_index("Fecha")[[
    "Ingreso Orquestación", "Ingreso Financiamiento", "Ingreso FX",
    "Ingreso Seguro Crédito", "Ingreso Seguro Carga",
    "Ingreso Navieras", "Ingreso Otros", "Total Ingresos"
]].transpose()
df_resumen.index.name = "Línea de Negocio"
st.dataframe(df_resumen.style.format("USD ${:,.0f}"))

# --- EXPORTAR A EXCEL ---
import io
excel_buffer = io.BytesIO()
with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
    df_resumen.to_excel(writer, sheet_name='Resumen')

st.download_button(
    label="⬇️ Descargar resumen en Excel",
    data=excel_buffer.getvalue(),
    file_name="resumen_presupuesto.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# --- GRÁFICO DE INGRESOS ---
st.subheader("📈 Ingresos por línea de negocio")
fig, ax = plt.subplots(figsize=(12, 5))
df_plot = df_filtrado.set_index("Fecha")[[
    "Ingreso Orquestación", "Ingreso Financiamiento", "Ingreso FX",
    "Ingreso Seguro Crédito", "Ingreso Seguro Carga",
    "Ingreso Navieras", "Ingreso Otros"
]]
df_plot.plot(kind="bar", stacked=True, ax=ax)
ax.set_ylabel("USD")
ax.set_title("Ingresos mensuales por línea de negocio")
st.pyplot(fig)
