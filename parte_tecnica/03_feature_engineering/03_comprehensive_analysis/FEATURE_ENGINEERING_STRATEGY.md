# 🎯 ESTRATEGIA DE FEATURE ENGINEERING - PREDICCIÓN PRECIO VARILLA t+1

**Proyecto**: CDO DeAcero - API Predicción Precio Varilla Corrugada
**Fecha**: 2025-09-29
**Versión**: 1.0
**Estado**: 📋 Documentada - Lista para Implementación

## 1. ANÁLISIS CRÍTICO DEL PROBLEMA

### 1.1 Naturaleza del Target
- **Variable objetivo**: Precio varilla México USD/ton (t+1)
- **Problema fundamental**: NO tenemos serie histórica directa del target
- **Proxy disponible**: LME Steel Rebar + spread calibrado (15.7% sept-2025)
- **Horizonte**: 1 día adelante (restricción del reto)
- **Métrica**: MAPE (Mean Absolute Percentage Error)

### 1.2 Características Temporales de las Fuentes

| Fuente | Frecuencia | Lag Publicación | Volatilidad | Relevancia Causal | Días Inhábiles/Año |
|--------|------------|-----------------|-------------|-------------------|-------------------|
| **LME SR/SC** | Diaria | 0-1 días | Alta | Directa (proxy principal) | ~112 (UK) |
| **USD/MXN** | Diaria | 0 días | Media | Alta (conversión precios) | ~114 (México) |
| **TIIE28** | Diaria | 0 días | Baja | Media (costo financiero) | ~114 (México) |
| **INPC** | Mensual | 9-10 días | Muy baja | Baja (ajuste inflación) | N/A |
| **EPU Indices** | Mensual | 30-35 días | Alta | Media (incertidumbre) | N/A |
| **Gas Natural** | Mensual | 15-20 días | Alta | Media (costo energético) | N/A |
| **Eventos Comerciales** | Irregular | 0 días | - | Alta (shocks arancelarios) | N/A |

### 1.3 Hallazgos Críticos
1. **Asincronía temporal severa**: Datos mensuales con lag vs predicción diaria
2. **Problema de identificación**: Sin histórico target, dependemos 100% del proxy LME
3. **Eventos discretos**: 19 eventos comerciales 2025 (11 negativos, 8 positivos)
4. **Días inhábiles**: 1,282 días donde México, USA y UK cerrados simultáneamente
5. **Restricción práctica**: Solo podemos usar datos disponibles en t para predecir t+1

## 2. ESTRATEGIA DE IMPUTACIÓN POR DÍAS INHÁBILES

### 2.1 Política General de Imputación
Basada en el análisis detallado en `HOLIDAY_IMPUTATION_STRATEGY.md`:

```python
def apply_holiday_aware_imputation(df, calendar_df):
    """
    Aplica estrategia diferenciada por tipo de día inhábil
    """
    imputation_strategies = {
        'lme_sr': {
            'weekend': 'LOCF',          # Viernes → Lunes
            'holiday_short': 'LOCF',     # ≤ 3 días
            'holiday_long': 'interpolate' # > 3 días (Semana Santa)
        },
        'usdmxn': {
            'weekend': 'LOCF',
            'holiday_mexico': 'LOCF' if days <= 3 else 'interpolate',
            'async_markets': 'fx_adjusted'  # Cuando MX abierto, LME cerrado
        },
        'tiie28': {
            'any': 'LOCF'  # Tasa estable, siempre LOCF
        }
    }
    
    # Marcar todas las imputaciones
    for col in df.columns:
        df[f'{col}_imputed'] = False
        df[f'{col}_imputation_method'] = None
```

### 2.2 Casos Especiales de Asincronía

```python
# Cuando México abierto pero LME cerrado (58 días/año)
asynchronous_days = {
    'good_friday': 'México opera, UK cerrado',
    'uk_bank_holidays': 'Mayo, Agosto bank holidays',
    'mx_holidays': 'Constitución, Benito Juárez, etc.'
}

# Estrategia específica
if mexico_open and lme_closed:
    # Ajuste por movimiento cambiario intraday
    lme_imputed = lme_last * (1 + 0.15 * fx_intraday_change)
    confidence = 'medium'  # Reducir confianza
```

## 3. ESTRATEGIA DE ANÁLISIS TEMPORAL

