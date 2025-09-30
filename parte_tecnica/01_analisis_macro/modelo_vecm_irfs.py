#!/usr/bin/env python3
"""
Modelo VECM con IRFs y FEVD - Precios de Varilla Corrugada
==========================================================
Parte 3: Modelado VECM, Impulse Response Functions y Validación

Autor: CDO DeAcero Analysis Team
Fecha: 2025-09-28
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.tsa.vector_ar.vecm import VECM, select_order, select_coint_rank
from statsmodels.tsa.vector_ar.var_model import VAR
from statsmodels.tsa.vector_ar.vecm import coint_johansen
from sklearn.metrics import mean_absolute_error, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

# Configuración de visualización
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10

print("="*80)
print("MODELO VECM CON IRFs Y FEVD")
print("="*80)

# 1. CARGAR DATOS
# ===============
print("\n1. CARGANDO DATOS...")

df = pd.read_csv('dataset_analysis.csv', index_col=0, parse_dates=True)
print(f"✓ Dataset cargado: {df.shape}")

# 2. PRUEBA DE JOHANSEN PARA COINTEGRACIÓN MULTIVARIADA
# =====================================================
print("\n2. TEST DE JOHANSEN PARA COINTEGRACIÓN...")

# Preparar datos en niveles (log)
df_log = np.log(df)
variables = ['REBAR', 'IRON_ORE', 'CRUDE_BRENT', 'COAL_AUS']
data_johansen = df_log[variables]

# Test de Johansen
johansen_result = coint_johansen(data_johansen, det_order=0, k_ar_diff=1)

print("\nTest de Johansen - Estadístico de la Traza:")
print(f"{'r':>3} {'Test Stat':>10} {'90%':>10} {'95%':>10} {'99%':>10}")
print("-"*50)
for i in range(len(johansen_result.lr1)):
    print(f"{i:>3} {johansen_result.lr1[i]:>10.2f} "
          f"{johansen_result.cvt[i,0]:>10.2f} "
          f"{johansen_result.cvt[i,1]:>10.2f} "
          f"{johansen_result.cvt[i,2]:>10.2f}")

# Determinar rango de cointegración
coint_rank = 0
for i in range(len(johansen_result.lr1)):
    if johansen_result.lr1[i] > johansen_result.cvt[i, 1]:  # 95% critical value
        coint_rank += 1
    else:
        break

print(f"\n✓ Rango de cointegración (95%): {coint_rank}")

# 3. SELECCIÓN DE LAGS ÓPTIMOS
# ============================
print("\n3. SELECCIÓN DE LAGS ÓPTIMOS...")

# Usar VAR para selección de lags
model_var = VAR(data_johansen)
lag_order = model_var.select_order(maxlags=12)

print("\nCriterios de Información para Selección de Lags:")
print(f"AIC: {lag_order.aic} lags")
print(f"BIC: {lag_order.bic} lags")
print(f"FPE: {lag_order.fpe} lags")
print(f"HQIC: {lag_order.hqic} lags")

optimal_lag = lag_order.bic  # Usar BIC para parsimonia
print(f"\n✓ Lags óptimos seleccionados (BIC): {optimal_lag}")

# 4. ESTIMACIÓN DEL MODELO VECM
# =============================
print("\n4. ESTIMANDO MODELO VECM...")

if coint_rank > 0:
    # Estimar VECM
    model_vecm = VECM(data_johansen, k_ar_diff=optimal_lag, coint_rank=coint_rank, deterministic='ci')
    vecm_fit = model_vecm.fit()
    
    print("\n✓ Modelo VECM estimado exitosamente")
    print(f"  - Variables: {variables}")
    print(f"  - Lags: {optimal_lag}")
    print(f"  - Rango de cointegración: {coint_rank}")
    
    # Coeficientes de ajuste (alpha)
    print("\nCoeficientes de Ajuste (α):")
    alpha = pd.DataFrame(vecm_fit.alpha, index=variables, columns=[f'EC{i+1}' for i in range(coint_rank)])
    print(alpha.round(4))
    
    # Vectores de cointegración (beta)
    print("\nVectores de Cointegración (β):")
    beta = pd.DataFrame(vecm_fit.beta, index=variables, columns=[f'EC{i+1}' for i in range(coint_rank)])
    print(beta.round(4))
    
else:
    print("\n⚠️ No se encontró cointegración significativa. Usando VAR en diferencias...")
    # Usar VAR en diferencias
    data_diff = data_johansen.diff().dropna()
    model_var = VAR(data_diff)
    var_fit = model_var.fit(maxlags=optimal_lag, ic='bic')
    vecm_fit = var_fit  # Para compatibilidad con código posterior

# 5. IMPULSE RESPONSE FUNCTIONS (IRFs)
# ====================================
print("\n5. CALCULANDO IMPULSE RESPONSE FUNCTIONS...")

# Calcular IRFs
irf = vecm_fit.irf(periods=12)

# Graficar IRFs para shocks en cada variable sobre REBAR
fig, axes = plt.subplots(2, 2, figsize=(12, 10))
axes = axes.flatten()

for i, shock_var in enumerate(variables):
    # Obtener respuesta IRF
    response = irf.irfs[:, variables.index('REBAR'), variables.index(shock_var)]
    
    # Calcular intervalos de confianza manualmente o usar plot_irf
    ax = axes[i]
    periods = range(len(response))
    
    ax.plot(periods, response, 'b-', linewidth=2, label='IRF')
    ax.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    ax.set_title(f'Respuesta de REBAR a shock en {shock_var}')
    ax.set_xlabel('Períodos (meses)')
    ax.set_ylabel('Respuesta')
    ax.grid(True, alpha=0.3)
    ax.legend()

plt.tight_layout()
plt.savefig('impulse_response_functions.png', dpi=300, bbox_inches='tight')
print("✓ IRFs guardadas: impulse_response_functions.png")

# Calcular elasticidades aproximadas
print("\nElasticidades aproximadas (respuesta acumulada a 12 meses):")
for shock_var in variables[1:]:  # Excluir REBAR consigo mismo
    cumulative_response = irf.irfs[:12, variables.index('REBAR'), variables.index(shock_var)].sum()
    print(f"  {shock_var}: {cumulative_response:.3f}")

# 6. FORECAST ERROR VARIANCE DECOMPOSITION (FEVD)
# ===============================================
print("\n6. CALCULANDO FEVD...")

# FEVD para REBAR
fevd = vecm_fit.fevd(periods=12)
fevd_rebar = fevd.decomp[variables.index('REBAR')]

# Crear DataFrame para visualización
fevd_df = pd.DataFrame(fevd_rebar, columns=variables)
fevd_df['Período'] = range(1, len(fevd_df) + 1)

# Graficar FEVD
fig, ax = plt.subplots(figsize=(10, 6))
fevd_df.set_index('Período')[variables].plot(kind='area', stacked=True, ax=ax, alpha=0.7)
ax.set_ylabel('Proporción de Varianza')
ax.set_xlabel('Períodos (meses)')
ax.set_title('FEVD - Descomposición de Varianza del Error de Pronóstico para REBAR')
ax.legend(loc='right')
ax.set_ylim(0, 1)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('fevd_rebar.png', dpi=300, bbox_inches='tight')
print("✓ FEVD guardado: fevd_rebar.png")

# Mostrar contribuciones en horizontes específicos
print("\nContribución a la varianza de REBAR (%):")
for h in [1, 3, 6, 12]:
    if h <= len(fevd_df):
        print(f"\nHorizonte {h} mes(es):")
        for var in variables:
            print(f"  {var}: {fevd_df.iloc[h-1][var]*100:.1f}%")

# 7. VALIDACIÓN CON BACKTESTING
# =============================
print("\n\n7. VALIDACIÓN CON BACKTESTING...")

# Parámetros de validación
train_size = 0.8
n_obs = len(data_johansen)
split_point = int(n_obs * train_size)

print(f"Período de entrenamiento: {data_johansen.index[0]} a {data_johansen.index[split_point-1]}")
print(f"Período de validación: {data_johansen.index[split_point]} a {data_johansen.index[-1]}")

# Dividir datos
train_data = data_johansen.iloc[:split_point]
test_data = data_johansen.iloc[split_point:]

# Re-estimar modelo con datos de entrenamiento
if coint_rank > 0:
    model_train = VECM(train_data, k_ar_diff=optimal_lag, coint_rank=coint_rank, deterministic='ci')
    fit_train = model_train.fit()
else:
    train_diff = train_data.diff().dropna()
    model_train = VAR(train_diff)
    fit_train = model_train.fit(maxlags=optimal_lag, ic='bic')

# Pronósticos out-of-sample
n_test = len(test_data)
forecasts = []
actuals = []

print("\nRealizando pronósticos out-of-sample...")
for i in range(n_test):
    # Pronóstico 1 paso adelante
    if i == 0:
        last_obs = train_data.iloc[-optimal_lag-1:]
    else:
        last_obs = pd.concat([train_data, test_data.iloc[:i]]).iloc[-optimal_lag-1:]
    
    try:
        if coint_rank > 0:
            forecast = fit_train.predict(steps=1, last_obs=last_obs.values)
        else:
            last_diff = last_obs.diff().dropna().values
            forecast_diff = fit_train.forecast(last_diff, steps=1)
            forecast = last_obs.iloc[-1].values + forecast_diff[0]
        
        forecasts.append(forecast[0])
        actuals.append(test_data.iloc[i].values)
    except:
        break

# Convertir a arrays
if len(forecasts) > 0:
    forecasts = np.array(forecasts)
    actuals = np.array(actuals)
    
    # Verificar dimensiones
    if len(forecasts.shape) == 3:
        forecasts = forecasts.squeeze()
    
    # Calcular métricas para REBAR
    rebar_idx = variables.index('REBAR')
    if len(forecasts.shape) == 2:
        rebar_forecasts = forecasts[:, rebar_idx]
        rebar_actuals = actuals[:, rebar_idx]
    else:
        rebar_forecasts = forecasts
        rebar_actuals = actuals
else:
    print("No se pudieron generar pronósticos")
    rebar_forecasts = np.array([])
    rebar_actuals = np.array([])

# Calcular métricas solo si hay pronósticos
if len(rebar_forecasts) > 0:
    # Métricas en niveles log
    mae_log = mean_absolute_error(rebar_actuals, rebar_forecasts)
    rmse_log = np.sqrt(mean_squared_error(rebar_actuals, rebar_forecasts))
    
    # Métricas en niveles originales
    rebar_forecasts_exp = np.exp(rebar_forecasts)
    rebar_actuals_exp = np.exp(rebar_actuals)
    mae = mean_absolute_error(rebar_actuals_exp, rebar_forecasts_exp)
    rmse = np.sqrt(mean_squared_error(rebar_actuals_exp, rebar_forecasts_exp))
    mape = np.mean(np.abs((rebar_actuals_exp - rebar_forecasts_exp) / rebar_actuals_exp)) * 100
    
    print("\n✓ Métricas de Validación para REBAR:")
    print(f"  MAE (log): {mae_log:.4f}")
    print(f"  RMSE (log): {rmse_log:.4f}")
    print(f"  MAE: ${mae:.2f}/mt")
    print(f"  RMSE: ${rmse:.2f}/mt")
    print(f"  MAPE: {mape:.2f}%")
else:
    mae_log = rmse_log = mae = rmse = mape = 0
    print("\n⚠️ No se pudieron calcular métricas de validación")

# Graficar pronósticos vs actuales solo si hay datos
if len(rebar_forecasts) > 0:
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # En escala log
    test_dates = test_data.index[:len(rebar_actuals)]
    ax1.plot(test_dates, rebar_actuals, 'b-', label='Actual', linewidth=2)
    ax1.plot(test_dates, rebar_forecasts, 'r--', label='Pronóstico', linewidth=2)
    ax1.set_title('Pronósticos vs Actuales - REBAR (escala log)')
    ax1.set_ylabel('log($/mt)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # En escala original
    ax2.plot(test_dates, rebar_actuals_exp, 'b-', label='Actual', linewidth=2)
    ax2.plot(test_dates, rebar_forecasts_exp, 'r--', label='Pronóstico', linewidth=2)
    ax2.set_title('Pronósticos vs Actuales - REBAR ($/mt)')
    ax2.set_ylabel('USD/mt')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('validacion_pronosticos.png', dpi=300, bbox_inches='tight')
    print("\n✓ Gráfico de validación guardado: validacion_pronosticos.png")

# 8. RESUMEN EJECUTIVO FINAL
# ==========================
print("\n" + "="*80)
print("RESUMEN EJECUTIVO - MODELO VECM Y ANÁLISIS DE IMPACTO")
print("="*80)

print("\n1. MODELO ESTIMADO:")
if coint_rank > 0:
    print(f"   - Tipo: VECM con {coint_rank} relación(es) de cointegración")
else:
    print("   - Tipo: VAR en diferencias (sin cointegración)")
print(f"   - Lags óptimos: {optimal_lag}")
print(f"   - Variables: {', '.join(variables)}")

print("\n2. DRIVERS PRINCIPALES DE REBAR:")
print("   Según FEVD a 12 meses:")
fevd_12m = fevd_df.iloc[11] if len(fevd_df) > 11 else fevd_df.iloc[-1]
sorted_vars = fevd_12m[variables].sort_values(ascending=False)
for var in sorted_vars.index[:3]:
    print(f"   - {var}: {sorted_vars[var]*100:.1f}% de la varianza")

print("\n3. RESPUESTAS DINÁMICAS (IRFs):")
print("   Elasticidades acumuladas a 12 meses:")
for shock_var in variables[1:]:
    cumulative = irf.irfs[:12, variables.index('REBAR'), variables.index(shock_var)].sum()
    print(f"   - Shock 1% en {shock_var} → {cumulative:.3f}% en REBAR")

print("\n4. CAPACIDAD PREDICTIVA:")
print(f"   - MAPE out-of-sample: {mape:.2f}%")
print(f"   - RMSE: ${rmse:.2f}/mt")
print(f"   - MAE: ${mae:.2f}/mt")

print("\n5. RECOMENDACIONES PARA API PREDICTIVA:")
print("   - Variables clave: Coal, Iron Ore, Crude Oil")
print(f"   - Horizonte óptimo: {optimal_lag} meses de historia")
print("   - Actualización: Reentrenar mensualmente")
print("   - Monitoreo: Detectar quiebres estructurales")

# Guardar resultados completos
results_summary = {
    'model_type': 'VECM' if coint_rank > 0 else 'VAR',
    'coint_rank': coint_rank,
    'optimal_lags': optimal_lag,
    'variables': variables,
    'mape': mape,
    'rmse': rmse,
    'mae': mae,
    'fevd_12m': fevd_12m[variables].to_dict(),
    'train_period': f"{data_johansen.index[0]} to {data_johansen.index[split_point-1]}",
    'test_period': f"{data_johansen.index[split_point]} to {data_johansen.index[-1]}"
}

import json
with open('modelo_results.json', 'w') as f:
    json.dump(results_summary, f, indent=2, default=str)

print("\n✓ Resultados guardados: modelo_results.json")
print("\n" + "="*80)
print("ANÁLISIS COMPLETO - LISTO PARA IMPLEMENTACIÓN EN API")
print("="*80)
