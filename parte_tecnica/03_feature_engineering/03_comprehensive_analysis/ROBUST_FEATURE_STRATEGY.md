# 🛡️ ESTRATEGIA ROBUSTA DE FEATURES - PRAGMÁTICA Y REALISTA

**Proyecto**: CDO DeAcero - Predicción Precio Varilla t+1
**Fecha**: 2025-09-28 20:30
**Timeline**: 4 días restantes (Sep 29 - Oct 2)
**Objetivo**: MAPE < 10% con máxima robustez

## 1. PRINCIPIOS DE ROBUSTECIMIENTO

### 1.1 Filosofía Core
```python
principles = {
    'simplicity_over_sophistication': True,
    'robustness_over_accuracy': True,
    'transparency_over_complexity': True,
    'fallbacks_everywhere': True,
    'fail_gracefully': True
}
```

### 1.2 Restricciones Aceptadas
- **UN punto de calibración**: 15.7% spread (lo que tenemos)
- **Sin histórico México**: 100% dependencia de proxy LME
- **Datos con lag**: Hasta 35 días para algunos indicadores
- **4 días para todo**: Modelo + API + Deploy

## 2. FEATURES CORE MÍNIMOS (15 MÁXIMO)

### 2.1 Tier 1: Críticos (5 features)
```python
critical_features = {
    # 1. Precio LME base
    'lme_sr_m01_lag1': {
        'source': 'LME SR',
        'fallback': 'last_known_value',
        'weight': 0.40
    },
    
    # 2. Tipo de cambio
    'usdmxn_lag1': {
        'source': 'Banxico',
        'fallback': 'last_known_value',
        'weight': 0.20
    },
    
    # 3. Spread calibrado
    'mexico_premium': {
        'value': 1.157,  # 15.7% fijo
        'confidence': 'medium',
        'weight': 0.20
    },
    
    # 4. Volatilidad reciente
    'lme_volatility_5d': {
        'calculation': 'std(returns_5d)',
        'fallback': 'historical_avg',
        'weight': 0.10
    },
    
    # 5. Cambio LME reciente
    'lme_momentum_5d': {
        'calculation': '(t-1 - t-5) / t-5',
        'fallback': 0,
        'weight': 0.10
    }
}
```

### 2.2 Tier 2: Importantes (5 features)
```python
important_features = {
    # 6. Estructura de futuros
    'contango_indicator': {
        'calculation': 'sign(M03 - M01)',  # Simple: backwardation vs contango
        'values': [-1, 0, 1],
        'fallback': 0
    },
    
    # 7. Spread rebar-scrap
    'rebar_scrap_spread_norm': {
        'calculation': '(SR - SC) / SR',  # Normalizado
        'fallback': 'historical_median'
    },
    
    # 8. Eventos comerciales próximos
    'trade_events_impact_7d': {
        'source': 'scores_formatted.md',
        'values': sum(next_7_days_impacts),
        'fallback': 0
    },
    
    # 9. Día de la semana
    'weekday_effect': {
        'monday': -0.02,     # Típicamente menor
        'friday': 0.01,      # Típicamente mayor
        'other': 0
    },
    
    # 10. Mes del año
    'seasonality_simple': {
        'Q1': -0.01,  # Típicamente débil
        'Q2': 0.02,   # Construcción activa
        'Q3': 0.01,   
        'Q4': -0.02   # Fin de año débil
    }
}
```

### 2.3 Tier 3: Contextuales (5 features)
```python
contextual_features = {
    # 11. TIIE real
    'real_interest_rate': {
        'calculation': 'tiie28 - last_inflation',
        'lag': 30,  # Acepta lag de inflación
        'fallback': 'last_known'
    },
    
    # 12. Incertidumbre global (simple)
    'uncertainty_indicator': {
        'high': volatility > p75 or events_negative > 2,
        'medium': 'default',
        'low': volatility < p25
    },
    
    # 13. Régimen de mercado
    'market_regime': {
        'bull': lme_ma5 > lme_ma20,
        'bear': lme_ma5 < lme_ma20,
        'neutral': 'otherwise'
    },
    
    # 14. Holiday effect
    'days_to_holiday': {
        'calculation': 'min(days_to_next_holiday)',
        'impact': -0.01 if days < 3 else 0
    },
    
    # 15. Confianza del modelo
    'model_confidence': {
        'high': all_data_fresh and volatility_low,
        'medium': 'default',
        'low': missing_data or extreme_event
    }
}
```

## 3. PIPELINE SIMPLIFICADO (IMPLEMENTABLE EN 4 DÍAS)

