# Fuentes de Datos Macroeconómicos - Guía de Descarga

## 🚨 DATO CRÍTICO DE CALIBRACIÓN
**Archivo**: `/docs/sources/99_custom/september_prices.md`
- **Precio México**: 625 USD/ton (26-sep-2025, SteelRadar)
- **Precio LME**: 540.50 USD/ton (26-sep-2025)
- **SPREAD CONFIRMADO**: 15.7% premium México vs LME
- **Implicación**: Este es nuestro único punto de calibración real para el MAPE

## 📊 Resumen de Fuentes Disponibles para el Modelo

### 1. **Banxico (Banco de México) - DISPONIBLE** ✅
**URL**: https://www.banxico.org.mx/SieAPIRest/service/v1/
**Método**: API REST con token gratuito
**Estado**: Ya implementado en `banxico_downloader.py`

**Series disponibles:**
- SF43718: Tipo de cambio FIX USD/MXN (diario)
- SP1: INPC General (mensual)
- SF43783: TIIE a 28 días (diario)
- SR16734: IGAE - Indicador Global de Actividad Económica (mensual)
- SP74665: Inflación no subyacente anual (mensual)

**Cómo obtener datos:**
```bash
# Ya implementado - usar el script existente
python banxico_downloader.py
```

### 2. **FRED (Federal Reserve Economic Data) - DISPONIBLE** ✅
**URL**: https://fred.stlouisfed.org/
**Método**: API REST gratuita con key
**Documentación**: https://fred.stlouisfed.org/docs/api/fred/

**Series clave para el modelo:**
- DFF: Federal Funds Rate (diario)
- CPIAUCSL: Consumer Price Index USA (mensual)
- DGS10: 10-Year Treasury Constant Maturity Rate
- DEXMXUS: Mexico/U.S. Exchange Rate (alternativa a Banxico)

**Cómo obtener API key:**
1. Registrarse en: https://fred.stlouisfed.org/docs/api/api_key.html
2. API key se envía por email instantáneamente
3. Límite: 120 requests/minuto (muy generoso)

**Instalación Python:**
```bash
pip install fredapi
```

**Código ejemplo:**
```python
from fredapi import Fred
fred = Fred(api_key='TU_API_KEY')

# Descargar Fed Funds Rate
fed_rate = fred.get_series('DFF', start_date='2010-01-01')
# Descargar inflación USA
us_cpi = fred.get_series('CPIAUCSL', start_date='2010-01-01')
```

### 3. **Policy Uncertainty Indices - DISPONIBLE** ✅
**URL Base**: https://www.policyuncertainty.com/
**Método**: Descarga directa CSV/Excel

**URLs específicas por país:**
- México: https://www.policyuncertainty.com/mexico_monthly.html
- USA: https://www.policyuncertainty.com/us_monthly.html
- China: https://www.policyuncertainty.com/scmp_monthly.html
- Turquía: https://www.policyuncertainty.com/turkiye_index.html

**Cómo descargar:**
```python
import pandas as pd

# Ejemplo para México
mexico_epu_url = "https://www.policyuncertainty.com/media/Mexico_Policy_Uncertainty_Data.xlsx"
mexico_epu = pd.read_excel(mexico_epu_url)

# Ejemplo para USA
us_epu_url = "https://www.policyuncertainty.com/media/US_Policy_Uncertainty_Data.xlsx"
us_epu = pd.read_excel(us_epu_url)
```

### 4. **LME (London Metal Exchange) - PARCIALMENTE DISPONIBLE** ⚠️
**Estado actual**: Archivos Excel ya en `/docs/sources/lme_closing prices/`
- SR Closing Prices.xlsx (Steel Rebar)
- SC Closing Prices.xlsx (Steel Scrap)

**Para datos actualizados:**
- **Opción 1**: LME oficial (requiere suscripción) - https://www.lme.com/
- **Opción 2**: Proveedores de datos financieros:
  - Refinitiv Datastream
  - Bloomberg Terminal
  - Quandl (algunos datos gratuitos)
  
**Alternativa gratuita (datos con retraso):**
- Investing.com API no oficial
- Yahoo Finance (limitado para commodities)

### 5. **Fuentes Adicionales Recomendadas**

#### **World Bank - Commodities** ✅
**URL**: https://www.worldbank.org/en/research/commodity-markets
**Método**: Descarga directa Excel ("Pink Sheet")
**Frecuencia**: Mensual
**Incluye**: Precios de energía, metales, agricultura

```python
# Pink Sheet mensual
wb_commodities_url = "https://thedocs.worldbank.org/en/doc/5d903e848db1d1b83e0ec8f744e55570-0350012021/related/CMO-Historical-Data-Monthly.xlsx"
commodities = pd.read_excel(wb_commodities_url, sheet_name='Monthly Prices')
```

#### **INEGI - México** ✅
**URL**: https://www.inegi.org.mx/app/indicadores/
**Método**: API REST o descarga directa
**Relevante para**:
- Índices de precios productor
- Producción industrial
- Indicadores de construcción

#### **Comtrade UN - Comercio Internacional** ✅
**URL**: https://comtradeplus.un.org/
**Método**: API con registro gratuito
**Útil para**: Flujos de importación/exportación de acero

### 6. **Script Consolidador Sugerido**

```python
# data_fetcher.py
import os
from datetime import datetime
import pandas as pd
from fredapi import Fred
import requests

class MacroDataFetcher:
    def __init__(self):
        self.fred_key = os.getenv('FRED_API_KEY')
        self.banxico_token = os.getenv('BANXICO_TOKEN')
        
    def fetch_all_macro_data(self, start_date='2010-01-01'):
        """Descarga todos los datos macro necesarios"""
        
        data = {}
        
        # 1. Datos FRED
        if self.fred_key:
            fred = Fred(api_key=self.fred_key)
            data['fed_rate'] = fred.get_series('DFF', start_date=start_date)
            data['us_cpi'] = fred.get_series('CPIAUCSL', start_date=start_date)
            
        # 2. Policy Uncertainty (directo)
        data['epu_mexico'] = pd.read_excel(
            "https://www.policyuncertainty.com/media/Mexico_Policy_Uncertainty_Data.xlsx"
        )
        
        # 3. World Bank Commodities
        data['wb_commodities'] = pd.read_excel(
            "https://thedocs.worldbank.org/en/doc/5d903e848db1d1b83e0ec8f744e55570-0350012021/related/CMO-Historical-Data-Monthly.xlsx",
            sheet_name='Monthly Prices'
        )
        
        return data
```

### 7. **Prioridad de Implementación**

1. **INMEDIATO**: Configurar FRED API para obtener tasas Fed e inflación USA
2. **HOY**: Descargar todos los índices EPU (archivos Excel directos)
3. **HOY**: Obtener Pink Sheet del World Bank
4. **MAÑANA**: Explorar INEGI para índices de construcción
5. **OPCIONAL**: Investigar proxies gratuitos para LME actualizados

### ⚠️ **Notas Importantes**

- **Frecuencia de actualización**: La mayoría de datos macro se actualizan mensualmente
- **Cacheo recomendado**: Guardar datos descargados para evitar límites de API
- **Versionado**: Mantener histórico de descargas para reproducibilidad
- **Validación**: Siempre verificar continuidad y calidad de series temporales

---

**Actualizado**: 2025-09-28
**Siguiente paso**: Implementar script consolidador con todas las fuentes
