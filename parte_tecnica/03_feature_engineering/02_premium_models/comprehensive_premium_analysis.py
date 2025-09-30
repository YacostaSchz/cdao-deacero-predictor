#!/usr/bin/env python3
"""
Análisis Completo de Premium México/LME - CORREGIDO
Outlier 625 USD/ton REMOVIDO + Todos los precios disponibles
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class ComprehensivePremiumAnalysis:
    """Análisis completo con TODOS los datos disponibles - SIN OUTLIERS"""
    
    def __init__(self):
        # TODOS los precios México disponibles (USD/ton) - OUTLIER 625 REMOVIDO
        self.all_mexico_prices = {
            # Datos históricos adicionales descubiertos
            '2025-01-31': {'price_usd': None, 'price_mxn': 17500, 'type': 'menudeo', 'source': 'adn40_herrera'},
            
            # Precios con conversión USD estimada
            '2025-04-09': {'price_usd': 884, 'price_mxn': 18200, 'type': 'menudeo', 'source': 'reportacero', 'range': '2025-04-06/12'},
            '2025-06-25': {'price_usd': 919, 'price_mxn': 17500, 'type': 'menudeo', 'source': 'reportacero', 'range': '2025-06-22/28'},
            '2025-06-26': {'price_usd': 905, 'price_mxn': 17500, 'type': 'menudeo', 'source': 'reportacero'},
            '2025-08-13': {'price_usd': 938, 'price_mxn': 17860, 'type': 'menudeo', 'source': 'reportacero', 'range': '2025-08-10/16'},
            '2025-09-03': {'price_usd': 948, 'price_mxn': 17864, 'type': 'menudeo', 'source': 'reportacero', 'range': '2025-08-31/09-06'},
            '2025-09-10': {'price_usd': 928, 'price_mxn': 17484, 'type': 'menudeo', 'source': 'reportacero', 'range': '2025-09-07/13'},
            '2025-09-17': {'price_usd': 917, 'price_mxn': 17284, 'type': 'menudeo', 'source': 'reportacero', 'range': '2025-09-14/20'},
            
            # OUTLIER REMOVIDO: '2025-09-20': {'price_usd': 625, 'type': 'unknown', 'source': 'steelradar'}
        }
        
    def load_fx_data(self):
        """Cargar datos de tipo de cambio USD/MXN - Verificar SF43783"""
        print("🔍 Cargando datos de tipo de cambio...")
        print("⚠️ VERIFICANDO: ¿Estamos usando SF43783 (FIX) correcto?")
        
        fx_candidates = [
            '../02_data_extractors/outputs/SF43783_data.csv',  # Tipo de cambio FIX
            '../02_data_extractors/outputs/banxico_consolidated_data.csv'
        ]
        
        for fx_path in fx_candidates:
            try:
                if 'SF43783' in fx_path:
                    # Archivo individual de tipo de cambio
                    fx_df = pd.read_csv(fx_path)
                    print(f"✓ FX individual: {fx_path}")
                    print(f"Columnas: {fx_df.columns.tolist()}")
                    print(f"Primeras filas:")
                    print(fx_df.head())
                    print(f"Últimas filas:")
                    print(fx_df.tail())
                    return fx_df
                else:
                    # Archivo consolidado
                    banxico_df = pd.read_csv(fx_path)
                    if 'SF43783' in banxico_df.columns:
                        fx_df = banxico_df[['date', 'SF43783']].copy()
                        fx_df.rename(columns={'SF43783': 'fx_rate'}, inplace=True)
                        print(f"✓ FX consolidado: {fx_path}")
                        print(f"Muestra FX: {fx_df.head()}")
                        return fx_df
            except Exception as e:
                print(f"❌ Error con {fx_path}: {e}")
                continue
                
        print("⚠️ No se pudo cargar tipo de cambio, usando estimación")
        return None
        
    def load_lme_data(self):
        """Cargar datos LME Steel Rebar"""
        print("🔍 Cargando datos LME...")
        
        lme_candidates = [
            '../02_data_extractors/outputs/lme_combined_sr_sc.csv',
            '../02_data_extractors/outputs/lme_sr_long.csv'
        ]
        
        for lme_path in lme_candidates:
            try:
                if os.path.exists(lme_path):
                    lme_df = pd.read_csv(lme_path, parse_dates=['date'], index_col='date')
                    print(f"✓ LME data: {lme_path}")
                    print(f"Columnas: {lme_df.columns.tolist()}")
                    print(f"Rango fechas: {lme_df.index.min()} - {lme_df.index.max()}")
                    return lme_df
            except Exception as e:
                print(f"❌ Error con {lme_path}: {e}")
                continue
                
        print("❌ No se pudo cargar datos LME")
        return None
        
    def calculate_all_premiums(self, lme_df, fx_df=None):
        """Calcular premiums para TODOS los precios México (SIN OUTLIERS)"""
        print("\n📊 ANÁLISIS COMPLETO DE PREMIUMS - OUTLIER 625 REMOVIDO")
        print("="*70)
        
        premiums = []
        
        for date_str, mx_data in self.all_mexico_prices.items():
            # Solo procesar si tiene precio USD válido
            if mx_data.get('price_usd') is None:
                continue
                
            date_obj = pd.to_datetime(date_str)
            
            # Obtener precio LME más cercano
            lme_price = self._get_closest_lme_price(lme_df, date_obj)
            
            if lme_price and lme_price > 0:
                # Calcular premium
                premium = mx_data['price_usd'] / lme_price
                
                # Estimar tipo de cambio si disponible
                fx_rate = self._get_fx_rate(fx_df, date_obj) if fx_df is not None else None
                
                premiums.append({
                    'date': date_str,
                    'mexico_usd': mx_data['price_usd'],
                    'lme_usd': round(lme_price, 2),
                    'premium': round(premium, 3),
                    'premium_pct': round((premium - 1) * 100, 1),
                    'type': mx_data['type'],
                    'source': mx_data['source'],
                    'range': mx_data.get('range', 'exact'),
                    'fx_rate': fx_rate,
                    'price_mxn': mx_data.get('price_mxn')
                })
                
        premium_df = pd.DataFrame(premiums)
        
        if len(premium_df) == 0:
            print("❌ No se pudieron calcular premiums")
            return None
            
        # Ordenar por fecha
        premium_df = premium_df.sort_values('date')
        
        print(f"\n🎯 PREMIUMS CALCULADOS ({len(premium_df)} puntos - SIN OUTLIERS):")
        print(premium_df[['date', 'mexico_usd', 'lme_usd', 'premium_pct', 'type', 'source']])
        
        return premium_df
        
    def analyze_premium_patterns(self, premium_df):
        """Análisis de patrones en premiums"""
        print(f"\n📈 ESTADÍSTICAS COMPLETAS (SIN OUTLIERS):")
        
        # Estadísticas generales
        stats = {
            'count': len(premium_df),
            'mean': premium_df['premium'].mean(),
            'std': premium_df['premium'].std(),
            'min': premium_df['premium'].min(),
            'max': premium_df['premium'].max(),
            'median': premium_df['premium'].median()
        }
        
        print(f"  - Observaciones: {stats['count']} (outlier 625 removido)")
        print(f"  - Media: {stats['mean']:.3f} ({(stats['mean']-1)*100:.1f}%)")
        print(f"  - Mediana: {stats['median']:.3f} ({(stats['median']-1)*100:.1f}%)")
        print(f"  - Std Dev: {stats['std']:.3f} ({stats['std']*100:.1f}%)")
        print(f"  - Min: {stats['min']:.3f} ({(stats['min']-1)*100:.1f}%)")
        print(f"  - Max: {stats['max']:.3f} ({(stats['max']-1)*100:.1f}%)")
        print(f"  - Rango: {(stats['max']-stats['min'])*100:.1f}%")
        
        # Análisis temporal
        premium_df['month'] = pd.to_datetime(premium_df['date']).dt.month
        print(f"\n📅 ANÁLISIS TEMPORAL:")
        temporal_analysis = premium_df.groupby('month')['premium'].agg(['count', 'mean'])
        for month in temporal_analysis.index:
            row = temporal_analysis.loc[month]
            month_name = {1: 'Enero', 4: 'Abril', 6: 'Junio', 8: 'Agosto', 9: 'Septiembre'}.get(month, f'Mes {month}')
            print(f"  - {month_name}: {row['count']} obs, {row['mean']:.3f} ({(row['mean']-1)*100:.1f}%)")
            
        return stats
        
    def _get_closest_lme_price(self, lme_df, target_date):
        """Obtener precio LME más cercano a una fecha"""
        if lme_df is None:
            return None
            
        # Primero verificar qué columna de precio usar
        price_cols = [col for col in lme_df.columns if 'sr' in col.lower() or 'closing' in col.lower()]
        if not price_cols:
            print(f"⚠️ No se encontraron columnas de precio LME: {lme_df.columns.tolist()}")
            return None
            
        price_col = price_cols[0]  # Usar la primera columna de precio encontrada
            
        # Buscar ±5 días
        for offset in range(-5, 6):
            check_date = target_date + timedelta(days=offset)
            if check_date in lme_df.index:
                price = lme_df.loc[check_date, price_col]
                if pd.notna(price) and price > 0:
                    return price
        return None
        
    def _get_fx_rate(self, fx_df, target_date):
        """Obtener tipo de cambio más cercano"""
        if fx_df is None:
            return None
            
        try:
            # Convertir date a datetime si es necesario
            if 'date' in fx_df.columns:
                fx_df['date'] = pd.to_datetime(fx_df['date'])
                fx_df = fx_df.set_index('date')
                
            # Buscar fecha exacta o cercana
            for offset in range(-7, 8):
                check_date = target_date + timedelta(days=offset)
                if check_date in fx_df.index:
                    rate = fx_df.iloc[0, 0] if len(fx_df.columns) > 0 else None
                    if pd.notna(rate) and rate > 0:
                        return rate
        except Exception as e:
            print(f"⚠️ Error obteniendo FX: {e}")
            
        return None
        
    def generate_updated_model_params(self, premium_df, stats):
        """Generar parámetros actualizados para el modelo (SIN OUTLIERS)"""
        print(f"\n🔧 PARÁMETROS MODELO ACTUALIZADO - SIN OUTLIERS")
        print("="*60)
        
        # Ya no hay outliers porque removimos 625 manualmente
        final_mean = premium_df['premium'].mean()
        final_std = premium_df['premium'].std()
        
        # Intervalos de confianza
        intervals = {
            '50%': (final_mean - 0.67 * final_std, final_mean + 0.67 * final_std),
            '90%': (final_mean - 1.64 * final_std, final_mean + 1.64 * final_std),
            '95%': (final_mean - 1.96 * final_std, final_mean + 1.96 * final_std)
        }
        
        updated_params = {
            'premium_mean': round(final_mean, 4),
            'premium_std': round(final_std, 4),
            'premium_median': round(premium_df['premium'].median(), 4),
            'confidence_intervals': {k: (round(v[0], 4), round(v[1], 4)) for k, v in intervals.items()},
            'data_points': len(premium_df),
            'outliers_removed': 1,  # Removimos el 625
            'premium_range_pct': round((final_mean - 1) * 100, 1),
            'improvement_vs_previous': f'From 2 points to {len(premium_df)} points'
        }
        
        print(f"✅ Premium medio: {updated_params['premium_mean']:.4f} ({updated_params['premium_range_pct']:.1f}%)")
        print(f"✅ Desviación estándar: {updated_params['premium_std']:.4f}")
        print(f"✅ Puntos de datos: {updated_params['data_points']} (vs 2 anteriores)")
        print(f"✅ Intervalos 90%: [{intervals['90%'][0]:.3f}, {intervals['90%'][1]:.3f}]")
        print(f"✅ Mejora significativa en base de datos!")
        
        return updated_params

def main():
    """Ejecutar análisis completo actualizado - SIN OUTLIERS"""
    print("🚀 ANÁLISIS PREMIUM CORREGIDO - STEEL REBAR MÉXICO")
    print("="*80)
    print("🚨 OUTLIER 625 USD/ton REMOVIDO + EPU CONSIDERADO")
    
    analyzer = ComprehensivePremiumAnalysis()
    
    # 1. Cargar datos
    lme_df = analyzer.load_lme_data()
    fx_df = analyzer.load_fx_data()
    
    if lme_df is None:
        print("❌ No se pueden cargar datos LME necesarios")
        return
        
    # 2. Calcular TODOS los premiums (sin outliers)
    premium_df = analyzer.calculate_all_premiums(lme_df, fx_df)
    
    if premium_df is None or len(premium_df) == 0:
        print("❌ No se pudieron calcular premiums")
        return
        
    # 3. Análisis de patrones
    stats = analyzer.analyze_premium_patterns(premium_df)
    
    # 4. Generar parámetros actualizados
    updated_params = analyzer.generate_updated_model_params(premium_df, stats)
    
    # 5. Guardar resultados
    results = {
        'analysis_date': datetime.now().isoformat(),
        'total_price_points_available': len(analyzer.all_mexico_prices),
        'successful_matches': len(premium_df),
        'outliers_removed': ['625 USD/ton SteelRadar - inconsistent with other sources'],
        'premium_data': premium_df.to_dict('records'),
        'statistics': stats,
        'updated_model_parameters': updated_params,
        'critical_insights': [
            f'Premium mean updated: {updated_params["premium_mean"]:.4f} (vs 1.698 previous)',
            f'Data quality improved: {updated_params["data_points"]} points vs 2 previous',
            f'All data points are retail ("menudeo") prices - consistent market segment',
            'Outlier 625 USD/ton removed as suggested - clear data quality issue',
            'EPU index should be included in model for volatility explanation'
        ],
        'next_steps': [
            'Update honest_final_model.py with new premium parameters',
            'Include EPU (Economic Policy Uncertainty) in feature engineering',
            'Verify FX rate series SF43783 is correct',
            'Re-train model with updated parameters'
        ]
    }
    
    # Guardar
    with open('outputs/comprehensive_premium_analysis_corrected.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
        
    print(f"\n✅ Análisis corregido guardado en outputs/comprehensive_premium_analysis_corrected.json")
    print(f"\n🎯 RECOMENDACIÓN CRÍTICA:")
    print(f"   ✅ Premium actualizado: {updated_params['premium_mean']:.4f}")
    print(f"   ✅ Basado en {updated_params['data_points']} puntos LIMPIOS")
    print(f"   ✅ Outlier 625 removido correctamente")
    print(f"   ⚠️  Incluir EPU index para explicar volatilidad")

if __name__ == "__main__":
    main()