### 3.1 Día 1 (Sep 29): Data Pipeline Básico
```python
# Morning (4 hrs)
def build_basic_pipeline():
    # 1. Cargar datos existentes
    lme_data = pd.read_csv('lme_combined_sr_sc.csv')
    banxico_data = load_banxico_cached()  # Ya descargado
    events_data = pd.read_csv('events_processed.csv')
    
    # 2. Alineación temporal simple
    df = align_daily_data(lme_data, banxico_data)
    
    # 3. Imputación básica
    df = apply_simple_imputation(df)  # LOCF con límite 3 días
    
    return df

# Afternoon (4 hrs)
def create_core_features(df):
    # Solo los 15 features definidos
    features = pd.DataFrame()
    
    # Tier 1: Críticos
    features['lme_lag1'] = df['sr_m01'].shift(1)
    features['fx_lag1'] = df['usdmxn'].shift(1)
    features['volatility_5d'] = df['sr_m01'].pct_change().rolling(5).std()
    
    # ... implementar los 15
    
    return features
```

### 3.2 Día 2 (Sep 30): Modelo Simple + Validación
```python
# Morning (4 hrs)
def train_robust_model(features, target):
    # 1. Split temporal estricto
    train_end = '2024-12-31'
    
    # 2. Modelo ensemble simple
    models = {
        'baseline': BaselineModel(),  # LME * 1.157
        'xgboost': XGBRegressor(max_depth=3, n_estimators=100),
        'linear': Ridge(alpha=1.0)
    }
    
    # 3. Validación robusta
    cv_scores = {}
    for name, model in models.items():
        scores = time_series_cv(model, features, target, n_splits=3)
        cv_scores[name] = scores
    
    # 4. Ensemble simple
    ensemble = VotingRegressor([
        ('base', baseline, 0.5),
        ('xgb', xgboost, 0.3),
        ('linear', linear, 0.2)
    ])
    
    return ensemble

# Afternoon (4 hrs)  
def implement_fallbacks():
    # Sistema de fallbacks en cascada
    fallback_system = {
        'level_1': 'use_all_features',
        'level_2': 'use_only_tier1_features',
        'level_3': 'use_only_lme_fx',
        'level_4': 'return_last_known_price'
    }
    
    return FallbackPredictor(models, fallback_system)
```

### 3.3 Día 3 (Oct 1): API Robusta
```python
# Morning (4 hrs)
@app.get("/predict/steel-rebar-price")
async def predict_price(x_api_key: str = Header(...)):
    try:
        # 1. Validación de API key
        if not validate_api_key(x_api_key):
            raise HTTPException(401)
        
        # 2. Rate limiting check
        if rate_limit_exceeded(x_api_key):
            raise HTTPException(429)
        
        # 3. Cache check
        cached = get_cached_prediction()
        if cached and cached.age < 3600:  # 1 hora
            return cached
        
        # 4. Obtener datos más recientes
        current_data = fetch_latest_data_with_fallbacks()
        
        # 5. Predicción con manejo de errores
        try:
            prediction = ensemble_model.predict(current_data)
            confidence = calculate_confidence(current_data)
        except Exception as e:
            # Fallback a modelo simple
            prediction = baseline_model.predict(current_data)
            confidence = 0.6
        
        # 6. Ajuste por eventos conocidos
        prediction = adjust_for_known_events(prediction, date)
        
        # 7. Formatear respuesta
        response = {
            "prediction_date": tomorrow(),
            "predicted_price_usd_per_ton": round(prediction, 2),
            "currency": "USD",
            "unit": "metric_ton",
            "model_confidence": confidence,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        # 8. Cache resultado
        cache_prediction(response)
        
        return response
        
    except Exception as e:
        # Fallback final
        return {
            "prediction_date": tomorrow(),
            "predicted_price_usd_per_ton": 625.0,  # Último conocido
            "model_confidence": 0.5,
            "warning": "Using fallback prediction"
        }

# Afternoon (4 hrs)
def implement_monitoring():
    # Dashboard simple
    @app.get("/health")
    def health_check():
        return {
            "status": "healthy",
            "data_freshness": check_data_age(),
            "model_version": "1.0",
            "last_prediction": get_last_prediction_time()
        }
    
    # Logging
    @app.middleware("http")
    async def log_requests(request, call_next):
        log_prediction_request(request)
        response = await call_next(request)
        log_prediction_response(response)
        return response
```

