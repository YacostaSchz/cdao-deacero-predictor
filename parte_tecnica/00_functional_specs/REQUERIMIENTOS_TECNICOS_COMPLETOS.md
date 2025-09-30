# 📋 REQUERIMIENTOS TÉCNICOS COMPLETOS - Prueba CDO DeAcero
## Predicción de Precios de Varilla Corrugada

### 📅 Información General
- **Plazo de entrega**: 7 días calendario desde la recepción
- **Inicio de evaluación**: Al día siguiente de la entrega
- **Período de evaluación**: 5 días consecutivos

---

## 🎯 1. OBJETIVO PRINCIPAL
Desarrollar y desplegar un **API REST** que prediga el precio de cierre del día siguiente para la varilla corrugada, utilizando datos históricos disponibles públicamente.

---

## 🔧 2. REQUERIMIENTOS FUNCIONALES

### 2.1 Endpoint Principal (OBLIGATORIO)
- **Método**: GET
- **Ruta**: `/predict/steel-rebar-price`
- **Acceso**: Público accesible por internet
- **Único endpoint**: Solo UN endpoint principal será evaluado

### 2.2 Formato de Respuesta (OBLIGATORIO)
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

### 2.3 Endpoint Raíz (OBLIGATORIO)
- **Método**: GET
- **Ruta**: `/`
- **Respuesta requerida**:
```json
{
    "service": "Steel Rebar Price Predictor",
    "version": "1.0",
    "documentation_url": "[URL a su documentación]",
    "data_sources": ["lista de fuentes utilizadas"],
    "last_model_update": "timestamp"
}
```

---

## 🔒 3. REQUERIMIENTOS DE SEGURIDAD Y CONTROL

### 3.1 Autenticación (OBLIGATORIO)
- **Header requerido**: `X-API-Key`
- **Valor**: Definido por el candidato
- **Aplicación**: En el endpoint principal

### 3.2 Rate Limiting (OBLIGATORIO)
- **Límite**: 100 requests por hora
- **Aplicación**: Por API key
- **Respuesta al exceder**: Retornar código HTTP apropiado (429)

### 3.3 Cache (OBLIGATORIO)
- **Duración máxima**: 1 hora
- **Propósito**: Evitar recálculos innecesarios
- **Aplicación**: En las predicciones

---

## 📊 4. REQUERIMIENTOS DE DATOS

### 4.1 Fuentes de Datos
- **Restricción**: Solo datos públicos disponibles
- **Sugerencias** (no obligatorias):
  - London Metal Exchange (LME)
  - Trading Economics
  - FRED (Federal Reserve Economic Data)
  - World Bank Commodity Price Data
  - Quandl/Nasdaq Data Link
  - Yahoo Finance
- **Libertad**: Puede usar cualquier fuente pública relevante

### 4.2 Manejo de Casos Especiales
- **Fines de semana**: Modelo debe manejarlos
- **Feriados**: Modelo debe manejarlos
- **Datos faltantes**: Documentar estrategia

---

## ⚡ 5. REQUERIMIENTOS DE RENDIMIENTO

### 5.1 Tiempo de Respuesta (OBLIGATORIO)
- **Máximo**: 2 segundos
- **Aplicación**: En el endpoint principal

### 5.2 Disponibilidad
- **Expectativa**: Servicio debe estar disponible durante la evaluación
- **Período**: 5 días consecutivos de evaluación

---

## 💰 6. RESTRICCIONES TÉCNICAS

### 6.1 Presupuesto Cloud (OBLIGATORIO)
- **Límite**: Menos de $5 USD/mes
- **Incluye**: Todos los servicios necesarios

### 6.2 Lenguajes Permitidos (OBLIGATORIO)
- Python
- R
- Java
- Node.js
- Go

### 6.3 Dependencias (OBLIGATORIO)
- **Prohibido**: APIs de pago
- **Prohibido**: Servicios que requieran licencias comerciales
- **Permitido**: Modelos pre-entrenados (con documentación)

---

## 📦 7. ENTREGABLES REQUERIDOS

### 7.1 URL del Endpoint (OBLIGATORIO)
- Dirección pública accesible del API
- Debe estar funcionando al momento de entrega

### 7.2 API Key (OBLIGATORIO)
- Valor de la API key para acceder al servicio
- Documentar cómo usarla

