# 🚨 VALIDACIÓN CRÍTICA DE CALIDAD DE DATOS - Modelo LME

**Fecha**: 2025-09-28 23:43
**Analista**: Sr Data Scientist - CausalOps
**Criticidad**: ALTA - Impacta directamente el MAPE del modelo

## ❓ Preguntas Críticas del Usuario

### 1. ¿Se hizo JOIN con el catálogo de holidays?
### 2. ¿Se validó que las series estén completas sin nulos?
### 3. ¿Se usó la estrategia de imputación?

---

## 📊 ESTADO ACTUAL - Análisis Crítico

### ✅ IMPLEMENTADO

1. **Catálogo de Holidays**:
   - ✅ Archivo generado: `outputs/holiday_calendar_2015_2026.csv`
   - ✅ Script: `holiday_calendar_analyzer.py` (480 líneas)
   - ✅ Cobertura: México, USA, UK, China, Turquía (2015-2026)
   - ✅ Total: 4,383 días con flags de holidays por país

2. **Estrategia de Imputación Documentada**:
   - ✅ Documento: `HOLIDAY_IMPUTATION_STRATEGY.md` (209 líneas)
   - ✅ Estrategias por fuente: LOCF, interpolación, ajuste FX
   - ✅ Código implementado en: `robust_feature_pipeline.py`
   
3. **Pipeline con Imputación**:
   - ✅ `RobustFeaturePipeline` clase completa (673 líneas)
   - ✅ Método `apply_holiday_imputation()` implementado (líneas 252-280)
   - ✅ Join con holidays en línea 222-246
   - ✅ Flags de imputación por columna

### ⚠️ POSIBLE PROBLEMA

**CRÍTICO**: No hay evidencia clara de que `TWO_STAGE_FINAL_MODEL.py` use el `RobustFeaturePipeline`

**Evidencia**:
```python
# TWO_STAGE_FINAL_MODEL.py línea 46
features_path = "outputs/features_dataset_latest.csv"
df = pd.read_csv(features_path, index_col=0, parse_dates=True)
```

**Pregunta sin responder**: 
- ¿El archivo `features_dataset_latest.csv` fue generado por `robust_feature_pipeline.py` con imputación de holidays?
- ¿O fue generado con imputación genérica SimpleImputer?

---

## 🔍 VALIDACIÓN NECESARIA

### Paso 1: Verificar Pipeline de Generación
```bash
# ¿Qué script generó features_dataset_latest.csv?
grep -r "features_dataset_latest.csv" --include="*.py" parte_tecnica/03_feature_engineering/

# Verificar fecha de generación
stat outputs/features_dataset_latest.csv

# Comparar con fecha de robust_feature_pipeline.py
stat 03_comprehensive_analysis/robust_feature_pipeline.py
```

### Paso 2: Revisar Columnas de Imputación
```python
# ¿Existen columnas *_imputed en el dataset?
df = pd.read_csv("outputs/features_dataset_latest.csv")
imputed_cols = [col for col in df.columns if '_imputed' in col]
print(f"Columnas de imputación encontradas: {imputed_cols}")
```

### Paso 3: Validar Nulos
```python
# Verificar completitud de series críticas
df = pd.read_csv("outputs/features_dataset_latest.csv", parse_dates=['date'])

critical_series = [
    'lme_sr_m01',
    'lme_sr_m01_lag1', 
    'usdmxn_lag1',
    'lme_volatility_5d',
    'lme_momentum_5d'
]

for col in critical_series:
    if col in df.columns:
        null_count = df[col].isna().sum()
        null_pct = (null_count / len(df)) * 100
        print(f"{col}: {null_count} nulos ({null_pct:.2f}%)")
```

### Paso 4: Verificar Join con Holiday Calendar
```python
# ¿Existen columnas de holidays en features_dataset?
holiday_cols = [col for col in df.columns if 'holiday' in col.lower() or 'weekend' in col.lower()]
print(f"Columnas de holidays: {holiday_cols}")

# ¿Hay flag days_to_holiday?
if 'days_to_holiday' in df.columns:
    print("✅ Feature days_to_holiday presente")
else:
    print("❌ Feature days_to_holiday NO encontrado")
```

---

## 🚨 HALLAZGOS PRELIMINARES

