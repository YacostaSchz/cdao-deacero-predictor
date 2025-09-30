# API Deployment Checklist - Modelo Predicción Precios Varilla Corrugada

**Proyecto**: CDO_DeAcero - Prueba Técnica  
**Fecha Creación**: 2025-09-29  
**Estado Modelo**: ✅ COMPLETADO - MAPE 1.53% v2.1 con datos sept completos  
**Cuenta GCP**: dra.acostas@gmail.com (personal) + dra.acostas@gmail.com (compartido)  
**Proyecto GCP**: cdo-yacosta  
**Presupuesto**: $0 USD/mes (100% free tier)  
**Fecha Límite**: 2025-10-03  
**URL Producción**: https://steel-predictor-190635835043.us-central1.run.app  
**Última Actualización**: 2025-09-29 22:30  

## 🎯 Requisitos Funcionales del API

### ✅ Endpoint Principal
- [x] **URL**: `GET /predict/steel-rebar-price` ✅ DEPLOYED
- [x] **Método**: GET only ✅
- [x] **Acceso**: Público por internet ✅ https://steel-predictor-190635835043.us-central1.run.app

### ✅ Respuesta JSON Requerida
```json
{
    "prediction_date": "2025-01-XX",
    "predicted_price_usd_per_ton": 750.45,
    "currency": "USD", 
    "unit": "metric_ton",
    "model_confidence": 0.85,
    "timestamp": "2025-01-XX T00:00:00Z"
}
```

### ✅ Endpoint Raíz (Documentación)
- [ ] **URL**: `GET /`
- [ ] **Respuesta**:
```json
{
    "service": "Steel Rebar Price Predictor",
    "version": "1.0",
    "documentation_url": "[URL a documentación]",
    "data_sources": ["LME", "Banxico", "EPU", "Trade Events"],
    "last_model_update": "timestamp"
}
```

## 🔐 Requisitos de Seguridad

### ✅ Autenticación
- [ ] Header obligatorio: `X-API-Key: [valor_definido]`
- [ ] Validación en cada request
- [ ] Rechazo 401 si falta o es inválida
- [ ] Almacenar API keys hasheadas (no plaintext)

### ✅ Rate Limiting
- [ ] **Límite**: 100 requests/hora por API key
- [ ] **Implementación**: Counter por key con TTL
- [ ] **Respuesta 429**: "Too Many Requests" cuando exceda
- [ ] **Headers**: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

## 🚀 Requisitos de Performance

### ✅ Tiempo de Respuesta
- [ ] **SLA**: < 2 segundos por request
- [ ] **Target interno**: < 500ms (para margen de seguridad)
- [ ] **Cold start**: Máximo 2 segundos

### ✅ Cache
- [ ] **TTL**: 1 hora máximo
- [ ] **Estrategia**: Predicción precalculada diaria
- [ ] **Storage**: Cloud Storage o Firestore
- [ ] **Invalidación**: Manual o por schedule

### ✅ Capacidad
- [ ] Soportar 60 requests/minuto (pico esperado)
- [ ] ~7,200 requests en 5 días de evaluación
- [ ] Escalar automáticamente si necesario

## 💰 Restricciones de Costo

### ✅ Presupuesto Cloud
- [ ] **Límite estricto**: < $5 USD/mes
- [ ] **Free Tier GCP**:
  - Cloud Run: 2M requests, 360k vCPU-seconds, 180k GiB-seconds/mes
  - BigQuery: 1TB queries, 10GB storage/mes
  - Firestore: 20k reads, 20k writes/día
  - Cloud Storage: 5GB storage, 1GB network egress

### ✅ Optimizaciones de Costo
- [ ] Cloud Run scale-to-zero cuando no hay tráfico
- [ ] Predicciones precalculadas (no compute en cada request)
- [ ] Minimal container size (< 250MB)
- [ ] Sin servicios de pago (Vertex AI endpoints, etc.)

## 🏗️ Arquitectura Técnica

### ✅ Stack Recomendado (Cloud Run)
- [ ] **Runtime**: Python 3.9+ con FastAPI
- [ ] **Container**: Docker multi-stage build
- [ ] **Size**: < 250MB final image
- [ ] **Memory**: 256MB (mínimo Cloud Run)
- [ ] **CPU**: 0.25 vCPU (suficiente para servir JSON)

### ✅ Componentes GCP
- [ ] **Cloud Run**: Servicio principal (scale-to-zero)
- [ ] **Cloud Storage**: Almacenar modelo (.pkl) y predicciones
- [ ] **Cloud Scheduler**: Actualizar predicción diaria
- [ ] **Firestore**: Rate limiting counters (opcional)
- [ ] **Secret Manager**: API keys y configuración sensible