### 3.1 Análisis de Estructura Temporal (ANTES de crear features)

```python
# PASO 1: Análisis univariado por serie
temporal_analysis = {}

for serie in ['lme_sr_m01', 'usdmxn', 'tiie28', 'gas_usd']:
    # Test estacionariedad
    tests = {
        'adf': adfuller(serie, autolag='AIC'),
        'kpss': kpss(serie, regression='ct'),
        'order_integration': determine_I_order(serie)
    }
    
    # Estructura de autocorrelación
    correlations = {
        'acf_values': acf(serie, nlags=60, alpha=0.05),
        'pacf_values': pacf(serie, nlags=60, alpha=0.05),
        'ljung_box': acorr_ljungbox(serie, lags=20, return_df=True)
    }
    
    # Estacionalidad y calendario
    seasonality = {
        'weekly_pattern': seasonal_decompose(serie, model='additive', period=5),
        'month_end_effect': detect_month_end_effects(serie),
        'holiday_effect': measure_holiday_impact(serie, holiday_calendar)
    }
    
    temporal_analysis[serie] = {
        'stationarity': tests,
        'correlation': correlations,
        'seasonality': seasonality
    }

# PASO 2: Análisis de lead-lag relationships
cross_correlation_matrix = pd.DataFrame()
for lag in range(-20, 21):  # ±20 días
    cross_correlation_matrix.loc[lag, 'lme_fx'] = crosscorr(lme_sr, usdmxn, lag)
    cross_correlation_matrix.loc[lag, 'lme_gas'] = crosscorr(lme_sr, gas_nat, lag)
    cross_correlation_matrix.loc[lag, 'lme_tiie'] = crosscorr(lme_sr, tiie28, lag)

# PASO 3: Test de causalidad de Granger con múltiples especificaciones
granger_results = {}
for p in [1, 5, 10, 20]:  # Diferentes órdenes de lag
    model = VAR(data[['lme_sr', 'usdmxn', 'tiie28']])
    results = model.fit(p)
    granger_results[f'lag_{p}'] = {
        'causality': results.test_causality('lme_sr', ['usdmxn', 'tiie28']),
        'aic': results.aic,
        'bic': results.bic
    }
```

### 3.2 Criterios de Selección de Lags

```python
lag_selection_criteria = {
    'statistical_significance': {
        'granger_causality': lambda lag: granger_pvalue(lag) < 0.05,
        'information_gain': lambda lag: mutual_info(y_t, x_t_lag) > 0.1,
        'partial_correlation': lambda lag: abs(pacf[lag]) > 2/sqrt(n)
    },
    
    'economic_relevance': {
        'trading_patterns': [1, 5, 20, 60],  # Diario, semanal, mensual, trimestral
        'settlement_cycles': [2, 3],          # T+2, T+3 liquidación
        'reporting_lags': {'inpc': 30, 'epu': 35, 'gas': 20}
    },
    
    'practical_constraints': {
        'data_availability': lambda lag: check_no_lookahead_bias(lag),
        'holiday_adjustment': lambda lag: validate_imputation_quality(lag),
        'computational_cost': lambda lag: lag <= 60  # Límite práctico
    }
}
```

## 4. ARQUITECTURA DE FEATURES PROPUESTA

### 4.1 Features Nivel 1: Directos de Mercado

