# 🚀 Ejemplos de Uso - Steel Price Predictor API

**Service URL**: https://steel-predictor-190635835043.us-central1.run.app  
**API Key**: test-api-key-12345-demo

---

## 🎯 ENDPOINT PRINCIPAL - Predicción de Precio

### Curl (Copiar y Pegar)
```bash
curl -X GET \
  -H "X-API-Key: test-api-key-12345-demo" \
  https://steel-predictor-190635835043.us-central1.run.app/predict/steel-rebar-price
```

### Respuesta Esperada
```json
{
  "prediction_date": "2025-10-01",
  "predicted_price_usd_per_ton": 941.0,
  "currency": "USD",
  "unit": "metric_ton",
  "model_confidence": 0.85,
  "timestamp": "2025-09-30T00:24:48Z"
}
```

---

## 📊 ENDPOINT EXTENDIDO - Con Breakdown Mayorista/Minorista

### Curl
```bash
curl -X GET \
  -H "X-API-Key: test-api-key-12345-demo" \
  https://steel-predictor-190635835043.us-central1.run.app/predict/steel-rebar-price/extended
```

### Respuesta Esperada
```json
{
  "prediction_date": "2025-10-01",
  "predicted_price_usd_per_ton": 941.0,
  "currency": "USD",
  "unit": "metric_ton",
  "model_confidence": 0.85,
  "price_level": "retail",
  "wholesale_price_usd": 835.04,
  "model_version": "v2.0",
  "data_quality_validated": true
}
```

---

## ℹ️ INFORMACIÓN DEL SERVICIO

### Curl
```bash
curl https://steel-predictor-190635835043.us-central1.run.app/
```

### Respuesta
```json
{
  "service": "Steel Rebar Price Predictor",
  "version": "v2.0",
  "documentation_url": "/docs",
  "data_sources": ["LME", "Banxico", "EPU", "Trade Events"],
  "last_model_update": "2025-09-29T17:04:52Z"
}
```

---

## 🏥 HEALTH CHECK

### Curl
```bash
curl https://steel-predictor-190635835043.us-central1.run.app/health
```

### Respuesta
```json
{
  "status": "healthy",
  "model_loaded": true,
  "cache_fresh": true
}
```

---

## 🔧 METADATA DEL MODELO

### Curl
```bash
curl -X GET \
  -H "X-API-Key: test-api-key-12345-demo" \
  https://steel-predictor-190635835043.us-central1.run.app/model/info
```

### Respuesta
```json
{
  "model_version": "v2.0-two-stage",
  "architecture": "LME (global) + Premium (MX local)",
  "trained_date": "2025-09-29T17:04:52.667431",
  "data_quality": "Validated with holiday imputation",
  "lme_mape_test": 1.55,
  "premium_mape_test": 1.03,
  "combined_mape": 1.29
}
```

---

## 📱 OTROS LENGUAJES

### Python
```python
import requests

url = "https://steel-predictor-190635835043.us-central1.run.app/predict/steel-rebar-price"
headers = {"X-API-Key": "test-api-key-12345-demo"}

response = requests.get(url, headers=headers)
data = response.json()

print(f"Precio previsto: {data['predicted_price_usd_per_ton']} USD/ton")
print(f"Fecha: {data['prediction_date']}")
print(f"Confianza: {data['model_confidence']}")
```

### JavaScript/Node.js
```javascript
const fetch = require('node-fetch');

const url = "https://steel-predictor-190635835043.us-central1.run.app/predict/steel-rebar-price";
const headers = { "X-API-Key": "test-api-key-12345-demo" };

fetch(url, { headers })
  .then(res => res.json())
  .then(data => {
    console.log(`Precio: ${data.predicted_price_usd_per_ton} USD/ton`);
    console.log(`Fecha: ${data.prediction_date}`);
  });
```

### PowerShell
```powershell
$url = "https://steel-predictor-190635835043.us-central1.run.app/predict/steel-rebar-price"
$headers = @{"X-API-Key" = "test-api-key-12345-demo"}

$response = Invoke-RestMethod -Uri $url -Headers $headers -Method Get
Write-Host "Precio: $($response.predicted_price_usd_per_ton) USD/ton"
```

---

## 🧪 TESTING

### Test Completo (Bash Script)
```bash
#!/bin/bash

BASE_URL="https://steel-predictor-190635835043.us-central1.run.app"
API_KEY="test-api-key-12345-demo"

echo "1. Service Info:"
curl -s $BASE_URL/ | jq '.'

echo -e "\n2. Health Check:"
curl -s $BASE_URL/health | jq '.'

echo -e "\n3. Prediction (con API key):"
curl -s -H "X-API-Key: $API_KEY" $BASE_URL/predict/steel-rebar-price | jq '.'

echo -e "\n4. Extended Prediction:"
curl -s -H "X-API-Key: $API_KEY" $BASE_URL/predict/steel-rebar-price/extended | jq '.'
```

---

## 📝 NOTAS IMPORTANTES

### Precio Minorista vs Mayorista
El API retorna precio **minorista** (consumidor final CDMX) por defecto:
- **Minorista**: 941 USD/t (premium 1.705 sobre LME)
- **Mayorista**: 835 USD/t (premium 1.569 sobre LME)

Para obtener precio mayorista:
```
price_wholesale = price_retail × 0.8874
```

### Rate Limiting
- **Límite**: 100 requests por hora por API key
- **Reset**: Cada hora en punto
- **Headers**: X-RateLimit-Limit, X-RateLimit-Remaining

### Cache
- Predicciones pre-calculadas diariamente
- Cache TTL: 24 horas
- Actualización: 6:00 AM Mexico City

---

## 🔗 DOCUMENTACIÓN INTERACTIVA

**Swagger UI**:
https://steel-predictor-190635835043.us-central1.run.app/docs

**ReDoc**:
https://steel-predictor-190635835043.us-central1.run.app/redoc

---

*Última actualización: 2025-09-29 18:25*
