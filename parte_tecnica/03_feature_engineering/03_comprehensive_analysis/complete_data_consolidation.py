#!/usr/bin/env python3
"""
Consolidación Completa de Datos - Steel Rebar México
Integrando prices_mxn.md + september_prices.md + Interpolación
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class CompleteDataConsolidation:
    """Consolidación de TODOS los datos disponibles con interpolación"""
    
    def __init__(self):
        # CONSOLIDACIÓN COMPLETA DE TODOS LOS PUNTOS DISPONIBLES
        self.all_price_points = {
            # === DATOS HISTÓRICOS 2025 ===
            '2025-01-31': {
                'price_mxn': 17500, 'price_usd': None, 'type': 'menudeo', 
                'source': 'adn40_herrera', 'quality': 'exact_date'
            },
            '2025-01-31_b': {
                'price_mxn': 17284, 'price_usd': None, 'type': 'menudeo', 
                'source': 'adn40_homedepot', 'quality': 'exact_date'
            },
            
            # === PERÍODO NOV 2024 - MAR 2025 ===
            '2025-02-15': {  # Punto medio del período estable
                'price_mxn': 17300, 'price_usd': None, 'type': 'menudeo', 
                'source': 'reportacero_stable_period', 'quality': 'period_average'
            },
            
            # === ABRIL 2025 ===
            '2025-04-01': {  # Inicio incremento 1.3%
                'price_mxn': 17500, 'price_usd': None, 'type': 'menudeo', 
                'source': 'reportacero', 'quality': 'range_start'
            },
            '2025-04-09': {  # Semana 15 - después incremento 5.4%
                'price_mxn': 18200, 'price_usd': 884, 'type': 'menudeo', 
                'source': 'reportacero', 'quality': 'converted_estimate'
            },
            
            # === JUNIO 2025 ===
            '2025-06-25': {  # Semana 26
                'price_mxn': 17500, 'price_usd': 919, 'type': 'menudeo', 
                'source': 'reportacero', 'quality': 'range_mid'
            },
            '2025-06-26': {  # Fecha exacta
                'price_mxn': 17500, 'price_usd': 905, 'type': 'menudeo', 
                'source': 'reportacero', 'quality': 'exact_date'
            },
            
            # === AGOSTO 2025 ===
            '2025-08-13': {  # Semana 33
                'price_mxn': 17860, 'price_usd': 938, 'type': 'menudeo', 
                'source': 'reportacero', 'quality': 'range_mid'
            },
            
            # === SEPTIEMBRE 2025 ===
            '2025-09-03': {  # Semana 36 (31 ago - 6 sep)
                'price_mxn': 17864, 'price_usd': 948, 'type': 'menudeo', 
                'source': 'reportacero', 'quality': 'range_mid'
            },
            '2025-09-10': {  # Semana 37 (7-13 sep)
                'price_mxn': 17484, 'price_usd': 928, 'type': 'menudeo', 
                'source': 'reportacero', 'quality': 'range_mid'
            },
            '2025-09-17': {  # Semana 38 (14-20 sep)
                'price_mxn': 17284, 'price_usd': 917, 'type': 'menudeo', 
                'source': 'reportacero', 'quality': 'range_mid'
            },
            
            # === DATOS ADICIONALES DE SEPTEMBER_PRICES.MD ===
            '2025-09-26': {  # SteelOrbis semanal
                'price_mxn': 13900, 'price_usd': None, 'type': 'mayorista', 
                'source': 'steeloribis_weekly', 'quality': 'weekly_indicative',
                'note': 'Significantly lower - different market segment?'
            },
            
            # === PRECIOS MAYORISTAS SEPTIEMBRE ===
            '2025-09-15': {  # Catálogo TuCompa (promedio rango)
                'price_mxn': 15449, 'price_usd': None, 'type': 'mayorista', 
                'source': 'tucompa_catalog', 'quality': 'catalog_mid'
            },
            '2025-09-15_b': {  # Catálogo MaxiAcer (promedio rango)
                'price_mxn': 15688, 'price_usd': None, 'type': 'mayorista', 
                'source': 'maxiacer_catalog', 'quality': 'catalog_mid'
            },
            '2025-09-15_c': {  # Construalianza
                'price_mxn': 18280, 'price_usd': None, 'type': 'minorista', 
                'source': 'construalianza', 'quality': 'catalog_exact'
            },
            '2025-09-15_d': {  # Materiales Cortés
                'price_mxn': 19000, 'price_usd': None, 'type': 'minorista', 
                'source': 'materialescortes', 'quality': 'catalog_exact'
            }
            
            # OUTLIER REMOVIDO: SteelRadar 625 USD/ton
        }
        
    def load_fx_data_comprehensive(self):
        """Cargar datos FX con mayor cobertura temporal"""
        print("🔍 Cargando datos FX completos...")
        
        fx_candidates = [
            '../02_data_extractors/outputs/banxico_consolidated_data.csv',
            '../02_data_extractors/outputs/SF43783_data.csv'
        ]
        
        for fx_path in fx_candidates:
            try:
                fx_df = pd.read_csv(fx_path)
                print(f"✓ FX data: {fx_path}")
                print(f"Columnas: {fx_df.columns.tolist()}")
                print(f"Muestra: {fx_df.head()}")
                
                # Procesar según estructura
                if 'SF43783' in fx_df.columns:
                    fx_clean = fx_df[['date', 'SF43783']].copy()
                    fx_clean.rename(columns={'SF43783': 'fx_rate'}, inplace=True)
                elif 'value' in fx_df.columns:
                    fx_clean = fx_df[['date', 'value']].copy()
                    fx_clean.rename(columns={'value': 'fx_rate'}, inplace=True)
                else:
                    continue
                    
                fx_clean['date'] = pd.to_datetime(fx_clean['date'])
                fx_clean = fx_clean.set_index('date').sort_index()
                
                print(f"✓ FX procesado: {len(fx_clean)} puntos")
                print(f"Rango: {fx_clean.index.min()} - {fx_clean.index.max()}")
                return fx_clean
                
            except Exception as e:
                print(f"❌ Error con {fx_path}: {e}")
                continue
                
        print("⚠️ Usando FX estimado")
        # FX estimado basado en datos típicos 2025
        dates = pd.date_range('2025-01-01', '2025-09-30', freq='D')
        fx_rates = np.linspace(17.8, 19.2, len(dates))  # Tendencia típica 2025
        return pd.DataFrame({'fx_rate': fx_rates}, index=dates)
        
    def convert_all_to_usd(self, fx_df):
        """Convertir TODOS los precios MXN a USD usando FX real"""
        print("\n💱 CONVIRTIENDO TODOS LOS PRECIOS A USD")
        print("="*60)
        
        converted_prices = {}
        
        for date_str, price_data in self.all_price_points.items():
            # Limpiar sufijos _b, _c, _d de la fecha
            clean_date = date_str.split('_')[0]
            date_obj = pd.to_datetime(clean_date)
            
            # Obtener FX rate más cercano
            fx_rate = self._get_fx_rate(fx_df, date_obj)
            
            # Convertir si es necesario
            if price_data.get('price_usd') is not None:
                # Ya tiene USD
                converted_usd = price_data['price_usd']
            elif price_data.get('price_mxn') is not None and fx_rate:
                # Convertir MXN a USD
                converted_usd = round(price_data['price_mxn'] / fx_rate, 0)
            else:
                converted_usd = None
                
            if converted_usd:
                converted_prices[date_str] = {
                    **price_data,
                    'price_usd_final': converted_usd,
                    'fx_rate_used': fx_rate,
                    'conversion_method': 'existing' if price_data.get('price_usd') else 'converted'
                }
                
        print(f"✅ Convertidos: {len(converted_prices)} puntos")
        return converted_prices
        
    def create_interpolated_series(self, converted_prices, lme_df):
        """Crear serie interpolada y calcular premiums"""
        print("\n📈 CREANDO SERIE INTERPOLADA")
        print("="*60)
        
        # Crear DataFrame base
        price_list = []
        for date_str, data in converted_prices.items():
            clean_date = date_str.split('_')[0]
            price_list.append({
                'date': clean_date,
                'mexico_usd': data['price_usd_final'],
                'mexico_mxn': data.get('price_mxn'),
                'type': data['type'],
                'source': data['source'],
                'quality': data['quality'],
                'fx_rate': data.get('fx_rate_used'),
                'original_key': date_str
            })
            
        df = pd.DataFrame(price_list)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        print(f"📊 Puntos base: {len(df)}")
        
        # Separar por tipo de mercado para interpolación diferenciada
        menudeo_df = df[df['type'] == 'menudeo'].copy()
        mayorista_df = df[df['type'] == 'mayorista'].copy()
        
        print(f"  - Menudeo: {len(menudeo_df)} puntos")
        print(f"  - Mayorista: {len(mayorista_df)} puntos")
        
        # Interpolación para menudeo (serie principal)
        if len(menudeo_df) > 2:
            full_dates = pd.date_range(menudeo_df['date'].min(), 
                                     menudeo_df['date'].max(), 
                                     freq='D')
            
            menudeo_interp = menudeo_df.set_index('date').reindex(full_dates)
            menudeo_interp['mexico_usd'] = menudeo_interp['mexico_usd'].interpolate(method='linear')
            menudeo_interp['type'] = 'menudeo'
            
            print(f"✅ Serie menudeo interpolada: {len(menudeo_interp)} días")
        
        # Calcular premiums vs LME
        premiums_data = []
        
        for date, row in menudeo_interp.iterrows():
            if pd.notna(row['mexico_usd']):
                lme_price = self._get_closest_lme_price(lme_df, date)
                
                if lme_price and lme_price > 0:
                    premium = row['mexico_usd'] / lme_price
                    
                    premiums_data.append({
                        'date': date,
                        'mexico_usd': row['mexico_usd'],
                        'lme_usd': lme_price,
                        'premium': premium,
                        'premium_pct': (premium - 1) * 100,
                        'data_type': 'interpolated' if pd.isna(menudeo_df.set_index('date').get(date, {}).get('mexico_usd')) else 'real'
                    })
                    
        premium_df = pd.DataFrame(premiums_data)
        
        print(f"✅ Premiums calculados: {len(premium_df)} puntos")
        print(f"  - Datos reales: {len(premium_df[premium_df['data_type'] == 'real'])}")
        print(f"  - Interpolados: {len(premium_df[premium_df['data_type'] == 'interpolated'])}")
        
        return df, menudeo_interp, premium_df
        
    def analyze_market_segments(self, original_df):
        """Analizar diferencias entre segmentos de mercado"""
        print("\n🏪 ANÁLISIS POR SEGMENTO DE MERCADO")
        print("="*60)
        
        segments = original_df.groupby('type').agg({
            'mexico_usd': ['count', 'mean', 'min', 'max', 'std'],
            'mexico_mxn': ['mean']
        }).round(2)
        
        print("📋 Estadísticas por segmento:")
        for segment in segments.index:
            data = segments.loc[segment]
            usd_mean = data[('mexico_usd', 'mean')]
            usd_count = data[('mexico_usd', 'count')]
            usd_range = f"{data[('mexico_usd', 'min')]}-{data[('mexico_usd', 'max')]}"
            
            print(f"  {segment.upper()}:")
            print(f"    - Observaciones: {int(usd_count)}")
            print(f"    - Promedio USD: {usd_mean}")
            print(f"    - Rango USD: {usd_range}")
            
        # Calcular spread mayorista vs menudeo
        menudeo_mean = segments.loc['menudeo', ('mexico_usd', 'mean')]
        mayorista_mean = segments.loc['mayorista', ('mexico_usd', 'mean')] if 'mayorista' in segments.index else None
        
        if mayorista_mean:
            spread = (menudeo_mean - mayorista_mean) / mayorista_mean * 100
            print(f"\n💰 SPREAD MENUDEO vs MAYORISTA: {spread:.1f}%")
            print(f"   - Menudeo: {menudeo_mean:.0f} USD/t")
            print(f"   - Mayorista: {mayorista_mean:.0f} USD/t")
        
        return segments
        
    def _get_fx_rate(self, fx_df, target_date):
        """Obtener tipo de cambio más cercano"""
        if fx_df is None or len(fx_df) == 0:
            return 18.5  # Estimación conservadora
            
        try:
            # Buscar fecha exacta o cercana
            for offset in range(-7, 8):
                check_date = target_date + timedelta(days=offset)
                if check_date in fx_df.index:
                    rate = fx_df.loc[check_date, 'fx_rate']
                    if pd.notna(rate) and rate > 0:
                        return rate
        except:
            pass
            
        # Si no encuentra, usar último valor disponible
        return fx_df['fx_rate'].dropna().iloc[-1] if len(fx_df['fx_rate'].dropna()) > 0 else 18.5
        
    def _get_closest_lme_price(self, lme_df, target_date):
        """Obtener precio LME más cercano"""
        if lme_df is None:
            return None
            
        price_cols = [col for col in lme_df.columns if 'sr' in col.lower() or 'closing' in col.lower()]
        if not price_cols:
            return None
            
        price_col = price_cols[0]
        
        for offset in range(-5, 6):
            check_date = target_date + timedelta(days=offset)
            if check_date in lme_df.index:
                price = lme_df.loc[check_date, price_col]
                if pd.notna(price) and price > 0:
                    return price
        return None

def main():
    """Ejecutar consolidación completa con interpolación"""
    print("🚀 CONSOLIDACIÓN COMPLETA - STEEL REBAR MÉXICO")
    print("="*80)
    print("📊 Integrando prices_mxn.md + september_prices.md + Interpolación")
    
    consolidator = CompleteDataConsolidation()
    
    # 1. Cargar datos base
    print(f"\n📋 PUNTOS DISPONIBLES: {len(consolidator.all_price_points)}")
    
    # 2. Cargar FX y LME
    fx_df = consolidator.load_fx_data_comprehensive()
    
    # Cargar LME
    try:
        lme_df = pd.read_csv('../02_data_extractors/outputs/lme_sr_long.csv', 
                           parse_dates=['date'], index_col='date')
        print(f"✓ LME data: {len(lme_df)} puntos")
    except:
        print("❌ No se pudo cargar LME")
        return
    
    # 3. Convertir todo a USD
    converted_prices = consolidator.convert_all_to_usd(fx_df)
    
    # 4. Crear series interpoladas
    original_df, interpolated_series, premium_df = consolidator.create_interpolated_series(
        converted_prices, lme_df)
    
    # 5. Análisis por segmentos
    segments_analysis = consolidator.analyze_market_segments(original_df)
    
    # 6. Estadísticas finales de premium
    print(f"\n📈 ESTADÍSTICAS PREMIUM FINALES:")
    print(f"  - Media: {premium_df['premium'].mean():.4f} ({premium_df['premium_pct'].mean():.1f}%)")
    print(f"  - Mediana: {premium_df['premium'].median():.4f}")
    print(f"  - Desv Std: {premium_df['premium'].std():.4f}")
    print(f"  - Puntos: {len(premium_df)}")
    
    # 7. Guardar resultados
    results = {
        'consolidation_date': datetime.now().isoformat(),
        'total_data_points': len(consolidator.all_price_points),
        'converted_points': len(converted_prices),
        'premium_points': len(premium_df),
        'interpolated_days': len(interpolated_series),
        
        'premium_statistics': {
            'mean': float(premium_df['premium'].mean()),
            'median': float(premium_df['premium'].median()),
            'std': float(premium_df['premium'].std()),
            'min': float(premium_df['premium'].min()),
            'max': float(premium_df['premium'].max())
        },
        
        'market_segments': segments_analysis.to_dict(),
        'premium_data': premium_df.to_dict('records'),
        'original_data': original_df.to_dict('records'),
        
        'key_insights': [
            f'Consolidated {len(converted_prices)} price points from both sources',
            f'Premium mean: {premium_df["premium"].mean():.4f} ({premium_df["premium_pct"].mean():.1f}%)',
            f'Market segmentation analysis included',
            'Interpolated series created for continuous modeling',
            'FX conversion applied to all MXN prices'
        ]
    }
    
    # Guardar archivos
    with open('outputs/complete_data_consolidation.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
        
    premium_df.to_csv('outputs/interpolated_premium_series.csv', index=False)
    
    print(f"\n✅ Consolidación completa guardada en outputs/")
    print(f"🎯 RESULTADO: {premium_df['premium'].mean():.4f} premium mean")
    print(f"📊 DATOS: {len(premium_df)} puntos vs {len(converted_prices)} originales")

if __name__ == "__main__":
    main()
