# Resumen Ejecutivo - Análisis Econométrico de Precios de Varilla Corrugada

**Fecha**: 2025-09-28  
**Objetivo**: Identificar y cuantificar los factores macroeconómicos que afectan el precio de la varilla corrugada (Steel rebar) para el desarrollo de un modelo predictivo.

## 📊 Datos Analizados

- **Fuente**: CMOHistoricalDataMonthly.xlsx - World Bank Commodity Price Data
- **Período**: 1979-01 a 2012-06 (33.5 años, 402 observaciones mensuales)
- **Variable objetivo**: Steel rebar [STL_JP_REBAR] en USD/tonelada métrica
- **Variables explicativas**: 
  - Iron ore, cfr spot [IRON_ORE]
  - Crude oil, Brent [CRUDE_BRENT]
  - Coal, Australian [COAL_AUS]

## 🔍 Hallazgos Principales

### 1. Estadísticas Descriptivas

**Steel Rebar (1979-2012)**:
- Precio promedio: $349.38/mt
- Desviación estándar: $137.79/mt
- Rango: $190.00 - $1,030.00/mt
- Volatilidad significativa con tendencia alcista

### 2. Correlaciones

**En niveles (precios nominales)**:
- COAL_AUS: 0.887 (más alta)
- IRON_ORE: 0.854
- CRUDE_BRENT: 0.844

**En cambios mensuales (Δlog)**:
- COAL_AUS: 0.225
- CRUDE_BRENT: 0.176
- IRON_ORE: 0.138

> **Insight**: Las correlaciones en niveles son muy altas debido a tendencias comunes, pero en cambios mensuales son moderadas, sugiriendo dinámicas diferenciadas.

### 3. Análisis de Estacionariedad

- **Niveles**: Todas las series son NO estacionarias (I(1))
- **Primeras diferencias log**: Todas las series son estacionarias
- **Implicación**: Necesidad de trabajar con modelos en diferencias o con corrección de error

### 4. Causalidad de Granger

Variables que causan estadísticamente los precios de REBAR:
- **IRON_ORE → REBAR**: Significativo con lag óptimo de 11 meses
- **COAL_AUS → REBAR**: Significativo con lag óptimo de 3 meses
- **REBAR también causa**: IRON_ORE (2 meses), CRUDE_BRENT (2 meses), COAL_AUS (7 meses)

> **Insight**: Existe retroalimentación bidireccional, sugiriendo un sistema dinámico complejo

### 5. Cointegración

- **Test de Johansen multivariado**: NO se encontró cointegración significativa al 95%
- **Test de Engle-Granger bivariado**: 
  - REBAR - IRON_ORE: Sí cointegrados (p-valor = 0.028)
  - REBAR - CRUDE_BRENT: No cointegrados
  - REBAR - COAL_AUS: No cointegrados

### 6. Modelo VAR en Diferencias

Dado que no hay cointegración multivariada clara:
- **Tipo de modelo**: VAR en primeras diferencias logarítmicas
- **Lags óptimos**: 2 (según criterio BIC)
- **Variables incluidas**: Δlog(REBAR), Δlog(IRON_ORE), Δlog(CRUDE_BRENT), Δlog(COAL_AUS)

### 7. Impulse Response Functions (IRFs)

**Elasticidades acumuladas a 12 meses** (shock de 1% en cada variable):
- Coal Australian → +0.330% en Rebar
- Iron Ore → +0.316% en Rebar  
- Crude Oil Brent → +0.117% en Rebar

> **Insight**: Coal e Iron Ore tienen los impactos más significativos en el precio del Rebar

### 8. Forecast Error Variance Decomposition (FEVD)

**Contribución a la varianza del error de pronóstico de REBAR**:

| Horizonte | REBAR | IRON_ORE | CRUDE_BRENT | COAL_AUS |
|-----------|-------|----------|-------------|----------|
| 1 mes     | 100%  | 0%       | 0%          | 0%       |
| 3 meses   | 90.3% | 5.5%     | 1.5%        | 2.7%     |
| 6 meses   | 89.7% | 5.8%     | 1.6%        | 2.9%     |
| 12 meses  | 89.7% | 5.8%     | 1.6%        | 2.9%     |

> **Insight**: El precio del Rebar es principalmente autoregresivo, pero Iron Ore contribuye ~6% a su varianza

### 9. Quiebres Estructurales

Períodos identificados con cambios significativos:
- **2008-2009**: Crisis financiera global
- **2011**: Alta volatilidad en commodities

## 💡 Conclusiones para el Modelo Predictivo

### Variables Clave a Incluir:
1. **Coal Australian** - Mayor impacto dinámico
2. **Iron Ore** - Input directo, alta correlación
3. **Crude Oil Brent** - Indicador energético
4. **Índices agregados** - iENERGY, iBASEMET (opcional)

### Especificación Recomendada:
- **Horizonte de datos**: Mínimo 3-6 meses de historia
- **Transformación**: Trabajar en log-diferencias para estacionariedad
- **Lags**: 2-3 meses para capturar dinámicas
- **Variables dummy**: Para crisis 2008-2009 y períodos de alta volatilidad

### Consideraciones Adicionales:
1. **Actualización frecuente**: Los parámetros cambian con el tiempo
2. **Monitoreo de quiebres**: Detectar cambios estructurales
3. **Combinación de modelos**: VAR + Machine Learning para mejor performance
4. **Features adicionales**: 
   - Spreads entre commodities
   - Volatilidad implícita
   - Indicadores económicos globales

## 📈 Próximos Pasos

1. **Extender el análisis** con datos más recientes (2012-2025)
2. **Incorporar variables adicionales**:
   - Tipos de cambio (USD index)
   - Indicadores de demanda China
   - Inventarios globales de acero
3. **Desarrollar modelo híbrido** combinando econometría y ML
4. **Implementar sistema de alertas** para cambios de régimen

---

**Nota**: Este análisis proporciona una base sólida para el desarrollo de la API predictiva de precios de varilla corrugada, identificando los principales drivers macroeconómicos y sus relaciones dinámicas.
