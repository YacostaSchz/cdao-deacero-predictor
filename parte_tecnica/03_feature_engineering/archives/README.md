# 📚 Archives - Historical Analysis

## 📋 RESUMEN

**Carpeta**: Análisis históricos y exploraciones descartadas  
**Propósito**: Mantener historial de decisiones y experimentos  
**Estado**: Solo referencia histórica  

---

## 📁 ARCHIVOS ARCHIVADOS

### 🔍 Análisis Exploratorios
- **`PREMIUM_DEFINITION_VERIFICATION.py`**
  - Verificación de definición de premium
  - Ejemplos concretos con datos reales
  - Aclaración conceptual México vs LME

- **`ECONOMETRIC_TRANSFORMATION_MODEL.py`**
  - Modelo econométrico de transformación LME → México
  - Enfoque con 25+ variables macro
  - Superseded por modelo dos etapas

- **`ENHANCED_ECONOMETRIC_MODEL.py`**
  - Análisis de variables disponibles vs utilizadas
  - Propuesta de modelo econométrico completo
  - Base conceptual para modelo final

### 📊 Modelos Anteriores
- **`FINAL_CONSOLIDATED_MODEL.py`**
  - Modelo consolidado anterior (v1.0)
  - Enfoque de transfer function fija
  - MAPE 0.48% (pero con premium fijo)

### 📄 Documentación Histórica
- **`FILE_ORGANIZATION_PLAN.md`**
  - Plan original de organización de archivos
  - Estructura inicial propuesta
  - Evolucionó a estructura actual

---

## 💡 LECCIONES APRENDIDAS

### 1. **Premium NO es Constante**
- Error inicial: asumir premium fijo 15.7%
- Realidad: premium dinámico 1.586 → 1.705
- Solución: Modelo de dos etapas

### 2. **Variables Globales vs Locales**
- Error: mezclar variables en un solo modelo
- Realidad: factores globales afectan LME, locales afectan premium
- Solución: Separación clara de variables

### 3. **Calidad de Datos Crítica**
- Error: usar datos sintéticos para validación
- Realidad: necesidad de datos reales mexicanos
- Solución: consolidación de 11 puntos reales

### 4. **Validación Rigurosa Esencial**
- Error: confiar en métricas de train/test simple
- Realidad: necesidad de validación de overfitting
- Solución: 4 tests independientes

---

## 🚫 ARCHIVOS NO USAR

**Estos archivos son solo referencia histórica**:
- NO usar para producción
- NO contienen el modelo final
- Pueden tener errores corregidos en versiones posteriores

**Para producción usar**: `../05_final_models/TWO_STAGE_FINAL_MODEL.py`

---

*Archivado: 2025-09-28*  
*Propósito: Historial de decisiones y aprendizajes*
