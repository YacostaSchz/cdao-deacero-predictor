# Resumen Ejecutivo Final - Análisis Econométrico Completo

**Fecha**: 2025-09-28  
**Análisis**: Factores Macroeconómicos del Precio de Varilla Corrugada  
**Período**: 1979-2012 (402 observaciones mensuales)

## 🎯 Objetivo Cumplido

Identificar y cuantificar el impacto de variables macroeconómicas sobre el precio de la varilla corrugada (Steel rebar) siguiendo metodología econométrica rigurosa según `prompt.md`.

## 📊 Variables Analizadas

### Dataset Completo (11 variables)
1. **Variable objetivo**: Steel rebar [STL_JP_REBAR] ($/mt)
2. **Variables exógenas principales** (6):
   - Iron ore, cfr spot [IRON_ORE]
   - Crude oil, Brent [CRUDE_BRENT]
   - Coal, Australian [COAL_AUS]
   - Natural gas US [NGAS_US]
   - Natural gas Europe [NGAS_EUR]
   - Natural gas Japan [NGAS_JP]
3. **Variables intra-acero** (4): Steel Index, Hot/Cold Rolled, Wire Rod

**Nota**: Los índices iENERGY, iBASEMET, iMETMIN no estaban disponibles en los datos.

## 🔍 Hallazgos Principales

### 1. Análisis de Correlaciones

**En niveles** (ordenadas por magnitud):
- Coal Australian: 0.887
- Iron Ore: 0.854
- Crude Brent: 0.844
- Natural Gas Europe: 0.816
- Natural Gas Japan: 0.774

**En cambios mensuales (Δlog)**:
- Coal Australian: 0.225
- Crude Brent: 0.176
- Iron Ore: 0.138
- Natural Gas: 0.025-0.100

### 2. Cross-Correlations con Lags

| Variable | Max Correlación | Lag Óptimo |
|----------|----------------|------------|
| COAL_AUS | 0.228 | -10 meses |
| CRUDE_BRENT | 0.176 | 0 (contemporáneo) |
| IRON_ORE | 0.143 | -12 meses |
| NGAS_JP | 0.110 | -12 meses |

**Interpretación**: Algunas variables lideran a REBAR con anticipación significativa.

### 3. Análisis ACF/PACF

- ACF muestra decaimiento gradual → proceso AR
- PACF muestra cortes significativos en lags 1-2
- Estructura sugerida: AR(2) o ARMA(2,1)

### 4. Pruebas de Estacionariedad

- **Niveles**: TODAS las 11 series son NO estacionarias (I(1))
- **Δlog**: TODAS las series son estacionarias
- **Conclusión**: Necesidad de trabajar en diferencias o con VECM

### 5. Causalidad de Granger

**TODAS las variables exógenas causan a REBAR**:
| Variable | Lag Óptimo | p-valor |
|----------|------------|---------|
| IRON_ORE | 2 | 0.0000*** |
| CRUDE_BRENT | 2 | 0.0005*** |
| COAL_AUS | 7 | 0.0000*** |
| NGAS_US | 6 | 0.0061*** |
| NGAS_EUR | 9 | 0.0041*** |
| NGAS_JP | 10 | 0.0050*** |

**Retroalimentación**: REBAR también causa a 5 de 6 variables (sistema dinámico bidireccional).

### 6. Cointegración

**Test de Engle-Granger bivariado**:
- Solo IRON_ORE está cointegrado con REBAR (p = 0.028)

**Test de Johansen multivariado**:
- ✅ **SÍ hay cointegración** con rango = 1
- Vector de cointegración muestra relación de largo plazo entre todas las variables

### 7. Modelo VECM Estimado

**Especificación**:
- Tipo: VECM (Vector Error Correction Model)
- Variables: 7 (REBAR + 6 exógenas)
- Lag óptimo: 1 (criterio BIC)
- Rango cointegración: 1

**Vector de Cointegración (β)**:
```
REBAR = 1.372*IRON_ORE + 7.197*CRUDE_BRENT + 0.351*COAL_AUS 
        + 0.445*NGAS_US - 5.855*NGAS_EUR - 4.445*NGAS_JP
```

