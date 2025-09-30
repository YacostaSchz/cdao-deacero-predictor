#!/usr/bin/env python3
"""
VALIDACIÓN DE OVERFITTING - MODELO LME
Análisis riguroso para detectar sobreajuste en el modelo de dos etapas
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge, LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.metrics import mean_absolute_percentage_error, r2_score
import matplotlib.pyplot as plt
import joblib
import warnings
warnings.filterwarnings('ignore')

class OverfittingValidator:
    """Validador de overfitting para modelo LME"""
    
    def __init__(self):
        self.results = {}
        
    def load_data(self):
        """Cargar datos para validación"""
        
        print("📊 CARGANDO DATOS PARA VALIDACIÓN OVERFITTING")
        print("="*70)
        
        # Cargar features dataset
        features_path = "outputs/features_dataset_latest.csv"
        df = pd.read_csv(features_path, index_col=0, parse_dates=True)
        df.index.name = 'date'
        
        # Filtrar 2025
        df_2025 = df[df.index >= '2025-01-01'].copy()
        print(f"✓ Datos 2025: {len(df_2025)} observaciones")
        
        # Agregar precio LME base si no existe
        if 'lme_sr_m01' not in df_2025.columns:
            # Crear serie sintética más realista
            np.random.seed(42)  # Para reproducibilidad
            trend = np.linspace(540, 550, len(df_2025))
            seasonal = 10 * np.sin(np.arange(len(df_2025)) * 2 * np.pi / 30)
            noise = 5 * np.random.randn(len(df_2025))
            df_2025['lme_sr_m01'] = trend + seasonal + noise
        
        return df_2025
    
    def prepare_lme_features(self, df):
        """Preparar features LME"""
        
        # Features LME
        lme_features = [
            'lme_sr_m01_lag1',
            'lme_volatility_5d',
            'lme_momentum_5d',
            'rebar_scrap_spread_norm',
        ]
        
        # Crear lags si no existen
        if 'lme_sr_m01_lag1' not in df.columns:
            df['lme_sr_m01_lag1'] = df['lme_sr_m01'].shift(1)
        
        # Crear volatilidad si no existe
        if 'lme_volatility_5d' not in df.columns:
            df['lme_volatility_5d'] = df['lme_sr_m01'].rolling(5).std()
        
        # Crear momentum si no existe
        if 'lme_momentum_5d' not in df.columns:
            df['lme_momentum_5d'] = df['lme_sr_m01'].pct_change(5)
        
        # Usar spread existente o crear uno sintético
        if 'rebar_scrap_spread_norm' not in df.columns:
            df['rebar_scrap_spread_norm'] = 0.25 + 0.1 * np.random.randn(len(df))
        
        # Filtrar features disponibles
        available_lme = [f for f in lme_features if f in df.columns]
        print(f"✓ Features LME: {available_lme}")
        
        # Target: LME t+1
        df['lme_target'] = df['lme_sr_m01'].shift(-1)
        
        return df[available_lme], df['lme_target']
    
    def test_simple_baseline(self, X, y):
        """Test 1: Comparar contra baseline simple"""
        
        print("\n🔍 TEST 1: BASELINE COMPARISON")
        print("="*50)
        
        # Preparar datos
        valid_mask = y.notna()
        X_valid = X[valid_mask]
        y_valid = y[valid_mask]
        
        # Split temporal
        split_date = '2025-08-01'
        X_train = X_valid[X_valid.index < split_date]
        X_test = X_valid[X_valid.index >= split_date]
        y_train = y_valid[y_valid.index < split_date]
        y_test = y_valid[y_valid.index >= split_date]
        
        # Modelos a comparar
        models = {
            'naive': None,  # Precio anterior
            'linear': LinearRegression(),
            'ridge': Ridge(alpha=1.0),
            'rf_simple': RandomForestRegressor(n_estimators=10, max_depth=3, random_state=42),
            'rf_complex': RandomForestRegressor(n_estimators=100, max_depth=5, random_state=42),
            'rf_overfit': RandomForestRegressor(n_estimators=200, max_depth=None, random_state=42)
        }
        
        results = {}
        
        for name, model in models.items():
            if name == 'naive':
                # Baseline: usar precio anterior
                y_pred_train = X_train['lme_sr_m01_lag1']
                y_pred_test = X_test['lme_sr_m01_lag1']
                
                # Alinear índices
                y_train_aligned = y_train.reindex(y_pred_train.index).dropna()
                y_pred_train_aligned = y_pred_train.reindex(y_train_aligned.index)
                
                y_test_aligned = y_test.reindex(y_pred_test.index).dropna()
                y_pred_test_aligned = y_pred_test.reindex(y_test_aligned.index)
                
                mape_train = np.mean(np.abs((y_train_aligned - y_pred_train_aligned) / y_train_aligned)) * 100
                mape_test = np.mean(np.abs((y_test_aligned - y_pred_test_aligned) / y_test_aligned)) * 100
                
            else:
                # Imputar y escalar
                imputer = SimpleImputer(strategy='mean')
                scaler = StandardScaler()
                
                X_train_imp = imputer.fit_transform(X_train)
                X_test_imp = imputer.transform(X_test)
                
                X_train_scaled = scaler.fit_transform(X_train_imp)
                X_test_scaled = scaler.transform(X_test_imp)
                
                # Entrenar
                model.fit(X_train_scaled, y_train)
                
                # Predecir
                y_pred_train = model.predict(X_train_scaled)
                y_pred_test = model.predict(X_test_scaled)
                
                mape_train = np.mean(np.abs((y_train - y_pred_train) / y_train)) * 100
                mape_test = np.mean(np.abs((y_test - y_pred_test) / y_test)) * 100
            
            # Calcular gap de overfitting
            overfitting_gap = mape_test - mape_train
            
            results[name] = {
                'mape_train': mape_train,
                'mape_test': mape_test,
                'overfitting_gap': overfitting_gap,
                'is_overfitting': overfitting_gap > 2.0  # Threshold 2%
            }
            
            print(f"{name:12} | Train: {mape_train:5.2f}% | Test: {mape_test:5.2f}% | Gap: {overfitting_gap:+5.2f}% | Overfit: {'⚠️' if overfitting_gap > 2.0 else '✅'}")
        
        self.results['baseline_comparison'] = results
        return results
    
    def test_cross_validation(self, X, y):
        """Test 2: Cross-validation temporal"""
        
        print("\n🔍 TEST 2: CROSS-VALIDATION TEMPORAL")
        print("="*50)
        
        # Preparar datos
        valid_mask = y.notna()
        X_valid = X[valid_mask]
        y_valid = y[valid_mask]
        
        if len(X_valid) < 100:
            print("⚠️ Datos insuficientes para CV")
            return {}
        
        # Time Series Cross-Validation
        tscv = TimeSeriesSplit(n_splits=5)
        
        models = {
            'linear': LinearRegression(),
            'ridge': Ridge(alpha=1.0),
            'rf_current': RandomForestRegressor(n_estimators=100, max_depth=5, random_state=42),
        }
        
        results = {}
        
        for name, model in models.items():
            print(f"\n📊 Evaluando {name}:")
            
            # Preparar pipeline
            imputer = SimpleImputer(strategy='mean')
            scaler = StandardScaler()
            
            cv_scores = []
            train_scores = []
            
            for fold, (train_idx, test_idx) in enumerate(tscv.split(X_valid)):
                X_train_fold = X_valid.iloc[train_idx]
                X_test_fold = X_valid.iloc[test_idx]
                y_train_fold = y_valid.iloc[train_idx]
                y_test_fold = y_valid.iloc[test_idx]
                
                # Procesar
                X_train_imp = imputer.fit_transform(X_train_fold)
                X_test_imp = imputer.transform(X_test_fold)
                
                X_train_scaled = scaler.fit_transform(X_train_imp)
                X_test_scaled = scaler.transform(X_test_imp)
                
                # Entrenar y evaluar
                model.fit(X_train_scaled, y_train_fold)
                
                y_pred_train = model.predict(X_train_scaled)
                y_pred_test = model.predict(X_test_scaled)
                
                mape_train = np.mean(np.abs((y_train_fold - y_pred_train) / y_train_fold)) * 100
                mape_test = np.mean(np.abs((y_test_fold - y_pred_test) / y_test_fold)) * 100
                
                train_scores.append(mape_train)
                cv_scores.append(mape_test)
                
                print(f"  Fold {fold+1}: Train {mape_train:.2f}% | Test {mape_test:.2f}%")
            
            mean_train = np.mean(train_scores)
            mean_cv = np.mean(cv_scores)
            std_cv = np.std(cv_scores)
            gap = mean_cv - mean_train
            
            results[name] = {
                'mean_train': mean_train,
                'mean_cv': mean_cv,
                'std_cv': std_cv,
                'overfitting_gap': gap,
                'is_stable': std_cv < 1.0,  # Baja variabilidad
                'is_overfitting': gap > 2.0
            }
            
            print(f"  📊 Promedio: Train {mean_train:.2f}% | CV {mean_cv:.2f}% ± {std_cv:.2f}% | Gap {gap:+.2f}%")
            print(f"  ✅ Estable: {'Sí' if std_cv < 1.0 else 'No'} | Overfitting: {'⚠️ Sí' if gap > 2.0 else '✅ No'}")
        
        self.results['cross_validation'] = results
        return results
    
    def test_learning_curves(self, X, y):
        """Test 3: Curvas de aprendizaje"""
        
        print("\n🔍 TEST 3: CURVAS DE APRENDIZAJE")
        print("="*50)
        
        # Preparar datos
        valid_mask = y.notna()
        X_valid = X[valid_mask]
        y_valid = y[valid_mask]
        
        # Split temporal
        split_date = '2025-08-01'
        X_train = X_valid[X_valid.index < split_date]
        X_test = X_valid[X_valid.index >= split_date]
        y_train = y_valid[y_valid.index < split_date]
        y_test = y_valid[y_valid.index >= split_date]
        
        # Preparar datos
        imputer = SimpleImputer(strategy='mean')
        scaler = StandardScaler()
        
        X_train_imp = imputer.fit_transform(X_train)
        X_test_imp = imputer.transform(X_test)
        
        X_train_scaled = scaler.fit_transform(X_train_imp)
        X_test_scaled = scaler.transform(X_test_imp)
        
        # Diferentes tamaños de muestra
        train_sizes = np.linspace(0.3, 1.0, 8)
        
        model = RandomForestRegressor(n_estimators=100, max_depth=5, random_state=42)
        
        train_scores = []
        test_scores = []
        sample_sizes = []
        
        for size in train_sizes:
            n_samples = int(len(X_train_scaled) * size)
            if n_samples < 20:
                continue
                
            # Muestra temporal (últimos n_samples)
            X_train_sample = X_train_scaled[-n_samples:]
            y_train_sample = y_train.iloc[-n_samples:]
            
            # Entrenar
            model.fit(X_train_sample, y_train_sample)
            
            # Evaluar
            y_pred_train = model.predict(X_train_sample)
            y_pred_test = model.predict(X_test_scaled)
            
            mape_train = np.mean(np.abs((y_train_sample - y_pred_train) / y_train_sample)) * 100
            mape_test = np.mean(np.abs((y_test - y_pred_test) / y_test)) * 100
            
            train_scores.append(mape_train)
            test_scores.append(mape_test)
            sample_sizes.append(n_samples)
            
            print(f"  Samples: {n_samples:3d} | Train: {mape_train:5.2f}% | Test: {mape_test:5.2f}% | Gap: {mape_test-mape_train:+5.2f}%")
        
        # Análisis de convergencia
        final_gap = test_scores[-1] - train_scores[-1] if test_scores else 0
        gap_trend = np.polyfit(sample_sizes, np.array(test_scores) - np.array(train_scores), 1)[0] if len(sample_sizes) > 2 else 0
        
        results = {
            'train_scores': train_scores,
            'test_scores': test_scores,
            'sample_sizes': sample_sizes,
            'final_gap': final_gap,
            'gap_trend': gap_trend,
            'is_converging': gap_trend < 0,  # Gap decreasing
            'is_overfitting': final_gap > 2.0
        }
        
        print(f"\n📊 ANÁLISIS:")
        print(f"  Gap final: {final_gap:+.2f}%")
        print(f"  Tendencia gap: {gap_trend:+.4f}% por muestra")
        print(f"  ✅ Convergiendo: {'Sí' if gap_trend < 0 else 'No'}")
        print(f"  ✅ Overfitting: {'⚠️ Sí' if final_gap > 2.0 else '✅ No'}")
        
        self.results['learning_curves'] = results
        return results
    
    def test_feature_importance_stability(self, X, y):
        """Test 4: Estabilidad de feature importance"""
        
        print("\n🔍 TEST 4: ESTABILIDAD FEATURE IMPORTANCE")
        print("="*50)
        
        # Preparar datos
        valid_mask = y.notna()
        X_valid = X[valid_mask]
        y_valid = y[valid_mask]
        
        # Multiple bootstrap samples
        n_bootstrap = 10
        feature_importances = []
        
        for i in range(n_bootstrap):
            # Bootstrap sample
            n_samples = len(X_valid)
            bootstrap_idx = np.random.choice(n_samples, n_samples, replace=True)
            
            X_boot = X_valid.iloc[bootstrap_idx]
            y_boot = y_valid.iloc[bootstrap_idx]
            
            # Preparar
            imputer = SimpleImputer(strategy='mean')
            scaler = StandardScaler()
            
            X_boot_imp = imputer.fit_transform(X_boot)
            X_boot_scaled = scaler.fit_transform(X_boot_imp)
            
            # Entrenar
            model = RandomForestRegressor(n_estimators=100, max_depth=5, random_state=i)
            model.fit(X_boot_scaled, y_boot)
            
            feature_importances.append(model.feature_importances_)
            
            print(f"  Bootstrap {i+1}: {dict(zip(X.columns, model.feature_importances_))}")
        
        # Análisis estabilidad
        importances_array = np.array(feature_importances)
        mean_importance = np.mean(importances_array, axis=0)
        std_importance = np.std(importances_array, axis=0)
        cv_importance = std_importance / (mean_importance + 1e-8)  # Coefficient of variation
        
        results = {
            'mean_importance': dict(zip(X.columns, mean_importance)),
            'std_importance': dict(zip(X.columns, std_importance)),
            'cv_importance': dict(zip(X.columns, cv_importance)),
            'is_stable': np.all(cv_importance < 0.3)  # CV < 30%
        }
        
        print(f"\n📊 ESTABILIDAD:")
        for i, feature in enumerate(X.columns):
            print(f"  {feature:20}: {mean_importance[i]:.3f} ± {std_importance[i]:.3f} (CV: {cv_importance[i]:.2f})")
        
        print(f"\n✅ Features estables: {'Sí' if np.all(cv_importance < 0.3) else 'No'}")
        
        self.results['feature_stability'] = results
        return results
    
    def generate_report(self):
        """Generar reporte final de overfitting"""
        
        print("\n\n🎯 REPORTE FINAL DE OVERFITTING")
        print("="*70)
        
        # Recopilar evidencia
        evidence = {
            'baseline_beats_complex': False,
            'cv_stable': False,
            'learning_converges': False,
            'features_stable': False,
            'overall_assessment': 'UNKNOWN'
        }
        
        # Test 1: Baseline comparison
        if 'baseline_comparison' in self.results:
            baseline_res = self.results['baseline_comparison']
            rf_complex = baseline_res.get('rf_complex', {})
            naive = baseline_res.get('naive', {})
            
            # ¿El modelo complejo supera significativamente al naive?
            if rf_complex and naive:
                improvement = naive['mape_test'] - rf_complex['mape_test']
                evidence['baseline_beats_complex'] = improvement > 1.0  # Al menos 1% mejor
                print(f"✅ Mejora vs baseline: {improvement:.2f}% {'✓' if improvement > 1.0 else '✗'}")
        
        # Test 2: CV stability
        if 'cross_validation' in self.results:
            cv_res = self.results['cross_validation']
            rf_cv = cv_res.get('rf_current', {})
            
            if rf_cv:
                evidence['cv_stable'] = rf_cv['is_stable'] and not rf_cv['is_overfitting']
                print(f"✅ CV estable: {rf_cv['is_stable']} | Sin overfitting: {not rf_cv['is_overfitting']}")
        
        # Test 3: Learning curves
        if 'learning_curves' in self.results:
            lc_res = self.results['learning_curves']
            evidence['learning_converges'] = lc_res['is_converging'] and not lc_res['is_overfitting']
            print(f"✅ Curvas convergen: {lc_res['is_converging']} | Sin overfitting: {not lc_res['is_overfitting']}")
        
        # Test 4: Feature stability
        if 'feature_stability' in self.results:
            fs_res = self.results['feature_stability']
            evidence['features_stable'] = fs_res['is_stable']
            print(f"✅ Features estables: {fs_res['is_stable']}")
        
        # Assessment final
        positive_evidence = sum([
            evidence['baseline_beats_complex'],
            evidence['cv_stable'],
            evidence['learning_converges'],
            evidence['features_stable']
        ])
        
        if positive_evidence >= 3:
            evidence['overall_assessment'] = 'NO_OVERFITTING'
            assessment_color = '✅'
        elif positive_evidence >= 2:
            evidence['overall_assessment'] = 'MILD_OVERFITTING'
            assessment_color = '⚠️'
        else:
            evidence['overall_assessment'] = 'LIKELY_OVERFITTING'
            assessment_color = '❌'
        
        print(f"\n{assessment_color} ASSESSMENT FINAL: {evidence['overall_assessment']}")
        print(f"Evidencia positiva: {positive_evidence}/4 tests")
        
        # Recomendaciones
        print(f"\n💡 RECOMENDACIONES:")
        if evidence['overall_assessment'] == 'NO_OVERFITTING':
            print("  ✅ Modelo válido para producción")
            print("  ✅ Performance en test es confiable")
        elif evidence['overall_assessment'] == 'MILD_OVERFITTING':
            print("  ⚠️ Overfitting leve detectado")
            print("  ⚠️ Considerar regularización adicional")
            print("  ⚠️ Monitorear performance en producción")
        else:
            print("  ❌ Overfitting significativo")
            print("  ❌ Reducir complejidad del modelo")
            print("  ❌ Más datos de entrenamiento necesarios")
        
        self.results['final_assessment'] = evidence
        return evidence

def main():
    """Ejecutar validación completa de overfitting"""
    
    print("🔍 VALIDACIÓN COMPLETA DE OVERFITTING - MODELO LME")
    print("="*80)
    
    # Crear validador
    validator = OverfittingValidator()
    
    # Cargar datos
    df = validator.load_data()
    X, y = validator.prepare_lme_features(df)
    
    # Ejecutar tests
    validator.test_simple_baseline(X, y)
    validator.test_cross_validation(X, y)
    validator.test_learning_curves(X, y)
    validator.test_feature_importance_stability(X, y)
    
    # Reporte final
    assessment = validator.generate_report()
    
    # Guardar resultados
    import json
    with open('outputs/overfitting_validation_report.json', 'w') as f:
        json.dump(validator.results, f, indent=2, default=str)
    
    print(f"\n📁 Reporte guardado: outputs/overfitting_validation_report.json")
    
    return assessment

if __name__ == "__main__":
    main()
