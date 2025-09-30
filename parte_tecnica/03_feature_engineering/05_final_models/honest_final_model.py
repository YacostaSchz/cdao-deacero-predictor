#!/usr/bin/env python3
"""
Modelo Final Honesto: Transfer Function con Incertidumbre Cuantificada
Basado en análisis econométrico con solo 4 puntos reales
"""

import pandas as pd
import numpy as np
import joblib
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
import warnings
warnings.filterwarnings('ignore')

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_percentage_error, mean_absolute_error
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer

class HonestTransferFunction:
    """Transfer function honesta LME → México con incertidumbre explícita"""
    
    def __init__(self):
        # Parámetros del premium basados en análisis econométrico
        self.premium_mean = 1.698  # 69.8%
        self.premium_std = 0.034   # 3.4%
        
        # Intervalos de confianza pre-calculados
        self.premium_intervals = {
            '50%': (1.676, 1.721),
            '90%': (1.643, 1.755),
            '95%': (1.632, 1.765)
        }
        
        # FX rate - último valor conocido o promedio histórico
        self.fx_rate_default = 19.0  # MXN/USD aproximado
        
    def predict_mexico_price(
        self, 
        lme_price: float,
        fx_rate: Optional[float] = None,
        return_intervals: bool = True,
        confidence_level: str = '90%'
    ) -> Dict[str, Any]:
        """
        Predecir precio México con incertidumbre cuantificada
        
        Args:
            lme_price: Precio LME en USD/ton
            fx_rate: Tipo de cambio USD/MXN (opcional)
            return_intervals: Si devolver intervalos de confianza
            confidence_level: Nivel de confianza para intervalos
            
        Returns:
            Dict con predicción e información adicional
        """
        # Usar FX rate proporcionado o default
        fx = fx_rate if fx_rate is not None else self.fx_rate_default
        
        # Predicción central
        price_usd = lme_price * self.premium_mean
        price_mxn = price_usd * fx
        
        result = {
            'predicted_price_usd': round(price_usd, 2),
            'predicted_price_mxn': round(price_mxn, 2),
            'confidence_level': 'Low',  # Por limitación de datos
            'components': {
                'lme_price_usd': lme_price,
                'fx_rate_used': fx,
                'premium_applied': self.premium_mean,
                'premium_percentage': round((self.premium_mean - 1) * 100, 1)
            }
        }
        
        if return_intervals:
            # Calcular intervalos
            interval = self.premium_intervals.get(confidence_level, self.premium_intervals['90%'])
            
            lower_usd = lme_price * interval[0]
            upper_usd = lme_price * interval[1]
            
            result['prediction_intervals'] = {
                'usd': {
                    f'lower_{confidence_level}': round(lower_usd, 2),
                    f'upper_{confidence_level}': round(upper_usd, 2)
                },
                'mxn': {
                    f'lower_{confidence_level}': round(lower_usd * fx, 2),
                    f'upper_{confidence_level}': round(upper_usd * fx, 2)
                }
            }
            
        return result