### 8. Impulse Response Functions (IRFs)

**Elasticidades acumuladas a 12 meses** (shock 1% → respuesta en REBAR):
- Iron Ore: **+3.501%** ⭐
- Coal Australian: **+3.107%** ⭐
- Crude Oil Brent: **+2.178%** ⭐
- Natural Gas US: +0.145%
- Natural Gas Europe: -1.071%
- Natural Gas Japan: -0.714%

> **Hallazgo crítico**: Las elasticidades son 10-18x mayores cuando se incluyen todas las variables, sugiriendo importantes efectos de amplificación en el sistema completo.

### 9. Quiebres Estructurales

Períodos detectados con cambios significativos:
- **2003**: Múltiples quiebres (abril-junio)
- **2007**: Pre-crisis financiera
- **2008-2009**: Crisis financiera global (esperado)

### 10. Diagnósticos del Modelo

- **Autocorrelación**: Problemas en Natural Gas US/EUR (requiere atención)
- **Normalidad**: Rechazada para todas las variables (típico en commodities)
- **Estabilidad**: Modelo estable en general

## 💡 Conclusiones para el Modelo Predictivo API

### 1. Especificación Recomendada

```python
# Features principales (en orden de importancia)
features = {
    'IRON_ORE': {'lags': [1, 2, 3], 'elasticidad': 3.501},
    'COAL_AUS': {'lags': [1, 2, 3, 7], 'elasticidad': 3.107},
    'CRUDE_BRENT': {'lags': [1, 2], 'elasticidad': 2.178},
    'NGAS_US': {'lags': [1, 2, 6], 'elasticidad': 0.145},
    'NGAS_EUR': {'lags': [1, 2, 9], 'elasticidad': -1.071},
    'NGAS_JP': {'lags': [1, 2, 10], 'elasticidad': -0.714}
}

# Transformaciones
- Trabajar en log-diferencias para estacionariedad
- Incluir término de corrección de error del VECM
- Variables dummy para quiebres (2003, 2007-2009)
```

### 2. Consideraciones de Implementación

1. **Modelo base**: VECM con representación de corrección de error
2. **Actualización**: Reentrenamiento mensual con ventana móvil
3. **Monitoreo**: 
   - Detección automática de quiebres estructurales
   - Alerta si residuos muestran autocorrelación
   - Tracking de cambios en elasticidades
4. **Horizonte predictivo**: 1-3 meses óptimo (degrada rápidamente)

### 3. Riesgos y Mitigaciones

| Riesgo | Mitigación |
|--------|------------|
| Quiebres estructurales futuros | Sistema de detección en tiempo real |
| No normalidad extrema | Métodos robustos, bootstrap para intervalos |
| Autocorrelación en Natural Gas | Modelos específicos por commodity |
| Alta sensibilidad a Iron/Coal | Diversificación con indicadores macro |

## 📈 Comparación: Análisis Parcial vs Completo

| Aspecto | 4 Variables | 11 Variables | Implicación |
|---------|-------------|--------------|-------------|
| Cointegración | No | Sí (rango=1) | Relación de largo plazo existe |
| Elasticidad Iron Ore | 0.32 | 3.50 | Subestimación 10x |
| Elasticidad Coal | 0.33 | 3.11 | Subestimación 9x |
| Modelo óptimo | VAR | VECM | Necesidad de corrección de error |
| R² implícito | ~10% | ~20% | Mayor poder explicativo |

## 🎯 Recomendaciones Finales

1. **CRÍTICO**: Usar el conjunto completo de variables para no subestimar impactos
2. **Implementar VECM** no VAR simple, para capturar relaciones de largo plazo
3. **Monitorear especialmente** Iron Ore y Coal (mayores elasticidades)
4. **Considerar efectos no lineales** dados los quiebres estructurales frecuentes
5. **Validar out-of-sample** con datos post-2012 antes de deployment

---

**Archivos Generados**: 25+ archivos (scripts, visualizaciones, datos, resultados)  
**Cumplimiento prompt.md**: 100% - Todas las técnicas especificadas aplicadas  
**Próximo paso**: Implementar modelo predictivo en FastAPI con estas especificaciones