### 3.4 Día 4 (Oct 2): Deploy + Testing
```python
# Morning (4 hrs)
def deploy_to_cloud():
    # 1. Dockerfile minimalista
    """
    FROM python:3.9-slim
    COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt
    COPY . /app
    WORKDIR /app
    CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
    """
    
    # 2. Deploy a Railway/Render
    # - Free tier o $5/mes
    # - Auto-scaling básico
    # - SSL incluido
    
    # 3. Variables de entorno
    env_vars = {
        'API_KEYS': encrypted_keys,
        'CACHE_TTL': 3600,
        'RATE_LIMIT': 100,
        'FALLBACK_PRICE': 625.0
    }

# Afternoon (4 hrs)
def final_testing():
    # 1. Tests de carga
    run_load_tests(endpoint, n_requests=1000)
    
    # 2. Tests de fallback
    test_missing_data_scenarios()
    test_extreme_values()
    test_api_key_validation()
    
    # 3. Documentación final
    generate_api_docs()
    create_postman_collection()
    write_deployment_guide()
```

## 4. SISTEMA DE FALLBACKS ROBUSTO

### 4.1 Cascada de Fallbacks
```python
class RobustPredictor:
    def predict(self, date):
        try:
            # Nivel 1: Modelo completo
            if all_features_available():
                return ensemble_predict()
        except:
            pass
            
        try:
            # Nivel 2: Solo features críticos
            if critical_features_available():
                return simple_model_predict()
        except:
            pass
            
        try:
            # Nivel 3: Solo LME y FX
            if lme_and_fx_available():
                return lme_price * 1.157 * fx_adjustment
        except:
            pass
            
        # Nivel 4: Último conocido
        return {
            'price': last_known_price,
            'confidence': 0.5,
            'warning': 'Using historical fallback'
        }
```

### 4.2 Manejo de Eventos Especiales
```python
def handle_special_events(prediction, date):
    # Ajustes por eventos conocidos
    if date in known_tariff_changes:
        prediction *= (1 + tariff_impact)
        
    if date in mexican_holidays:
        prediction *= 0.98  # Típicamente menor
        
    if high_volatility_detected():
        # Ampliar intervalos de confianza
        confidence_interval *= 1.5
        
    return prediction
```

## 5. MÉTRICAS DE ÉXITO REALISTAS

### 5.1 KPIs Ajustados
```python
realistic_targets = {
    'mape_target': '< 12%',         # Más realista
    'availability': '> 99%',         # Crítico
    'response_time': '< 500ms',      # Rápido
    'fallback_usage': '< 10%',       # Monitorear
    'cache_hit_rate': '> 80%'        # Eficiencia
}
```

### 5.2 Plan de Contingencia
```python
contingency_plans = {
    'model_drift': 'Alert + use baseline',
    'data_outage': 'Use cached + fallbacks',
    'high_error': 'Switch to conservative model',
    'api_overload': 'Scale horizontally',
    'unknown_event': 'Widen confidence intervals'
}
```

## 6. DOCUMENTACIÓN DE LIMITACIONES

### 6.1 Limitaciones Conocidas
```markdown
## Limitaciones del Modelo

1. **Calibración**: Basada en un solo punto (Sept 2025)
2. **Datos históricos**: Sin precios México reales
3. **Lag temporal**: Algunos indicadores con 30+ días de retraso
4. **Eventos**: No predice shocks no programados
5. **Horario**: Predicciones matutinas usan datos t-2

## Recomendaciones de Uso

- Mejores predicciones: 12:00-17:00 México (datos frescos)
- Mayor incertidumbre: Lunes temprano, días festivos
- Verificar confidence score antes de decisiones críticas
```

## 7. CHECKLIST DE IMPLEMENTACIÓN

### Día 1 (Sep 29)
- [ ] Pipeline de datos básico (4 hrs)
- [ ] 15 features core implementados (4 hrs)
- [ ] Validación de no-leakage

### Día 2 (Sep 30)  
- [ ] Modelo ensemble simple (4 hrs)
- [ ] Sistema de fallbacks (4 hrs)
- [ ] Backtesting básico

### Día 3 (Oct 1)
- [ ] API FastAPI funcional (4 hrs)
- [ ] Rate limiting y cache (2 hrs)
- [ ] Monitoring básico (2 hrs)

### Día 4 (Oct 2)
- [ ] Deploy a cloud (4 hrs)
- [ ] Testing completo (2 hrs)
- [ ] Documentación final (2 hrs)

---

**PRINCIPIO RECTOR**: "Es mejor un modelo simple que funciona al 99% del tiempo que uno complejo que falla cuando más se necesita"

**Última actualización**: 2025-09-28 20:30
**Autor**: Sistema Sr Data Scientist "CausalOps" 
**Estado**: Estrategia Robusta Lista para Ejecución
