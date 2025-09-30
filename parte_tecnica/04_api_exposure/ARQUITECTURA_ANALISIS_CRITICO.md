# Análisis Crítico de Arquitectura - API Deployment

**Fecha**: 2025-09-29  
**Analista**: Sr Data Scientist - CausalOps  
**Contexto**: Deployment de modelo Two-Stage (MAPE 1.05%) con restricción $5/mes  

## 🎯 Resumen Ejecutivo

### Situación Actual
- **Modelo**: Two-Stage completado, MAPE 1.05% (excepcional)
- **Tiempo restante**: 4 días hasta deadline
- **Restricción crítica**: < $5 USD/mes
- **Tráfico esperado**: ~1,440 requests/día durante 5 días evaluación
- **Cuenta GCP**: Personal (dra.acostas@gmail.com)
- **Proyecto**: cdo-yacosta

### Recomendación Principal
**Cloud Run con predicciones precalculadas** es la opción óptima por:
1. Costo efectivo (free tier cubre 100% necesidades)
2. Implementación rápida (2 días máximo)
3. Mantenimiento simple
4. Escalabilidad futura

## 📊 Análisis Comparativo de Arquitecturas

### 1️⃣ Cloud Run + Predicción Precalculada (RECOMENDADA)

#### Arquitectura
```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│ Cloud Scheduler │────►│ Cloud Run    │────►│   Cloud     │
│ (Daily Update)  │     │ (FastAPI)    │     │  Storage    │
└─────────────────┘     └──────────────┘     │ (JSON/PKL)  │
                               ▲              └─────────────┘
                               │
                        ┌──────┴──────┐
                        │   Client    │
                        │  Requests   │
                        └─────────────┘
```

#### Ventajas
- ✅ **Costo**: $0/mes con free tier (2M requests, 180k vCPU-seconds)
- ✅ **Performance**: <100ms latencia (solo sirve JSON precalculado)
- ✅ **Simplicidad**: FastAPI + Docker, stack conocido
- ✅ **Scale-to-zero**: No paga cuando no hay tráfico
- ✅ **Flexibilidad total**: Control completo sobre lógica

#### Desventajas
- ❌ Requiere conocimiento Docker (mitigable con templates)
- ❌ Setup inicial más manual que Functions

#### Implementación Estimada
- **Día 1**: FastAPI app + Docker (8h)
- **Día 2**: Deploy + Testing (4h)
- **Total**: 1.5 días

### 2️⃣ Cloud Functions + BigQuery

#### Arquitectura
```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│ Cloud Scheduler │────►│   BigQuery   │────►│   Cloud     │
│ (Daily ML)      │     │  (ML.ARIMA)  │     │  Function   │
└─────────────────┘     └──────────────┘     │  (Python)   │
                                              └─────────────┘
                                                     ▲
                                                     │
                                              ┌──────┴──────┐
                                              │   Client    │
                                              │  Requests   │
                                              └─────────────┘
```

#### Ventajas
- ✅ **Desarrollo rápido**: No Docker, solo código Python
- ✅ **BigQuery ML**: Retraining con SQL (CREATE MODEL)
- ✅ **Costo**: $0/mes igualmente (misma free tier)

#### Desventajas
- ❌ **Modelo limitado**: Two-Stage model no cabe en BQ ML
- ❌ **Latencia BQ**: 200-500ms si consulta en tiempo real
- ❌ **Menos control**: Limitaciones de Functions runtime

#### Implementación Estimada
- **Día 1**: Function + BigQuery setup (6h)
- **Total**: 1 día (pero modelo incompatible)

### 3️⃣ Vertex AI (NO VIABLE)

#### Por qué NO es viable
- ❌ **Costo prohibitivo**: $540+/mes (endpoint 24/7)
- ❌ **No scale-to-zero**: Siempre consume recursos
- ❌ **Overkill**: Para 1 modelo simple es excesivo
- ❌ **Tiempo**: Setup complejo, 3+ días

#### Cuándo sería útil
- Múltiples modelos complejos
- Presupuesto enterprise ($1000+/mes)
- Requerimientos MLOps avanzados

## 🔍 Análisis de Restricciones

### 1. Presupuesto < $5/mes

| Servicio | Free Tier | Necesitamos | ¿Suficiente? |
|----------|-----------|-------------|--------------|
| Cloud Run | 2M requests/mes | 7,200 total | ✅ Sobra 99.6% |
| Cloud Run | 180k vCPU-s/mes | ~100 vCPU-s | ✅ Sobra 99.9% |
| Storage | 5GB/mes | <1MB | ✅ Sobra 99.9% |
| Firestore | 20k reads/día | ~1,440/día | ✅ Sobra 93% |

**Conclusión**: Free tier cubre 100% sin riesgo.

### 2. Performance < 2s

