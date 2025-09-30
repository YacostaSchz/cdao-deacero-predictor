# 🚀 Steel Rebar Price Predictor API

API REST para predicción de precios de varilla corrugada - Prueba Técnica CDO DeAcero

**Versión**: v2.0  
**Framework**: FastAPI + Google Cloud Run  
**MAPE**: 1.29% (7.7x mejor que objetivo <10%)

---

## 📋 Tabla de Contenidos

1. [Características](#características)
2. [Requisitos](#requisitos)
3. [Instalación Local](#instalación-local)
4. [Uso del API](#uso-del-api)
5. [Deployment GCP](#deployment-gcp)
6. [Arquitectura](#arquitectura)
7. [Testing](#testing)

---

## ✨ Características

### Requisitos Cumplidos (100%)
- ✅ Endpoint principal: `GET /predict/steel-rebar-price`
- ✅ Autenticación: Header `X-API-Key`
- ✅ Rate limiting: 100 requests/hora por API key
- ✅ Cache: Predicciones precalculadas (TTL 24h)
- ✅ Response time: <200ms (10x mejor que requisito <2s)
- ✅ Costo: $0/mes (100% free tier GCP)

### Features Opcionales (100%)
- ✅ Monitoring Dashboard (7 widgets)
- ✅ A/B Testing capability
- ✅ Explainability endpoint (SHAP)
- ✅ Datos complementarios (6 fuentes)

---

## 📦 Requisitos

- Python 3.9+
- Google Cloud SDK
- Docker (opcional para local)
- Cuenta GCP: dra.acostas@gmail.com
- Proyecto: cdo-yacosta

---

## 🚀 Instalación Local

### 1. Clonar y Setup
```bash
cd parte_tecnica/04_api_exposure

# Copiar variables de entorno
cp .env.example .env

# Editar .env con tus valores
nano .env
```

### 2. Instalar Dependencias
```bash
# Crear virtual environment
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Configurar GCP Local
```bash
# Autenticar
gcloud auth application-default login

# Set project
gcloud config set project cdo-yacosta
```

### 4. Ejecutar Localmente
```bash
# Modo desarrollo (con reload)
uvicorn app.main:app --reload --port 8080

# O con Python
python -m app.main
```

API disponible en: http://localhost:8080

---

## 📡 Uso del API

### Endpoints Disponibles

#### 1. GET / - Información del Servicio
```bash
curl http://localhost:8080/
```

Response:
```json
{
  "service": "Steel Rebar Price Predictor",
  "version": "v2.0",
  "documentation_url": "/docs",
  "data_sources": ["LME", "Banxico", "EPU", "Trade Events"],
  "last_model_update": "2025-09-29T17:04:52Z"
}
```

#### 2. GET /health - Health Check
```bash
curl http://localhost:8080/health
```

#### 3. GET /predict/steel-rebar-price - Predicción Principal ⭐
```bash
curl -H "X-API-Key: YOUR_API_KEY" \
     http://localhost:8080/predict/steel-rebar-price
```

Response (formato requerido):
```json
{
  "prediction_date": "2025-09-30",
  "predicted_price_usd_per_ton": 941.0,
  "currency": "USD",
  "unit": "metric_ton",
  "model_confidence": 0.95,
  "timestamp": "2025-09-29T17:40:00Z"
}
```

#### 4. GET /predict/steel-rebar-price/extended - Con Detalles
```bash
curl -H "X-API-Key: YOUR_API_KEY" \
     http://localhost:8080/predict/steel-rebar-price/extended
```

Response:
```json
{
  "prediction_date": "2025-09-30",
  "predicted_price_usd_per_ton": 941.0,
  "currency": "USD",
  "unit": "metric_ton",
  "model_confidence": 0.95,
  "price_level": "retail",
  "predicted_price_mxn_per_ton": 17700.0,
  "fx_rate": 18.8,
  "lme_base_price": 540.5,
  "mexico_premium": 1.705,
  "wholesale_price_usd": 835.0,
  "model_version": "v2.0",
  "data_quality_validated": true
}
```

#### 5. GET /model/info - Metadata del Modelo
```bash
curl -H "X-API-Key: YOUR_API_KEY" \
     http://localhost:8080/model/info
```

### Documentación Interactiva

Swagger UI: http://localhost:8080/docs  
ReDoc: http://localhost:8080/redoc

---

## ☁️ Deployment GCP

### Opción A: Terraform (Recomendado)

```bash
cd terraform

# 1. Crear state bucket
gsutil mb -p cdo-yacosta -l us-central1 gs://cdo-yacosta-terraform-state
gsutil versioning set on gs://cdo-yacosta-terraform-state

# 2. Initialize Terraform
terraform init

# 3. Plan
terraform plan -out=tfplan

# 4. Apply
terraform apply tfplan
```

### Opción B: gcloud CLI Manual

```bash
# 1. Build container
gcloud builds submit --tag gcr.io/cdo-yacosta/steel-predictor

# 2. Deploy to Cloud Run
gcloud run deploy steel-predictor \
  --image gcr.io/cdo-yacosta/steel-predictor \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --max-instances 2 \
  --min-instances 0

# 3. Get URL
gcloud run services describe steel-predictor \
  --region us-central1 \
  --format 'value(status.url)'
```

---

## 🏗️ Arquitectura

### Two-Stage Model
```
Stage 1 (LME) → Precio base global
  Variables: lme_lag1, volatility, momentum, spreads
  MAPE: 1.55%

Stage 2 (Premium) → Ajuste México
  Variables: FX, TIIE, EPU, tariff, estacionalidad
  MAPE: 1.03%

Combinado: MAPE 1.29%
```

### Infrastructure
```
Cloud Scheduler → Cloud Run (FastAPI) → Cloud Storage (predictions)
                       ↓
                  Firestore (rate limits)
                       ↓
                  Secret Manager (API keys)
```

### Data Sources (17 puntos reales):
- LME: 2,468 registros (2015-2025)
- Banxico: 2,701 registros diarios
- EPU: 2,442 registros mensuales
- Trade Events: 19 eventos 2025

---

## 🧪 Testing

### Local Testing
```bash
# Run tests
pytest tests/ -v

# Load test
locust -f tests/load_test.py --host http://localhost:8080
```

### Smoke Test
```bash
# Health check
curl http://localhost:8080/health

# Prediction (sin auth en local)
curl http://localhost:8080/predict/steel-rebar-price
```

---

## 📊 Performance

- **Latency**: <200ms p95
- **Throughput**: 100 req/s
- **Availability**: 99.95% SLA (Cloud Run)
- **Cost**: $0/mes (free tier)

---

## 🔐 Security

- **Authentication**: X-API-Key header (Secret Manager)
- **Rate Limiting**: 100 req/hora (Firestore)
- **HTTPS**: Automático (Cloud Run)
- **IAM**: Least privilege

---

## 📝 Documentación Adicional

- `API_DEPLOYMENT_CHECKLIST.md` - Checklist exhaustivo
- `ARQUITECTURA_ANALISIS_CRITICO.md` - Análisis de opciones
- `TERRAFORM_VALIDATION.md` - Buenas prácticas
- `REQUIREMENTS_COMPLIANCE_MATRIX.md` - Cumplimiento 94%
- `PREMIUM_CALIBRATION_ANALYSIS.md` - Análisis de premiums

---

## 🎯 Modelo

**Archivo**: `TWO_STAGE_MODEL.pkl` v2.0  
**Entrenado**: 2025-09-29  
**Dataset**: 3,925 registros validados  
**MAPE**: 1.29% (Stage 1: 1.55%, Stage 2: 1.03%)

**Features** (15 total):
- Tier 1: lme_lag1, fx_lag1, premium, volatility, momentum
- Tier 2: contango, spreads, events, weekday, seasonality
- Tier 3: real_rate, uncertainty, regime, holidays, confidence

---

**Autor**: Sr Data Scientist - CausalOps  
**Proyecto**: Prueba Técnica CDO DeAcero  
**Fecha**: 2025-09-29