### En TWO_STAGE_FINAL_MODEL.py (líneas 30-31)
```python
self.lme_imputer = SimpleImputer(strategy='mean')
self.premium_imputer = SimpleImputer(strategy='mean')
```

**⚠️ PROBLEMA POTENCIAL**:
- El modelo usa `SimpleImputer(strategy='mean')` genérico
- NO usa la imputación inteligente basada en holidays
- Esto puede introducir bias en días festivos

### Consecuencias
1. **LOCF no aplicado**: Fines de semana no se manejan correctamente
2. **Mean imputation**: Puede distorsionar precios en gaps largos
3. **Holidays no considerados**: Asincronía México-UK no manejada

---

## ✅ SOLUCIÓN RECOMENDADA

### Opción 1: Usar Features Pre-Procesados (RÁPIDO)
```python
# Ejecutar robust_feature_pipeline.py PRIMERO
python robust_feature_pipeline.py

# Esto genera features_dataset_latest.csv CON imputación correcta
# Luego ejecutar TWO_STAGE_FINAL_MODEL.py
```

### Opción 2: Integrar Imputación en TWO_STAGE (MEJOR)
```python
# Modificar TWO_STAGE_FINAL_MODEL.py
def load_data(self):
    # 1. Cargar raw data
    df = self._load_raw_data()
    
    # 2. Cargar holiday calendar
    holidays = pd.read_csv("outputs/holiday_calendar_2015_2026.csv", 
                          index_col=0, parse_dates=True)
    
    # 3. Join con holidays
    df = df.join(holidays[['is_weekend', 'Mexico_holiday', 'UK_holiday']], how='left')
    
    # 4. Aplicar imputación inteligente
    df = self.apply_holiday_aware_imputation(df)
    
    return df

def apply_holiday_aware_imputation(self, df):
    """Imputación basada en holidays, no mean genérico"""
    # LOCF para LME (máximo 3 días = fin de semana largo)
    df['sr_m01'] = df['sr_m01'].fillna(method='ffill', limit=3)
    
    # LOCF para FX (máximo 3 días)
    df['usdmxn'] = df['usdmxn'].fillna(method='ffill', limit=3)
    
    # Marcar imputaciones
    df['sr_m01_imputed'] = df['sr_m01'].isna()
    
    return df
```

---

## 📋 CHECKLIST DE VALIDACIÓN

- [ ] **Ejecutar**: `robust_feature_pipeline.py` para generar dataset con imputación correcta
- [ ] **Verificar**: Que `features_dataset_latest.csv` tenga columnas `*_imputed`
- [ ] **Validar**: Cero nulos en features críticos del Tier 1
- [ ] **Confirmar**: Join con holiday calendar aplicado
- [ ] **Test**: Comparar MAPE con/sin imputación basada en holidays
- [ ] **Documentar**: Métricas de calidad de imputación

---

## 💡 RECOMENDACIÓN URGENTE

**ACCIÓN INMEDIATA**:
```bash
cd C:\Users\draac\Documents\cursor\cdao_model\parte_tecnica\03_feature_engineering\03_comprehensive_analysis

# Ejecutar pipeline robusto
python robust_feature_pipeline.py

# Esto debería generar:
# - outputs/features_dataset_latest.csv (con holiday imputation)
# - outputs/features_validation_{timestamp}.json
# - outputs/imputation_report_{timestamp}.txt

# Luego re-entrenar modelo
cd ../05_final_models
python TWO_STAGE_FINAL_MODEL.py
```

---

## 🎯 CRITERIOS DE ÉXITO

### Para considerar el modelo production-ready:

1. **Nulos**: 0% en features Tier 1 después de imputación
2. **Imputación**: <5% de valores imputados en total
3. **Holiday Coverage**: 100% de festivos marcados
4. **Validación**: RMSE imputación <0.5% para gaps ≤3 días
5. **Transparencia**: Flags `*_imputed` presentes en dataset

---

## ⏰ IMPACTO EN TIMELINE

**Tiempo estimado para validación completa**: 2-4 horas

**Prioridad**: CRÍTICA - Debe hacerse ANTES del deployment

**Justificación**:
- MAPE 1.05% puede estar inflado si hay problemas de imputación
- Producción fallará si hay nulos no manejados
- Holidays no considerados = predicciones incorrectas en fines de semana

---

*Este documento identifica un gap crítico que debe resolverse antes del deploy*
