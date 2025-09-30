#!/usr/bin/env python3
"""
VALIDACIÓN CRÍTICA DE CALIDAD DE DATOS
Responde a las preguntas del usuario sobre holidays, nulos e imputación
"""

import pandas as pd
import numpy as np
from pathlib import Path

def validate_data_quality():
    """Validación completa de calidad de datos"""
    
    print("🔍 VALIDACIÓN CRÍTICA DE CALIDAD DE DATOS")
    print("="*80)
    print()
    
    # 1. Validar dataset de features
    print("1️⃣ VALIDANDO DATASET DE FEATURES")
    print("-"*80)
    
    features_path = "outputs/features_dataset_latest.csv"
    if not Path(features_path).exists():
        print(f"❌ ERROR: {features_path} no encontrado")
        return False
    
    df = pd.read_csv(features_path, index_col=0)
    print(f"✅ Dataset cargado: {len(df)} registros, {len(df.columns)} columnas")
    print(f"   Período: {df.index.min()} a {df.index.max()}")
    print()
    
    # 2. Validar nulos en features críticos
    print("2️⃣ VALIDANDO NULOS EN FEATURES CRÍTICOS (TIER 1)")
    print("-"*80)
    
    critical_features = [
        'lme_sr_m01_lag1',
        'usdmxn_lag1', 
        'mexico_premium',
        'lme_volatility_5d',
        'lme_momentum_5d'
    ]
    
    total_nulls = 0
    unexpected_nulls = 0
    for col in critical_features:
        if col in df.columns:
            nulls = df[col].isna().sum()
            pct = (nulls / len(df)) * 100
            
            # Lags tienen 1 null esperado en el primer registro
            if col.endswith('_lag1') and nulls == 1:
                status = "✅"
                print(f"{status} {col:30s}: {nulls:4d} nulos ({pct:5.2f}%) [ESPERADO: primer día]")
            elif nulls == 0:
                status = "✅"
                print(f"{status} {col:30s}: {nulls:4d} nulos ({pct:5.2f}%)")
            else:
                status = "❌"
                print(f"{status} {col:30s}: {nulls:4d} nulos ({pct:5.2f}%) [INESPERADO]")
                unexpected_nulls += nulls
            
            total_nulls += nulls
        else:
            print(f"❌ {col:30s}: COLUMNA NO ENCONTRADA")
    
    print()
    if unexpected_nulls > 0:
        print(f"⚠️ NULOS INESPERADOS EN TIER 1: {unexpected_nulls}")
        print("   ⛔ ESTO ES INACEPTABLE PARA PRODUCCIÓN")
    else:
        print(f"✅ TIER 1 COMPLETO - Solo nulos esperados en primer día ({total_nulls} total)")
    print()
    
    # 3. Validar join con holiday calendar
    print("3️⃣ VALIDANDO JOIN CON HOLIDAY CALENDAR")
    print("-"*80)
    
    expected_holiday_cols = [
        'is_weekend',
        'is_holiday_mx',
        'Mexico_holiday',
        'UK_holiday',
        'USA_holiday',
        'days_to_holiday'
    ]
    
    found_holiday_cols = []
    for col in df.columns:
        if any(keyword in col.lower() for keyword in ['holiday', 'weekend']):
            found_holiday_cols.append(col)
    
    if found_holiday_cols:
        print(f"✅ Columnas de holidays encontradas: {len(found_holiday_cols)}")
        for col in found_holiday_cols:
            print(f"   - {col}")
    else:
        print("❌ NO SE ENCONTRARON COLUMNAS DE HOLIDAYS")
    print()
    
    # 4. Validar columnas de imputación
    print("4️⃣ VALIDANDO MARCADORES DE IMPUTACIÓN")
    print("-"*80)
    
    imputed_cols = [col for col in df.columns if '_imputed' in col.lower()]
    if imputed_cols:
        print(f"✅ Columnas de imputación encontradas: {len(imputed_cols)}")
        for col in imputed_cols:
            n_imputed = df[col].sum()
            pct = (n_imputed / len(df)) * 100
            print(f"   - {col}: {n_imputed} días ({pct:.2f}%)")
    else:
        print("❌ NO SE ENCONTRARON COLUMNAS *_imputed")
        print("   ⚠️ No hay transparencia sobre qué valores fueron imputados")
    print()
    
    # 5. Validar holiday calendar separado
    print("5️⃣ VALIDANDO HOLIDAY CALENDAR SEPARADO")
    print("-"*80)
    
    holiday_cal_path = "outputs/holiday_calendar_2015_2026.csv"
    if Path(holiday_cal_path).exists():
        holidays = pd.read_csv(holiday_cal_path, index_col=0)
        print(f"✅ Holiday calendar encontrado: {len(holidays)} registros")
        print(f"   Columnas: {list(holidays.columns)}")
    else:
        print(f"❌ Holiday calendar NO encontrado: {holiday_cal_path}")
    print()
    
    # 6. Resumen de validación
    print("6️⃣ RESUMEN DE VALIDACIÓN")
    print("="*80)
    
    issues = []
    
    if unexpected_nulls > 0:
        issues.append(f"❌ {unexpected_nulls} nulos INESPERADOS en features Tier 1")
    
    if len(found_holiday_cols) < 2:
        issues.append(f"❌ Solo {len(found_holiday_cols)} columnas de holidays (esperadas: 3+)")
    
    if len(imputed_cols) == 0:
        issues.append("❌ NO hay columnas *_imputed para transparencia")
    
    if issues:
        print("⛔ DATASET NO ESTÁ LISTO PARA PRODUCCIÓN")
        print()
        for issue in issues:
            print(f"   {issue}")
        print()
        print("🔧 ACCIÓN REQUERIDA:")
        print("   1. Ejecutar robust_feature_pipeline.py con rutas correctas")
        print("   2. Verificar que se aplique holiday imputation completa")
        print("   3. Re-generar features_dataset_latest.csv")
        print("   4. Re-entrenar modelo con datos limpios")
    else:
        print("✅ DATASET ESTÁ LISTO PARA PRODUCCIÓN")
    
    print()
    return len(issues) == 0

if __name__ == "__main__":
    is_valid = validate_data_quality()
    exit(0 if is_valid else 1)
