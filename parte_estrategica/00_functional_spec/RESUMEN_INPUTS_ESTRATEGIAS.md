# 📊 Resumen de Inputs para Generar las 3 Estrategias - CDO DeAcero

## 🎯 Contexto
Dado que NO tenemos acceso a datos internos de DeAcero, este documento resume todos los inputs disponibles (datos públicos, benchmarks y estimaciones) para desarrollar las 3 estrategias solicitadas.

---

## 📈 Datos Base del PDF (Confirmados)

| Concepto | Valor | Fuente |
|----------|-------|---------|
| **Producción anual** | 1,000,000 ton | PDF caso |
| **Scrap actual** | 5% (50,000 ton/año) | PDF caso |
| **Costo por ton scrap** | $200 USD | PDF caso |
| **Pérdida anual por scrap** | $10M USD | PDF caso |
| **OTIF actual** | 85% | PDF caso |
| **Pedidos anuales** | 10,000 | PDF caso |
| **Valor promedio pedido** | $20,000 USD | PDF caso |
| **Penalizaciones OTIF** | 3% del valor pedido | PDF caso |
| **Costo transporte urgente** | $500/incidente | PDF caso |
| **Consumo energético** | 450 kWh/ton | PDF caso |
| **Costo energía** | $0.08 USD/kWh | PDF caso |
| **Gasto energético anual** | $36M USD | PDF caso |
| **Presupuesto máximo** | $5M USD | PDF caso |
| **Plazo implementación** | 12 meses | PDF caso |

---

## 🌍 Benchmarks de la Industria (Fuentes Públicas)

### 🔧 Scrap/Calidad
| Benchmark | Valor | Fuente |
|-----------|-------|---------|
| **Scrap mundial EAF** | 2.3-4% | World Steel Association |
| **ArcelorMittal** | 2.5-3% | Reportes públicos |
| **Nippon Steel** | 2.3% | Caso documentado |
| **Reducción con IoT/Vision** | 15-25% | Tata Steel, Baosteel |
| **Causas típicas scrap** | 40% superficial, 30% dimensional | World Steel |

### 📦 OTIF/Supply Chain
| Benchmark | Valor | Fuente |
|-----------|-------|---------|
| **OTIF Construcción** | 92-95% | APICS |
| **OTIF Automotriz** | 98%+ | APICS |
| **Mejora con TMS** | 8-12 puntos | Forrester |
| **Lead time México urbano** | 3-5 días | SCT México |
| **Forecast accuracy típico** | 70-80% | Gartner |

### ⚡ Energía
| Benchmark | Valor | Fuente |
|-----------|-------|---------|
| **Consumo Japón** | 380-420 kWh/ton | IEA |
| **Consumo Europa BAT** | 400-430 kWh/ton | EU Commission |
| **Perfil EAF** | 70% horno, 20% laminación | US DOE |
| **Reducción con EMS** | 8-15% | ENERGY STAR |
| **Factor de carga típico** | 0.7-0.8 | IEEE |

---

## 💰 Costos de Tecnología (Benchmarks 2024)

### 🖥️ Estrategia 1: Scrap (MES/IoT/Vision)
| Componente | Costo | Fuente |
|------------|-------|---------|
| **MES completo** | $1.5-3M | ARC Advisory |
| **Computer Vision** | $500k-1.5M | Cognex, Keyence |
| **Sensores IoT** | $50-500/punto | Industrial IoT Alliance |
| **Plataforma Analytics** | $200-500k | Gartner |
| **Total estimado** | $2-3M | Análisis |

### 🚚 Estrategia 2: OTIF (Supply Chain)
| Componente | Costo | Fuente |
|------------|-------|---------|
| **TMS básico** | $300-700k | Forrester |
| **Plataforma visibilidad** | $200-500k | FourKites, project44 |
| **EDI setup** | $50-150k | EDI providers |
| **Analytics SC** | $200-400k | Gartner |
| **Total estimado** | $1-2M | Análisis |

### ⚡ Estrategia 3: Energía (EMS)
| Componente | Costo | Fuente |
|------------|-------|---------|
| **EMS básico** | $300-800k | Schneider, ABB |
| **Controladores horno** | $50-200k/unidad | Siemens |
| **Sensores energía** | $1-5k/punto | Fluke, Yokogawa |
| **Software optimización** | $200-500k | AspenTech |
| **Total estimado** | $2-4M | Análisis |

---

## 📊 ROI Esperados (Casos Documentados)

| Estrategia | Inversión | Ahorro Anual | ROI | Casos de Referencia |
|------------|-----------|--------------|-----|-------------------|
| **Scrap** | $2-3M | $4M | 12-18 meses | Tata Steel, JSW |
| **OTIF** | $1-2M | $1.1M | 12-24 meses | Nucor, Gerdau |
| **Energía** | $2-4M | $3.6M | 8-14 meses | POSCO, ThyssenKrupp |

---

## ✅ Supuestos Clave (Sin Datos Internos)

### 🏭 Operacionales
- Planta opera 24/7 con 3 turnos de 8 horas
- OEE actual estimado: 65-75% (promedio industria)
- Mix productos: 70% varilla, 30% otros largos
- Mantenimientos: 10% tiempo programado

### 🚛 Logísticos
- Distribución: 60% local (< 300km), 40% foráneo
- Flota: 30% propia, 70% tercerizada
- Almacenes: 1 principal + 3 regionales

### 👥 Organizacionales
- Cultura tradicional con resistencia al cambio moderada
- Edad promedio operadores: 40-45 años
- Nivel digitalización actual: bajo (escala 1-5: 2)
- Sindicato presente pero colaborativo

### 💻 Tecnológicos
- ERP existente pero no integrado
- SCADA básico en planta
- Sin sistemas analytics actuales
- Infraestructura IT limitada

---

## 🎯 Metodología Sin Datos Internos

1. **Comparar estado actual vs benchmarks**
   - Scrap: 5% vs 2.3-3% mundial
   - OTIF: 85% vs 92-95% industria
   - Energía: 450 vs 400-430 kWh/ton

2. **Estimar mejoras basadas en casos públicos**
   - Reducción scrap: 20% (de 5% a 4%)
   - Mejora OTIF: 10 puntos (de 85% a 95%)
   - Ahorro energía: 10% (de 450 a 405 kWh/ton)

3. **Calcular ROI con benchmarks de costos**
   - Usar rangos de inversión documentados
   - Aplicar ahorros calculados del PDF
   - Considerar plazos típicos de la industria

4. **Documentar todos los supuestos**
   - Ser transparente sobre limitaciones
   - Usar rangos en lugar de números exactos
   - Citar fuentes para credibilidad

---

## 📚 Fuentes Principales

1. **World Steel Association** - worldsteel.org
2. **APICS/ASCM** - ascm.org
3. **US DOE** - energy.gov/eere
4. **Gartner** - gartner.com
5. **Forrester** - forrester.com
6. **IEA** - iea.org
7. **ENERGY STAR** - energystar.gov
8. **Casos públicos**: Reportes anuales de Tata, POSCO, Nucor, ArcelorMittal

---

**Fecha**: 2025-09-26
**Versión**: 1.0
**Propósito**: Consolidar todos los inputs disponibles para generar las 3 estrategias sin necesidad de datos internos de DeAcero