### ✅ Modelo y Datos
- [ ] **Modelo**: TWO_STAGE_MODEL.pkl (ya entrenado)
- [ ] **Size**: Verificar < 100MB
- [ ] **Loading**: En memoria al iniciar container
- [ ] **Predicción**: Precalculada, no en tiempo real

## 📝 Implementación Detallada

### ✅ Estructura del Proyecto
```
parte_tecnica/
├── 04_api_exposure/
│   ├── app/
│   │   ├── main.py              # FastAPI app
│   │   ├── models.py            # Pydantic models
│   │   ├── auth.py             # Authentication logic
│   │   ├── rate_limiter.py     # Rate limiting
│   │   ├── cache.py            # Cache management
│   │   └── config.py           # Configuration
│   ├── predictor/
│   │   ├── model_loader.py     # Load TWO_STAGE_MODEL.pkl
│   │   ├── predictor.py        # Prediction logic
│   │   └── scheduler.py        # Daily prediction update
│   ├── Dockerfile              # Multi-stage build
│   ├── requirements.txt        # Dependencies
│   ├── .env.example           # Environment variables
│   └── deploy/
│       ├── cloudbuild.yaml    # CI/CD pipeline
│       └── terraform/         # IaC (optional)
```

### ✅ FastAPI Implementation
- [ ] **Endpoints**:
  - `GET /` - Documentation
  - `GET /predict/steel-rebar-price` - Main prediction
  - `GET /health` - Health check
  - `GET /metrics` - Prometheus metrics (opcional)
- [ ] **Middleware**:
  - CORS configuration
  - Request ID tracking
  - Error handling
  - Logging
- [ ] **Validation**:
  - Pydantic models for response
  - Input validation
  - Error responses standardized

### ✅ Authentication Implementation
```python
# Pseudocode for auth.py
def verify_api_key(x_api_key: str = Header(...)):
    if not x_api_key:
        raise HTTPException(401, "Missing X-API-Key header")
    
    # Check against hashed keys in Secret Manager
    if not is_valid_key(x_api_key):
        raise HTTPException(401, "Invalid API key")
    
    return x_api_key
```

### ✅ Rate Limiting Implementation
```python
# Options:
1. In-memory (simple but not distributed)
2. Firestore (distributed, costs reads/writes)
3. Redis/Memorystore (overkill for budget)

# Recommended: Firestore with TTL
def check_rate_limit(api_key: str):
    doc_ref = firestore.collection('rate_limits').document(api_key)
    hour_key = datetime.now().strftime("%Y%m%d%H")
    
    # Atomic increment
    doc_ref.update({
        f'requests.{hour_key}': firestore.Increment(1)
    })
    
    # Check limit
    doc = doc_ref.get()
    if doc.exists and doc.to_dict().get(f'requests.{hour_key}', 0) > 100:
        raise HTTPException(429, "Rate limit exceeded")
```

### ✅ Cache Strategy
```python
# Daily prediction update
def update_daily_prediction():
    # Load model
    model = load_model('gs://cdo-yacosta-models/TWO_STAGE_MODEL.pkl')
    
    # Get latest data
    latest_data = fetch_latest_indicators()
    
    # Generate prediction
    prediction = model.predict(latest_data)
    
    # Store in Cloud Storage
    prediction_data = {
        "prediction_date": tomorrow_date,
        "predicted_price_usd_per_ton": float(prediction),
        "currency": "USD",
        "unit": "metric_ton", 
        "model_confidence": 0.95,  # Based on MAPE 1.05%
        "generated_at": datetime.utcnow().isoformat()
    }
    
    # Save to GCS
    blob = bucket.blob('predictions/current.json')
    blob.upload_from_string(json.dumps(prediction_data))
```

## 🚀 Deployment Steps

### ✅ Local Development
- [ ] Setup Python environment
- [ ] Install dependencies
- [ ] Test with uvicorn locally
- [ ] Verify all endpoints work
- [ ] Test rate limiting logic
- [ ] Load test with locust/k6

### ✅ Docker Build
```dockerfile
# Multi-stage Dockerfile
FROM python:3.9-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.9-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY . .
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### ✅ GCP Setup
```bash
# 1. Authenticate with personal account
gcloud config configurations activate personal
gcloud auth login
gcloud config set project cdo-yacosta

# 2. Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable secretmanager.googleapis.com

# 3. Create service account
gcloud iam service-accounts create steel-predictor-sa \
  --display-name="Steel Price Predictor Service Account"

