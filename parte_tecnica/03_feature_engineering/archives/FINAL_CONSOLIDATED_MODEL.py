#!/usr/bin/env python3
"""
MODELO FINAL CONSOLIDADO - Steel Rebar México
Consolidando TODO el aprendizaje del proyecto con enfoque honesto
"""

import pandas as pd
import numpy as np
import joblib
import json
from datetime import datetime
from typing import Dict, Any, Optional
import warnings
warnings.filterwarnings('ignore')

from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer

class FinalConsolidatedModel:
    """Modelo final que consolida TODO el aprendizaje del proyecto"""
    
    def __init__(self):
        # Precios México 2025 VALIDADOS (solo menudeo para consistencia)
        self.validated_mexico_prices = {
            '2025-04-09': {'price_usd': 884, 'lme_approx': 565, 'premium': 1.565},  # 56.5%
            '2025-06-25': {'price_usd': 919, 'lme_approx': 541, 'premium': 1.699},  # 69.9%
            '2025-06-26': {'price_usd': 905, 'lme_approx': 541, 'premium': 1.674},  # 67.4%
            '2025-08-13': {'price_usd': 938, 'lme_approx': 542, 'premium': 1.731},  # 73.1%
            '2025-09-03': {'price_usd': 948, 'lme_approx': 540, 'premium': 1.756},  # 75.6%
            '2025-09-10': {'price_usd': 928, 'lme_approx': 540, 'premium': 1.719},  # 71.9%
            '2025-09-17': {'price_usd': 917, 'lme_approx': 540, 'premium': 1.698}   # 69.8%
        }
        
        # Estadísticas finales del premium (SOLO MENUDEO)
        premiums_only = [data['premium'] for data in self.validated_mexico_prices.values()]
        self.premium_stats = {
            'mean': np.mean(premiums_only),
            'std': np.std(premiums_only),
            'median': np.median(premiums_only),
            'min': np.min(premiums_only),
            'max': np.max(premiums_only),
            'count': len(premiums_only)
        }
        
        print(f"📊 PREMIUM FINAL VALIDADO:")
        print(f"  - Media: {self.premium_stats['mean']:.3f} ({(self.premium_stats['mean']-1)*100:.1f}%)")
        print(f"  - Rango: {self.premium_stats['min']:.3f} - {self.premium_stats['max']:.3f}")
        print(f"  - Datos: {self.premium_stats['count']} puntos menudeo validados")
        
    def load_features_dataset(self):
        """Cargar dataset de features ya creado"""
        try:
            # Usar el dataset ya creado en comprehensive analysis
            features_df = pd.read_csv('outputs/features_dataset_latest.csv', index_col=0)
            features_df.index = pd.to_datetime(features_df.index)
            
            # Filtrar solo 2025
            features_2025 = features_df[features_df.index >= '2025-01-01'].copy()
            
            print(f"✓ Features 2025: {len(features_2025)} días")
            return features_2025
            
        except Exception as e:
            print(f"❌ Error cargando features: {e}")
            return None
            
    def create_honest_target(self, features_df):
        """Crear target honesto usando LME directo (no sintético)"""
        print("\n🎯 CREANDO TARGET HONESTO")
        print("="*50)
        
        # Target = LME price (predecimos LME, no México sintético)
        if 'lme_sr_m01_lag1' in features_df.columns:
            # Target es LME t+1 (el precio actual, no lag)
            lme_target = features_df['lme_sr_m01_lag1'].shift(-1)  # t+1
            print(f"✅ Target: LME price t+1")
        else:
            print("❌ No se encontró columna LME")
            return None
            
        return lme_target
        
    def train_final_lme_model(self, features_df, target):
        """Entrenar modelo final para predecir LME"""
        print("\n🤖 ENTRENANDO MODELO LME FINAL")
        print("="*50)
        
        # Features core más importantes
        core_features = [
            'lme_sr_m01_lag1',      # Precio anterior (AR)
            'lme_volatility_5d',    # Volatilidad
            'lme_momentum_5d',      # Momentum
            'usdmxn_lag1',          # FX
            'real_interest_rate',   # Tasa real
            'uncertainty_indicator', # EPU proxy
            'rebar_scrap_spread_norm' # Steel fundamentals
        ]
        
        # Filtrar features disponibles
        available_features = [f for f in core_features if f in features_df.columns]
        print(f"Features disponibles: {available_features}")
        
        # Preparar datos
        X = features_df[available_features].copy()
        y = target.copy()
        
        # Filtrar datos válidos
        valid_mask = y.notna() & X.notna().all(axis=1)
        X_valid = X[valid_mask]
        y_valid = y[valid_mask]
        
        print(f"✅ Datos válidos: {len(X_valid)} observaciones")
        
        if len(X_valid) < 10:
            print("❌ Insuficientes datos para entrenamiento")
            return None, None
            
        # División temporal
        train_size = int(0.8 * len(X_valid))
        X_train = X_valid.iloc[:train_size]
        y_train = y_valid.iloc[:train_size]
        X_test = X_valid.iloc[train_size:]
        y_test = y_valid.iloc[train_size:]
        
        print(f"Train: {len(X_train)}, Test: {len(X_test)}")
        
        # Modelo simple y robusto
        imputer = SimpleImputer(strategy='median')
        X_train_imputed = imputer.fit_transform(X_train)
        X_test_imputed = imputer.transform(X_test)
        
        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=8,
            min_samples_split=10,
            random_state=42
        )
        
        model.fit(X_train_imputed, y_train)
        
        # Evaluación
        train_pred = model.predict(X_train_imputed)
        test_pred = model.predict(X_test_imputed)
        
        train_mape = np.mean(np.abs((y_train - train_pred) / y_train)) * 100
        test_mape = np.mean(np.abs((y_test - test_pred) / y_test)) * 100 if len(y_test) > 0 else 0
        
        print(f"✅ Train MAPE: {train_mape:.2f}%")
        print(f"✅ Test MAPE: {test_mape:.2f}%")
        
        # Feature importance
        importance_df = pd.DataFrame({
            'feature': available_features,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print(f"\n📊 Feature Importance:")
        print(importance_df)
        
        return model, imputer
        
    def create_transfer_function(self):
        """Transfer function final honesta"""
        print(f"\n💱 TRANSFER FUNCTION FINAL")
        print("="*50)
        
        # Usar estadísticas premium menudeo validadas
        mean_premium = self.premium_stats['mean']
        std_premium = self.premium_stats['std']
        
        # Intervalos de confianza
        intervals = {
            '90%': (mean_premium - 1.64 * std_premium, mean_premium + 1.64 * std_premium),
            '95%': (mean_premium - 1.96 * std_premium, mean_premium + 1.96 * std_premium)
        }
        
        transfer_params = {
            'premium_mean': round(mean_premium, 4),
            'premium_std': round(std_premium, 4),
            'intervals': {k: [round(v[0], 4), round(v[1], 4)] for k, v in intervals.items()},
            'fx_rate_default': 19.0,  # MXN/USD actual
            'data_points': self.premium_stats['count'],
            'market_segment': 'menudeo',
            'confidence': 'Medium'
        }
        
        print(f"✅ Premium medio: {transfer_params['premium_mean']:.3f}")
        print(f"✅ Intervalo 90%: {transfer_params['intervals']['90%']}")
        print(f"✅ Basado en: {transfer_params['data_points']} puntos validados")
        
        return transfer_params
        
    def predict_mexico_price(self, lme_model, imputer, transfer_params, X_features, fx_rate=None):
        """Predicción final completa"""
        
        # 1. Predecir LME
        X_imputed = imputer.transform(X_features.reshape(1, -1))
        lme_prediction = lme_model.predict(X_imputed)[0]
        
        # 2. Aplicar transfer function
        fx = fx_rate if fx_rate else transfer_params['fx_rate_default']
        premium = transfer_params['premium_mean']
        premium_std = transfer_params['premium_std']
        
        # Precio central
        mexico_usd = lme_prediction * premium
        mexico_mxn = mexico_usd * fx
        
        # Intervalos
        interval_90 = transfer_params['intervals']['90%']
        mexico_usd_lower = lme_prediction * interval_90[0]
        mexico_usd_upper = lme_prediction * interval_90[1]
        
        return {
            'predicted_price_usd_per_ton': round(mexico_usd, 2),
            'predicted_price_mxn_per_ton': round(mexico_mxn, 2),
            'confidence': transfer_params['confidence'],
            'prediction_intervals': {
                'usd_90%': [round(mexico_usd_lower, 2), round(mexico_usd_upper, 2)],
                'mxn_90%': [round(mexico_usd_lower * fx, 2), round(mexico_usd_upper * fx, 2)]
            },
            'components': {
                'lme_forecast_usd': round(lme_prediction, 2),
                'premium_applied': premium,
                'fx_rate_used': fx
            },
            'metadata': {
                'model_version': 'final-consolidated',
                'data_points_used': transfer_params['data_points'],
                'market_segment': transfer_params['market_segment'],
                'timestamp': datetime.now().isoformat()
            }
        }

def main():
    """Crear modelo final consolidado"""
    print("🚀 MODELO FINAL CONSOLIDADO - STEEL REBAR MÉXICO")
    print("="*80)
    print("🎯 Consolidando TODO el aprendizaje del proyecto")
    
    model = FinalConsolidatedModel()
    
    # 1. Cargar features
    features_df = model.load_features_dataset()
    if features_df is None:
        print("❌ No se pudieron cargar features")
        return
        
    # 2. Crear target honesto
    target = model.create_honest_target(features_df)
    if target is None:
        print("❌ No se pudo crear target")
        return
        
    # 3. Entrenar modelo LME
    lme_model, imputer = model.train_final_lme_model(features_df, target)
    if lme_model is None:
        print("❌ No se pudo entrenar modelo")
        return
        
    # 4. Transfer function
    transfer_params = model.create_transfer_function()
    
    # 5. Ejemplo de predicción
    print(f"\n📡 EJEMPLO PREDICCIÓN API:")
    print("="*50)
    
    # Última fila de features
    available_features = [f for f in [
        'lme_sr_m01_lag1', 'lme_volatility_5d', 'lme_momentum_5d',
        'usdmxn_lag1', 'real_interest_rate', 'uncertainty_indicator',
        'rebar_scrap_spread_norm'
    ] if f in features_df.columns]
    
    last_features = features_df[available_features].iloc[-1:].values
    
    prediction = model.predict_mexico_price(
        lme_model, imputer, transfer_params, 
        last_features, fx_rate=19.0
    )
    
    print(json.dumps(prediction, indent=2))
    
    # 6. Guardar modelo final
    final_package = {
        'lme_model': lme_model,
        'imputer': imputer,
        'transfer_params': transfer_params,
        'feature_names': available_features,
        'premium_stats': model.premium_stats,
        'model_metadata': {
            'version': 'final-consolidated',
            'created': datetime.now().isoformat(),
            'methodology': 'LME prediction + validated premium transfer',
            'data_quality': 'Medium - 7 validated points',
            'confidence': transfer_params['confidence']
        }
    }
    
    joblib.dump(final_package, 'outputs/FINAL_CONSOLIDATED_MODEL.pkl')
    
    with open('outputs/final_prediction_example.json', 'w') as f:
        json.dump(prediction, f, indent=2)
        
    print(f"\n✅ MODELO FINAL CONSOLIDADO GUARDADO")
    print(f"📦 Archivo: outputs/FINAL_CONSOLIDATED_MODEL.pkl")
    print(f"📡 Ejemplo: outputs/final_prediction_example.json")
    
    return final_package

if __name__ == "__main__":
    main()
