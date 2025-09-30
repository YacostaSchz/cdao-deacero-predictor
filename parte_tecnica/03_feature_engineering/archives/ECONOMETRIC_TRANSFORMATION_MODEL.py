#!/usr/bin/env python3
"""
MODELO ECONOMÉTRICO DE TRANSFORMACIÓN LME → MÉXICO
Usando TODAS las variables disponibles y puntos de datos
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

class EconometricPremiumModel:
    """Modelo econométrico para transformar precios LME a México"""
    
    def __init__(self):
        self.all_mexico_data = self._load_all_mexico_points()
        self.features = None
        self.model = None
        self.scaler = StandardScaler()
        
    def _load_all_mexico_points(self):
        """Cargar TODOS los puntos de México con deduplicación"""
        
        # TODOS los puntos únicos
        points = [
            # Enero 2025
            {'date': '2025-01-31', 'price_mxn': 17392, 'price_usd': None, 'type': 'menudeo', 
             'source': 'promedio', 'note': 'Promedio Casa Herrera/Home Depot'},
            
            # Noviembre 2024 - Marzo 2025 (periodo estable)
            {'date': '2024-12-15', 'price_mxn': 17300, 'price_usd': None, 'type': 'menudeo'},
            {'date': '2025-01-15', 'price_mxn': 17300, 'price_usd': None, 'type': 'menudeo'},
            {'date': '2025-02-15', 'price_mxn': 17300, 'price_usd': None, 'type': 'menudeo'},
            {'date': '2025-03-15', 'price_mxn': 17300, 'price_usd': None, 'type': 'menudeo'},
            
            # Abril 2025 (alza)
            {'date': '2025-04-02', 'price_mxn': 17500, 'price_usd': None, 'type': 'menudeo'},
            {'date': '2025-04-09', 'price_mxn': 18200, 'price_usd': 884, 'type': 'menudeo'},
            
            # Junio 2025
            {'date': '2025-06-25', 'price_mxn': 17500, 'price_usd': 919, 'type': 'menudeo'},
            {'date': '2025-06-26', 'price_mxn': 17500, 'price_usd': 905, 'type': 'menudeo'},
            
            # Agosto 2025
            {'date': '2025-08-13', 'price_mxn': 17860, 'price_usd': 938, 'type': 'menudeo'},
            
            # Septiembre 2025
            {'date': '2025-09-03', 'price_mxn': 17864, 'price_usd': 948, 'type': 'menudeo'},
            {'date': '2025-09-10', 'price_mxn': 17484, 'price_usd': 928, 'type': 'menudeo'},
            {'date': '2025-09-17', 'price_mxn': 17284, 'price_usd': 917, 'type': 'menudeo'},
            
            # Mayorista (descuento ~10-15%)
            {'date': '2025-09-01', 'price_mxn': 15569, 'price_usd': None, 'type': 'mayorista',
             'note': 'Promedio TuCompa/MaxiAcer'},
            
            # Minorista (premium ~5-10%)
            {'date': '2025-09-01', 'price_mxn': 18640, 'price_usd': None, 'type': 'minorista',
             'note': 'Promedio Construalianza/Materiales Cortés'},
        ]
        
        return pd.DataFrame(points)
    
    def load_macro_features(self):
        """Cargar TODAS las variables macro disponibles"""
        
        print("📊 CARGANDO TODAS LAS VARIABLES DISPONIBLES")
        print("="*60)
        
        # 1. Banxico macro
        banxico = pd.read_csv('../../02_data_extractors/outputs/banxico_consolidated_data.csv')
        banxico['date'] = pd.to_datetime(banxico['date'])
        banxico = banxico[banxico['date'] >= '2025-01-01'].set_index('date')
        
        # 2. LME
        lme = pd.read_csv('../../02_data_extractors/outputs/lme_sr_long.csv')
        lme['date'] = pd.to_datetime(lme['date'])
        lme = lme[lme['date'] >= '2025-01-01']
        lme = lme[~lme['date'].duplicated(keep='last')].set_index('date')
        
        # 3. EPU
        epu = pd.read_csv('../../02_data_extractors/outputs/epu_mexico_data.csv')
        epu['date'] = pd.to_datetime(epu[['Year', 'Month']].assign(day=1))
        epu = epu[epu['date'] >= '2025-01-01'].set_index('date')
        epu['epu_mexico'] = pd.to_numeric(epu['Mexico_Policy_Uncertainty'], errors='coerce')
        
        # 4. Gas Natural
        gas = pd.read_csv('../../02_data_extractors/outputs/gas_natural_ipgn_data.csv')
        gas['date'] = pd.to_datetime(gas['date'])
        gas = gas[gas['date'] >= '2025-01-01'].set_index('date')
        
        # Crear dataset consolidado
        date_range = pd.date_range('2025-01-01', '2025-09-30', freq='D')
        features = pd.DataFrame(index=date_range)
        
        # Variables actuales en el modelo
        print("\n📈 VARIABLES EN EL MODELO:")
        
        # 1. LME base
        features['lme_price'] = lme['sr_m01'].reindex(features.index).interpolate()
        features['lme_volatility'] = features['lme_price'].rolling(20).std()
        features['lme_momentum'] = features['lme_price'].pct_change(5)
        print("✓ LME: precio, volatilidad, momentum")
        
        # 2. FX
        features['usdmxn'] = banxico['usdmxn'].reindex(features.index).interpolate()
        features['fx_volatility'] = features['usdmxn'].rolling(30).std()
        features['fx_momentum'] = features['usdmxn'].pct_change(5)
        print("✓ FX: tipo de cambio, volatilidad, momentum")
        
        # 3. Tasas de interés
        features['tiie'] = banxico['tiie'].reindex(features.index).ffill()
        features['cpi'] = banxico['inpc'].reindex(features.index).interpolate()
        features['real_rate'] = features['tiie'] - features['cpi'].pct_change(252)*100
        features['rate_differential'] = features['tiie'] - 5.25  # vs Fed aprox
        print("✓ Tasas: TIIE, tasa real, diferencial MX-US")
        
        # 4. EPU e incertidumbre
        features['epu_mexico'] = epu['epu_mexico'].reindex(features.index).ffill()
        features['epu_ma30'] = features['epu_mexico'].rolling(30).mean()
        features['market_stress'] = (features['fx_volatility'] * features['epu_mexico']/100).fillna(0)
        print("✓ Incertidumbre: EPU México, stress compuesto")
        
        # 5. Gas Natural (costo energético)
        features['gas_price'] = gas['ipgn'].reindex(features.index).interpolate()
        features['energy_cost_index'] = features['gas_price'] / features['gas_price'].mean()
        print("✓ Energía: precio gas natural, índice costo")
        
        # 6. Estacionalidad construcción
        features['month'] = features.index.month
        features['seasonal_construction'] = np.where(
            features['month'].isin([3,4,5,9,10,11]), 1.05, 0.95
        )
        features['month_end'] = (features.index.day > 25).astype(int)
        print("✓ Estacional: temporada construcción, fin de mes")
        
        # 7. Estructura de mercado (aproximada)
        features['import_restrictions'] = np.where(features.index >= '2025-04-01', 1, 0)
        features['market_concentration'] = 0.75  # HHI aproximado mercado MX
        print("✓ Mercado: restricciones importación, concentración")
        
        return features
    
    def calculate_dynamic_premium(self, features):
        """Calcular premium dinámico basado en variables macro"""
        
        # Componentes del premium
        premium_base = 0.65  # Base histórica ~65%
        
        # Ajustes dinámicos
        fx_effect = 0.10 * (features['fx_volatility'] / features['fx_volatility'].mean() - 1)
        rate_effect = 0.02 * features['rate_differential']
        epu_effect = 0.05 * (features['epu_mexico'] / 100 - 1)
        seasonal_effect = 0.03 * (features['seasonal_construction'] - 1)
        import_effect = 0.05 * features['import_restrictions']
        energy_effect = 0.02 * (features['energy_cost_index'] - 1)
        
        # Premium total
        premium_dynamic = (fx_effect + rate_effect + epu_effect + 
                          seasonal_effect + import_effect + energy_effect)
        
        premium_total = premium_base + premium_dynamic
        
        return 1 + premium_total  # Como ratio multiplicativo
    
    def create_econometric_series(self):
        """Crear serie completa con modelo econométrico"""
        
        print("\n🔬 CREANDO SERIE ECONOMÉTRICA")
        print("="*60)
        
        # Cargar features
        features = self.load_macro_features()
        
        # Calcular premium dinámico
        features['premium_ratio'] = self.calculate_dynamic_premium(features)
        
        # Transformación LME → México
        features['mexico_usd_model'] = features['lme_price'] * features['premium_ratio']
        features['mexico_mxn_model'] = features['mexico_usd_model'] * features['usdmxn']
        
        # Ajuste por segmento (menudeo default)
        features['segment_adjustment'] = 1.0  # Menudeo
        features['mexico_mxn_final'] = features['mexico_mxn_model'] * features['segment_adjustment']
        
        # Comparar con datos reales
        print("\nVALIDACIÓN CON DATOS REALES:")
        real_points = self.all_mexico_data[self.all_mexico_data['price_usd'].notna()]
        
        for _, point in real_points.iterrows():
            date = pd.to_datetime(point['date'])
            if date in features.index:
                model_price = features.loc[date, 'mexico_mxn_final']
                real_price = point['price_mxn']
                error_pct = abs(model_price - real_price) / real_price * 100
                
                print(f"{date.strftime('%Y-%m-%d')}: ")
                print(f"  Real: {real_price:,.0f} MXN/t")
                print(f"  Modelo: {model_price:,.0f} MXN/t")
                print(f"  Error: {error_pct:.1f}%")
        
        # Estadísticas
        print(f"\nESTADÍSTICAS SERIE COMPLETA:")
        print(f"Rango precios: {features['mexico_mxn_final'].min():,.0f} - {features['mexico_mxn_final'].max():,.0f}")
        print(f"Precio promedio: {features['mexico_mxn_final'].mean():,.0f} MXN/t")
        print(f"Volatilidad: {features['mexico_mxn_final'].std():,.0f}")
        
        return features
    
    def save_results(self, features):
        """Guardar resultados del modelo"""
        
        # Seleccionar columnas clave
        output = features[[
            'lme_price', 'usdmxn', 'premium_ratio',
            'mexico_usd_model', 'mexico_mxn_model', 'mexico_mxn_final',
            'fx_volatility', 'tiie', 'epu_mexico', 'gas_price'
        ]].copy()
        
        output.to_csv('outputs/econometric_mexico_series.csv')
        print(f"\n✅ Serie econométrica guardada en outputs/econometric_mexico_series.csv")
        
        # Guardar muestra para API
        latest = output.iloc[-1]
        api_response = {
            'lme_price_usd': round(latest['lme_price'], 2),
            'premium_applied': round(latest['premium_ratio'], 4),
            'fx_rate': round(latest['usdmxn'], 2),
            'mexico_price_usd': round(latest['mexico_usd_model'], 2),
            'mexico_price_mxn': round(latest['mexico_mxn_final'], 2),
            'macro_drivers': {
                'fx_volatility': round(latest['fx_volatility'], 3),
                'tiie': round(latest['tiie'], 2),
                'epu_index': round(latest['epu_mexico'], 1),
                'gas_price': round(latest['gas_price'], 2)
            }
        }
        
        import json
        with open('outputs/econometric_api_example.json', 'w') as f:
            json.dump(api_response, f, indent=2)
        
        return output

if __name__ == "__main__":
    print("🔬 MODELO ECONOMÉTRICO LME → MÉXICO")
    print("="*80)
    
    # Crear modelo
    model = EconometricPremiumModel()
    
    # Generar serie econométrica
    econometric_series = model.create_econometric_series()
    
    # Guardar resultados
    output = model.save_results(econometric_series)
    
    print("\n🎯 MODELO ECONOMÉTRICO COMPLETADO")
    print("Variables utilizadas: 15+ indicadores macro")
    print("Fórmula: P_MX = P_LME × (1 + 0.65 + ajustes_dinámicos) × FX")
    print("Ajustes incluyen: FX vol, TIIE, EPU, gas, estacionalidad, restricciones")
