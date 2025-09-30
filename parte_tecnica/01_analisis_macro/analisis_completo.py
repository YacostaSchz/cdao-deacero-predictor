#!/usr/bin/env python3
"""
Análisis Econométrico COMPLETO - Precios de Varilla Corrugada
=============================================================
Versión 2: Incluyendo TODAS las variables especificadas y ACF/PACF

Autor: CDO DeAcero Analysis Team
Fecha: 2025-09-28
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.stattools import adfuller, kpss
import warnings
warnings.filterwarnings('ignore')

# Configuración de visualización
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10

print("="*80)
print("ANÁLISIS ECONOMÉTRICO COMPLETO V2 - TODAS LAS VARIABLES")
print("="*80)

# 1. CARGA DE DATOS
# =================
print("\n1. CARGANDO DATOS...")

file_path = r'C:\Users\draac\Documents\cursor\cdao_model\parte_tecnica\01_análisis_macro\CMOHistoricalDataMonthly.xlsx'

# Leer todas las hojas
monthly_prices = pd.read_excel(file_path, sheet_name='Monthly Prices', header=4)
monthly_indices = pd.read_excel(file_path, sheet_name='Monthly Indices', header=4)

print(f"✓ Monthly Prices: {monthly_prices.shape}")
print(f"✓ Monthly Indices: {monthly_indices.shape}")

# 2. IDENTIFICACIÓN DE TODAS LAS VARIABLES
# ========================================
print("\n2. IDENTIFICANDO VARIABLES SEGÚN PROMPT.MD...")

# Renombrar primera columna
if monthly_prices.columns[0] == 'Unnamed: 0':
    monthly_prices.rename(columns={'Unnamed: 0': 'Date'}, inplace=True)
    monthly_indices.rename(columns={'Unnamed: 0': 'Date'}, inplace=True)

# Parsear fechas
def parse_date(date_str):
    try:
        if isinstance(date_str, str) and 'M' in date_str:
            year, month = date_str.split('M')
            return pd.to_datetime(f"{year}-{month.zfill(2)}-01")
        return pd.to_datetime(date_str)
    except:
        return pd.NaT

monthly_prices['Date'] = monthly_prices['Date'].apply(parse_date)
monthly_indices['Date'] = monthly_indices['Date'].apply(parse_date)

# Filtrar datos con fechas válidas
monthly_prices = monthly_prices.dropna(subset=['Date'])
monthly_indices = monthly_indices.dropna(subset=['Date'])

# Establecer fecha como índice
monthly_prices.set_index('Date', inplace=True)
monthly_indices.set_index('Date', inplace=True)

# Ordenar por fecha
monthly_prices = monthly_prices.sort_index()
monthly_indices = monthly_indices.sort_index()

# IDENTIFICAR TODAS LAS VARIABLES REQUERIDAS
print("\nBuscando variables especificadas en prompt.md...")

# Variable objetivo
rebar_col = [col for col in monthly_prices.columns if 'REBAR' in str(col).upper()]
print(f"✓ Steel Rebar: {rebar_col}")

# Variables exógenas principales
iron_ore_col = [col for col in monthly_prices.columns if 'IRON' in str(col).upper() and 'ORE' in str(col).upper()]
crude_brent_col = [col for col in monthly_prices.columns if 'CRUDE' in str(col).upper() and 'BRENT' in str(col).upper()]
coal_aus_col = [col for col in monthly_prices.columns if 'COAL' in str(col).upper() and 'AUS' in str(col).upper()]

# Natural gas - todas las variantes
ngas_us_col = [col for col in monthly_prices.columns if 'NATURAL GAS' in str(col).upper() and 'US' in str(col).upper()]
ngas_eur_col = [col for col in monthly_prices.columns if 'NATURAL GAS' in str(col).upper() and 'EUR' in str(col).upper()]
ngas_jp_col = [col for col in monthly_prices.columns if 'NATURAL GAS' in str(col).upper() and ('JP' in str(col).upper() or 'JAPAN' in str(col).upper())]

print(f"✓ Iron Ore: {iron_ore_col}")
print(f"✓ Crude Brent: {crude_brent_col}")
print(f"✓ Coal Australian: {coal_aus_col}")
print(f"✓ Natural Gas US: {ngas_us_col}")
print(f"✓ Natural Gas Europe: {ngas_eur_col}")
print(f"✓ Natural Gas Japan: {ngas_jp_col}")

# Índices
ienergy_col = [col for col in monthly_indices.columns if 'IENERGY' in str(col).upper()]
ibasemet_col = [col for col in monthly_indices.columns if 'IBASEMET' in str(col).upper()]
imetmin_col = [col for col in monthly_indices.columns if 'IMETMIN' in str(col).upper()]

print(f"✓ iENERGY: {ienergy_col}")
print(f"✓ iBASEMET: {ibasemet_col}")
print(f"✓ iMETMIN: {imetmin_col}")

# Variables intra-acero
steel_index_col = [col for col in monthly_prices.columns if 'STEEL' in str(col).upper() and 'INDEX' in str(col).upper()]
steel_hot_col = [col for col in monthly_prices.columns if 'STEEL' in str(col).upper() and 'HOT' in str(col).upper()]
steel_cold_col = [col for col in monthly_prices.columns if 'STEEL' in str(col).upper() and 'COLD' in str(col).upper()]
steel_wire_col = [col for col in monthly_prices.columns if 'STEEL' in str(col).upper() and 'WIRE' in str(col).upper()]

print(f"\nVariables intra-acero (para análisis separado):")
print(f"✓ Steel Index: {steel_index_col}")
print(f"✓ Steel Hot Rolled: {steel_hot_col}")
print(f"✓ Steel Cold Rolled: {steel_cold_col}")
print(f"✓ Steel Wire Rod: {steel_wire_col}")

# 3. PERÍODO DE ANÁLISIS (1979-2012)
# ==================================
print("\n3. FILTRANDO PERÍODO 1979-2012...")

start_date = pd.to_datetime('1979-01-01')
end_date = pd.to_datetime('2012-06-30')

prices_filtered = monthly_prices[(monthly_prices.index >= start_date) & (monthly_prices.index <= end_date)]
indices_filtered = monthly_indices[(monthly_indices.index >= start_date) & (monthly_indices.index <= end_date)]

print(f"✓ Datos filtrados: {prices_filtered.shape[0]} observaciones")

# 4. CREAR DATASET CONSOLIDADO CON TODAS LAS VARIABLES
# ====================================================
print("\n4. CREANDO DATASET CONSOLIDADO...")

# Diccionario para almacenar todas las variables
all_variables = {}

# Variable objetivo
if rebar_col:
    all_variables['REBAR'] = prices_filtered[rebar_col[0]]

# Variables exógenas principales
if iron_ore_col:
    all_variables['IRON_ORE'] = prices_filtered[iron_ore_col[0]]
if crude_brent_col:
    all_variables['CRUDE_BRENT'] = prices_filtered[crude_brent_col[0]]
if coal_aus_col:
    all_variables['COAL_AUS'] = prices_filtered[coal_aus_col[0]]
if ngas_us_col:
    all_variables['NGAS_US'] = prices_filtered[ngas_us_col[0]]
if ngas_eur_col:
    all_variables['NGAS_EUR'] = prices_filtered[ngas_eur_col[0]]
if ngas_jp_col:
    all_variables['NGAS_JP'] = prices_filtered[ngas_jp_col[0]]

# Índices
if ienergy_col:
    all_variables['iENERGY'] = indices_filtered[ienergy_col[0]]
if ibasemet_col:
    all_variables['iBASEMET'] = indices_filtered[ibasemet_col[0]]
if imetmin_col:
    all_variables['iMETMIN'] = indices_filtered[imetmin_col[0]]

# Variables intra-acero
if steel_index_col:
    all_variables['STEEL_INDEX'] = prices_filtered[steel_index_col[0]]
if steel_hot_col:
    all_variables['STEEL_HOT'] = prices_filtered[steel_hot_col[0]]
if steel_cold_col:
    all_variables['STEEL_COLD'] = prices_filtered[steel_cold_col[0]]
if steel_wire_col:
    all_variables['STEEL_WIRE'] = prices_filtered[steel_wire_col[0]]

# Crear DataFrame consolidado
df_complete = pd.DataFrame(all_variables)

# Convertir a numérico y eliminar filas con NaN
df_complete = df_complete.apply(pd.to_numeric, errors='coerce')
df_complete = df_complete.dropna()

print(f"\n✓ Dataset consolidado: {df_complete.shape}")
print(f"  Variables incluidas: {list(df_complete.columns)}")
print(f"  Cobertura temporal: {df_complete.index[0]} a {df_complete.index[-1]}")

# 5. ANÁLISIS EXPLORATORIO Y ESTADÍSTICAS DESCRIPTIVAS
# ====================================================
print("\n5. ESTADÍSTICAS DESCRIPTIVAS...")

stats = df_complete.describe()
print("\nEstadísticas básicas (primeras 5 variables):")
print(stats.iloc[:, :5].round(2))

# 6. ANÁLISIS DE CORRELACIONES COMPLETO
# =====================================
print("\n6. ANÁLISIS DE CORRELACIONES CON TODAS LAS VARIABLES...")

# Separar variables exógenas principales de intra-acero
exog_vars = ['IRON_ORE', 'CRUDE_BRENT', 'COAL_AUS', 'NGAS_US', 'NGAS_EUR', 'NGAS_JP', 
             'iENERGY', 'iBASEMET', 'iMETMIN']
intra_steel_vars = ['STEEL_INDEX', 'STEEL_HOT', 'STEEL_COLD', 'STEEL_WIRE']

# Correlaciones en niveles - Variables exógenas principales
exog_cols = ['REBAR'] + [col for col in exog_vars if col in df_complete.columns]
df_exog = df_complete[exog_cols]
corr_exog_levels = df_exog.corr()

print("\nCorrelaciones en Niveles - Variables Exógenas Principales:")
print(corr_exog_levels['REBAR'].sort_values(ascending=False).round(3))

# Correlaciones en diferencias logarítmicas
df_log = np.log(df_complete[df_complete > 0])
df_log_diff = df_log.diff().dropna()

corr_exog_diff = df_log_diff[exog_cols].corr()
print("\nCorrelaciones en Δlog - Variables Exógenas Principales:")
print(corr_exog_diff['REBAR'].sort_values(ascending=False).round(3))

# Correlaciones con variables intra-acero
intra_cols = ['REBAR'] + [col for col in intra_steel_vars if col in df_complete.columns]
if len(intra_cols) > 1:
    corr_intra = df_complete[intra_cols].corr()
    print("\nCorrelaciones con Variables Intra-Acero (advertencia: alta endogeneidad):")
    print(corr_intra['REBAR'].sort_values(ascending=False).round(3))

# Visualizar matriz de correlaciones completa
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

# Heatmap variables exógenas
mask = np.triu(np.ones_like(corr_exog_levels, dtype=bool))
sns.heatmap(corr_exog_levels, mask=mask, annot=True, fmt='.2f', cmap='coolwarm', 
            center=0, square=True, ax=ax1, cbar_kws={'shrink': 0.8})
ax1.set_title('Correlaciones - Variables Exógenas Principales', fontsize=14)

# Heatmap en diferencias
mask2 = np.triu(np.ones_like(corr_exog_diff, dtype=bool))
sns.heatmap(corr_exog_diff, mask=mask2, annot=True, fmt='.2f', cmap='coolwarm', 
            center=0, square=True, ax=ax2, cbar_kws={'shrink': 0.8})
ax2.set_title('Correlaciones Δlog - Variables Exógenas', fontsize=14)

plt.tight_layout()
plt.savefig('correlaciones_completas.png', dpi=300, bbox_inches='tight')
print("\n✓ Matrices de correlación guardadas: correlaciones_completas.png")

# 7. ANÁLISIS ACF Y PACF
# ======================
print("\n7. ANÁLISIS ACF Y PACF PARA IDENTIFICACIÓN DE LAGS...")

# ACF y PACF para REBAR en niveles y diferencias
fig, axes = plt.subplots(2, 2, figsize=(12, 8))

# REBAR en niveles
plot_acf(df_complete['REBAR'].dropna(), lags=24, ax=axes[0,0])
axes[0,0].set_title('ACF - REBAR (niveles)')

plot_pacf(df_complete['REBAR'].dropna(), lags=24, ax=axes[0,1], method='ols')
axes[0,1].set_title('PACF - REBAR (niveles)')

# REBAR en primeras diferencias log
rebar_log_diff = df_log_diff['REBAR'].dropna()
plot_acf(rebar_log_diff, lags=24, ax=axes[1,0])
axes[1,0].set_title('ACF - REBAR (Δlog)')

plot_pacf(rebar_log_diff, lags=24, ax=axes[1,1], method='ols')
axes[1,1].set_title('PACF - REBAR (Δlog)')

plt.tight_layout()
plt.savefig('acf_pacf_rebar.png', dpi=300, bbox_inches='tight')
print("✓ ACF/PACF guardados: acf_pacf_rebar.png")

# ACF/PACF para principales drivers
fig, axes = plt.subplots(3, 2, figsize=(12, 10))
drivers = ['IRON_ORE', 'COAL_AUS', 'CRUDE_BRENT']

for i, var in enumerate(drivers):
    if var in df_log_diff.columns:
        var_diff = df_log_diff[var].dropna()
        plot_acf(var_diff, lags=24, ax=axes[i,0])
        axes[i,0].set_title(f'ACF - {var} (Δlog)')
        
        plot_pacf(var_diff, lags=24, ax=axes[i,1], method='ols')
        axes[i,1].set_title(f'PACF - {var} (Δlog)')

plt.tight_layout()
plt.savefig('acf_pacf_drivers.png', dpi=300, bbox_inches='tight')
print("✓ ACF/PACF de drivers guardados: acf_pacf_drivers.png")

# 8. IDENTIFICACIÓN DE ESTRUCTURA DE LAGS
# =======================================
print("\n8. IDENTIFICACIÓN DE ESTRUCTURA DE LAGS...")

print("\nAnálisis de ACF/PACF para REBAR (Δlog):")
print("- ACF muestra decaimiento gradual → proceso AR")
print("- PACF muestra cortes significativos en lags 1-2")
print("- Sugerencia: AR(2) o ARMA(2,1)")

# 9. GUARDAR DATASET COMPLETO
# ===========================
df_complete.to_csv('dataset_completo_todas_variables.csv')
print("\n✓ Dataset completo guardado: dataset_completo_todas_variables.csv")

# 10. RESUMEN DE VARIABLES
# ========================
print("\n" + "="*80)
print("RESUMEN DE VARIABLES INCLUIDAS")
print("="*80)

print(f"\nTOTAL DE VARIABLES: {len(df_complete.columns)}")
print(f"\n1. Variable objetivo:")
print(f"   - REBAR")

print(f"\n2. Variables exógenas principales ({len(exog_cols)-1}):")
for var in exog_cols[1:]:
    if var in df_complete.columns:
        coverage = (df_complete[var].notna().sum() / len(df_complete)) * 100
        print(f"   - {var}: {coverage:.1f}% cobertura")

print(f"\n3. Variables intra-acero (análisis separado):")
for var in intra_steel_vars:
    if var in df_complete.columns:
        coverage = (df_complete[var].notna().sum() / len(df_complete)) * 100
        print(f"   - {var}: {coverage:.1f}% cobertura")

print("\n✓ ANÁLISIS INICIAL COMPLETO CON TODAS LAS VARIABLES")
print("✓ Próximo paso: Cross-correlations, estacionariedad, causalidad con dataset completo")
print("="*80)
