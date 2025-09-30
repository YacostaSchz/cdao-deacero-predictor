#!/usr/bin/env python3
"""
Análisis Econométrico Honesto: LME → México Transfer Function
Con reconocimiento explícito de limitaciones de datos
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class HonestEconometricAnalysis:
    """Análisis transparente con cuantificación de incertidumbre"""
    
    def __init__(self):
        self.real_mexico_prices = {
            '2025-06-26': {'price_mxn': 17500, 'price_usd': 905, 'source': 'reportacero'},
            '2025-08-10': {'price_mxn': 17860, 'price_usd': 938, 'source': 'reportacero'},
            '2025-09-14': {'price_mxn': 17284, 'price_usd': 940, 'source': 'reportacero'},
            '2025-09-20': {'price_mxn': None, 'price_usd': 625, 'source': 'steelradar'}
        }
        
    def load_data(self):
        """Cargar datos con manejo transparente de limitaciones"""
        print("🔍 Cargando datos disponibles...")
        
        # LME data
        try:
            # Buscar primero el archivo combinado
            lme_path = '../02_data_extractors/outputs/lme_combined_sr_sc.csv'
            if not os.path.exists(lme_path):
                # Si no existe, buscar archivos separados
                lme_sr_path = '../02_data_extractors/outputs/lme_sr_long.csv'
                if os.path.exists(lme_sr_path):
                    lme_df = pd.read_csv(lme_sr_path, parse_dates=['date'], index_col='date')
                    # Renombrar columnas si es necesario
                    if 'closing_price' in lme_df.columns:
                        lme_df.rename(columns={'closing_price': 'sr_m01'}, inplace=True)
                else:
                    raise FileNotFoundError("No LME data found")
            else:
                lme_df = pd.read_csv(lme_path, parse_dates=['date'], index_col='date')
            print(f"✓ LME data: {len(lme_df)} días")
        except Exception as e:
            print(f"❌ Error cargando LME data: {e}")
            return None, None, None
            
        # Banxico FX data
        try:
            fx_path = '../02_data_extractors/outputs/SF43783_data.csv'  # Tipo de cambio
            if os.path.exists(fx_path):
                fx_df = pd.read_csv(fx_path, parse_dates=['date'], index_col='date')
                # Renombrar columna si es necesario
                if 'value' in fx_df.columns:
                    fx_df.rename(columns={'value': 'fx_rate'}, inplace=True)
            else:
                # Buscar en el archivo consolidado
                banxico_path = '../02_data_extractors/outputs/banxico_consolidated_data.csv'
                fx_df = pd.read_csv(banxico_path, parse_dates=['date'], index_col='date')
                if 'SF43783' in fx_df.columns:
                    fx_df = fx_df[['SF43783']].rename(columns={'SF43783': 'fx_rate'})
            print(f"✓ FX data: {len(fx_df)} días")
        except Exception as e:
            print(f"❌ Error cargando FX data: {e}")
            fx_df = None
            
        # Real Mexico prices (sparse)
        mexico_df = pd.DataFrame.from_dict(self.real_mexico_prices, orient='index')
        mexico_df.index = pd.to_datetime(mexico_df.index)
        print(f"⚠️  Mexico real prices: Solo {len(mexico_df)} puntos")
        
        return lme_df, fx_df, mexico_df
        
    def analyze_premiums(self, lme_df, mexico_df):
        """Analizar premiums observados con honestidad sobre dispersión"""
        print("\n📊 ANÁLISIS DE PREMIUMS MÉXICO/LME")
        print("="*50)
        
        premiums = []
        for date, mx_data in self.real_mexico_prices.items():
            if mx_data['price_usd']:
                # Buscar precio LME más cercano
                date_obj = pd.to_datetime(date)
                lme_price = self._get_closest_lme_price(lme_df, date_obj)
                
                if lme_price:
                    premium = mx_data['price_usd'] / lme_price
                    premiums.append({
                        'date': date,
                        'mexico_usd': mx_data['price_usd'],
                        'lme_usd': lme_price,
                        'premium': premium,
                        'premium_pct': (premium - 1) * 100,
                        'source': mx_data['source']
                    })
        
        premium_df = pd.DataFrame(premiums)
        
        # Estadísticas críticas
        print("\n🎯 Premiums Observados:")
        print(premium_df[['date', 'mexico_usd', 'lme_usd', 'premium_pct', 'source']])
        
        print(f"\n📈 Estadísticas de Premium:")
        print(f"  - Media: {premium_df['premium'].mean():.2f} ({premium_df['premium_pct'].mean():.1f}%)")
        print(f"  - Std Dev: {premium_df['premium'].std():.2f} ({premium_df['premium_pct'].std():.1f}%)")
        print(f"  - Min: {premium_df['premium'].min():.2f} ({premium_df['premium_pct'].min():.1f}%)")
        print(f"  - Max: {premium_df['premium'].max():.2f} ({premium_df['premium_pct'].max():.1f}%)")
        print(f"  - Rango: {premium_df['premium_pct'].max() - premium_df['premium_pct'].min():.1f}%")
        
        # Advertencia crítica
        print("\n⚠️  ADVERTENCIA CRÍTICA:")
        print(f"  - Solo {len(premium_df)} observaciones reales")
        print(f"  - Dispersión ENORME: {premium_df['premium_pct'].std():.1f}% std dev")
        print(f"  - Posibles problemas: Diferentes calidades, mercados, timing")
        
        return premium_df
        
    def _get_closest_lme_price(self, lme_df, target_date):
        """Obtener precio LME más cercano a una fecha"""
        if 'sr_m01' not in lme_df.columns:
            return None
            
        # Buscar ±3 días
        for offset in range(-3, 4):
            check_date = target_date + timedelta(days=offset)
            if check_date in lme_df.index:
                return lme_df.loc[check_date, 'sr_m01']
        return None
        
    def analyze_temporal_lag(self, lme_df, mexico_df):
        """Analizar lag temporal LME → México"""
        print("\n⏱️  ANÁLISIS DE LAG TEMPORAL")
        print("="*50)
        
        # Con solo 4 puntos, análisis muy limitado
        print("⚠️  Análisis limitado por escasez de datos")
        print("Suposiciones basadas en teoría económica:")
        print("  - LME cierra 17:00 Londres = 11:00 México")
        print("  - Transmisión de precios: 1-3 días típicamente")
        print("  - Mayor lag en períodos de alta volatilidad")
        
        return {
            'estimated_lag_days': 1,
            'confidence': 'Very Low',
            'note': 'Based on theory, not empirical evidence'
        }
        
    def build_transfer_model(self, premium_stats):
        """Construir modelo de transferencia honesto"""
        print("\n🔧 MODELO DE TRANSFERENCIA PROPUESTO")
        print("="*50)
        
        model = {
            'type': 'Simple Transfer Function with Uncertainty',
            'equation': 'P_Mexico_MXN = P_LME_USD × FX_USD/MXN × Premium_t',
            'components': {
                'lme_model': 'Tus features existentes (lags, spreads, etc.)',
                'fx_model': 'ARIMA simple o último valor',
                'premium_model': {
                    'point_estimate': premium_stats['premium'].mean(),
                    'uncertainty': premium_stats['premium'].std(),
                    'distribution': 'Normal (por simplicidad)',
                    'confidence_intervals': {
                        '50%': [
                            premium_stats['premium'].mean() - 0.67 * premium_stats['premium'].std(),
                            premium_stats['premium'].mean() + 0.67 * premium_stats['premium'].std()
                        ],
                        '90%': [
                            premium_stats['premium'].mean() - 1.64 * premium_stats['premium'].std(),
                            premium_stats['premium'].mean() + 1.64 * premium_stats['premium'].std()
                        ],
                        '95%': [
                            premium_stats['premium'].mean() - 1.96 * premium_stats['premium'].std(),
                            premium_stats['premium'].mean() + 1.96 * premium_stats['premium'].std()
                        ]
                    }
                }
            },
            'limitations': [
                'Premium basado en solo 4 observaciones',
                'Asume normalidad sin evidencia suficiente',
                'Ignora posibles cambios estructurales',
                'No captura estacionalidad o tendencias'
            ]
        }
        
        print(json.dumps(model, indent=2))
        return model
        
    def generate_implementation_plan(self):
        """Plan de implementación honesto y pragmático"""
        print("\n📋 PLAN DE IMPLEMENTACIÓN RECOMENDADO")
        print("="*50)
        
        plan = {
            'immediate_actions': [
                '1. Mantener tu modelo LME existente (RandomForest)',
                '2. Añadir componente FX simple (último valor o MA)',
                '3. Implementar premium estocástico con intervalos amplios',
                '4. API con respuesta transparente sobre incertidumbre'
            ],
            'api_response_format': {
                'predicted_price_mxn': 'float',
                'predicted_price_usd': 'float',
                'confidence_level': 'Low',
                'prediction_intervals': {
                    'mxn': {'50%': [], '90%': []},
                    'usd': {'50%': [], '90%': []}
                },
                'components': {
                    'lme_forecast_usd': 'float',
                    'fx_rate': 'float',
                    'premium_applied': 'float'
                },
                'metadata': {
                    'model_version': '1.0-honest',
                    'data_points_used': 4,
                    'last_updated': 'date',
                    'warnings': []
                }
            }
        }
        
        print(json.dumps(plan, indent=2))
        return plan

def main():
    """Ejecutar análisis completo"""
    print("🚀 ANÁLISIS ECONOMÉTRICO HONESTO - STEEL REBAR MÉXICO")
    print("="*60)
    
    analyzer = HonestEconometricAnalysis()
    
    # 1. Cargar datos
    lme_df, fx_df, mexico_df = analyzer.load_data()
    
    if lme_df is None:
        print("❌ No se pueden cargar datos necesarios")
        return
        
    # 2. Analizar premiums
    premium_df = analyzer.analyze_premiums(lme_df, mexico_df)
    
    # 3. Analizar lag temporal
    lag_analysis = analyzer.analyze_temporal_lag(lme_df, mexico_df)
    
    # 4. Construir modelo
    transfer_model = analyzer.build_transfer_model(premium_df)
    
    # 5. Plan de implementación
    implementation = analyzer.generate_implementation_plan()
    
    # 6. Guardar resultados
    results = {
        'analysis_date': datetime.now().isoformat(),
        'real_prices_count': len(mexico_df),
        'premium_statistics': {
            'mean': float(premium_df['premium'].mean()),
            'std': float(premium_df['premium'].std()),
            'min': float(premium_df['premium'].min()),
            'max': float(premium_df['premium'].max())
        },
        'lag_analysis': lag_analysis,
        'transfer_model': transfer_model,
        'implementation_plan': implementation,
        'critical_warnings': [
            'Model based on only 4 real price points',
            'Premium volatility is extremely high (16%-74%)',
            'No validation possible with current data',
            'High uncertainty in predictions expected'
        ]
    }
    
    with open('outputs/honest_econometric_analysis.json', 'w') as f:
        json.dump(results, f, indent=2)
        
    print("\n✅ Análisis guardado en outputs/honest_econometric_analysis.json")
    print("\n🎯 SIGUIENTE PASO: Implementar modelo con estos parámetros honestos")

if __name__ == "__main__":
    main()