```python
# A. LME Base (variable más importante)
lme_features = {
    # Niveles con validación de disponibilidad
    'lme_sr_m01_t1': {
        'value': lag(1),
        'available_when': 'not holiday_uk',
        'imputation': 'LOCF'
    },
    'lme_sr_m01_t5': {
        'value': lag(5),
        'available_when': 'always',
        'imputation': 'interpolate'
    },
    'lme_sr_m01_t20': {
        'value': lag(20),
        'available_when': 'always',
        'imputation': 'interpolate'
    },
    
    # Cambios porcentuales robustos a gaps
    'lme_sr_pct_1d': pct_change(1, skip_holidays=True),
    'lme_sr_pct_5d': pct_change(5, method='geometric_mean'),
    'lme_sr_pct_20d': pct_change(20, method='geometric_mean'),
    
    # Volatilidad realizada ajustada por días hábiles
    'lme_sr_vol_5d': rolling_std(5, min_periods=3, ddof=1),
    'lme_sr_vol_20d': rolling_std(20, min_periods=15, ddof=1),
    'lme_sr_vol_realized': realized_volatility(returns_5min),  # Si disponible
    
    # Estructura temporal de futuros
    'contango_3m': (M03 - M01) / M01,
    'contango_6m': (M06 - M01) / M01,
    'futures_slope': linear_regression(M01...M15),
    'futures_curvature': quadratic_coefficient(M01...M15),
    
    # Spreads inter-commodity
    'rebar_scrap_spread': SR_M01 - SC_M01,
    'rebar_scrap_ratio': SR_M01 / SC_M01,
    'spread_zscore': (spread - ma_20) / std_20
}

# B. Ajustes Cambiarios con hora de corte
fx_features = {
    'usdmxn_t0': {
        'value': get_fx_rate(),
        'cutoff_time': '14:00 Mexico/City',
        'fallback': lag(1)
    },
    'usdmxn_pct_1d': pct_change(1),
    'usdmxn_pct_5d': pct_change(5),
    'fx_volatility_5d': garch_volatility(5),  # GARCH para FX
    'fx_regime': threshold_model(volatility)   # High/Low vol regime
}

# C. Macro México con manejo de publicación
macro_features = {
    'tiie28_real': tiie28 - expected_inflation,
    'tiie28_spread_vs_ma': tiie28 - rolling_mean(tiie28, 20),
    'inflation_surprise': actual_inpc - consensus_forecast,
    'real_rate': {
        'value': tiie28 - last_published_inflation,
        'lag': 30,  # INPC publicado con 30 días de retraso
        'imputation': 'forward_fill'
    }
}
```

### 4.2 Features Nivel 2: Incertidumbre y Sentimiento

```python
# D. Economic Policy Uncertainty con sincronización
epu_features = {
    'epu_mexico_last': {
        'value': last_available_value,
        'typical_lag': 30,
        'imputation': 'forward_fill'
    },
    'epu_usa_last': last_available_value,
    'epu_turkey_last': last_available_value,  # Crítico por referencia LME
    'epu_china_last': last_available_value,
    
    # Métricas derivadas
    'epu_spread_mx_us': epu_mx - epu_us,
    'epu_global_avg': weighted_mean([epu_mx, epu_us, epu_cn, epu_tr]),
    'epu_momentum': epu_current - epu_3m_ago,
    'epu_dispersion': std([epu_mx, epu_us, epu_cn, epu_tr])
}

# E. Eventos Comerciales (scores_formatted.md)
trade_events_features = {
    # Ventana móvil de impacto
    'tariff_impact_7d': {
        'value': sum(events_window(t, t+7).impact_scores),
        'decay': 'exponential',  # Más peso a eventos próximos
        'range': [-11, +8]       # Basado en eventos 2025
    },
    'tariff_impact_30d': sum(events_window(t, t+30).impact_scores),
    
    # Eventos específicos por tipo
    'us_section_232_active': binary_indicator('section_232'),
    'mx_antidumping_count': count_active_measures('antidumping'),
    'investigation_pending': count_investigations('active'),
    
    # Sentimiento neto calibrado
    'trade_sentiment_score': {
        'value': (positive_events - negative_events) / total_events,
        'window': 30,
        'weights': {'US': 0.5, 'MX': 0.3, 'CN': 0.2}
    },
    
    # Proximidad temporal con decay
    'days_to_next_major_event': {
        'value': min(days_to_events[abs(impact) > 0.5]),
        'cap': 30,  # Máximo relevancia 30 días
        'transform': lambda x: 1 / (1 + x)  # Decay function
    }
}

# F. Gas Natural con alineación mensual
gas_features = {
    'gas_ipgn_usd': {
        'value': last_published_value,
        'typical_lag': 15,
        'currency_adjusted': True
    },
    'gas_henryhub_spread': ipgn - henryhub,
    'energy_cost_index': weighted_avg(gas, electricity, coal)
}
```

### 4.3 Features Nivel 3: Interacciones y No-linealidades