class HonestFinalModel:
    """Modelo final con componentes LME + Transfer Function"""
    
    def __init__(self):
        self.lme_model = None
        self.transfer_function = HonestTransferFunction()
        self.feature_names = None
        self.imputer = None
        self.metadata = {
            'version': '1.0-honest',
            'created_date': datetime.now().isoformat(),
            'data_points_used': 4,
            'premium_based_on': 2,  # Solo 2 puntos pudieron emparejarse
            'confidence': 'Very Low'
        }
        
    def train_lme_model(self, X_train, y_train, feature_names):
        """Entrenar modelo para predecir LME"""
        print("🔧 Entrenando modelo LME...")
        
        self.feature_names = feature_names
        
        # Imputación de NaNs
        self.imputer = SimpleImputer(strategy='median')
        X_train_imputed = self.imputer.fit_transform(X_train)
        
        # Random Forest simple pero robusto
        self.lme_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=20,
            random_state=42,
            n_jobs=-1
        )
        
        self.lme_model.fit(X_train_imputed, y_train)
        
        # Calcular importancia de features
        feature_importance = pd.DataFrame({
            'feature': feature_names,
            'importance': self.lme_model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\n📊 Top 5 Features más importantes:")
        print(feature_importance.head())
        
        return self
        
    def predict(
        self, 
        X: np.ndarray,
        fx_rate: Optional[float] = None,
        return_details: bool = True
    ) -> Dict[str, Any]:
        """
        Predicción completa: LME → Transfer → México
        
        Args:
            X: Features para predicción (1 fila)
            fx_rate: Tipo de cambio (opcional)
            return_details: Si devolver detalles completos
            
        Returns:
            Dict con predicción y metadata
        """
        if self.lme_model is None:
            raise ValueError("Modelo no entrenado. Llamar train_lme_model primero.")
            
        # Predecir LME
        X_imputed = self.imputer.transform(X.reshape(1, -1))
        lme_prediction = self.lme_model.predict(X_imputed)[0]
        
        # Aplicar transfer function
        mexico_prediction = self.transfer_function.predict_mexico_price(
            lme_price=lme_prediction,
            fx_rate=fx_rate,
            return_intervals=True,
            confidence_level='90%'
        )
        
        # Agregar metadata
        result = {
            **mexico_prediction,
            'metadata': {
                **self.metadata,
                'lme_model_type': 'RandomForestRegressor',
                'transfer_function': 'Premium-based (69.8% ± 3.4%)',
                'warnings': [
                    'Based on only 4 historical Mexico price points',
                    'Premium calculated from only 2 LME-matched points',
                    'No real validation possible with current data',
                    'High uncertainty in predictions',
                    'FX rate may not reflect current market'
                ]
            }
        }
        
        if return_details:
            result['feature_values'] = {
                name: float(X[0, i]) for i, name in enumerate(self.feature_names)
                if not np.isnan(X[0, i])
            }
            
        return result
        
    def save(self, filepath: str):
        """Guardar modelo completo"""
        model_package = {
            'lme_model': self.lme_model,
            'transfer_function_params': {
                'premium_mean': self.transfer_function.premium_mean,
                'premium_std': self.transfer_function.premium_std,
                'premium_intervals': self.transfer_function.premium_intervals
            },
            'feature_names': self.feature_names,
            'imputer': self.imputer,
            'metadata': self.metadata
        }
        
        joblib.dump(model_package, filepath)
        print(f"✅ Modelo guardado en: {filepath}")
        
    @classmethod
    def load(cls, filepath: str):
        """Cargar modelo"""
        model_package = joblib.load(filepath)
        
        instance = cls()
        instance.lme_model = model_package['lme_model']
        instance.feature_names = model_package['feature_names']
        instance.imputer = model_package['imputer']
        instance.metadata = model_package['metadata']
        
        # Reconstruir transfer function
        tf_params = model_package['transfer_function_params']
        instance.transfer_function.premium_mean = tf_params['premium_mean']
        instance.transfer_function.premium_std = tf_params['premium_std']
        instance.transfer_function.premium_intervals = tf_params['premium_intervals']
        
        return instance

def create_api_response(prediction: Dict[str, Any]) -> Dict[str, Any]:
    """Formatear respuesta para API según especificaciones"""
    return {
        "predicted_price_usd_per_ton": prediction['predicted_price_usd'],
        "predicted_price_mxn_per_ton": prediction['predicted_price_mxn'],
        "confidence": prediction['confidence_level'],
        "prediction_intervals": prediction.get('prediction_intervals', {}),
        "components": prediction.get('components', {}),
        "metadata": prediction.get('metadata', {}),
        "timestamp": datetime.now().isoformat(),
        "api_version": "1.0"
    }

def main():
    """Demo de entrenamiento y predicción"""
    print("🚀 MODELO FINAL HONESTO - STEEL REBAR MÉXICO")
    print("="*60)
    
    # Cargar datos de features
    try:
        # Intentar cargar el dataset de features ya creado
        features_df = pd.read_csv('outputs/features_dataset_latest.csv', 
                                 index_col=0)  # Primera columna es el índice
        # Convertir índice a datetime
        features_df.index = pd.to_datetime(features_df.index)
        features_df.index.name = 'date'
        print(f"✓ Features cargados: {len(features_df)} días")
        
        # Separar features y target - usar target_mexico_price
        target_col = 'target_mexico_price'
        feature_cols = [col for col in features_df.columns 
                       if col not in [target_col, 'target', 'data_quality_score']]
        
        # Filtrar filas con target válido
        valid_mask = features_df[target_col].notna()
        features_df = features_df[valid_mask]
        
        X = features_df[feature_cols].values
        y = features_df[target_col].values
        
        print(f"✓ Datos con target válido: {len(features_df)} días")
        
        # Split temporal
        split_date = '2025-06-01'
        train_mask = features_df.index < split_date
        
        X_train = X[train_mask]
        y_train = y[train_mask]
        X_test = X[~train_mask]
        y_test = y[~train_mask]
        
        print(f"Train: {len(X_train)} samples")
        print(f"Test: {len(X_test)} samples")
        
        # Crear y entrenar modelo
        model = HonestFinalModel()
        model.train_lme_model(X_train, y_train, feature_cols)
        
        # Ejemplo de predicción
        print("\n🎯 EJEMPLO DE PREDICCIÓN")
        print("="*50)
        
        # Última fila disponible
        last_features = X_test[-1:]
        prediction = model.predict(last_features, fx_rate=19.0)
        
        # Formatear como respuesta API
        api_response = create_api_response(prediction)
        
        print("\n📡 Respuesta API:")
        print(json.dumps(api_response, indent=2))
        
        # Guardar modelo
        model.save('outputs/honest_final_model.pkl')
        
        # Guardar ejemplo de respuesta
        with open('outputs/api_response_example.json', 'w') as f:
            json.dump(api_response, f, indent=2)
            
        print("\n✅ Modelo y ejemplo guardados en outputs/")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        print("Asegúrate de haber ejecutado robust_feature_pipeline.py primero")

if __name__ == "__main__":
    main()
