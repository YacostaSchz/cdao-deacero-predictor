# 🔬 Feature Engineering & Modeling - CDO DeAcero

## 📋 RESUMEN EJECUTIVO

**Proyecto**: Predicción precio varilla corrugada México  
**Objetivo**: API REST con MAPE < 10%  
**Resultado**: Modelo dos etapas con MAPE < 2.5% ✅  
**Estado**: Listo para producción  

---

## 🏗️ ESTRUCTURA DE CARPETAS

```
03_feature_engineering/
├── 📊 outputs/                     # Datasets y modelos entrenados
├── 📁 01_baseline_analysis/         # Análisis exploratorio inicial
├── 📁 02_premium_models/           # Modelos de premium México/LME
├── 📁 03_comprehensive_analysis/   # Feature engineering robusto
├── 📁 05_final_models/            # Modelo final de dos etapas
├── 📁 archives/                   # Análisis históricos
└── 📄 README.md                   # Esta documentación
```

### 📂 Descripción de Carpetas

#### `01_baseline_analysis/`
**Propósito**: Análisis exploratorio inicial y auditoría de datos
- Validación temporal de fuentes
- Identificación de holidays y missing data
- Estrategias de imputación

#### `02_premium_models/`
**Propósito**: Análisis del premium México/LME
- Consolidación de precios mexicanos reales
- Validación de 11 puntos de datos (vs 7 iniciales)
- Framework de validación de premium dinámico
- **Descubrimiento clave**: Premium varía 1.586 → 1.705 (post-aranceles)

#### `03_comprehensive_analysis/`
**Propósito**: Feature engineering robusto y pipeline completo
- 70+ features propuestas inicialmente
- Reducción a 15 features core
- Pipeline de robustecimiento

#### `05_final_models/` ⭐
**Propósito**: Modelo final de dos etapas (PRODUCCIÓN)
- **TWO_STAGE_FINAL_MODEL.py**: Modelo principal
- **OVERFITTING_VALIDATION.py**: Validación de robustez
- **TWO_STAGE_MODEL_SUMMARY.md**: Documentación ejecutiva

#### `archives/`
**Propósito**: Análisis históricos y exploraciones
- Modelos descartados
- Análisis conceptuales
- Experimentos preliminares

---

## 🚀 EVOLUCIÓN DEL ANÁLISIS

### Fase 1: Exploración Inicial (Días 1-2)
- **Descubrimiento**: Falta de serie histórica nacional de precios varilla
- **Estrategia inicial**: Usar LME + premium fijo 15.7%
- **Problema**: Premium no era constante

### Fase 2: Análisis de Premium (Día 3)
- **Descubrimiento crítico**: Premium varía significativamente
- **Datos reales**: 11 puntos consolidados (no 7)
- **Cambio estructural**: Aranceles abril 2025 (+12pp premium)

### Fase 3: Modelo Dos Etapas (Día 4) ⭐
- **Insight clave**: Separar variables globales vs locales
- **Arquitectura**: LME (global) + Premium (MX local)
- **Resultado**: MAPE < 2.5% + interpretabilidad económica

---

## 🎯 MODELO FINAL: DOS ETAPAS

### Arquitectura Validada

```python
# ETAPA 1: Predicción LME (solo variables globales)
LME[t+1] = RandomForest(
    lme_lag1,           # 46.8% importancia
    rebar_scrap_spread, # 33.3% importancia  
    lme_volatility,     # 10.7% importancia
    lme_momentum        # 9.3% importancia
)

# ETAPA 2: Premium dinámico (solo variables MX)
Premium[t] = Ridge(
    post_tariff,        # +5.97% (cambio estructural)
    usdmxn_lag1,        # -0.37% (FX alto → premium bajo)
    real_interest_rate, # +0.35% (costo capital)
    construction_season # +0.14% (demanda estacional)
)

# PRECIO FINAL
P_Mexico_MXN = LME[t+1] × Premium[t] × FX[t]
```

### Performance Validada

| Métrica | Resultado | Target | Status |
|---------|-----------|--------|--------|
| **LME MAPE** | 1.91% | < 3% | ✅ |
| **Premium MAPE** | 0.83% | < 3% | 🎯 |
| **Combined MAPE** | < 2.5% | < 10% | 🚀 |
| **Overfitting** | No detectado | N/A | ✅ |

---

## 📊 DATOS Y FEATURES

### Fuentes de Datos
1. **LME**: London Metal Exchange (rebar & scrap futures)
2. **Banxico**: USD/MXN, TIIE, INPC (macro mexicano)
3. **EPU**: Economic Policy Uncertainty Index
4. **Gas Natural**: IPGN (costos energéticos)
5. **Precios México**: 11 puntos reales consolidados de reportacero.com

### Features Core Utilizadas

#### Etapa 1 - LME (4 features globales)
- `lme_sr_m01_lag1`: Precio anterior (autoregresivo)
- `lme_volatility_5d`: Volatilidad mercado
- `lme_momentum_5d`: Momentum tendencial
- `rebar_scrap_spread_norm`: Fundamentales acero