```python
# G. Interacciones económicamente relevantes
interaction_features = {
    # Efecto conjunto volatilidad-spread
    'vol_contango_interaction': lme_vol_20d * contango_3m,
    'vol_regime_spread': lme_vol_20d * rebar_scrap_spread,
    
    # Ajuste por incertidumbre
    'uncertainty_adjusted_lme': lme_sr_m01 * (1 + epu_global/1000),
    'fx_stress_indicator': fx_vol * epu_mexico,
    
    # Presión por eventos comerciales
    'tariff_adjusted_spread': rebar_scrap_spread * (1 + tariff_impact_7d/10),
    'trade_war_premium': base_spread * trade_sentiment_score,
    
    # Régimen de mercado
    'market_regime': {
        'high_vol': lme_vol_20d > percentile(80),
        'contango': futures_slope > 0,
        'risk_off': epu_global > percentile(75),
        'trade_stress': tariff_impact_30d < -3
    },
    
    # No linealidades
    'lme_squared': lme_sr_m01 ** 2,
    'vol_sqrt': sqrt(lme_vol_20d),
    'log_spread': log(max(rebar_scrap_spread, 1))
}

# H. Features técnicos con justificación económica
technical_features = {
    # Momentum ajustado por días hábiles
    'lme_rsi_14': {
        'value': rsi(14, adjusted_for_holidays=True),
        'interpretation': 'overbought/oversold'
    },
    
    # Mean reversion
    'lme_zscore_20': (lme_sr - ma_20) / std_20,
    'bollinger_position': (lme_sr - bb_lower) / (bb_upper - bb_lower),
    
    # Microestructura
    'roll_return': front_month_return - next_month_return,
    'calendar_spread_percentile': percentile_rank(M02 - M01, 252)
}
```

## 5. VALIDACIÓN CAUSAL Y SELECCIÓN

### 5.1 Framework de Validación Multi-Criterio

```python
def validate_feature_causality(feature, target, data):
    """
    Validación comprehensiva de relevancia causal
    """
    # 1. Tests estadísticos
    statistical_tests = {
        'granger_causality': {
            'test': granger_causality_test(feature, target, maxlag=20),
            'threshold': 0.05,
            'weight': 0.25
        },
        'transfer_entropy': {
            'test': transfer_entropy(feature, target, k=5),
            'threshold': 0.1,
            'weight': 0.15
        },
        'ccm_causality': {
            'test': convergent_cross_mapping(feature, target),
            'threshold': 0.7,
            'weight': 0.10
        }
    }
    
    # 2. Métricas de información
    information_metrics = {
        'mutual_info': {
            'value': mutual_info_regression(feature, target),
            'threshold': 0.1,
            'weight': 0.20
        },
        'conditional_mi': {
            'value': conditional_mutual_info(feature, target, confounders),
            'threshold': 0.05,
            'weight': 0.10
        }
    }
    
    # 3. Importancia en modelos
    model_importance = {
        'rf_importance': RandomForest().feature_importances_,
        'xgb_gain': XGBoost().get_score(importance_type='gain'),
        'shap_values': shap.TreeExplainer(model).shap_values(X)
    }
    
    # 4. Estabilidad temporal
    stability_metrics = {
        'rolling_correlation': {
            'mean': rolling_corr.mean(),
            'std': rolling_corr.std(),
            'trend': kendall_tau(rolling_corr, time)
        },
        'regime_consistency': correlation_by_market_regime(),
        'structural_breaks': bai_perron_test(feature, target)
    }
    
    # 5. Validación económica
    economic_validation = {
        'sign_consistency': check_economic_sign(feature, target),
        'magnitude_plausible': check_effect_size(feature, target),
        'lead_lag_correct': verify_temporal_ordering(feature, target)
    }
    
    # Score compuesto
    final_score = weighted_average(all_metrics, weights)
    return {
        'include_feature': final_score > 0.6,
        'score': final_score,
        'details': all_metrics
    }
```

### 5.2 Métricas de Impacto y Selección

```python
feature_impact_analysis = {
    # Impacto predictivo
    'mape_reduction': {
        'metric': (mape_baseline - mape_with_feature) / mape_baseline,
        'test': 'time_series_cv',
        'folds': TimeSeriesSplit(n_splits=5)
    },
    
    # Contribución marginal
    'shapley_value': {
        'metric': shapley_permutation_value(feature, model),
        'baseline': 'median_prediction',
        'n_permutations': 100
    },
    
    # Robustez
    'stability_score': {
        'temporal': feature_importance_over_time(window=60),
        'cross_market': feature_importance_by_regime(),
        'bootstrap': bootstrap_feature_importance(n_iter=1000)
    },
    
    # Interacciones
    'interaction_effects': {
        'h_statistic': friedman_h_statistic(feature, other_features),
        'synergy': measure_feature_synergy(feature_pairs)
    }
}

# Proceso de selección
selected_features = []
for feature in candidate_features:
    if all([
        impact_analysis[feature]['mape_reduction'] > 0.01,  # 1% mejora mínima
        stability_score[feature] > 0.7,                     # Estable
        economic_validation[feature] == True,               # Sentido económico
        holiday_robustness[feature] > 0.8                  # Robusto a imputación
    ]):
        selected_features.append(feature)
```

