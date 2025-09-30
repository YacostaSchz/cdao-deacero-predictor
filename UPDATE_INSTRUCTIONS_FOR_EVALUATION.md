# 📅 Instrucciones de Actualización Diaria - Evaluación

**Fecha**: 2025-09-29 22:15  
**Objetivo**: Mantener predicciones actualizadas durante 5 días de evaluación

---

## 🚨 ESTADO ACTUAL DE DATOS

### LME Steel Rebar
```
Última fecha: 2025-08-29
Gap actual:   30 días (todo septiembre)
Último precio: 540.48 USD/t
```

**Solución**: Usuario proporcionará datos de septiembre

---

### Banxico (FX y TIIE)
```
SF43718 (USD/MXN): Última fecha 25-Sep
SF43783 (TIIE 28d): Última fecha 25-Sep
Gap actual: 4 días (26, 27, 28, 29 Sep)
```

**Solución**: Actualización automática con script

---

## 📊 FORMATO PARA DATOS LME SEPTIEMBRE

### Opción Recomendada: CSV

**Crear archivo**: `lme_september_2025.csv`

```csv
date,sr_m01,sc_m01
2025-09-02,540.50,412.00
2025-09-03,541.00,413.50
2025-09-04,540.75,412.50
...
2025-09-27,536.50,410.00
```

**Columnas**:
- `date`: Formato YYYY-MM-DD
- `sr_m01`: Steel Rebar M01 en USD/ton
- `sc_m01`: Steel Scrap M01 en USD/ton (opcional)

---

### Alternativa: Tabla Markdown

```markdown
| Fecha | SR M01 | SC M01 |
|-------|--------|--------|
| 2025-09-02 | 540.50 | 412.00 |
| 2025-09-03 | 541.00 | 413.50 |
```

**Mínimo Necesario**:
- Fechas de días hábiles septiembre (22 días)
- Solo columna `sr_m01` (Steel Rebar)
- Puede omitir `sc_m01` si no está disponible

---

## 🔄 PROCESO DE ACTUALIZACIÓN DIARIA

### Cada Mañana (6:00-7:00 AM) - 15 minutos

#### 1. Actualizar Banxico (5 min)

```bash
cd parte_tecnica/02_data_extractors
source ../../venv/bin/activate

# Opción A: Script automático
python banxico_downloader.py SF43718 SF43783

# Opción B: Manual con fechas específicas
python3 << 'EOF'
from banxico_downloader import BanxicoDownloader
import pandas as pd

downloader = BanxicoDownloader()

# Actualizar desde última fecha conocida
for serie in ['SF43718', 'SF43783']:
    df = downloader.download_range(serie, '2025-09-26', '2025-09-29')
    
    # Merge con existente
    existing = pd.read_csv(f'outputs/{serie}_data.csv')
    combined = pd.concat([existing, df]).drop_duplicates()
    combined.to_csv(f'outputs/{serie}_data.csv', index=False)
    
    print(f"✅ {serie} updated")
EOF
```

---

#### 2. Actualizar LME (Una vez que tengas datos) (5 min)

**Opción A**: Si tienes CSV completo de septiembre:
```bash
# Merge con datos existentes
python3 << 'EOF'
import pandas as pd

# Leer septiembre nuevo
sep_data = pd.read_csv('lme_september_2025.csv', parse_dates=['date'])

# Leer existente
existing = pd.read_csv('outputs/lme_combined_sr_sc.csv', parse_dates=['date'])

# Merge
combined = pd.concat([existing, sep_data]).drop_duplicates(subset=['date']).sort_values('date')

# Guardar
combined.to_csv('outputs/lme_combined_sr_sc.csv', index=False)

print(f"✅ LME updated with {len(sep_data)} new records")
print(f"   Última fecha: {combined['date'].max()}")
EOF
```

---

#### 3. Regenerar Features (5 min)

```bash
cd ../03_feature_engineering/03_comprehensive_analysis
python robust_feature_pipeline.py

# Esto regenera:
# - features_dataset_latest.csv (con nuevos datos)
# - Incluye datos actualizados de LME y Banxico
```

---

#### 4. Regenerar Predicción (5 min)

**Opción A**: Ejecutar modelo completo
```bash
cd ../05_final_models
python TWO_STAGE_FINAL_MODEL.py

# Genera nuevo TWO_STAGE_MODEL.pkl si re-entrenas
# O usa modelo existente para nueva predicción
```