# 4. Grant permissions
gcloud projects add-iam-policy-binding cdo-yacosta \
  --member="serviceAccount:steel-predictor-sa@cdo-yacosta.iam.gserviceaccount.com" \
  --role="roles/datastore.user"

# 5. Create secrets
echo -n "your-api-key-here" | gcloud secrets create api-keys --data-file=-
```

### ✅ Cloud Run Deployment
```bash
# 1. Build container
gcloud builds submit --tag gcr.io/cdo-yacosta/steel-predictor

# 2. Deploy to Cloud Run
gcloud run deploy steel-predictor \
  --image gcr.io/cdo-yacosta/steel-predictor \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --service-account steel-predictor-sa@cdo-yacosta.iam.gserviceaccount.com \
  --max-instances 2 \
  --min-instances 0 \
  --memory 256Mi \
  --cpu 0.25 \
  --timeout 60 \
  --concurrency 80

# 3. Get service URL
gcloud run services describe steel-predictor --region us-central1 --format 'value(status.url)'
```

### ✅ Cloud Scheduler Setup
```bash
# Create daily prediction update job
gcloud scheduler jobs create http update-steel-prediction \
  --location us-central1 \
  --schedule "0 6 * * *" \
  --time-zone "America/Mexico_City" \
  --uri "https://steel-predictor-xxx.run.app/internal/update-prediction" \
  --http-method POST \
  --headers "X-API-Key=internal-scheduler-key"
```

## 📊 Monitoring & Operations

### ✅ Logging
- [ ] Structured logging (JSON format)
- [ ] Request/response logging
- [ ] Error tracking
- [ ] Performance metrics

### ✅ Monitoring
- [ ] Cloud Run metrics dashboard
- [ ] Uptime checks
- [ ] Alert on errors > threshold
- [ ] Alert on latency > 1.5s

### ✅ Testing Strategy
- [ ] Unit tests for each component
- [ ] Integration tests for API
- [ ] Load testing (vegeta/k6)
- [ ] End-to-end test automation

## 📋 Pre-Launch Checklist

### ✅ Security
- [ ] API keys stored in Secret Manager
- [ ] HTTPS only (Cloud Run provides)
- [ ] No sensitive data in logs
- [ ] Input validation on all endpoints

### ✅ Documentation
- [ ] API documentation (OpenAPI/Swagger)
- [ ] README with deployment instructions
- [ ] Architecture diagram
- [ ] Postman collection

### ✅ Cost Verification
- [ ] Estimate monthly requests
- [ ] Verify free tier coverage
- [ ] Set up billing alerts at $4
- [ ] Document cost breakdown

## 🚨 Risk Mitigation

### ✅ Technical Risks
- [ ] **Cold starts**: Pre-warm with uptime checks
- [ ] **Model drift**: Monitor prediction accuracy
- [ ] **Data freshness**: Alert if data > 24h old
- [ ] **Dependency updates**: Lock versions

### ✅ Operational Risks
- [ ] **Backup API keys**: Store securely
- [ ] **Rollback plan**: Keep previous versions
- [ ] **Incident response**: Document procedures
- [ ] **Data backup**: Export predictions daily

## 📝 Entregables Finales

### ✅ Para la Evaluación
- [ ] URL del endpoint público
- [ ] API Key funcional
- [ ] Repositorio GitHub con:
  - [ ] Código fuente completo
  - [ ] README detallado
  - [ ] Instrucciones de deployment
  - [ ] Justificación técnica de decisiones
- [ ] Postman collection para testing
- [ ] Documentación de arquitectura

### ✅ Extras Valorados
- [ ] Dashboard de monitoreo
- [ ] CI/CD pipeline
- [ ] Tests automatizados
- [ ] Endpoint de explicabilidad
- [ ] Métricas de performance

## 🎯 Criterios de Éxito

### ✅ Cuantitativos
- [ ] MAPE < 10% mantenido en producción
- [ ] Latencia < 500ms p95
- [ ] Uptime > 99.5%
- [ ] Costo < $5/mes verificado

### ✅ Cualitativos
- [ ] Código limpio y documentado
- [ ] Arquitectura escalable
- [ ] Fácil de mantener
- [ ] Seguro y robusto

---

**NOTA IMPORTANTE**: Con el modelo Two-Stage ya alcanzando MAPE 1.05%, el foco debe estar en:
1. **Simplicidad**: No sobre-ingeniería, el modelo ya es excelente
2. **Confiabilidad**: Asegurar uptime y consistencia
3. **Costo**: Mantenerse estrictamente bajo $5/mes
4. **Velocidad**: Desplegar rápido, quedan solo 4 días

