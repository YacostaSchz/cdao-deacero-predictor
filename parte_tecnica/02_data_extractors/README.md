# Data Extractors - CDO DeAcero

Este directorio contiene todos los scripts necesarios para descargar y procesar las fuentes de datos macroeconómicos para el modelo de predicción de precios de varilla corrugada.

## 🚨 Información Crítica del Proyecto

### Calibración de Referencia (26-sep-2025)
- **Precio México**: 625 USD/ton (SteelRadar)
- **Precio LME**: 540.50 USD/ton
- **SPREAD CONFIRMADO**: 15.7% premium México vs LME
- **Implicación**: Este es nuestro único punto de calibración real para el MAPE

### Estado de las Fuentes
- ✅ **Banxico**: Solo datos macro (tipo cambio, inflación, TIIE)
- ❌ **Banxico**: NO tiene commodities ni precios de varilla (confirmado)
- ✅ **LME**: Archivos Excel locales con futuros M01-M15
- ✅ **EPU**: Índices de incertidumbre descargables sin autenticación
- ✅ **World Bank**: Pink Sheet mensual de commodities
- ⚠️ **FRED**: Requiere API key gratuita

## 📁 Estructura de Archivos

```
02_data_extractors/
├── README.md                    # Este archivo
├── install_dependencies.sh      # Script de instalación
├── banxico_downloader.py       # Descargador de Banxico (funcional)
├── macro_data_fetcher.py       # Descargador consolidado (todas las fuentes)
├── ESTRATEGIA_DATOS_ACTUALIZADA.md  # Estrategia completa del proyecto
├── FUENTES_DATOS_MACRO.md      # Guía detallada de fuentes
└── outputs/                    # Directorio de salida para datos descargados
    ├── banxico_*.csv          # Datos de Banxico
    ├── lme_*.csv              # Datos LME procesados
    ├── epu_*.csv              # Índices EPU
    ├── world_bank_*.csv       # Commodities World Bank
    └── fred_*.csv             # Datos FRED (si configurado)
```

## 🚀 Guía Rápida de Uso

### 1. Instalación de Dependencias

```bash
# Dar permisos de ejecución
chmod +x install_dependencies.sh

# Ejecutar instalación
./install_dependencies.sh
```

### 2. Configuración (Opcional pero Recomendado)

```bash
# Para FRED API (gratuita):
# 1. Obtener key en: https://fred.stlouisfed.org/docs/api/api_key.html
# 2. Configurar:
export FRED_API_KEY='tu_api_key_aqui'
```

### 3. Descarga de Datos

#### Opción A: Descarga Completa (Recomendado)
```bash
python macro_data_fetcher.py
# Seleccionar opción 1
```

#### Opción B: Solo Banxico
```bash
python banxico_downloader.py
# Seleccionar opción 5 (ejecutar todo)
```

#### Opción C: Descargas Específicas
```bash
python macro_data_fetcher.py
# Opciones:
# 2 - Solo Banxico + LME
# 3 - Solo EPU indices
# 4 - Solo World Bank
# 5 - Verificar LME local
```

## 📊 Fuentes de Datos Disponibles

### 1. Banxico (Sistema de Información Económica)
**Script**: `banxico_downloader.py`
**Series disponibles**:
- SF43718: Tipo de cambio FIX USD/MXN (diaria)
- SP1: INPC General (mensual)
- SF43783: TIIE a 28 días (diaria)
- SR16734: IGAE - actividad económica (mensual)
- SP74665: Inflación no subyacente anual (mensual)

**Uso**:
```bash
python banxico_downloader.py
```

### 2. LME (London Metal Exchange)
**Ubicación**: `/docs/sources/lme_closing prices/`
**Archivos**:
- SR Closing Prices.xlsx (Steel Rebar FOB Turkey)
- SC Closing Prices.xlsx (Steel Scrap CFR Turkey)

**Estructura**: Date + M01-M15 (contratos futuros)

### 3. Economic Policy Uncertainty (EPU)
**Descarga**: Directa sin autenticación
**Países**: México, USA, China, Turquía
**Formato**: Excel → CSV

### 4. World Bank Commodities
**Fuente**: Pink Sheet mensual
**Incluye**: Energía, metales, agricultura
**Series clave**: Steel rebar, Iron ore, Coal, Oil

### 5. FRED (Federal Reserve Economic Data)
**Requiere**: API key gratuita
**Series clave**:
- DFF: Federal Funds Rate
- CPIAUCSL: CPI USA
- DGS10: 10-Year Treasury
- DEXMXUS: Exchange Rate

## 🎯 Pipeline de Uso para el Modelo

```python
# 1. Descargar todos los datos
python macro_data_fetcher.py  # Opción 1

# 2. Verificar archivos generados
ls outputs/

# 3. En tu modelo predictivo:
import pandas as pd

# Cargar datos
banxico_fx = pd.read_csv('outputs/SF43718_data.csv')
lme_rebar = pd.read_csv('outputs/lme_rebar.csv')
epu_mexico = pd.read_csv('outputs/epu_mexico.csv')

# Aplicar calibración
MEXICO_PREMIUM = 1.157  # 15.7% spread confirmado
precio_base_lme = lme_rebar['M01'].iloc[-1]  # Front month
precio_mexico = precio_base_lme * MEXICO_PREMIUM
```

## ⚠️ Notas Importantes

1. **Series Descontinuadas**: NO usar SP9709 (varilla corrugada) - sin datos desde 2011
2. **Calibración**: Siempre validar contra spread 15.7% México/LME
3. **Frecuencia**: Alinear series temporales (diarias vs mensuales)
4. **Rate Limits**: Scripts respetan límites de API automáticamente

## 🐛 Troubleshooting

### Error: "No module named 'fredapi'"
```bash
pip install fredapi
```

### Error: "FRED_API_KEY not configured"
Normal si no tienes key. El script continuará sin datos FRED.

### Error al leer archivos Excel
```bash
pip install openpyxl
```

### Banxico retorna error 429
Límite de API alcanzado. Esperar 5 minutos.

## 📈 Próximos Pasos

1. ✅ Descargar todos los datos disponibles
2. 🔄 Crear pipeline de feature engineering
3. 🔄 Implementar modelo con calibración 15.7%
4. 📋 Desarrollar API REST de predicción

---

**Última actualización**: 2025-09-28
**Autor**: Sistema CDO DeAcero
**Estado**: Scripts funcionales y documentados