#### Etapa 2 - Premium (6 features MX)
- `usdmxn_lag1`: Tipo de cambio lag1
- `real_interest_rate`: Tasa real México
- `uncertainty_indicator`: EPU proxy
- `post_tariff`: Dummy aranceles (abril 2025)
- `construction_season`: Estacionalidad
- `month`: Efectos mensuales

---

## 🔍 VALIDACIONES REALIZADAS

### 1. Validación de Datos
- ✅ 11 puntos de precios México consolidados
- ✅ Outlier 625 USD/ton removido (SteelRadar)
- ✅ Correlación Premium-FX: -0.700 (confirmada)

### 2. Validación de Modelo
- ✅ Split temporal (Aug 1, 2025)
- ✅ Cross-validation 5-fold
- ✅ Curvas de aprendizaje convergentes
- ✅ Feature importance estable

### 3. Validación Económica
- ✅ Coeficientes con signos esperados
- ✅ Cambio estructural capturado (aranceles)
- ✅ Interpretabilidad completa

### 4. Validación de Overfitting
- ✅ Train-test gap: +1.13% (saludable)
- ✅ CV estable: ±0.27%
- ✅ Features estables: CV < 0.26
- ✅ **Conclusión**: NO overfitting

---

## 📈 EJEMPLO DE PREDICCIÓN

```json
{
  "lme_forecast": 539.39,
  "premium_forecast": 1.6886,
  "price_usd": 910.82,
  "price_mxn": 17123.41,
  "confidence_interval_95%": {
    "usd": [879.10, 942.54],
    "mxn": [16527.14, 17719.68]
  },
  "fx_rate_used": 18.8
}
```

---

## 🎯 ARCHIVOS CLAVE PARA PRODUCCIÓN

### Modelos Entrenados
- `outputs/TWO_STAGE_MODEL.pkl` - Modelo principal ⭐
- `outputs/FINAL_CONSOLIDATED_MODEL.pkl` - Modelo anterior
- `outputs/overfitting_validation_report.json` - Reporte validación

### Datasets
- `outputs/features_dataset_latest.csv` - Features completas (271 obs 2025)
- `outputs/two_stage_prediction_example.json` - Formato API

### Documentación
- `05_final_models/TWO_STAGE_MODEL_SUMMARY.md` - Resumen ejecutivo ⭐
- `02_premium_models/README.md` - Análisis de premium
- `FILE_ORGANIZATION_PLAN.md` - Plan de organización

---

## 🔬 INSIGHTS TÉCNICOS CLAVE

### 1. **Separación de Variables es Crítica**
- Variables globales (LME) vs locales (MX) deben modelarse por separado
- Mezclar ambas introduce ruido y reduce interpretabilidad

### 2. **Premium México/LME es Dinámico**
- NO es constante (67-75% rango observado)
- Fuertemente correlacionado con variables macro MX
- Cambio estructural post-aranceles abril 2025

### 3. **Calidad de Datos Importa**
- 11 puntos reales > 7 puntos iniciales
- Remoción de outliers mejora significativamente el modelo
- Interpolación inteligente > imputación simple

### 4. **Validación Rigurosa es Esencial**
- 4 tests independientes de overfitting
- Cross-validation temporal (no aleatorio)
- Feature importance debe ser estable

---

## 🚀 PRÓXIMOS PASOS

### Implementación API
1. **FastAPI wrapper** para `TWO_STAGE_MODEL.pkl`
2. **Endpoint**: `GET /predict/steel-rebar-price`
3. **Autenticación**: X-API-Key
4. **Rate limiting**: 100 req/hour
5. **Cache**: 1 hora TTL

### Deployment
- **Platform**: Railway/Render
- **Budget**: < $5 USD/mes
- **Requirements**: `requirements.txt` actualizado

---

## 📊 MÉTRICAS DE ÉXITO ALCANZADAS

| KPI | Target | Achieved | Status |
|-----|--------|----------|--------|
| **MAPE** | < 10% | < 2.5% | 🚀 **SUPERADO** |
| **Interpretabilidad** | Alta | ✅ | ✅ **LOGRADO** |
| **Robustez** | Sin overfitting | ✅ | ✅ **VALIDADO** |
| **Datos reales** | Usar todos | 11 puntos | ✅ **COMPLETO** |

---

## 🏆 LOGROS PRINCIPALES

1. **Arquitectura innovadora**: Modelo dos etapas económicamente interpretable
2. **Performance excepcional**: MAPE 4x mejor que target
3. **Validación rigurosa**: 4 tests independientes sin overfitting
4. **Datos maximizados**: 11 puntos reales consolidados
5. **Cambio estructural**: Capturado efecto aranceles abril 2025

---

*Documentación generada: 2025-09-28*  
*Autor: Sr Data Scientist - CausalOps Agent*  
*Status: Ready for Production* ⭐
