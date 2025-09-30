#!/usr/bin/env python3
"""
Modelo 2025 Enfocado - Steel Rebar México Premium
Solo datos 2025 + Todos los factores macro disponibles
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import SelectKBest, f_regression
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score, mean_absolute_error

class Focused2025Model:
    """Modelo enfocado exclusivamente en 2025 con factores macroeconómicos"""
    
    def __init__(self):
        # TODOS los precios México 2025 disponibles (consolidados)
        self.mexico_prices_2025 = {
            # Período estable Nov 2024 - Mar 2025
            '2025-01-15': {'price_mxn': 17300, 'price_usd': None, 'type': 'menudeo', 'source': 'reportacero_stable'},
            '2025-01-31': {'price_mxn': 17500, 'price_usd': None, 'type': 'menudeo', 'source': 'adn40_herrera'},
            '2025-01-31_b': {'price_mxn': 17284, 'price_usd': None, 'type': 'menudeo', 'source': 'adn40_homedepot'},
            '2025-03-15': {'price_mxn': 17300, 'price_usd': None, 'type': 'menudeo', 'source': 'reportacero_stable'},
            
            # Incremento abril
            '2025-04-01': {'price_mxn': 17500, 'price_usd': None, 'type': 'menudeo', 'source': 'reportacero_increment'},
            '2025-04-09': {'price_mxn': 18200, 'price_usd': 884, 'type': 'menudeo', 'source': 'reportacero'},
            
            # Junio
            '2025-06-25': {'price_mxn': 17500, 'price_usd': 919, 'type': 'menudeo', 'source': 'reportacero'},
            '2025-06-26': {'price_mxn': 17500, 'price_usd': 905, 'type': 'menudeo', 'source': 'reportacero'},
            
            # Agosto
            '2025-08-13': {'price_mxn': 17860, 'price_usd': 938, 'type': 'menudeo', 'source': 'reportacero'},
            
            # Septiembre (datos semanales)
            '2025-09-03': {'price_mxn': 17864, 'price_usd': 948, 'type': 'menudeo', 'source': 'reportacero'},
            '2025-09-10': {'price_mxn': 17484, 'price_usd': 928, 'type': 'menudeo', 'source': 'reportacero'},
            '2025-09-17': {'price_mxn': 17284, 'price_usd': 917, 'type': 'menudeo', 'source': 'reportacero'},
            
            # Mayoristas septiembre (para análisis spread)
            '2025-09-15': {'price_mxn': 15449, 'price_usd': None, 'type': 'mayorista', 'source': 'tucompa'},
            '2025-09-15_b': {'price_mxn': 15688, 'price_usd': None, 'type': 'mayorista', 'source': 'maxiacer'},
            '2025-09-26': {'price_mxn': 13900, 'price_usd': None, 'type': 'mayorista', 'source': 'steeloribis'}
        }
        
    def load_2025_data(self):
        """Cargar SOLO datos 2025 para mayor precisión"""
        print("🔍 Cargando datos 2025 únicamente...")
        
        datasets = {}
        start_2025 = '2025-01-01'
        
        # 1. Banxico 2025
        try:
            banxico_df = pd.read_csv('../../02_data_extractors/outputs/banxico_consolidated_data.csv')
            if 'fecha' in banxico_df.columns:
                banxico_df.rename(columns={'fecha': 'date'}, inplace=True)
            banxico_df['date'] = pd.to_datetime(banxico_df['date'])
            
            # FILTRAR SOLO 2025
            banxico_2025 = banxico_df[banxico_df['date'] >= start_2025].copy()
            banxico_2025 = banxico_2025.set_index('date').sort_index()
            
            datasets['banxico'] = banxico_2025
            print(f"✓ Banxico 2025: {len(banxico_2025)} días")
            print(f"  - Columnas: {list(banxico_2025.columns)}")
            print(f"  - Rango: {banxico_2025.index.min().date()} - {banxico_2025.index.max().date()}")
            
        except Exception as e:
            print(f"❌ Banxico: {e}")
            
        # 2. LME 2025 (solo M01, sin duplicados)
        try:
            lme_raw = pd.read_csv('../../02_data_extractors/outputs/lme_sr_long.csv')
            lme_raw['date'] = pd.to_datetime(lme_raw['date'])
            
            # FILTRAR 2025 + solo M01
            lme_2025 = lme_raw[
                (lme_raw['date'] >= start_2025) & 
                (lme_raw['contract'] == 'M01')
            ].copy()
            
            lme_2025 = lme_2025.set_index('date').sort_index()
            # Eliminar duplicados
            lme_2025 = lme_2025[~lme_2025.index.duplicated(keep='last')]
            
            datasets['lme'] = lme_2025
            print(f"✓ LME 2025 (M01 only): {len(lme_2025)} días, sin duplicados")
            
        except Exception as e:
            print(f"❌ LME: {e}")
            
        # 3. EPU México 2025
        try:
            epu_df = pd.read_csv('../../02_data_extractors/outputs/epu_mexico_data.csv')
            if 'Year' in epu_df.columns and 'Month' in epu_df.columns:
                epu_df['date'] = pd.to_datetime(epu_df[['Year', 'Month']].assign(day=1))
                
                # FILTRAR 2025
                epu_2025 = epu_df[epu_df['date'] >= start_2025].copy()
                epu_2025 = epu_2025.set_index('date').sort_index()
                
                datasets['epu'] = epu_2025
                print(f"✓ EPU México 2025: {len(epu_2025)} meses")
                
        except Exception as e:
            print(f"⚠️ EPU: {e}")
            
        return datasets
        
    def create_2025_drivers(self, datasets):
        """Crear dataset de drivers solo para 2025"""
        print("\n🔧 DATASET DRIVERS 2025 ÚNICAMENTE")
        print("="*60)
        
        # Rango 2025 únicamente
        date_range = pd.date_range('2025-01-01', '2025-09-30', freq='D')
        drivers_df = pd.DataFrame(index=date_range)
        drivers_df.index.name = 'date'
        
        print(f"📅 Período enfocado: {date_range[0].date()} - {date_range[-1].date()}")
        
        # === BANXICO VARIABLES ===
        if 'banxico' in datasets:
            banxico = datasets['banxico']
            
            # USD/MXN (SF43783)
            if 'SF43783' in banxico.columns:
                fx_series = banxico['SF43783'].reindex(drivers_df.index, method='ffill')
                drivers_df['usdmxn_rate'] = fx_series
                
                # Volatilidad FX (30d rolling)
                drivers_df['usdmxn_volatility'] = fx_series.rolling(30).std()
                
                # Momentum FX (5d change)
                drivers_df['usdmxn_momentum'] = fx_series.pct_change(5)
                
                print(f"  ✓ FX: {fx_series.dropna().count()} valores")
                
            # TIIE 28 días (SF43878 o similar)
            tiie_candidates = ['SF43878', 'SF43718']  # TIIE 28d, TIIE Fondeo
            for tiie_col in tiie_candidates:
                if tiie_col in banxico.columns:
                    tiie_series = banxico[tiie_col].reindex(drivers_df.index, method='ffill')
                    drivers_df['tiie_rate'] = tiie_series
                    print(f"  ✓ TIIE ({tiie_col}): {tiie_series.dropna().count()} valores")
                    break
                    
            # INPC (SP74665) para tasa real
            if 'SP74665' in banxico.columns:
                inpc_series = banxico['SP74665'].reindex(drivers_df.index, method='ffill')
                # Aproximar inflación YoY
                inpc_yoy = inpc_series.pct_change(252) * 100  # Anual aprox
                
                if 'tiie_rate' in drivers_df.columns:
                    drivers_df['real_interest_rate'] = drivers_df['tiie_rate'] - inpc_yoy
                    print(f"  ✓ Tasa Real calculada")
                    
        # === LME VARIABLES ===
        if 'lme' in datasets:
            lme_data = datasets['lme']
            if 'price_usd_ton' in lme_data.columns:
                lme_prices = lme_data['price_usd_ton'].reindex(drivers_df.index, method='ffill')
                drivers_df['lme_price'] = lme_prices
                
                # Volatilidad LME
                drivers_df['lme_volatility'] = lme_prices.rolling(30).std()
                
                # Momentum LME
                drivers_df['lme_momentum'] = lme_prices.pct_change(5)
                
                print(f"  ✓ LME: {lme_prices.dropna().count()} valores")
                
        # === EPU (MENSUAL) ===
        if 'epu' in datasets:
            epu_data = datasets['epu']
            # Buscar columna correcta de EPU
            epu_col = None
            for col in epu_data.columns:
                if 'uncertainty' in col.lower() or 'index' in col.lower():
                    epu_col = col
                    break
            
            if epu_col is None:
                epu_col = epu_data.columns[2]  # Tercera columna (Mexican Policy Uncertainty Index)
            
            try:
                epu_series = pd.to_numeric(epu_data[epu_col], errors='coerce')
                epu_series = epu_series.reindex(drivers_df.index, method='ffill')
                drivers_df['epu_mexico'] = epu_series
                
                # EPU normalizado (z-score) solo si hay datos válidos
                if epu_series.dropna().count() > 0:
                    epu_mean = epu_series.mean()
                    epu_std = epu_series.std()
                    drivers_df['epu_normalized'] = (epu_series - epu_mean) / epu_std
                    
                print(f"  ✓ EPU México ({epu_col}): {epu_series.dropna().count()} valores")
            except Exception as e:
                print(f"  ⚠️ Error procesando EPU: {e}")
                # Continuar sin EPU
            
        # === VARIABLES DERIVADAS ===
        
        # Market stress (combinando volatilidades)
        stress_components = []
        if 'usdmxn_volatility' in drivers_df.columns:
            fx_stress = (drivers_df['usdmxn_volatility'] - drivers_df['usdmxn_volatility'].mean()) / drivers_df['usdmxn_volatility'].std()
            stress_components.append(fx_stress.fillna(0))
            
        if 'lme_volatility' in drivers_df.columns:
            lme_stress = (drivers_df['lme_volatility'] - drivers_df['lme_volatility'].mean()) / drivers_df['lme_volatility'].std()
            stress_components.append(lme_stress.fillna(0))
            
        if 'epu_normalized' in drivers_df.columns:
            stress_components.append(drivers_df['epu_normalized'].fillna(0))
            
        if stress_components:
            drivers_df['market_stress'] = np.mean(stress_components, axis=0)
            print(f"  ✓ Market Stress calculado")
            
        # Ciclos estacionales (2025 específicos)
        days_in_2025 = (drivers_df.index - pd.Timestamp('2025-01-01')).days
        
        # Ciclo trimestral (Q1=construcción baja, Q2-Q3=alta)
        quarterly_cycle = np.sin(2 * np.pi * days_in_2025 / 91.25) * 0.05  # ~3 meses
        drivers_df['seasonal_construction'] = quarterly_cycle
        
        # Efectos de fin de mes (inventarios)
        drivers_df['month_end_effect'] = np.where(drivers_df.index.day >= 25, 0.02, 0)
        
        print(f"\n✅ Dataset 2025: {len(drivers_df)} días × {len(drivers_df.columns)} variables")
        print(f"Variables creadas: {list(drivers_df.columns)}")
        
        return drivers_df
        
    def create_premium_target_2025(self, drivers_df):
        """Crear serie premium objetivo para 2025 con interpolación inteligente"""
        print("\n🎯 SERIE PREMIUM OBJETIVO 2025")
        print("="*50)
        
        # Convertir precios México a USD y calcular premiums
        premium_points = []
        
        for date_str, data in self.mexico_prices_2025.items():
            clean_date = date_str.split('_')[0]  # Remover sufijos
            date_obj = pd.to_datetime(clean_date)
            
            # Obtener FX rate de esa fecha
            fx_rate = self._get_fx_from_drivers(drivers_df, date_obj)
            
            # Convertir a USD si es necesario
            if data.get('price_usd'):
                mexico_usd = data['price_usd']
            elif data.get('price_mxn') and fx_rate:
                mexico_usd = data['price_mxn'] / fx_rate
            else:
                continue
                
            # Obtener LME del mismo día
            lme_price = self._get_lme_from_drivers(drivers_df, date_obj)
            
            if lme_price and lme_price > 0:
                premium = mexico_usd / lme_price
                premium_points.append({
                    'date': date_obj,
                    'premium': premium,
                    'mexico_usd': mexico_usd,
                    'lme_usd': lme_price,
                    'fx_rate': fx_rate,
                    'type': data['type'],
                    'source': data['source']
                })
                
        premium_df = pd.DataFrame(premium_points).set_index('date').sort_index()
        print(f"✅ Puntos premium calculados: {len(premium_df)}")
        
        # Mostrar análisis detallado
        print("\n📊 PREMIUMS CALCULADOS 2025:")
        display_df = premium_df[['mexico_usd', 'lme_usd', 'premium', 'type', 'source']].copy()
        display_df['premium_pct'] = (display_df['premium'] - 1) * 100
        print(display_df.round(3))
        
        # Estadísticas por tipo
        type_stats = premium_df.groupby('type')['premium'].agg(['count', 'mean', 'std'])
        print(f"\n📋 ESTADÍSTICAS POR TIPO:")
        for tipo in type_stats.index:
            stats = type_stats.loc[tipo]
            print(f"  {tipo.upper()}: {int(stats['count'])} obs, {stats['mean']:.3f} ({(stats['mean']-1)*100:.1f}%)")
            
        # Crear serie interpolada (solo menudeo para consistencia)
        menudeo_premiums = premium_df[premium_df['type'] == 'menudeo']['premium'].copy()
        
        # Interpolación lineal entre puntos
        premium_full = pd.Series(index=drivers_df.index, dtype=float)
        for date, premium in menudeo_premiums.items():
            premium_full[date] = premium
            
        premium_interpolated = premium_full.interpolate(method='linear')
        
        # Ajustes por factores macro disponibles
        adjustments = pd.Series(0.0, index=drivers_df.index)
        
        if 'market_stress' in drivers_df.columns:
            stress_effect = drivers_df['market_stress'] * 0.03  # ±3% por stress
            adjustments += stress_effect.fillna(0)
            
        if 'seasonal_construction' in drivers_df.columns:
            seasonal_effect = drivers_df['seasonal_construction']
            adjustments += seasonal_effect.fillna(0)
            
        # Premium final ajustado
        premium_final = premium_interpolated * (1 + adjustments)
        
        # Suavizar
        premium_smoothed = premium_final.rolling(5, center=True).mean().fillna(premium_final)
        
        print(f"\n✅ Serie premium 2025: {premium_smoothed.notna().sum()} días válidos")
        print(f"   Media: {premium_smoothed.mean():.4f} ({(premium_smoothed.mean()-1)*100:.1f}%)")
        print(f"   Std: {premium_smoothed.std():.4f}")
        
        return premium_smoothed, premium_df
        
    def _get_fx_from_drivers(self, drivers_df, date_obj):
        """Obtener FX rate de drivers_df"""
        if 'usdmxn_rate' not in drivers_df.columns:
            return 18.5  # Default
            
        # Buscar fecha exacta o cercana
        for offset in range(-5, 6):
            check_date = date_obj + timedelta(days=offset)
            if check_date in drivers_df.index:
                fx_rate = drivers_df.loc[check_date, 'usdmxn_rate']
                if pd.notna(fx_rate) and fx_rate > 0:
                    return fx_rate
        return 18.5
        
    def _get_lme_from_drivers(self, drivers_df, date_obj):
        """Obtener LME price de drivers_df"""
        if 'lme_price' not in drivers_df.columns:
            return None
            
        # Buscar fecha exacta o cercana
        for offset in range(-5, 6):
            check_date = date_obj + timedelta(days=offset)
            if check_date in drivers_df.index:
                lme_price = drivers_df.loc[check_date, 'lme_price']
                if pd.notna(lme_price) and lme_price > 0:
                    return lme_price
        return None
        
    def train_sophisticated_model(self, drivers_df, premium_target):
        """Entrenar modelo con features macroeconómicos"""
        print("\n🤖 ENTRENANDO MODELO SOFISTICADO 2025")
        print("="*60)
        
        # Features (excluyendo LME price que es endógeno)
        feature_cols = [col for col in drivers_df.columns if col not in ['lme_price']]
        
        # Preparar datos
        X = drivers_df[feature_cols].copy()
        y = premium_target.copy()
        
        # Filtrar datos válidos
        valid_dates = y.dropna().index
        X_valid = X.loc[valid_dates].fillna(method='ffill').fillna(0)
        y_valid = y.loc[valid_dates]
        
        print(f"✅ Datos válidos: {len(X_valid)} días × {len(feature_cols)} features")
        
        if len(X_valid) < 20:
            print("⚠️ Pocos datos para ML, usando estadísticas descriptivas")
            return None, None, None, X_valid, y_valid
            
        # Normalización
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_valid)
        
        # Selección de features (top K)
        k_features = min(6, len(feature_cols))
        selector = SelectKBest(f_regression, k=k_features)
        X_selected = selector.fit_transform(X_scaled, y_valid)
        selected_features = np.array(feature_cols)[selector.get_support()]
        
        print(f"✅ Features seleccionados: {list(selected_features)}")
        
        # Division temporal
        train_size = max(10, int(0.7 * len(X_selected)))
        X_train = X_selected[:train_size]
        X_test = X_selected[train_size:]
        y_train = y_valid.iloc[:train_size]
        y_test = y_valid.iloc[train_size:]
        
        print(f"Train: {len(X_train)}, Test: {len(X_test)}")
        
        # Modelos
        models = {
            'Ridge': Ridge(alpha=0.1),
            'RandomForest': RandomForestRegressor(n_estimators=50, max_depth=5, random_state=42)
        }
        
        best_model = None
        best_score = -np.inf
        
        for name, model in models.items():
            try:
                model.fit(X_train, y_train)
                
                if len(X_test) > 0:
                    test_pred = model.predict(X_test)
                    test_score = r2_score(y_test, test_pred)
                else:
                    test_score = 0
                    
                train_pred = model.predict(X_train)
                train_score = r2_score(y_train, train_pred)
                
                print(f"  {name}: Train R² = {train_score:.3f}, Test R² = {test_score:.3f}")
                
                if test_score > best_score:
                    best_score = test_score
                    best_model = model
                    
            except Exception as e:
                print(f"  ❌ {name}: {e}")
                
        print(f"✅ Mejor modelo seleccionado: R² = {best_score:.3f}")
        
        return best_model, scaler, selector, X_valid, y_valid

def main():
    """Análisis completo enfocado 2025"""
    print("🚀 MODELO ENFOCADO 2025 - STEEL REBAR MÉXICO")
    print("="*80)
    print("🎯 Solo datos 2025 + Factores macro + Interpolación inteligente")
    
    model = Focused2025Model()
    
    # 1. Cargar datos 2025
    datasets = model.load_2025_data()
    
    if not datasets:
        print("❌ No se pudieron cargar datos mínimos")
        return
        
    # 2. Crear drivers 2025
    drivers_df = model.create_2025_drivers(datasets)
    
    # 3. Serie premium objetivo
    premium_target, premium_points = model.create_premium_target_2025(drivers_df)
    
    # 4. Entrenar modelo sofisticado
    trained_model, scaler, selector, X_valid, y_valid = model.train_sophisticated_model(
        drivers_df, premium_target)
    
    # 5. Estadísticas finales
    premium_stats = {
        'methodology': 'Focused 2025 analysis with macro factors',
        'data_period': '2025-01-01 to 2025-09-30',
        'premium_mean': float(premium_target.mean()),
        'premium_std': float(premium_target.std()),
        'premium_median': float(premium_target.median()),
        'real_data_points': len(premium_points),
        'interpolated_days': int(premium_target.notna().sum()),
        'model_trained': trained_model is not None,
        'data_sources': list(datasets.keys()),
        'confidence_level': 'Medium' if len(premium_points) >= 8 else 'Low'
    }
    
    print(f"\n🎯 RESULTADOS FINALES 2025:")
    print(f"  ✅ Premium medio: {premium_stats['premium_mean']:.4f} ({(premium_stats['premium_mean']-1)*100:.1f}%)")
    print(f"  ✅ Puntos reales: {premium_stats['real_data_points']}")
    print(f"  ✅ Serie interpolada: {premium_stats['interpolated_days']} días")
    print(f"  ✅ Confianza: {premium_stats['confidence_level']}")
    
    # 6. Guardar resultados
    with open('../outputs/focused_2025_analysis.json', 'w') as f:
        json.dump(premium_stats, f, indent=2, default=str)
        
    # Guardar serie premium
    premium_series_df = pd.DataFrame({
        'date': premium_target.index,
        'premium': premium_target.values
    }).dropna()
    premium_series_df.to_csv('../outputs/premium_series_2025.csv', index=False)
    
    # Guardar dataset completo de drivers
    drivers_df.to_csv('../outputs/macro_drivers_2025.csv')
    
    print(f"\n✅ Análisis 2025 completo guardado en outputs/")
    
    return premium_stats

if __name__ == "__main__":
    main()