## 6. PIPELINE DE IMPLEMENTACIÓN

### 6.1 Fase 1: Preparación y Análisis Temporal (2-3 horas)

```python
# 1. Setup inicial
def phase1_temporal_analysis():
    # Cargar datos con calendario de días inhábiles
    data = load_all_data_sources()
    calendar = pd.read_csv('holiday_calendar_2015_2026.csv')
    
    # Alinear temporalmente
    aligned_data = temporal_alignment(data, calendar, freq='D')
    
    # Análisis completo
    results = {
        'stationarity': run_stationarity_tests(aligned_data),
        'acf_pacf': compute_correlation_functions(aligned_data),
        'seasonality': detect_seasonal_patterns(aligned_data),
        'cross_correlations': analyze_lead_lag_relationships(aligned_data),
        'granger_causality': test_granger_causality(aligned_data)
    }
    
    # Documentar hallazgos
    save_temporal_analysis_report(results)
    return results
```

### 6.2 Fase 2: Construcción de Features (3-4 horas)

```python
# 2. Feature Engineering
def phase2_feature_construction():
    # Aplicar imputación holiday-aware
    imputed_data = apply_holiday_imputation(aligned_data, calendar)
    
    # Construir features por nivel
    features = {}
    features.update(create_lme_features(imputed_data))
    features.update(create_fx_features(imputed_data))
    features.update(create_macro_features(imputed_data))
    features.update(create_uncertainty_features(imputed_data))
    features.update(create_trade_event_features(imputed_data, events_df))
    features.update(create_interaction_features(features))
    
    # Validar no-leakage
    validate_no_lookahead_bias(features)
    
    # Generar metadata
    feature_metadata = generate_feature_documentation(features)
    
    return features, feature_metadata
```

### 6.3 Fase 3: Selección y Validación (2-3 horas)

```python
# 3. Feature Selection
def phase3_feature_selection():
    # Split temporal correcto
    train_end = '2024-12-31'
    val_end = '2025-06-30'
    
    # Selección multi-criterio
    selected = []
    for feature_name, feature_data in features.items():
        validation_results = validate_feature_causality(
            feature_data, 
            target, 
            data[data.index <= train_end]
        )
        
        if validation_results['include_feature']:
            selected.append({
                'name': feature_name,
                'score': validation_results['score'],
                'importance': validation_results['details']
            })
    
    # Ordenar por importancia
    selected_features = sorted(selected, key=lambda x: x['score'], reverse=True)
    
    # Eliminar redundantes
    final_features = remove_redundant_features(selected_features, threshold=0.9)
    
    return final_features[:50]  # Top 50 features
```

### 6.4 Fase 4: Evaluación y Documentación (2 horas)

```python
# 4. Evaluación final
def phase4_evaluation():
    # Backtesting con ventana deslizante
    backtest_results = []
    for date in pd.date_range(val_start, val_end):
        # Simular predicción real-time
        available_data = get_data_available_at(date)
        features_t = compute_features(available_data)
        prediction = model.predict(features_t)
        actual = get_actual_price(date + 1)
        
        backtest_results.append({
            'date': date,
            'predicted': prediction,
            'actual': actual,
            'mape': abs(prediction - actual) / actual
        })
    
    # Análisis de resultados
    evaluation_metrics = {
        'mape_overall': np.mean([r['mape'] for r in backtest_results]),
        'mape_by_regime': analyze_by_market_regime(backtest_results),
        'mape_by_holiday': analyze_by_holiday_type(backtest_results),
        'feature_importance_final': get_final_feature_importance(model),
        'residual_analysis': analyze_residuals(backtest_results)
    }
    
    # Generar reporte
    create_evaluation_report(evaluation_metrics)
    
    return evaluation_metrics
```

