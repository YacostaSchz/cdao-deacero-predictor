# 📅 ESTRATEGIA DE DÍAS INHÁBILES E IMPUTACIÓN
## Análisis 2015-2026 para Predicción de Precio Varilla Corrugada

**Generado**: 2025-09-28 19:45  
**Cobertura**: 2015-01-01 a 2026-12-31  
**Países**: México, USA, UK (LME), China, Turquía  

---

## 📊 RESUMEN EJECUTIVO

### Días Inhábiles Promedio por País
| País | Festivos/Año | Con Fines de Semana | Total Días Cerrados/Año |
|------|--------------|---------------------|-------------------------|
| México | 9.8 | + 104 (sáb/dom) | ~114 días |
| USA | 9.0 | + 104 (sáb/dom) | ~113 días |
| UK (LME) | 8.2 | + 104 (sáb/dom) | ~112 días |
| China | 16.0 | + 104 (sáb/dom) | ~120 días |
| Turquía | 6.0 | + 104 (sáb/dom) | ~110 días |

### Hallazgos Críticos
- **1,282 días** donde México, USA y UK están cerrados simultáneamente
- **58 días** donde México está abierto pero LME cerrado ⚠️
- China tiene las vacaciones más largas (Golden Weeks de 7 días)

---

## 🎯 ESTRATEGIAS DE IMPUTACIÓN POR FUENTE

### 1. LME Steel Rebar (Variable Principal)
```python
# Estrategia: LOCF (Last Observation Carried Forward)
if gap_days <= 3:
    use_LOCF()  # Viernes se extiende a lunes
elif gap_days > 3:
    use_linear_interpolation()  # Semana Santa, etc.
    
# Validación
if abs(imputed - actual) > 2 * volatility_20d:
    flag_as_anomaly()
```

**Justificación**: Precios de cierre se mantienen hasta siguiente día hábil

### 2. Banxico (USD/MXN, TIIE)
```python
# Fines de semana normales
weekend_imputation = LOCF(max_days=2)

# Días festivos México
if mexican_holiday:
    if consecutive_days <= 3:
        use_LOCF()
    else:
        use_interpolation()
```

**Casos Especiales**:
- Semana Santa: Hasta 4 días consecutivos
- Fin de año: Puede combinar con fines de semana

### 3. Asincronía México-LME
```python
# Cuando México abierto pero LME cerrado
if mexico_open and lme_closed:
    # Ajuste por movimiento cambiario
    lme_imputed = lme_last * (1 + 0.15 * fx_change)
    set_flag('lme_imputed', True)
```

**Días Típicos**:
- Good Friday (UK cerrado, México abierto)
- UK Bank Holidays
- Día de la Constitución México (LME abierto)

### 4. EPU Indices (Mensual)
- **No requieren imputación diaria**
- Publicación puede retrasarse 1-2 días por holidays
- Usar último valor conocido hasta nueva publicación

---

## 📋 IMPLEMENTACIÓN EN EL PIPELINE

### Código de Imputación
```python
def apply_holiday_imputation(df, calendar_df):
    """
    Aplica estrategia de imputación basada en calendario de días inhábiles
    """
    # Cargar calendario
    calendar = pd.read_csv('holiday_calendar_2015_2026.csv', index_col=0, parse_dates=True)
    
    # Para cada serie
    for col in ['sr_m01', 'usdmxn', 'tiie28']:
        # Identificar gaps
        gaps = df[col].isna()
        
        if gaps.any():
            # Verificar si es día inhábil
            gap_dates = df.index[gaps]
            is_holiday = calendar.loc[gap_dates, f'{source_country}_holiday']
            
            # Aplicar estrategia
            if is_holiday.all():
                # LOCF para holidays
                df[col] = df[col].ffill(limit=3)
            else:
                # Interpolación para gaps largos
                df[col] = df[col].interpolate(method='time')
                
            # Marcar imputaciones
            df[f'{col}_imputed'] = gaps
    
    return df
```

### Validación Post-Imputación
```python
def validate_imputation(df_imputed, df_actual):
    """
    Calcula métricas de calidad de imputación
    """
    metrics = {}
    
    for col in ['sr_m01', 'usdmxn']:
        mask = df_imputed[f'{col}_imputed'] == True
        if mask.any():
            imputed_values = df_imputed.loc[mask, col]
            actual_values = df_actual.loc[mask, col]
            
            metrics[col] = {
                'rmse': np.sqrt(((imputed_values - actual_values) ** 2).mean()),
                'mae': (imputed_values - actual_values).abs().mean(),
                'max_error': (imputed_values - actual_values).abs().max()
            }
    
    return metrics
```

---

## 🚨 CASOS ESPECIALES 2024-2026

### Semana Santa
- **2024**: 28 marzo - 1 abril (Jueves-Lunes)
- **2025**: 17-21 abril (Jueves-Lunes)
- **2026**: 2-6 abril (Jueves-Lunes)

**Estrategia**: Interpolación lineal LME, LOCF para Banxico

### Fin de Año
- **Navidad + Año Nuevo**: Puede crear gaps de 4-5 días
- **Estrategia**: Usar último valor de diciembre para primeros días enero

### Golden Week China
- **Spring Festival**: 7 días consecutivos (fecha variable)
- **National Day**: 1-7 octubre
- **Impacto**: EPU China sin actualización por ~10 días

---

## 📊 MÉTRICAS DE CALIDAD

### Esperadas por Tipo de Imputación
| Método | RMSE Típico | Casos de Uso |
|--------|-------------|--------------|
| LOCF (1-3 días) | < 0.5% | Fines de semana |
| Interpolación (4-7 días) | < 1.5% | Semana Santa |
| Ajuste FX | < 2.0% | Asincronía mercados |

### Flags de Calidad
```python
quality_flags = {
    'imputation_method': 'LOCF|interpolation|fx_adjusted',
    'gap_days': int,
    'confidence': 'high|medium|low',
    'anomaly_detected': bool
}
```

---

## ✅ CHECKLIST DE IMPLEMENTACIÓN

- [ ] Cargar `holiday_calendar_2015_2026.csv` en pipeline
- [ ] Implementar función `apply_holiday_imputation()`
- [ ] Añadir columnas `*_imputed` para transparencia
- [ ] Validar contra datos históricos conocidos
- [ ] Documentar casos de imputación en logs
- [ ] Monitorear calidad de imputación en producción

---

## 📎 ARCHIVOS GENERADOS

1. **holiday_calendar_2015_2026.csv** (4,383 filas)
   - Columnas: date, is_weekend, {country}_holiday, {country}_business_day
   
2. **imputation_strategies.json**
   - Estrategias detalladas por fuente de datos
   
3. **holiday_calendar_analyzer.py**
   - Script para regenerar calendario con updates

---

*Documento parte del pipeline de features para predicción de precio varilla corrugada t+1*
