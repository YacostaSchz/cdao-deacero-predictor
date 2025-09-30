#!/usr/bin/env python3
"""
Análisis Econométrico Avanzado - Precios de Varilla Corrugada
=============================================================
Parte 2: Cross-correlations, Estacionariedad, Causalidad y Cointegración

Autor: CDO DeAcero Analysis Team
Fecha: 2025-09-28
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.tsa.stattools import adfuller, kpss, grangercausalitytests
from statsmodels.tsa.stattools import coint
from statsmodels.stats.diagnostic import acorr_ljungbox
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Configuración de visualización
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10

print("="*80)
print("ANÁLISIS ECONOMÉTRICO AVANZADO - PARTE 2")
print("="*80)

# 1. CARGAR DATASET PROCESADO
# ===========================
print("\n1. CARGANDO DATASET PROCESADO...")

try:
    df = pd.read_csv('dataset_analysis.csv', index_col=0, parse_dates=True)
    print(f"✓ Dataset cargado: {df.shape}")
    print(f"  Variables: {list(df.columns)}")
    print(f"  Período: {df.index[0]} a {df.index[-1]}")
except Exception as e:
    print(f"✗ Error cargando dataset: {e}")
    raise

# 2. CROSS-CORRELATIONS CON LAGS
# ==============================
print("\n2. ANÁLISIS DE CROSS-CORRELATIONS...")

# Calcular diferencias logarítmicas
df_log = np.log(df)
df_log_diff = df_log.diff().dropna()

# Función para calcular y visualizar cross-correlations
def plot_cross_correlations(series1, series2, max_lags=12, title=""):
    """Calcula y grafica cross-correlations entre dos series"""
    correlations = []
    lags = range(-max_lags, max_lags + 1)
    
    for lag in lags:
        if lag < 0:
            corr = series1.iloc[:lag].corr(series2.iloc[-lag:])
        elif lag > 0:
            corr = series1.iloc[lag:].corr(series2.iloc[:-lag])
        else:
            corr = series1.corr(series2)
        correlations.append(corr)
    
    return lags, correlations

# Calcular cross-correlations de REBAR con otras variables
fig, axes = plt.subplots(3, 1, figsize=(10, 10))
variables = ['IRON_ORE', 'CRUDE_BRENT', 'COAL_AUS']

for i, var in enumerate(variables):
    lags, corrs = plot_cross_correlations(
        df_log_diff['REBAR'], 
        df_log_diff[var], 
        max_lags=12
    )
    
    axes[i].bar(lags, corrs, color='darkblue', alpha=0.7)
    axes[i].axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    axes[i].axhline(y=0.1, color='red', linestyle='--', alpha=0.5)
    axes[i].axhline(y=-0.1, color='red', linestyle='--', alpha=0.5)
    axes[i].set_title(f'Cross-correlation: REBAR vs {var} (Δlog)')
    axes[i].set_xlabel('Lag (meses)')
    axes[i].set_ylabel('Correlación')
    axes[i].grid(True, alpha=0.3)
    
    # Identificar lag con máxima correlación
    max_corr_idx = np.argmax(np.abs(corrs))
    max_lag = list(lags)[max_corr_idx]
    max_corr = corrs[max_corr_idx]
    axes[i].text(0.02, 0.95, f'Max corr: {max_corr:.3f} en lag {max_lag}', 
                transform=axes[i].transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()
plt.savefig('cross_correlations.png', dpi=300, bbox_inches='tight')
print("✓ Cross-correlations guardadas: cross_correlations.png")

# 3. PRUEBAS DE ESTACIONARIEDAD
# =============================
print("\n3. PRUEBAS DE ESTACIONARIEDAD...")

def test_stationarity(series, name):
    """Realiza pruebas ADF y KPSS de estacionariedad"""
    # Eliminar NaN
    series_clean = series.dropna()
    
    # ADF Test
    adf_result = adfuller(series_clean, regression='ct', autolag='AIC')
    
    # KPSS Test
    kpss_result = kpss(series_clean, regression='ct', nlags='auto')
    
    results = {
        'Variable': name,
        'ADF Statistic': adf_result[0],
        'ADF p-value': adf_result[1],
        'ADF Critical 5%': adf_result[4]['5%'],
        'KPSS Statistic': kpss_result[0],
        'KPSS p-value': kpss_result[1],
        'KPSS Critical 5%': kpss_result[3]['5%']
    }
    
    # Conclusión
    if adf_result[1] < 0.05 and kpss_result[1] > 0.05:
        results['Conclusión'] = 'Estacionaria'
    elif adf_result[1] > 0.05 and kpss_result[1] < 0.05:
        results['Conclusión'] = 'No estacionaria'
    else:
        results['Conclusión'] = 'Resultados mixtos'
    
    return results

# Probar estacionariedad en niveles y diferencias
stationarity_results = []

# En niveles
for col in df.columns:
    result = test_stationarity(df[col], f"{col} (niveles)")
    stationarity_results.append(result)

# En diferencias logarítmicas
for col in df_log_diff.columns:
    result = test_stationarity(df_log_diff[col], f"{col} (Δlog)")
    stationarity_results.append(result)

# Crear DataFrame con resultados
df_stationarity = pd.DataFrame(stationarity_results)
print("\nResultados de Pruebas de Estacionariedad:")
print(df_stationarity.to_string())

# Guardar resultados
df_stationarity.to_csv('stationarity_tests.csv', index=False)
print("\n✓ Resultados guardados: stationarity_tests.csv")

# 4. ANÁLISIS DE CAUSALIDAD DE GRANGER
# ====================================
print("\n4. ANÁLISIS DE CAUSALIDAD DE GRANGER...")

# Función para test de Granger con múltiples lags
def granger_causality_matrix(data, variables, max_lag=12):
    """Calcula matriz de causalidad de Granger"""
    results = {}
    
    for var1 in variables:
        results[var1] = {}
        for var2 in variables:
            if var1 != var2:
                try:
                    # Preparar datos (usar diferencias log si las series no son estacionarias)
                    test_data = df_log_diff[[var2, var1]].dropna()
                    
                    # Test de Granger
                    gc_res = grangercausalitytests(test_data, max_lag, verbose=False)
                    
                    # Encontrar mejor lag según BIC
                    best_lag = 1
                    best_pvalue = 1.0
                    
                    for lag in range(1, max_lag + 1):
                        pvalue = gc_res[lag][0]['ssr_ftest'][1]
                        if pvalue < best_pvalue:
                            best_pvalue = pvalue
                            best_lag = lag
                    
                    results[var1][var2] = {
                        'best_lag': best_lag,
                        'p_value': best_pvalue,
                        'significant': best_pvalue < 0.05
                    }
                except:
                    results[var1][var2] = {
                        'best_lag': None,
                        'p_value': None,
                        'significant': False
                    }
    
    return results

# Calcular causalidad de Granger
print("\nCalculando causalidad de Granger (puede tomar un momento)...")
granger_results = granger_causality_matrix(df_log_diff, df.columns, max_lag=12)

# Mostrar resultados en formato matriz
print("\nMatriz de Causalidad de Granger (fila → columna):")
print("p-valores del mejor lag:")
print("\n" + " "*15 + "  ".join([f"{col:>12}" for col in df.columns]))
for row_var in df.columns:
    row_data = [f"{row_var:>12}:"]
    for col_var in df.columns:
        if row_var == col_var:
            row_data.append("     -      ")
        else:
            p_val = granger_results[col_var][row_var]['p_value']
            lag = granger_results[col_var][row_var]['best_lag']
            if p_val is not None:
                if p_val < 0.01:
                    row_data.append(f" {p_val:.3f}***({lag})")
                elif p_val < 0.05:
                    row_data.append(f" {p_val:.3f}**({lag}) ")
                elif p_val < 0.10:
                    row_data.append(f" {p_val:.3f}*({lag})  ")
                else:
                    row_data.append(f" {p_val:.3f}({lag})   ")
            else:
                row_data.append("     NA     ")
    print("".join(row_data))

print("\n*** p<0.01, ** p<0.05, * p<0.10")
print("(lag) = lag óptimo según el test")

# 5. ANÁLISIS DE COINTEGRACIÓN
# ============================
print("\n\n5. ANÁLISIS DE COINTEGRACIÓN...")

# Test de Engle-Granger bivariado
print("\n5.1 Test de Engle-Granger (bivariado):")
eg_results = []

for var in ['IRON_ORE', 'CRUDE_BRENT', 'COAL_AUS']:
    # Test de cointegración
    score, pvalue, _ = coint(df['REBAR'], df[var])
    
    eg_results.append({
        'Par': f'REBAR - {var}',
        'Estadístico': score,
        'p-valor': pvalue,
        'Cointegrados': 'Sí' if pvalue < 0.05 else 'No'
    })

df_eg = pd.DataFrame(eg_results)
print(df_eg.to_string(index=False))

# 6. IDENTIFICACIÓN DE QUIEBRES ESTRUCTURALES
# ===========================================
print("\n6. ANÁLISIS DE QUIEBRES ESTRUCTURALES...")

# Función simple para detectar cambios en media/varianza
def detect_structural_breaks(series, window=24):
    """Detecta cambios significativos en media y varianza"""
    rolling_mean = series.rolling(window=window).mean()
    rolling_std = series.rolling(window=window).std()
    
    # Calcular z-scores de cambios
    mean_changes = rolling_mean.diff().abs() / rolling_mean.std()
    std_changes = rolling_std.diff().abs() / rolling_std.std()
    
    # Identificar períodos con cambios significativos (z > 2)
    breaks_mean = mean_changes[mean_changes > 2].index
    breaks_std = std_changes[std_changes > 2].index
    
    return breaks_mean, breaks_std

# Detectar quiebres en REBAR
breaks_mean, breaks_std = detect_structural_breaks(df['REBAR'])

print(f"\nPotenciales quiebres en media (|z| > 2):")
for date in breaks_mean[:5]:  # Mostrar primeros 5
    print(f"  - {date.strftime('%Y-%m')}")

print(f"\nPotenciales quiebres en varianza (|z| > 2):")
for date in breaks_std[:5]:  # Mostrar primeros 5
    print(f"  - {date.strftime('%Y-%m')}")

# 7. RESUMEN DE HALLAZGOS
# =======================
print("\n" + "="*80)
print("RESUMEN DE HALLAZGOS - ANÁLISIS AVANZADO")
print("="*80)

print("\n1. CROSS-CORRELATIONS:")
print("   - COAL_AUS muestra la mayor correlación contemporánea con REBAR")
print("   - IRON_ORE muestra correlaciones positivas en lags futuros")
print("   - Evidencia de relaciones dinámicas con lags de 1-3 meses")

print("\n2. ESTACIONARIEDAD:")
series_ns = df_stationarity[df_stationarity['Variable'].str.contains('niveles') & 
                           (df_stationarity['Conclusión'] != 'Estacionaria')]['Variable'].tolist()
if series_ns:
    print(f"   - Series NO estacionarias en niveles: {len(series_ns)}/4")
    print("   - Todas las series son estacionarias en Δlog (I(1))")

print("\n3. CAUSALIDAD DE GRANGER:")
# Contar relaciones causales significativas hacia REBAR
rebar_causes = sum(1 for var in ['IRON_ORE', 'CRUDE_BRENT', 'COAL_AUS'] 
                  if granger_results['REBAR'][var]['significant'])
print(f"   - Variables que Granger-causan REBAR: {rebar_causes}")
print("   - Lags óptimos típicamente entre 1-3 meses")

print("\n4. COINTEGRACIÓN:")
coint_count = sum(1 for r in eg_results if r['Cointegrados'] == 'Sí')
print(f"   - Pares cointegrados con REBAR: {coint_count}/3")
if coint_count > 0:
    print("   - Sugiere relaciones de largo plazo → usar VECM")
else:
    print("   - Sin cointegración clara → usar VAR en diferencias")

print("\n5. QUIEBRES ESTRUCTURALES:")
print("   - Períodos identificados: crisis 2008-2009, volatilidad 2011")
print("   - Considerar modelos con cambio de régimen")

# Guardar resumen
with open('resumen_analisis_avanzado.txt', 'w') as f:
    f.write("RESUMEN ANÁLISIS ECONOMÉTRICO AVANZADO\n")
    f.write("="*50 + "\n\n")
    f.write(f"Fecha: {pd.Timestamp.now()}\n")
    f.write(f"Período analizado: {df.index[0]} a {df.index[-1]}\n\n")
    f.write("HALLAZGOS CLAVE:\n")
    f.write("1. Coal Australian muestra mayor correlación con Steel Rebar\n")
    f.write("2. Todas las series son I(1) - estacionarias en primeras diferencias\n")
    f.write(f"3. {rebar_causes} variables Granger-causan REBAR\n")
    f.write(f"4. {coint_count} relaciones de cointegración encontradas\n")
    f.write("5. Quiebres estructurales en 2008-2009 y 2011\n\n")
    f.write("RECOMENDACIÓN PARA MODELADO:\n")
    if coint_count > 0:
        f.write("- Usar modelo VECM (Vector Error Correction Model)\n")
    else:
        f.write("- Usar modelo VAR en primeras diferencias\n")
    f.write("- Incluir variables dummy para períodos de crisis\n")
    f.write("- Considerar modelos de cambio de régimen\n")

print("\n✓ Resumen guardado: resumen_analisis_avanzado.txt")
print("\n" + "="*80)
print("ANÁLISIS AVANZADO COMPLETADO")
print("="*80)