## 7. CONSIDERACIONES CRÍTICAS Y MITIGACIONES

### 7.1 Riesgos Identificados

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Overfitting al spread 15.7% | Alta | Alto | Intervalos de confianza amplios, validación robusta |
| Cambio estructural en mercados | Media | Alto | Monitoreo de drift, re-entrenamiento automático |
| Falla en imputación holidays | Baja | Medio | Validación específica por tipo de día inhábil |
| Eventos comerciales no previstos | Media | Alto | Buffer en confidence score, alertas manuales |
| Lag de datos mensuales | Certeza | Medio | Features alternativos de alta frecuencia |

### 7.2 Estrategias de Mitigación

```python
mitigation_strategies = {
    'confidence_intervals': {
        'method': 'quantile_regression',
        'levels': [0.1, 0.25, 0.75, 0.9],
        'adjustment': 'heteroscedastic'  # Más amplios en alta volatilidad
    },
    
    'model_ensemble': {
        'models': ['xgboost', 'random_forest', 'elastic_net'],
        'weights': 'dynamic',  # Basado en performance reciente
        'diversity': 'feature_subsampling'
    },
    
    'drift_detection': {
        'metrics': ['psi', 'kolmogorov_smirnov', 'wasserstein'],
        'threshold': 0.1,
        'action': 'alert_and_retrain'
    },
    
    'fallback_rules': {
        'no_lme_data': 'use_last_known + fx_adjustment',
        'extreme_event': 'widen_confidence_intervals',
        'model_failure': 'return_baseline_forecast'
    }
}
```

## 8. MÉTRICAS DE ÉXITO Y MONITOREO

### 8.1 KPIs del Sistema

```python
success_metrics = {
    # Performance
    'mape_target': {
        'value': '< 10%',
        'measurement': 'rolling_7_days',
        'critical': '< 15%'
    },
    
    # Robustez
    'availability': {
        'value': '> 99.5%',
        'measurement': 'uptime_percentage',
        'includes': 'holiday_handling'
    },
    
    # Calidad de features
    'feature_coverage': {
        'value': '> 95%',
        'measurement': 'non_null_ratio',
        'by': 'feature_group'
    },
    
    # Confianza
    'prediction_confidence': {
        'high_confidence': '> 60% predictions',
        'low_confidence_accuracy': 'wider_intervals_contain_actual'
    }
}
```

### 8.2 Dashboard de Monitoreo

```python
monitoring_dashboard = {
    'real_time': {
        'current_prediction': 'USD/ton',
        'confidence_level': 'high/medium/low',
        'features_status': 'available/imputed/missing',
        'market_regime': 'normal/volatile/stressed'
    },
    
    'daily_summary': {
        'mape_yesterday': '%',
        'features_used': 'count',
        'imputation_rate': '%',
        'warnings': ['list']
    },
    
    'weekly_analysis': {
        'mape_trend': 'chart',
        'feature_importance_changes': 'heatmap',
        'holiday_impact_analysis': 'table',
        'trade_event_effects': 'timeline'
    }
}
```

## 9. CONCLUSIONES Y PRÓXIMOS PASOS

### 9.1 Entregables Esperados
1. **Feature dataset**: 50-70 features validados y documentados
2. **Pipeline código**: Reproducible y modular
3. **Documentación**: Completa con justificación económica
4. **Métricas validación**: MAPE < 10% en backtest

### 9.2 Timeline de Implementación
- **2-3 horas**: Análisis temporal completo
- **3-4 horas**: Construcción de features
- **2-3 horas**: Selección y validación
- **2 horas**: Evaluación y documentación
- **Total**: 9-12 horas de desarrollo

### 9.3 Criterios de Go/No-Go
```python
go_criteria = all([
    mape_validation < 0.10,           # MAPE < 10%
    feature_stability > 0.80,         # Features estables
    holiday_robustness > 0.85,        # Robusto a imputación
    economic_interpretability == True, # Sentido económico
    no_data_leakage == True          # Sin filtración
])
```

---

**Nota**: Esta estrategia integra completamente la gestión de días inhábiles documentada en `HOLIDAY_IMPUTATION_STRATEGY.md` y los eventos comerciales de `scores_formatted.md`.

**Última actualización**: 2025-09-29
**Autor**: Sistema Sr Data Scientist "CausalOps"
**Estado**: Listo para implementación
