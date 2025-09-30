# 📁 Especificaciones Funcionales - Parte Técnica

## 🎯 Propósito
Esta carpeta contiene todas las especificaciones funcionales y técnicas para el desarrollo de la API REST de predicción de precios de varilla corrugada.

## 📋 Documentos Disponibles

### 1. REQUERIMIENTOS_TECNICOS_COMPLETOS.md
- **Contenido**: Listado exhaustivo de 40+ requerimientos técnicos
- **Estructura**:
  - Objetivo principal
  - Requerimientos funcionales (endpoints, formatos)
  - Seguridad y control (auth, rate limiting, cache)
  - Requerimientos de datos
  - Performance y restricciones
  - Entregables esperados
  - Criterios de evaluación
  - Features opcionales
  - Checklist de cumplimiento
- **Estado**: ✅ Completado (2025-09-27)

## 🔑 Puntos Críticos Identificados

### Restricciones Técnicas
- **Presupuesto**: < $5 USD/mes (muy limitado)
- **Tiempo respuesta**: < 2 segundos
- **Sin APIs de pago**: Solo fuentes públicas gratuitas

### Evaluación
- **MAPE**: 60% del puntaje (métrica crítica)
- **5 días consecutivos** de evaluación
- **50% eliminados** por mayor error

### Arquitectura Sugerida
- Solución serverless (AWS Lambda, Google Cloud Functions)
- Micro-instancia con cache agresivo
- Modelo simple pero robusto

## 📅 Próximos Pasos
1. Diseño de arquitectura técnica
2. Selección de fuentes de datos públicas
3. Definición del modelo predictivo
4. Plan de implementación

---

**Última actualización**: 2025-09-27  
**Responsable**: CDO Candidato
