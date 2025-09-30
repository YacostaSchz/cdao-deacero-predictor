# Manual de Uso - API del SIE (Banco de México) - ACTUALIZADO 2025

Este documento proporciona una guía **ACTUALIZADA** para consumir la API del Sistema de Información Económica (SIE) de Banco de México en el contexto del proyecto CDO DeAcero.

**⚠️ ACTUALIZACIÓN CRÍTICA**: Las series de commodities y varilla corrugada están **DESCONTINUADAS** desde 2011. Este manual refleja las series **ACTUALES** disponibles.

**Documentación oficial**: https://www.banxico.org.mx/SieAPIRest/

## 📋 Índice

1. [Estado Actual y Series Disponibles](#1-estado-actual-y-series-disponibles)
2. [Configuración Inicial](#2-configuración-inicial)
3. [Series ACTUALES Disponibles](#3-series-actuales-disponibles)
4. [Implementación con banxico_downloader.py](#4-implementación-con-banxico_downloaderpy)
5. [Fuentes Alternativas de Datos](#5-fuentes-alternativas-de-datos)
6. [Estrategia Integrada del Proyecto](#6-estrategia-integrada-del-proyecto)

---

## 1. Estado Actual y Series Disponibles

### ⚠️ INFORMACIÓN CRÍTICA PARA EL PROYECTO

**Series DESCONTINUADAS (NO usar)**:
- ❌ SP9709: Índice de precios varilla corrugada (última obs: junio 2011)
- ❌ SP67487: Índices exportación varilla (descontinuada 2011)
- ❌ SP66938: Índices productor varilla (descontinuada 2011)
- ❌ SP66321: Índice construcción varilla (descontinuada 2011)
- ❌ SP68002: Actividad industrial (descontinuada 2011)

**Búsqueda exhaustiva realizada**: 55+ series probadas, **CERO commodities encontrados** en Banxico (sin petróleo, gas, carbón, mineral de hierro, acero).

### ✅ Series ACTUALES Disponibles (Septiembre 2025)

| Serie | Descripción | Frecuencia | Último Dato |
|-------|-------------|------------|-------------|
| **SF43718** | Tipo de cambio FIX USD/MXN | Diaria | Sep 2025 ✅ |
| **SP1** | INPC General (inflación) | Mensual | Ago 2025 ✅ |
| **SF43783** | TIIE a 28 días | Diaria | Sep 2025 ✅ |
| **SR16734** | IGAE (actividad económica) | Mensual | May 2023 ⚠️ |
| **SP74665** | Inflación no subyacente anual | Mensual | Ago 2025 ✅ |

---

## 2. Configuración Inicial

### 2.1 Token del Proyecto (Disponible)

```python
# Token activo del proyecto
TOKEN = "32579942613d1555d2347fe008a3ccc17e3f568fb5a47ca9ba3234b1b77d75ef"
```

### 2.2 Límites de Consultas

| Tipo de Consulta | Límite | Periodo |
|------------------|---------|---------|
| **Metadatos** | 80 consultas | Por minuto |
| **Datos históricos** | 200 consultas | En 5 minutos |

---

## 3. Series ACTUALES Disponibles

### 3.1 Endpoints para Series Vigentes

Base URL: `https://www.banxico.org.mx/SieAPIRest/service/v1`

#### SF43718 - Tipo de Cambio FIX (Diaria)
```bash
# Metadatos
/series/SF43718?locale=es

# Dato más reciente
/series/SF43718/datos/oportuno

# Rango de fechas
/series/SF43718/datos/2025-01-01/2025-09-28
```

#### SP1 - INPC General (Mensual)
```bash
# Metadatos
/series/SP1?locale=es

# Histórico completo
/series/SP1/datos

# Últimos 12 meses
/series/SP1/datos/2024-09-01/2025-09-28
```

#### SF43783 - TIIE 28 días (Diaria)
```bash
# Metadatos
/series/SF43783?locale=es

# Dato oportuno
/series/SF43783/datos/oportuno

# Año 2025
/series/SF43783/datos/2025-01-01/2025-09-28
```

---

## 4. Implementación con banxico_downloader.py

### 4.1 Script Actualizado y Funcional

El proyecto ya cuenta con `banxico_downloader.py` completamente funcional:

```python
from parte_tecnica.02_data_extractors.banxico_downloader import BanxicoDownloader

# Inicializar con token
downloader = BanxicoDownloader()  # Token cargado automáticamente

# Verificar periodicidad de series actuales
periodicidades = downloader.check_all_periodicities()

# Descargar datos recientes (2025)
data_2025 = downloader.download_strategic(full_history=False)

# Obtener valores más recientes
latest_values = downloader.get_latest_values()
```

### 4.2 Menú Interactivo del Script

```bash
python parte_tecnica/02_data_extractors/banxico_downloader.py

# Opciones disponibles:
# 1. Verificar periodicidad de las series
# 2. Obtener valores más recientes
# 3. Descarga inicial (solo 2025)
# 4. Descarga completa (desde 2015)
# 5. Ejecutar todo (recomendado)
```

### 4.3 Archivos de Salida

```
parte_tecnica/02_data_extractors/outputs/
├── banxico_series_periodicidad.csv    # Metadatos de series
├── banxico_latest_values.csv          # Valores más recientes
├── banxico_consolidated_data.csv      # Dataset consolidado
├── SF43718_data.csv                   # Tipo de cambio
├── SP1_data.csv                       # INPC
├── SF43783_data.csv                   # TIIE
├── SR16734_data.csv                   # IGAE
└── SP74665_data.csv                   # Inflación no subyacente
```

---

## 5. Fuentes Alternativas de Datos

### 5.1 Calibración Crítica del Proyecto

**ÚNICO PUNTO DE REFERENCIA REAL (26-sep-2025)**:
- **Precio México**: 625 USD/ton (SteelRadar)
- **Precio LME**: 540.50 USD/ton
- **SPREAD CONFIRMADO**: 15.7% premium México vs LME

### 5.2 Fuentes Complementarias Necesarias

#### FRED API (Federal Reserve) ✅
```python
# Instalación
pip install fredapi

# Uso
from fredapi import Fred
fred = Fred(api_key='TU_API_KEY')  # Obtener en https://fred.stlouisfed.org/docs/api/api_key.html

# Series clave
fed_rate = fred.get_series('DFF')        # Federal Funds Rate
us_cpi = fred.get_series('CPIAUCSL')     # CPI USA
treasury_10y = fred.get_series('DGS10')  # 10-Year Treasury
```

#### Policy Uncertainty Indices ✅
```python
import pandas as pd

# Descarga directa sin autenticación
mexico_epu = pd.read_excel("https://www.policyuncertainty.com/media/Mexico_Policy_Uncertainty_Data.xlsx")
us_epu = pd.read_excel("https://www.policyuncertainty.com/media/US_Policy_Uncertainty_Data.xlsx")
china_epu = pd.read_excel("https://www.policyuncertainty.com/media/China_Policy_Uncertainty_Data.xlsx")
turkey_epu = pd.read_excel("https://www.policyuncertainty.com/media/Turkey_EPU_Data.xlsx")
```

#### World Bank Commodities (Pink Sheet) ✅
```python
# Descarga mensual de commodities
wb_url = "https://thedocs.worldbank.org/en/doc/5d903e848db1d1b83e0ec8f744e55570-0350012021/related/CMO-Historical-Data-Monthly.xlsx"
commodities = pd.read_excel(wb_url, sheet_name='Monthly Prices')

# Incluye: energía, metales, agricultura
```

#### LME Data (Local) ✅
```python
# Archivos ya disponibles en el proyecto
lme_rebar = pd.read_excel("docs/sources/lme_closing prices/SR Closing Prices.xlsx")  # Steel Rebar
lme_scrap = pd.read_excel("docs/sources/lme_closing prices/SC Closing Prices.xlsx")  # Steel Scrap

# Estructura: Date + M01-M15 (contratos futuros)
```

---

## 6. Estrategia Integrada del Proyecto

### 6.1 Pipeline de Datos Completo

```python
# Pseudocódigo de la estrategia
def predict_steel_rebar_price():
    # 1. Base: Precio LME Steel Rebar
    lme_price = get_lme_front_month()  # M01
    
    # 2. Ajuste por spread histórico
    MEXICO_PREMIUM = 1.157  # 15.7% confirmado sept 2025
    
    # 3. Variables macro de Banxico
    fx_rate = get_banxico_data('SF43718')     # USD/MXN
    inflation = get_banxico_data('SP1')        # INPC
    interest_rate = get_banxico_data('SF43783') # TIIE
    
    # 4. Ajustes adicionales
    epu_mexico = get_epu_index('mexico')
    fed_rate = get_fred_data('DFF')
    
    # 5. Modelo predictivo
    mexico_price = lme_price * MEXICO_PREMIUM * macro_adjustments
    
    return mexico_price
```

### 6.2 Prioridad de Implementación

1. **INMEDIATO**: 
   - ✅ Datos Banxico (ya implementado)
   - 🔄 Procesar archivos LME locales
   - 🔄 Descargar EPU indices

2. **HOY**:
   - 🔄 Configurar FRED API
   - 🔄 Descargar World Bank Pink Sheet

3. **MAÑANA**:
   - 🔄 Integrar todas las fuentes
   - 🔄 Validar calibración 15.7%

### 6.3 Estado Actual del Proyecto

- **Fase 1**: ✅ COMPLETADA (preparación de datos)
- **Fase 2**: 🚧 EN PROGRESO (pipeline de datos)
- **Fase 3**: 📋 PENDIENTE (modelo y API)
- **Plazo**: 4 días restantes (hasta Oct 3, 2025)

---

## 🔗 Referencias y Documentación

- **banxico_downloader.py**: Script funcional en `/parte_tecnica/02_data_extractors/`
- **ESTRATEGIA_DATOS_ACTUALIZADA.md**: Estrategia completa del proyecto
- **FUENTES_DATOS_MACRO.md**: Guía detallada de todas las fuentes
- **Token Banxico**: Incluido en `sie.txt`
- **API Banxico**: https://www.banxico.org.mx/SieAPIRest/

---

**Última actualización**: 2025-09-28
**Autor**: Sistema CDO DeAcero
**Estado**: Documentación actualizada con series vigentes y estrategia actual