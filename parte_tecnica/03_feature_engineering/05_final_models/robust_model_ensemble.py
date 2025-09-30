#!/usr/bin/env python3
"""
ROBUST MODEL ENSEMBLE - CDO DeAcero
Modelo ensemble con sistema de fallbacks de 4 niveles

Implementa modelo robusto para predicción precio varilla t+1
Autor: Sistema Sr Data Scientist "CausalOps"
Fecha: 2025-09-28
"""

import pandas as pd
import numpy as np
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Union, Any
import json
import logging
import pickle
from pathlib import Path

# ML Libraries
from sklearn.ensemble import RandomForestRegressor, VotingRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge, ElasticNet
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error
# import xgboost as xgb  # Commented out due to OpenMP issues on macOS

# Configuración
warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RobustModelEnsemble:
    """Modelo ensemble robusto con sistema de fallbacks de 4 niveles"""
    
    def __init__(self, features_file: str = "outputs/features_dataset_latest.csv"):
        self.features_file = Path(features_file)
        self.MEXICO_PREMIUM = 1.157  # 15.7% spread calibrado
        self.FALLBACK_PRICE = 625.0  # Último precio conocido USD/ton
        
        # Configuración de tiers de features
        self.tier1_features = [
            'lme_sr_m01_lag1', 'usdmxn_lag1', 'mexico_premium', 
            'lme_volatility_5d', 'lme_momentum_5d'
        ]
        
        self.tier2_features = [
            'contango_indicator', 'rebar_scrap_spread_norm', 'trade_events_impact_7d',
            'weekday_effect', 'seasonality_simple'
        ]
        
        self.tier3_features = [
            'real_interest_rate', 'uncertainty_indicator', 'market_regime',
            'days_to_holiday', 'model_confidence'
        ]
        
        self.all_features = self.tier1_features + self.tier2_features + self.tier3_features
        
        # Modelos del ensemble
        self.models = {}
        self.ensemble_model = None
        self.fallback_models = {}
        
        logger.info("🛡️ RobustModelEnsemble inicializado")

    def load_features_dataset(self) -> Tuple[pd.DataFrame, pd.Series]:
        """Cargar dataset de features y target"""
        logger.info("📊 Cargando dataset de features...")
        
        if not self.features_file.exists():
            raise FileNotFoundError(f"Features dataset no encontrado: {self.features_file}")
        
        # Cargar dataset completo
        df = pd.read_csv(self.features_file, index_col=0, parse_dates=True)
        
        # Separar features y target
        features = df[self.all_features].copy()
        target = df['target_mexico_price'].copy()
        
        # Eliminar filas donde target es NaN (último día, etc.)
        valid_rows = target.notna()
        features = features[valid_rows]
        target = target[valid_rows]
        
        logger.info(f"✅ Dataset cargado:")
        logger.info(f"   - Registros válidos: {len(features)}")
        logger.info(f"   - Features: {len(features.columns)}")
        logger.info(f"   - Período: {features.index.min()} a {features.index.max()}")
        logger.info(f"   - Target range: {target.min():.2f} - {target.max():.2f} USD/ton")
        
        return features, target

    def create_temporal_split(self, features: pd.DataFrame, target: pd.Series) -> Dict:
        """Crear split temporal para entrenamiento y validación"""
        logger.info("📅 Creando split temporal...")
        
        # Split temporal estricto (sin data leakage)
        total_data = len(features)
        train_size = int(0.7 * total_data)  # 70% para entrenamiento
        val_size = int(0.2 * total_data)    # 20% para validación
        # 10% para test final
        
        train_end_idx = train_size
        val_end_idx = train_size + val_size
        
        splits = {
            'train': {
                'features': features.iloc[:train_end_idx],
                'target': target.iloc[:train_end_idx],
                'period': f"{features.index[0]} to {features.index[train_end_idx-1]}"
            },
            'validation': {
                'features': features.iloc[train_end_idx:val_end_idx],
                'target': target.iloc[train_end_idx:val_end_idx],
                'period': f"{features.index[train_end_idx]} to {features.index[val_end_idx-1]}"
            },
            'test': {
                'features': features.iloc[val_end_idx:],
                'target': target.iloc[val_end_idx:],
                'period': f"{features.index[val_end_idx]} to {features.index[-1]}"
            }
        }
        
        logger.info(f"✅ Split temporal creado:")
        for split_name, split_data in splits.items():
            logger.info(f"   - {split_name}: {len(split_data['features'])} registros ({split_data['period']})")
        
        return splits

    def create_baseline_model(self, features: pd.DataFrame, target: pd.Series) -> Any:
        """Crear modelo baseline: LME * 1.157 * ajustes"""
        logger.info("📊 Creando modelo baseline...")
        
        class BaselineModel:
            def __init__(self, mexico_premium=1.157):
                self.mexico_premium = mexico_premium
                self.name = "Baseline_LME_Premium"
                
            def fit(self, X, y):
                # Calcular ajuste promedio basado en FX y otros factores
                if 'lme_sr_m01_lag1' in X.columns and 'usdmxn_lag1' in X.columns:
                    base_prediction = X['lme_sr_m01_lag1'] * self.mexico_premium
                    actual_target = y
                    
                    # Calcular factor de ajuste promedio
                    adjustment_factor = (actual_target / base_prediction).median()
                    self.adjustment_factor = adjustment_factor
                    
                    logger.info(f"   Baseline fit: adjustment_factor = {adjustment_factor:.4f}")
                else:
                    self.adjustment_factor = 1.0
                
                return self
                
            def predict(self, X):
                if 'lme_sr_m01_lag1' in X.columns:
                    predictions = X['lme_sr_m01_lag1'] * self.mexico_premium * self.adjustment_factor
                    # Aplicar ajustes menores
                    if 'weekday_effect' in X.columns:
                        predictions *= (1 + X['weekday_effect'])
                    if 'seasonality_simple' in X.columns:
                        predictions *= (1 + X['seasonality_simple'])
                    return predictions
                else:
                    return pd.Series(self.FALLBACK_PRICE, index=X.index)
        
        baseline = BaselineModel(self.MEXICO_PREMIUM)
        return baseline

    def create_ml_models(self) -> Dict[str, Any]:
        """Crear modelos ML para el ensemble"""
        logger.info("🤖 Creando modelos ML...")
        
        models = {
            'gradient_boosting': GradientBoostingRegressor(
                n_estimators=100,
                max_depth=3,        # Evitar overfitting
                learning_rate=0.1,
                subsample=0.8,
                random_state=42,
                n_iter_no_change=10  # Early stopping
            ),
            
            'random_forest': RandomForestRegressor(
                n_estimators=100,
                max_depth=5,        # Simplificar
                min_samples_split=10,
                min_samples_leaf=5,
                random_state=42,
                n_jobs=-1
            ),
            
            'ridge': Ridge(
                alpha=1.0,          # Regularización moderada
                random_state=42
            ),
            
            'elastic_net': ElasticNet(
                alpha=0.1,
                l1_ratio=0.5,      # Balance L1/L2
                random_state=42,
                max_iter=1000
            )
        }
        
        logger.info(f"✅ {len(models)} modelos ML creados")
        return models

    def train_ensemble_model(self, splits: Dict) -> VotingRegressor:
        """Entrenar modelo ensemble con validación temporal"""
        logger.info("🚀 Entrenando modelo ensemble...")
        
        train_features = splits['train']['features']
        train_target = splits['train']['target']
        
        # 1. Crear baseline model
        baseline_model = self.create_baseline_model(train_features, train_target)
        baseline_model.fit(train_features, train_target)
        
        # 2. Crear ML models
        ml_models = self.create_ml_models()
        
        # 3. Entrenar cada modelo y evaluar
        model_scores = {}
        trained_models = {}
        
        for name, model in ml_models.items():
            try:
                # Time series cross validation
                tscv = TimeSeriesSplit(n_splits=3)
                scores = cross_val_score(
                    model, train_features, train_target, 
                    cv=tscv, scoring='neg_mean_absolute_percentage_error'
                )
                
                # Entrenar en todos los datos de train
                model.fit(train_features, train_target)
                
                model_scores[name] = -scores.mean()  # Convertir a MAPE positivo
                trained_models[name] = model
                
                logger.info(f"   {name}: MAPE = {model_scores[name]:.2%}")
                
            except Exception as e:
                logger.warning(f"⚠️ Error entrenando {name}: {e}")
                model_scores[name] = 1.0  # MAPE muy alto para exclusión
        
        # 4. Seleccionar mejores modelos para ensemble
        best_models = sorted(model_scores.items(), key=lambda x: x[1])[:3]  # Top 3
        
        # 5. Crear ensemble con pesos dinámicos
        ensemble_estimators = [
            ('baseline', baseline_model),
        ]
        
        # Agregar mejores ML models
        for model_name, score in best_models:
            if score < 0.15:  # Solo si MAPE < 15%
                ensemble_estimators.append((model_name, trained_models[model_name]))
        
        # Crear VotingRegressor
        if len(ensemble_estimators) > 1:
            ensemble = VotingRegressor(
                estimators=ensemble_estimators,
                weights=None  # Pesos uniformes por simplicidad
            )
            ensemble.fit(train_features, train_target)
        else:
            # Fallback a solo baseline si ML models fallan
            ensemble = baseline_model
        
        # Guardar modelos individuales para fallbacks
        self.models['baseline'] = baseline_model
        self.models.update(trained_models)
        self.ensemble_model = ensemble
        
        logger.info(f"✅ Ensemble entrenado con {len(ensemble_estimators)} modelos")
        
        return ensemble

    def create_fallback_system(self) -> Dict[str, Any]:
        """Crear sistema de fallbacks de 4 niveles"""
        logger.info("🛡️ Creando sistema de fallbacks...")
        
        class RobustPredictor:
            def __init__(self, ensemble_model, models, tier_features, mexico_premium, fallback_price):
                self.ensemble_model = ensemble_model
                self.models = models
                self.tier1_features = tier_features['tier1']
                self.tier2_features = tier_features['tier2'] 
                self.tier3_features = tier_features['tier3']
                self.mexico_premium = mexico_premium
                self.fallback_price = fallback_price
                
            def predict(self, X: pd.DataFrame, return_level: bool = False) -> Union[pd.Series, Tuple[pd.Series, str]]:
                """Predicción con fallbacks en cascada"""
                predictions = pd.Series(index=X.index, dtype=float)
                levels_used = pd.Series(index=X.index, dtype=str)
                
                for idx in X.index:
                    x_row = X.loc[[idx]]
                    prediction, level = self._predict_single_row(x_row)
                    predictions[idx] = prediction
                    levels_used[idx] = level
                
                if return_level:
                    return predictions, levels_used
                else:
                    return predictions
            
            def _predict_single_row(self, x_row: pd.DataFrame) -> Tuple[float, str]:
                """Predicción para una sola fila con fallbacks"""
                try:
                    # NIVEL 1: Modelo completo (15 features)
                    all_features_available = all(pd.notna(x_row[f].iloc[0]) for f in self.tier1_features + self.tier2_features)
                    
                    if all_features_available:
                        prediction = self.ensemble_model.predict(x_row)[0]
                        return prediction, "level_1_full_model"
                        
                except Exception:
                    pass
                
                try:
                    # NIVEL 2: Solo features críticos (Tier 1)
                    tier1_available = all(pd.notna(x_row[f].iloc[0]) for f in self.tier1_features)
                    
                    if tier1_available and 'baseline' in self.models:
                        prediction = self.models['baseline'].predict(x_row[self.tier1_features])[0]
                        return prediction, "level_2_critical_only"
                        
                except Exception:
                    pass
                
                try:
                    # NIVEL 3: LME + FX básico
                    lme_available = pd.notna(x_row['lme_sr_m01_lag1'].iloc[0])
                    fx_available = pd.notna(x_row['usdmxn_lag1'].iloc[0])
                    
                    if lme_available:
                        base_price = x_row['lme_sr_m01_lag1'].iloc[0] * self.mexico_premium
                        
                        # Ajuste por FX si disponible
                        if fx_available:
                            # Ajuste simple por cambio en FX reciente
                            fx_current = x_row['usdmxn_lag1'].iloc[0]
                            fx_adjustment = 1.0  # Simplificado para robustez
                            prediction = base_price * fx_adjustment
                        else:
                            prediction = base_price
                            
                        return prediction, "level_3_lme_fx_basic"
                        
                except Exception:
                    pass
                
                # NIVEL 4: Último precio conocido
                return self.fallback_price, "level_4_fallback"
        
        # Configuración de tiers para fallbacks
        tier_config = {
            'tier1': self.tier1_features,
            'tier2': self.tier2_features,
            'tier3': self.tier3_features
        }
        
        fallback_predictor = RobustPredictor(
            self.ensemble_model, 
            self.models, 
            tier_config,
            self.MEXICO_PREMIUM,
            self.FALLBACK_PRICE
        )
        
        self.fallback_models['robust_predictor'] = fallback_predictor
        
        logger.info("✅ Sistema de fallbacks creado")
        return self.fallback_models

    def validate_model_performance(self, splits: Dict) -> Dict:
        """Validar performance del modelo en train/validation/test"""
        logger.info("🔍 Validando performance del modelo...")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'model_performance': {},
            'fallback_analysis': {},
            'feature_importance': {}
        }
        
        # Evaluar en cada split
        for split_name, split_data in splits.items():
            X = split_data['features']
            y = split_data['target']
            
            if len(X) == 0:
                continue
                
            # Predicciones del ensemble
            try:
                predictions = self.ensemble_model.predict(X)
                mape = mean_absolute_percentage_error(y, predictions)
                rmse = np.sqrt(mean_squared_error(y, predictions))
                
                results['model_performance'][split_name] = {
                    'mape': mape,
                    'rmse': rmse,
                    'predictions_count': len(predictions),
                    'period': split_data['period']
                }
                
                logger.info(f"   {split_name}: MAPE = {mape:.2%}, RMSE = {rmse:.2f}")
                
            except Exception as e:
                logger.warning(f"⚠️ Error evaluando {split_name}: {e}")
                results['model_performance'][split_name] = {'error': str(e)}
        
        # Análisis de fallbacks en validation set
        if 'validation' in splits:
            X_val = splits['validation']['features']
            y_val = splits['validation']['target']
            
            if len(X_val) > 0:
                # Test del sistema de fallbacks
                robust_predictor = self.fallback_models['robust_predictor']
                predictions, levels = robust_predictor.predict(X_val, return_level=True)
                
                # Análisis por nivel de fallback
                fallback_analysis = {}
                for level in levels.unique():
                    level_mask = (levels == level)
                    if level_mask.sum() > 0:
                        level_predictions = predictions[level_mask]
                        level_actual = y_val[level_mask]
                        level_mape = mean_absolute_percentage_error(level_actual, level_predictions)
                        
                        fallback_analysis[level] = {
                            'usage_count': level_mask.sum(),
                            'usage_pct': level_mask.mean(),
                            'mape': level_mape
                        }
                
                results['fallback_analysis'] = fallback_analysis
                
                logger.info("📊 Análisis de fallbacks:")
                for level, stats in fallback_analysis.items():
                    logger.info(f"   {level}: {stats['usage_pct']:.1%} uso, MAPE = {stats['mape']:.2%}")
        
        # Feature importance (si disponible)
        try:
            if hasattr(self.ensemble_model, 'feature_importances_'):
                importances = self.ensemble_model.feature_importances_
            elif hasattr(self.ensemble_model, 'estimators_'):
                # Para VotingRegressor, promediar importancias
                importances_list = []
                for name, estimator in self.ensemble_model.named_estimators_.items():
                    if hasattr(estimator, 'feature_importances_'):
                        importances_list.append(estimator.feature_importances_)
                
                if importances_list:
                    importances = np.mean(importances_list, axis=0)
                else:
                    importances = None
            else:
                importances = None
            
            if importances is not None:
                feature_importance = dict(zip(self.all_features, importances))
                # Ordenar por importancia
                sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
                results['feature_importance'] = dict(sorted_features)
                
                logger.info("🔍 Top 5 features más importantes:")
                for feat, imp in sorted_features[:5]:
                    logger.info(f"   {feat}: {imp:.4f}")
                    
        except Exception as e:
            logger.warning(f"⚠️ Error calculando feature importance: {e}")
        
        return results

    def save_model_artifacts(self, model_results: Dict) -> Dict[str, str]:
        """Guardar modelo y resultados"""
        logger.info("💾 Guardando artefactos del modelo...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        saved_files = {}
        
        try:
            # 1. Guardar modelo ensemble
            model_file = f"outputs/ensemble_model_{timestamp}.pkl"
            with open(model_file, 'wb') as f:
                pickle.dump(self.ensemble_model, f)
            saved_files['ensemble_model'] = model_file
            
            # 2. Guardar sistema de fallbacks
            fallback_file = f"outputs/fallback_system_{timestamp}.pkl"
            with open(fallback_file, 'wb') as f:
                pickle.dump(self.fallback_models, f)
            saved_files['fallback_system'] = fallback_file
            
            # 3. Guardar resultados de validación
            results_file = f"outputs/model_validation_{timestamp}.json"
            with open(results_file, 'w') as f:
                json.dump(model_results, f, indent=2, default=str)
            saved_files['validation_results'] = results_file
            
            # 4. Crear versiones latest
            latest_model = "outputs/ensemble_model_latest.pkl"
            latest_fallback = "outputs/fallback_system_latest.pkl"
            latest_results = "outputs/model_validation_latest.json"
            
            with open(latest_model, 'wb') as f:
                pickle.dump(self.ensemble_model, f)
            with open(latest_fallback, 'wb') as f:
                pickle.dump(self.fallback_models, f)
            with open(latest_results, 'w') as f:
                json.dump(model_results, f, indent=2, default=str)
            
            saved_files.update({
                'latest_model': latest_model,
                'latest_fallback': latest_fallback,
                'latest_results': latest_results
            })
            
            logger.info("✅ Artefactos guardados exitosamente")
            
        except Exception as e:
            logger.error(f"❌ Error guardando artefactos: {e}")
            raise
        
        return saved_files

    def generate_model_summary(self, model_results: Dict, saved_files: Dict) -> str:
        """Generar resumen del modelo entrenado"""
        
        summary = []
        summary.append("# 🤖 RESUMEN DEL MODELO ENSEMBLE")
        summary.append(f"**Fecha**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary.append(f"**Estado**: Modelo entrenado y validado")
        summary.append("")
        
        # Performance summary
        summary.append("## 📊 Performance del Modelo")
        if 'model_performance' in model_results:
            for split_name, metrics in model_results['model_performance'].items():
                if 'mape' in metrics:
                    summary.append(f"- **{split_name.capitalize()}**: MAPE = {metrics['mape']:.2%}, RMSE = {metrics['rmse']:.2f}")
        
        # Fallback analysis
        summary.append("\n## 🛡️ Análisis de Fallbacks")
        if 'fallback_analysis' in model_results:
            for level, stats in model_results['fallback_analysis'].items():
                summary.append(f"- **{level}**: {stats['usage_pct']:.1%} uso, MAPE = {stats['mape']:.2%}")
        
        # Feature importance
        summary.append("\n## 🔍 Top Features")
        if 'feature_importance' in model_results:
            top_features = list(model_results['feature_importance'].items())[:8]
            for feat, imp in top_features:
                summary.append(f"- **{feat}**: {imp:.4f}")
        
        # Files created
        summary.append("\n## 📁 Archivos Generados")
        for file_type, file_path in saved_files.items():
            summary.append(f"- **{file_type}**: `{file_path}`")
        
        summary.append(f"\n---\n*Modelo generado por Robust Model Ensemble v1.0*")
        
        summary_text = "\n".join(summary)
        
        # Guardar resumen
        summary_file = f"outputs/model_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(summary_file, 'w') as f:
            f.write(summary_text)
        
        logger.info(f"📄 Resumen guardado: {summary_file}")
        
        return summary_text

def main():
    """Función principal para entrenar el modelo ensemble"""
    logger.info("🚀 Iniciando entrenamiento de modelo ensemble...")
    
    try:
        # 1. Inicializar ensemble
        ensemble = RobustModelEnsemble()
        
        # 2. Cargar datos de features
        features, target = ensemble.load_features_dataset()
        
        # 3. Crear splits temporales
        splits = ensemble.create_temporal_split(features, target)
        
        # 4. Entrenar modelo ensemble
        trained_model = ensemble.train_ensemble_model(splits)
        
        # 5. Crear sistema de fallbacks
        fallback_system = ensemble.create_fallback_system()
        
        # 6. Validar performance
        model_results = ensemble.validate_model_performance(splits)
        
        # 7. Guardar todo
        saved_files = ensemble.save_model_artifacts(model_results)
        
        # 8. Generar resumen
        summary = ensemble.generate_model_summary(model_results, saved_files)
        
        logger.info("✅ Entrenamiento completado exitosamente!")
        
        # Preview de resultados
        print("\n🎯 RESUMEN DEL MODELO:")
        print("="*60)
        if 'model_performance' in model_results:
            for split_name, metrics in model_results['model_performance'].items():
                if 'mape' in metrics:
                    print(f"{split_name.capitalize()}: MAPE = {metrics['mape']:.2%}")
        
        print(f"\nArchivos guardados:")
        for file_type, file_path in saved_files.items():
            if 'latest' in file_type:
                print(f"  {file_type}: {file_path}")
        
        return ensemble, model_results, saved_files
        
    except Exception as e:
        logger.error(f"❌ Error en entrenamiento: {e}")
        raise

if __name__ == "__main__":
    ensemble, results, files = main()