### 7.3 Repositorio de Código (OBLIGATORIO)
- **Plataforma**: GitHub o GitLab
- **Contenido requerido**:
  - ✅ Código fuente completo
  - ✅ README con instrucciones de despliegue
  - ✅ Descripción del modelo
  - ✅ Features utilizados
  - ✅ Justificación de decisiones técnicas

---

## 📈 8. CRITERIOS DE EVALUACIÓN

### 8.1 Evaluación Cuantitativa (60% del puntaje)
- **Duración**: 5 días consecutivos
- **Método**: Llamadas diarias al API
- **Comparación**: Predicción vs precio real del día siguiente
- **Métrica principal**: MAPE (Mean Absolute Percentage Error)
- **Criterio eliminatorio**: 50% de candidatos con mayor error serán excluidos

### 8.2 Evaluación Cualitativa (40% del puntaje)
- **Ingeniería de Features** (15%):
  - Creatividad en variables
  - Relevancia de features
- **Robustez del Sistema** (10%):
  - Manejo de errores
  - Disponibilidad del servicio
- **Calidad del Código** (10%):
  - Estructura
  - Documentación
  - Mejores prácticas
- **Escalabilidad** (5%):
  - Diseño para crecimiento futuro

---

## ✨ 9. FEATURES OPCIONALES (Valorados pero no obligatorios)

### 9.1 Monitoreo
- Dashboard de performance del modelo
- Métricas de uso del API

### 9.2 A/B Testing
- Capacidad de probar múltiples modelos
- Infraestructura para experimentos

### 9.3 Explicabilidad
- Endpoint adicional: `/explain/prediction`
- Factores que influyen en la predicción

### 9.4 Datos Complementarios
- Indicadores económicos
- Tipos de cambio
- Índices industriales
- Indicadores de incertidumbre/volatilidad

---

## 📋 10. CHECKLIST DE CUMPLIMIENTO

### Requerimientos Obligatorios:
- [ ] API REST desplegado y accesible públicamente
- [ ] Endpoint GET `/predict/steel-rebar-price` funcional
- [ ] Respuesta JSON con todos los campos requeridos
- [ ] Endpoint raíz `/` con información del servicio
- [ ] Autenticación con header `X-API-Key`
- [ ] Rate limiting de 100 requests/hora implementado
- [ ] Cache de máximo 1 hora implementado
- [ ] Tiempo de respuesta < 2 segundos
- [ ] Costo operativo < $5 USD/mes
- [ ] Lenguaje permitido (Python/R/Java/Node.js/Go)
- [ ] Sin dependencias comerciales/de pago
- [ ] Manejo de fines de semana y feriados
- [ ] URL del endpoint entregada
- [ ] API Key entregada
- [ ] Repositorio con código fuente
- [ ] README con instrucciones de despliegue
- [ ] Documentación del modelo y features
- [ ] Justificación de decisiones técnicas

### Requerimientos Implícitos:
- [ ] Modelo predictivo funcional
- [ ] Datos históricos integrados
- [ ] Manejo de errores implementado
- [ ] Logs apropiados
- [ ] Código limpio y mantenible
- [ ] Arquitectura escalable

### Features Opcionales:
- [ ] Dashboard de monitoreo
- [ ] Capacidad de A/B testing
- [ ] Endpoint de explicabilidad
- [ ] Indicadores económicos adicionales
- [ ] Métricas de incertidumbre

---

## 💡 11. CONSIDERACIONES IMPORTANTES

### 11.1 Sobre el Modelo
- Patrones estacionales en commodities
- Correlación con mineral de hierro y carbón de coque
- Impacto de eventos geopolíticos
- Influencia de tipos de cambio

### 11.2 Filosofía de Desarrollo
- "Un modelo simple bien implementado es mejor que uno complejo mal ejecutado"
- Documentar todas las decisiones
- Priorizar robustez sobre complejidad

### 11.3 Endpoints Adicionales
- Permitidos pero no evaluados para MAPE
- Solo el endpoint principal cuenta para la métrica de error

---

**Fecha de creación**: 2025-09-26  
**Propósito**: Checklist completo para desarrollo de API de predicción de precios  
**Estado**: Lista de requerimientos completa y validada contra el PDF
