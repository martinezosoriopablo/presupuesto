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
fecha_inicio = st.sidebar.date_input("📅 Fecha de inicio", datetime.date(2025, 8, 1))
fecha_inicio = pd.to_datetime(fecha_inicio)

periodos = 25
fechas = [fecha_inicio + pd.DateOffset(months=i) for i in range(periodos)]

# --- FILTRO DE PERIODO ---
st.sidebar.header("📅 Filtro de periodo a visualizar")
opcion_periodo = st.sidebar.radio(
    "Selecciona periodo:",
    ["Todo", "Año 2025", "Año 2026", "Próximo trimestre", "Próximo semestre", "Próximos 24 meses"],
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
# Fechas de proyección: desde julio 2025 en adelante
fecha_inicio = pd.to_datetime("2025-08-01")
periodos = 25
fechas = [fecha_inicio + pd.DateOffset(months=i) for i in range(periodos)]

# Proyección con crecimiento anual acumulativo por mes
for i, fecha in enumerate(fechas):
    mes_idx = i + 18  # 18 valores reales hasta junio 2025
    año_anterior_idx = mes_idx - 12

    if año_anterior_idx < len(containers_reales):
        base = containers_reales[año_anterior_idx]
    else:
        base = containers_reales[año_anterior_idx]

    nuevo_valor = round(base * (1 + crecimiento_anual), 2)
    containers_reales.append(nuevo_valor)

containers_proyectados = containers_reales[18:]  # Solo proyecciones desde julio 2025



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
# --- Valores base predeterminados (ago-2025 a dic-2026) ---
valores_base = [
    500000, 500000, 1000000, 1500000, 4500000, 4500000, 4500000, 6500000,
    8500000, 10500000, 12500000, 14500000, 16500000, 18000000,
    20000000, 20000000, 20000000, 20000000,20000000,20000000,20000000,20000000,20000000,20000000,20000000
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

spread_fx_pct = st.sidebar.number_input("🪙 Spread promedio (% sobre USD)", value=0.20, step=0.01, format="%.2f")
spread_fx = spread_fx_pct / 100
precio_contenedor = st.sidebar.number_input("💲 Precio por container (USD)", value=30000)

# --- Tasas de crecimiento mensual por año ---
st.sidebar.subheader("📆 Crecimiento mensual FX por año")
crecimiento_fx_mes_2025 = st.sidebar.slider("🔹 2025 (% mensual)", 0.0, 100.0, 35.0) / 100
crecimiento_fx_mes_2026 = st.sidebar.slider("🔹 2026 (% mensual)", 0.0, 100.0, 20.0) / 100
crecimiento_fx_mes_2027 = st.sidebar.slider("🔹 2027 (% mensual)", 0.0, 100.0, 10.0) / 100

# --- Función para obtener crecimiento según año ---
def tasa_mensual(fecha):
    if fecha.year == 2025:
        return crecimiento_fx_mes_2025
    elif fecha.year == 2026:
        return crecimiento_fx_mes_2026
    elif fecha.year == 2027:
        return crecimiento_fx_mes_2027
    else:
        return 0.0

# --- Calcular FX base inicial según la opción seleccionada ---
def calcular_fx(base_inicial):
    for i in range(periodos):
        if i < mes_inicio_fx:
            vol_fx.append(0)
        elif i == mes_inicio_fx:
            vol_fx.append(base_inicial)
        else:
            crecimiento = tasa_mensual(fechas[i])
            vol_fx.append(vol_fx[-1] * (1 + crecimiento))

vol_fx = []

# --- Determinar base inicial según opción elegida ---
if fx_base == "Valor inicial":
    fx_inicial = st.sidebar.number_input("📍 Volumen FX inicial (USD)", value=1_000_000)
    calcular_fx(fx_inicial)

elif fx_base == "Monto financiado":
    pct_fx = st.sidebar.slider("💸 % del monto financiado que pasa por FX", 0.0, 100.0, 80.0) / 100
    base_inicial = df["Monto Financiado"][mes_inicio_fx] * pct_fx
    calcular_fx(base_inicial)

elif fx_base == "Valor orquestado":
    pct_fx_o = st.sidebar.slider("📦 % de la orquestación que pasa por FX", 0.0, 100.0, 5.0) / 100
    base_inicial = df["Containers"][mes_inicio_fx] * precio_contenedor * pct_fx_o
    calcular_fx(base_inicial)

else:
    pct_fx = st.sidebar.slider("💸 % del monto financiado que pasa por FX", 0.0, 100.0, 80.0) / 100
    pct_fx_o = st.sidebar.slider("📦 % de la orquestación que pasa por FX", 0.0, 100.0, 5.0) / 100
    base_f = df["Monto Financiado"][mes_inicio_fx] * pct_fx
    base_o = df["Containers"][mes_inicio_fx] * precio_contenedor * pct_fx_o
    base_total = base_f + base_o
    calcular_fx(base_total)

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
comision_nav = st.sidebar.slider("💰 Comisión sobre monto pagado (%)", 0.0, 1.5, 0.75) / 100

# Parte variable (comisión)
monto_fletes = valor_carga * 0.10
n_pagos_max = monto_fletes / flete_prom
ingreso_nav_var = [m * pct_part_nav * comision_nav if i >= mes_inicio_nav else 0 for i, m in enumerate(monto_fletes)]

# --- SUSCRIPCIÓN MÓDULO DE PAGOS ---
st.sidebar.header("🧾 Suscripción Módulo Auditoria Fletes")
mes_inicio_suscripcion = st.sidebar.slider("🕒 Mes inicio suscripción módulo", 0, periodos - 1, 2)
clientes_iniciales = st.sidebar.number_input("👥 Clientes iniciales", min_value=0, value=5)
crecimiento_clientes = st.sidebar.slider("📈 Crecimiento mensual clientes activos (%)", 0.0, 50.0, 20.0) / 100
precio_suscripcion = st.sidebar.number_input("💵 Precio mensual por cliente (USD)", value=150.0)

clientes_activos = []
for i in range(periodos):
    if i < mes_inicio_suscripcion:
        clientes_activos.append(0)
    elif i == mes_inicio_suscripcion:
        clientes_activos.append(clientes_iniciales)
    else:
        clientes_activos.append(clientes_activos[-1] * (1 + crecimiento_clientes))

ingreso_nav_fijo = [c * precio_suscripcion for c in clientes_activos]

# Guardar en DataFrame
df["Clientes Activos Módulo Fletes"] = [round(c) for c in clientes_activos]
df["Ingreso Modulo Auditoria Fletes"] = ingreso_nav_fijo

df["Ingreso Navieras Variable"] = ingreso_nav_var
df["Ingreso Navieras"] = df["Ingreso Modulo Auditoria Fletes"] + df["Ingreso Navieras Variable"]



# --- GATEWAY PAGO FACTURAS DE EXPORTACIÓN ---
st.sidebar.header("🏗️ Gateway Pago Facturas de Exportación")
mes_inicio_prov = st.sidebar.slider("🕒 Mes inicio gateway pago exportaciones", 0, periodos - 1, 3)
pct_prov = st.sidebar.slider("📦 % de carga orquestada que paga proveedores", 0.0, 20.0, 0.6) / 100
pct_uso_cliente_final = st.sidebar.slider("👥 % de clientes del cliente que usan el gateway", 0.0, 100.0, 100.0) / 100

monto_proveedor_base = []
ingreso_proveedores = []

# Asegurar existencia de clientes_acumulados
if "Clientes Activos Módulo Fletes" not in df.columns:
    df["Clientes Activos Módulo Fletes"] = [0] * periodos

clientes_modulo = df["Clientes Activos Módulo Fletes"]
total_clientes_mes = max(max(clientes_modulo), 1)  # evitar división por 0

for i in range(periodos):
    if i < mes_inicio_prov or clientes_modulo[i] == 0:
        monto_proveedor_base.append(0)
        ingreso_proveedores.append(0)
    else:
        proporcion_clientes = clientes_modulo[i] / total_clientes_mes
        carga_asociada = df["Containers"][i] * proporcion_clientes
        carga_efectiva = carga_asociada * pct_uso_cliente_final

        base = carga_efectiva * precio_contenedor * pct_prov
        monto_proveedor_base.append(base)
        ingreso_proveedores.append(base * spread_fx)

df["Monto Gateway Proveedores"] = monto_proveedor_base
df["Ingreso Gateway Proveedores"] = ingreso_proveedores



# --- GATEWAY INLAND ---
st.sidebar.header("🚚 Gateway Inland (Pago Local)")
mes_inicio_inland = st.sidebar.slider("🕒 Mes inicio Inland", 0, periodos - 1, 3)
pct_part_inland = st.sidebar.slider("📦 % de carga que contrata Inland", 0.0, 20.0, 10.0) / 100
precio_inland = st.sidebar.number_input("💲 Precio por contenedor Inland (USD)", value=2.0)

# Cálculo: contenedores que usan Inland
containers_inland = df["Containers"] * pct_part_inland

# Ingreso: contenedores Inland * precio fijo
ingreso_inland = containers_inland * precio_inland

# Aplicar desde mes de inicio
df["Containers Inland"] = containers_inland
df["Ingreso Pago Inland"] = [ing if i >= mes_inicio_inland else 0 for i, ing in enumerate(ingreso_inland)]
df["Monto Pago Inland"] = containers_inland *precio_contenedor




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

elif opcion_periodo == "Próximos 24 meses":
    df_filtrado = df[(df["Fecha"] >= fecha_inicio) & (df["Fecha"] < fecha_inicio + pd.DateOffset(months=25))]



# --- CÁLCULOS Y COLUMNAS PERSONALIZADAS ---

# Recalculo de valores base
df_filtrado["Monto Asegurado SC"] = valor_carga * pct_aseg_sc
df_filtrado["Monto Asegurado SCA"] = valor_carga * pct_aseg_sca
df_filtrado["Monto Pagado Navieras"] = valor_carga * 0.10 * pct_part_nav

df_filtrado["Containers Orquestados"] = df_filtrado["Containers"]
df_filtrado["Monto Financiado Total"] = df_filtrado["Monto Financiado"]
df_filtrado["Volumen FX Total"] = df_filtrado["Volumen FX"]

# Agregar columnas de navieras y proveedores
df_filtrado["Ingreso Modulo Auditoria Fletes"] = df["Ingreso Modulo Auditoria Fletes"]
df_filtrado["Ingreso Navieras Variable"] = df["Ingreso Navieras Variable"]
df_filtrado["Ingreso Navieras"] = df["Ingreso Navieras"]
df_filtrado["Monto Gateway Proveedores"] = df["Monto Gateway Proveedores"]
df_filtrado["Ingreso Gateway Proveedores"] = df["Ingreso Gateway Proveedores"]
df_filtrado["Monto Pago Inland"] = df["Monto Pago Inland"]
df_filtrado["Ingreso Pago Inland"] = df["Ingreso Pago Inland"]

# Total ingresos
df_filtrado["Total Ingresos"] = df_filtrado[[
    "Ingreso Orquestación", "Ingreso Financiamiento", "Ingreso FX",
    "Ingreso Seguro Crédito", "Ingreso Seguro Carga",
    "Ingreso Navieras", "Ingreso Gateway Proveedores", "Ingreso Pago Inland"
]].sum(axis=1)

# --- KPIs del periodo seleccionado ---
st.subheader("📌 KPIs del periodo seleccionado")
st.markdown("---")

# Función para renderizar cada fila
def render_kpi_row(icon, title, label1, val1, label2, val2, label3, val3):
    col0, col1, col2, col3 = st.columns([2, 2.5, 2.5, 2.5])
    with col0:
        st.markdown(f"### {icon} **{title}**")
    with col1:
        st.metric(label1, val1)
    with col2:
        st.metric(label2, val2)
    with col3:
        st.metric(label3, val3)
    st.markdown("<hr style='border-top: 1px dashed #DDD;'>", unsafe_allow_html=True)
# --- Cálculo de KPIs base ---
total_containers = df_filtrado['Containers'].sum()
ingreso_orquestacion = df_filtrado["Ingreso Orquestación"].sum()
margen_orquestacion = ingreso_orquestacion / (total_containers * precio_contenedor) * 100 if total_containers > 0 else 0

monto_fin = df_filtrado['Monto Financiado'].sum()
ingreso_fin = df_filtrado['Ingreso Financiamiento'].sum()
margen_fin = ingreso_fin / monto_fin * 100 if monto_fin != 0 else 0

vol_fx = df_filtrado['Volumen FX'].sum()
ingreso_fx = df_filtrado['Ingreso FX'].sum()
margen_fx = ingreso_fx / vol_fx * 100 if vol_fx != 0 else 0

monto_sc = df_filtrado['Monto Asegurado SC'].sum()
ingreso_sc = df_filtrado['Ingreso Seguro Crédito'].sum()
margen_sc = ingreso_sc / monto_sc * 100 if monto_sc != 0 else 0

monto_sca = df_filtrado['Monto Asegurado SCA'].sum()
ingreso_sca = df_filtrado['Ingreso Seguro Carga'].sum()
margen_sca = ingreso_sca / monto_sca * 100 if monto_sca != 0 else 0

monto_nav = df_filtrado['Monto Pagado Navieras'].sum()
ingreso_nav = df_filtrado['Ingreso Navieras'].sum()
margen_nav = ingreso_nav / monto_nav * 100 if monto_nav != 0 else 0

monto_prov = df_filtrado['Monto Gateway Proveedores'].sum()
ingreso_prov = df_filtrado['Ingreso Gateway Proveedores'].sum()
margen_prov = ingreso_prov / monto_prov * 100 if monto_prov != 0 else 0

monto_inland = df_filtrado['Monto Pago Inland'].sum()
ingreso_inland = df_filtrado['Ingreso Pago Inland'].sum()
margen_inland = ingreso_inland / monto_inland * 100 if monto_inland != 0 else 0

# --- KPIs por línea de negocio (respetando tus nombres) ---
render_kpi_row("📦", "Orquestación",
    "Total Containers", f"{total_containers:,.0f}",
    "Ingreso Orquestación", f"USD ${ingreso_orquestacion:,.0f}",
    "Margen Orquestación", f"{margen_orquestacion:.2f}%"
)

render_kpi_row("💸", "Financiamiento",
    "Monto Financiado", f"USD ${monto_fin:,.0f}",
    "Ingreso Financiamiento", f"USD ${ingreso_fin:,.0f}",
    "Margen Financiamiento", f"{margen_fin:.2f}%"
)

render_kpi_row("💱", "FX",
    "Volumen FX", f"USD ${vol_fx:,.0f}",
    "Ingreso FX", f"USD ${ingreso_fx:,.0f}",
    "Margen FX", f"{margen_fx:.2f}%"
)

render_kpi_row("🛡️", "Seguro Crédito",
    "Monto Asegurado", f"USD ${monto_sc:,.0f}",
    "Ingreso Seguro Crédito", f"USD ${ingreso_sc:,.0f}",
    "Margen Seguro Crédito", f"{margen_sc:.2f}%"
)

render_kpi_row("📦", "Seguro de Carga",
    "Monto Asegurado", f"USD ${monto_sca:,.0f}",
    "Ingreso Seguro Carga", f"USD ${ingreso_sca:,.0f}",
    "Margen Seguro Carga", f"{margen_sca:.3f}%"
)

render_kpi_row("🚢", "Pago a Navieras",
    "Monto Pagado", f"USD ${monto_nav:,.0f}",
    "Ingreso Navieras", f"USD ${ingreso_nav:,.0f}",
    "Margen Navieras", f"{margen_nav:.2f}%"
)

render_kpi_row("🏗️", "Gateway de Pago",
    "Monto Gateway", f"USD ${monto_prov:,.0f}",
    "Ingreso Proveedores", f"USD ${ingreso_prov:,.0f}",
    "Margen Proveedores", f"{margen_prov:.2f}%"
)

render_kpi_row("🚚", "Inland",
    "Monto Inland", f"USD ${monto_inland:,.0f}",
    "Ingreso Inland", f"USD ${ingreso_inland:,.0f}",
    "Margen Inland", f"{margen_inland:.2f}%"
)


total_ingresos= (
    ingreso_orquestacion + ingreso_fin + ingreso_fx +
    ingreso_sc + ingreso_sca + ingreso_nav + ingreso_prov + ingreso_inland)
total_ingresos_orquestacion= ingreso_orquestacion 

total_ingresos_financieros= ( ingreso_fin + ingreso_fx +
    ingreso_sc + ingreso_sca + ingreso_nav + ingreso_prov + ingreso_inland)

usd_x_container_orq= total_ingresos_orquestacion/ total_containers if total_containers != 0 else 0
usd_x_container_fin= total_ingresos_financieros/ total_containers if total_containers != 0 else 0
render_kpi_row("📈","KPIs Globales",
    "Total Ingresos", f"USD ${total_ingresos:,.0f}",
    "USD por Contenedor Orquestacion", f"USD ${usd_x_container_orq:,.2f}",    
    "USD por Contenedor Prod. Fin.", f"USD ${usd_x_container_fin:,.2f}")
 





# Crear resumen transpuesto desde df_filtrado
df_resumen = df_filtrado.set_index("Fecha")[[ 
    "Containers Orquestados", "Ingreso Orquestación",
    "Monto Financiado Total", "Ingreso Financiamiento",
    "Volumen FX Total", "Ingreso FX",
    "Monto Asegurado SC", "Ingreso Seguro Crédito",
    "Monto Asegurado SCA", "Ingreso Seguro Carga",
    "Monto Pagado Navieras", "Ingreso Modulo Auditoria Fletes", "Ingreso Navieras Variable", "Ingreso Navieras",
    "Monto Gateway Proveedores", "Ingreso Gateway Proveedores",
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
    "🔷 NAVIERAS": ["Monto Pagado Navieras", "Ingreso Modulo Auditoria Fletes", "Ingreso Navieras Variable", "Ingreso Navieras"],
    "🔷 PROVEEDORES": ["Monto Gateway Proveedores", "Ingreso Gateway Proveedores", "Monto Pago Inland", "Ingreso Pago Inland"]
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



col1, col2 = st.columns(2)

# ---------- Gráfico Mensual ----------
with col1:
    st.markdown("#### 📅 Ingresos Mensuales")
    df_plot_mes = df_filtrado.copy()
    df_plot_mes["Fechas"] = df_plot_mes["Fecha"].dt.strftime("%b-%y")
    df_plot_mes.set_index("Fechas", inplace=True)
    df_plot_mes = df_plot_mes[[ 
        "Ingreso Orquestación", "Ingreso Financiamiento", "Ingreso FX",
        "Ingreso Seguro Crédito", "Ingreso Seguro Carga",
        "Ingreso Navieras", "Ingreso Gateway Proveedores", "Ingreso Pago Inland"
    ]]
    fig1, ax1 = plt.subplots(figsize=(10, 5))
    df_plot_mes.plot(kind="bar", stacked=True, ax=ax1)
    ax1.set_ylabel("USD")
    ax1.set_title("Mensual")
    ax1.tick_params(axis='x', rotation=45)
    st.pyplot(fig1)

# ---------- Gráfico Trimestral ----------
with col2:
    st.markdown("#### 🗓️ Ingresos Trimestrales")
    df_plot_trim = df_filtrado.copy()
    df_plot_trim["Trimestre"] = df_plot_trim["Fecha"].dt.to_period("Q").astype(str).str.replace("Q", "T")
    df_trim_grouped = df_plot_trim.groupby("Trimestre")[[
        "Ingreso Orquestación", "Ingreso Financiamiento", "Ingreso FX",
        "Ingreso Seguro Crédito", "Ingreso Seguro Carga",
        "Ingreso Navieras", "Ingreso Gateway Proveedores", "Ingreso Pago Inland"
    ]].sum()
    fig2, ax2 = plt.subplots(figsize=(10, 5))
    df_trim_grouped.plot(kind="bar", stacked=True, ax=ax2)
    ax2.set_ylabel("USD")
    ax2.set_title("Trimestral")
    ax2.tick_params(axis='x', rotation=0)
    st.pyplot(fig2)