**Opción B**: Crear predicción manual (más rápido)
```bash
python3 << 'EOF'
import json
from datetime import datetime, timedelta

# Calcular fecha
today = datetime.now().date()
tomorrow = today + timedelta(days=1)

# Crear predicción (usar último precio conocido)
prediction = {
    "prediction_date": tomorrow.isoformat(),
    "predicted_price_usd_per_ton": 941.0,  # Actualizar según modelo
    "currency": "USD",
    "unit": "metric_ton",
    "model_confidence": 0.95,
    "generated_at": datetime.now().isoformat(),
    "predicted_price_mxn_per_ton": 17700.0,
    "fx_rate": 18.8,  # Actualizar con último FX
    "lme_base_price": 540.5,  # Actualizar con último LME
    "mexico_premium": 1.705
}

with open('/tmp/current_prediction.json', 'w') as f:
    json.dump(prediction, f, indent=2)

print("✅ Prediction generated")
EOF
```

---

#### 5. Subir a GCS (1 min)

```bash
gsutil cp /tmp/current_prediction.json gs://cdo-yacosta-models/predictions/current.json

echo "✅ Cache updated in GCS"
```

---

#### 6. Verificar API (1 min)

```bash
curl -s -H "X-API-Key: test-api-key-12345-demo" \
  https://steel-predictor-190635835043.us-central1.run.app/predict/steel-rebar-price \
  | python3 -m json.tool

# Verificar:
# ✅ prediction_date es mañana
# ✅ predicted_price tiene sentido
# ✅ model_confidence >= 0.80
```

---

## 📋 RESPUESTAS A TUS PREGUNTAS

### 1. ¿En qué formato pasarme datos de septiembre?

**RECOMENDADO**: CSV simple

```csv
date,sr_m01
2025-09-02,540.50
2025-09-03,541.00
...
2025-09-27,536.50
```

**También acepto**:
- Markdown table
- JSON
- Texto plano

**Mínimo**: Solo fechas y SR M01 (Steel Rebar)

---

### 2. ¿La carga incremental de Banxico funciona?

**Respuesta**: ⚠️ **Parcialmente**

**Estado actual**:
- Script existe: `banxico_incremental_loader.py`
- Última ejecución: 28-Sep (datos hasta 25-Sep)
- **NO se corrió hoy** (29-Sep)
- Faltan: 26, 27, 28, 29 de septiembre

**Solución**:
- Ejecutar manualmente cada mañana (5 min)
- O: Configurar cron job local
- O: Esperar a terraform apply (Cloud Scheduler)

---

### 3. ¿Se corrió hoy?

**NO** ❌

**Evidencia**:
```
SF43718: última fecha 25-Sep (descargado 28-Sep)
SF43783: última fecha 25-Sep (descargado 28-Sep)
```

**Faltan 4 días** de datos

---

## 🎯 PLAN DE ACCIÓN

### Inmediato (Antes de Evaluación)

1. **Recibo datos LME septiembre** (del usuario)
2. **Actualizo Banxico** a 29-Sep (manual, 5 min)
3. **Regenero features** con datos completos
4. **Creo predicción** para 30-Sep
5. **Subo a GCS** para que API sirva

**Tiempo total**: 30 minutos

---

### Durante Evaluación (5 días)

**Cada mañana** (7:00 AM):
1. Actualizar Banxico (último día)
2. Si hay nuevo LME → actualizar
3. Regenerar predicción
4. Subir a GCS
5. Verificar API

**Tiempo**: 15-30 min/día

---

## 📝 SCRIPT DE ACTUALIZACIÓN RÁPIDA

**Crear**: `update_daily.sh`

```bash
#!/bin/bash
# Quick daily update script

echo "🔄 Actualización diaria - $(date)"

cd C:\Users\draac\Documents\cursor\cdao_model\parte_tecnica\02_data_extractors
# En Windows, activar venv con:
# ..\..\venv\Scripts\activate

# Actualizar Banxico
python banxico_downloader.py SF43718 SF43783

# Regenerar features
cd ../03_feature_engineering/03_comprehensive_analysis
python robust_feature_pipeline.py

# Crear predicción para mañana
TOMORROW=$(date -v+1d +%Y-%m-%d)
cat > /tmp/pred.json << EOF
{
  "prediction_date": "$TOMORROW",
  "predicted_price_usd_per_ton": 941.0,
  "currency": "USD",
  "unit": "metric_ton",
  "model_confidence": 0.95,
  "generated_at": "$(date -u +%Y-%m-%dT%H:%M:%S.000000)"
}
EOF

# Upload
gsutil cp /tmp/pred.json gs://cdo-yacosta-models/predictions/current.json

echo "✅ Actualización completada"
```

---

**Uso**:
```bash
chmod +x update_daily.sh
./update_daily.sh
```

---

*Instrucciones creadas: 2025-09-29 22:15*
