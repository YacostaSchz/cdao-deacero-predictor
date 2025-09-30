# 📊 README - Dataset de Eventos Comerciales de Acero México 2025

## 🎯 Descripción General

Este dataset contiene un registro histórico de eventos comerciales significativos relacionados con la industria del acero entre México y otros países durante el año 2025. Se enfoca principalmente en medidas arancelarias, investigaciones antidumping, y decisiones comerciales que impactan el mercado mexicano del acero.

## 📌 Contexto y Propósito

### Solicitud Original
> "Ármame un dataset con eventos históricos relacionados con el acero entre México y otros países (principalmente Estados Unidos). (aranceles/dumping) Requiero que busques en internet y me generes: fecha: año-mm-dd descripción del evento: score [-1,1]: -1 es un impacto negativo para el acero de México (dumping, aumento aranceles) +1 es impacto positivo para el acero de México (no procede dumping, aranceles bajan) referencia: liga con la nota. Espero puedas obtenerlo de todo lo que va de 2025, puede ser desde la primera fecha en la que se da noticia de algo así como de cuando entra en vigor"

### Uso en el Modelo Predictivo
Este dataset es **CRÍTICO** para el modelo de predicción de precios de varilla corrugada ya que:
- Captura **eventos de política comercial** que afectan directamente los precios
- Proporciona **señales anticipadas** de cambios en el mercado
- Permite incorporar **factores geopolíticos** en las predicciones
- Ayuda a calibrar el **spread México/LME** que actualmente es 15.7%

## 📋 Estructura del Dataset

### Campos

| Campo | Tipo | Descripción |
|-------|------|-------------|
| **Fecha** | YYYY-MM-DD | Fecha del evento o entrada en vigor de la medida |
| **Descripción** | Texto | Resumen detallado del evento comercial |
| **Impacto** | [-1, +1] | Score de impacto en la industria mexicana del acero |
| **Referencia** | Texto | Fuente de la información |

### Sistema de Scoring

- **-1**: Impacto **NEGATIVO** para el acero mexicano
  - Nuevos aranceles de EE.UU. contra México
  - Investigaciones antidumping contra productos mexicanos
  - Determinaciones desfavorables en casos comerciales
  - Márgenes de dumping aplicados a exportadores mexicanos

- **+1**: Impacto **POSITIVO** para el acero mexicano
  - México impone/mantiene aranceles protectores
  - Propuestas de reciprocidad arancelaria
  - Medidas defensivas contra importaciones desleales
  - Protección de la industria nacional

## 📊 Resumen Estadístico (2025)

### Distribución Temporal
- **Total de eventos**: 19
- **Período cubierto**: Enero - Septiembre 2025
- **Mes con más actividad**: Marzo (4 eventos)

### Balance de Impactos
- **Eventos positivos (+1)**: 8 (42.1%)
- **Eventos negativos (-1)**: 11 (57.9%)
- **Balance neto**: -3 (tendencia negativa)

### Principales Actores
1. **Estados Unidos**: 10 eventos (52.6%)
   - Todos con impacto negativo (-1)
   - Aranceles Sección 232, investigaciones antidumping

2. **China**: 3 eventos (15.8%)
   - México protegiendo contra importaciones chinas (+1)

3. **Otros**: España, Vietnam (medidas defensivas mexicanas)

## 🔍 Hallazgos Clave

### 1. **Escalada Arancelaria EE.UU.**
- **12 de marzo**: Fin de exenciones, arancel 25% universal al acero
- **18 de agosto**: Expansión a 400 productos derivados, arancel 50%
- **Impacto acumulado**: Presión significativa en exportaciones mexicanas

### 2. **Casos Específicos contra DeAcero**
- **4 de agosto**: Margen antidumping 13.45% en varilla
- **16 de septiembre**: Derechos retroactivos desde abril 2024
- **Relevancia**: DeAcero es productor clave para el mercado interno

### 3. **Respuesta Mexicana**
- **11 de septiembre**: Propuesta de aranceles 10-50% (35% para acero)
- **Múltiples medidas**: Protección contra China, Vietnam, España
- **Estrategia**: Defensa activa del mercado interno

## 🎯 Implicaciones para el Modelo

### Factores a Considerar
1. **Volatilidad por eventos**: Los cambios arancelarios generan picos de precio
2. **Asimetría temporal**: Anuncios vs. implementación efectiva
3. **Efectos cascada**: Medidas de EE.UU. afectan toda la región
4. **Reciprocidad**: México responde con medidas espejo

### Integración con el Modelo Predictivo
```python
# Pseudocódigo para incorporar eventos
def ajuste_por_eventos(fecha, precio_base):
    eventos = obtener_eventos_ventana(fecha, ventana=30)
    factor_ajuste = 1.0
    
    for evento in eventos:
        if evento.impacto == -1:
            # Eventos negativos aumentan spread México/LME
            factor_ajuste *= 1.02  # +2% por evento negativo
        else:
            # Eventos positivos reducen spread
            factor_ajuste *= 0.99  # -1% por evento positivo
    
    return precio_base * factor_ajuste
```

## 🔄 Mantenimiento del Dataset

### Actualización
- **Frecuencia recomendada**: Mensual
- **Fuentes principales**:
  - Federal Register (EE.UU.)
  - Diario Oficial de la Federación (México)
  - Steel Market Update
  - Holland & Knight alerts

### Validación
- Verificar fechas de implementación vs. anuncio
- Confirmar impactos con datos de precio reales
- Actualizar scores basado en efectos observados

## ⚠️ Limitaciones y Consideraciones

1. **Sesgo temporal**: Solo cubre 2025, no captura tendencias históricas
2. **Simplificación del score**: Sistema binario puede perder matices
3. **Lag de implementación**: Tiempo entre anuncio y efecto en precios
4. **Interacciones complejas**: Eventos pueden tener efectos combinados

## 📁 Archivos Relacionados

- `scores.md`: Dataset original con formato de tabla
- `scores_formatted.md`: Versión formateada y limpia
- `september_prices.md`: Precios reales para calibración
- `ESTRATEGIA_DATOS_ACTUALIZADA.md`: Estrategia completa del modelo

## 🚀 Próximos Pasos

1. **Expandir cobertura temporal**: Incluir 2023-2024 para mayor contexto
2. **Enriquecer scoring**: Sistema multinivel (-2 a +2) para mayor granularidad
3. **Automatizar actualización**: Script para monitorear fuentes oficiales
4. **Backtesting**: Validar impacto histórico de eventos similares

---

**Nota**: Este dataset es fundamental para entender la dinámica del mercado del acero mexicano en 2025, especialmente considerando que el spread México/LME actual (15.7%) está influenciado significativamente por estas medidas comerciales.

*Última actualización: 28 de septiembre de 2025*