| Componente | Latencia | Notas |
|------------|----------|-------|
| Cloud Run warm | 50-100ms | Container ya iniciado |
| Cloud Run cold | 1-2s | Primera request |
| Leer JSON cache | <10ms | Desde memoria |
| Network RTT | 50-100ms | Variable |
| **Total P95** | **<200ms** | **Cumple 10x** |

### 3. Rate Limiting 100/hora

**Opciones evaluadas**:

#### A. In-Memory (Simple)
```python
# Diccionario en memoria
rate_limits = {}  # {api_key: {hour: count}}
```
- ✅ Simplicidad máxima
- ❌ Se pierde en restart
- ❌ No distribuido

#### B. Firestore (Recomendado)
```python
# Documento por API key con TTL
firestore.collection('limits').document(api_key)
```
- ✅ Persistente
- ✅ Distribuido
- ✅ Free tier suficiente
- ❌ +50ms latencia

#### C. Redis/Memorystore
- ❌ Costo $50+/mes
- ❌ Overkill para este volumen

**Decisión**: Firestore para producción, in-memory para MVP.

## 💡 Estrategia de Implementación Óptima

### Fase 1: MVP Funcional (Día 1)
```
Morning (4h):
- FastAPI básico con 2 endpoints
- Autenticación X-API-Key hardcoded
- Rate limiting in-memory simple
- Respuesta JSON estática

Afternoon (4h):
- Dockerizar aplicación
- Deploy a Cloud Run
- Test endpoints públicos
- Documentación básica
```

### Fase 2: Producción (Día 2)
```
Morning (4h):
- Integrar modelo real (.pkl)
- Cloud Storage para predicciones
- Cloud Scheduler daily update
- Firestore rate limiting

Afternoon (4h):
- Testing exhaustivo
- Monitoring setup
- Documentation final
- Postman collection
```

### Fase 3: Polish (Día 3)
```
- CI/CD con Cloud Build
- Alertas y dashboards
- Load testing
- Optimizaciones finales
```

## 🚨 Riesgos y Mitigaciones

### Riesgo 1: Cold Start > 2s
**Probabilidad**: Media  
**Impacto**: Alto (falla requisito)  
**Mitigación**: 
- Container mínimo (<100MB)
- Uptime checks cada 5 min
- Min instances = 1 durante evaluación

### Riesgo 2: Costo inesperado
**Probabilidad**: Baja  
**Impacto**: Alto (falla restricción)  
**Mitigación**:
- Billing alerts en $3
- Quotas en Cloud Run
- Monitoring diario

### Riesgo 3: Modelo no carga
**Probabilidad**: Baja  
**Impacto**: Crítico  
**Mitigación**:
- Verificar tamaño .pkl < 100MB
- Test local exhaustivo
- Fallback a modelo simple

## 📈 Análisis Costo-Beneficio

### Opción Cloud Run
**Costo desarrollo**: 16 horas ($0 real)  
**Costo operación**: $0/mes  
**Beneficios**:
- Cumple 100% requisitos
- Extensible futuro
- Portfolio showcase

### ROI Estimado
- Tiempo invertido: 2 días
- Aprendizaje: Cloud Run, GCP, MLOps
- Valor CV: Alto (arquitectura cloud moderna)

## 🎯 Decisión Final y Justificación

### Arquitectura Seleccionada: Cloud Run + Predicciones Precalculadas

#### Justificación Técnica
1. **Performance**: Latencia <200ms garantizada
2. **Costo**: $0/mes con free tier
3. **Simplicidad**: Stack Python/Docker familiar
4. **Tiempo**: Implementable en 2 días

#### Justificación de Negocio
1. **Confiabilidad**: SLA 99.95% de Google
2. **Escalabilidad**: De 0 a 1000 QPS sin cambios
3. **Mantenibilidad**: Código simple, bien documentado

#### Por qué NO las otras opciones
- **Functions**: Modelo Two-Stage incompatible con BigQuery ML
- **Vertex AI**: 108x sobre presupuesto ($540 vs $5)

## 🏁 Siguientes Pasos Inmediatos

1. **HOY (4h)**:
   - [ ] Crear estructura proyecto FastAPI
   - [ ] Endpoint básico funcionando
   - [ ] Dockerfile inicial

2. **MAÑANA (8h)**:
   - [ ] Deploy a Cloud Run
   - [ ] Integración modelo real
   - [ ] Testing completo

3. **PASADO MAÑANA (4h)**:
   - [ ] Documentación final
   - [ ] Entrega

## 💭 Reflexión Final

> "La perfección se alcanza no cuando no hay nada más que añadir, sino cuando no hay nada más que quitar." - Antoine de Saint-Exupéry

Con un modelo que ya logra MAPE 1.05%, la arquitectura debe ser **simple, confiable y económica**. Cloud Run ofrece el balance perfecto entre estas tres dimensiones.

No necesitamos Kubernetes, ni Vertex AI, ni arquitecturas complejas. Solo un container eficiente sirviendo JSON precalculado.

**El modelo ya ganó. Ahora solo necesitamos servirlo bien.**

