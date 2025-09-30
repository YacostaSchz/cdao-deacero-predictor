#!/usr/bin/env python3
"""
Temporal Audit Analyzer for Steel Rebar Price Prediction
Audita fuentes de datos para verificar usabilidad en predicción t+1
Autor: CDO DeAcero - Analista Senior Series Temporales
Fecha: 2025-09-28
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Optional
import os
import warnings
warnings.filterwarnings('ignore')

class TemporalAuditAnalyzer:
    """Analizador de auditoría temporal para fuentes de datos"""
    
    def __init__(self, output_dir: str = "parte_tecnica/02_data_extractors/outputs"):
        self.output_dir = output_dir
        self.analysis_window = ("2024-01-01", "2025-12-31")
        self.cutoff_timezone = "America/Mexico_City"  # Mercado mexicano
        self.results = {}
        
    def load_and_sample(self, file_path: str, source_name: str) -> pd.DataFrame:
        """Carga fuente y filtra a ventana 2024-2025"""
        print(f"\n{'='*60}")
        print(f"ANALIZANDO: {source_name}")
        print(f"{'='*60}")
        
        # Cargar datos
        df = pd.read_csv(os.path.join(self.output_dir, file_path))
        print(f"Registros totales: {len(df)}")
        print(f"Columnas: {list(df.columns)}")
        
        # Detectar columna temporal principal
        date_cols = [col for col in df.columns if any(x in col.lower() for x in ['date', 'fecha', 'year', 'año'])]
        if not date_cols:
            print("⚠️ No se encontró columna de fecha clara")
            return df
            
        primary_time_col = date_cols[0]
        print(f"Columna temporal principal: {primary_time_col}")
        
        # Convertir a datetime
        df[primary_time_col] = pd.to_datetime(df[primary_time_col], errors='coerce')
        
        # Filtrar ventana de análisis
        start_date = pd.to_datetime(self.analysis_window[0])
        end_date = pd.to_datetime(self.analysis_window[1])
        
        df_window = df[(df[primary_time_col] >= start_date) & 
                      (df[primary_time_col] <= end_date)].copy()
        
        print(f"\nVentana 2024-2025:")
        print(f"  - Registros en ventana: {len(df_window)}")
        if len(df_window) > 0:
            print(f"  - Fecha mínima: {df_window[primary_time_col].min()}")
            print(f"  - Fecha máxima: {df_window[primary_time_col].max()}")
        
        # Estadísticas de calidad
        print(f"\nCalidad de datos:")
        for col in df_window.columns:
            missing_pct = df_window[col].isna().sum() / len(df_window) * 100
            if missing_pct > 0:
                print(f"  - {col}: {missing_pct:.1f}% faltantes")
        
        # Detectar duplicados
        dup_exact = df_window.duplicated().sum()
        print(f"  - Duplicados exactos: {dup_exact}")
        
        if primary_time_col in df_window.columns:
            dup_temporal = df_window.duplicated(subset=[primary_time_col]).sum()
            print(f"  - Duplicados por fecha: {dup_temporal}")
        
        return df_window
    
    def infer_frequency(self, df: pd.DataFrame, time_col: str) -> Dict:
        """Infiere frecuencia y patrones temporales"""
        print(f"\nAnálisis de frecuencia:")
        
        if time_col not in df.columns:
            return {"error": "Columna temporal no encontrada"}
        
        # Ordenar por fecha
        df_sorted = df.sort_values(time_col)
        
        # Calcular deltas
        time_deltas = df_sorted[time_col].diff().dropna()
        
        if len(time_deltas) == 0:
            return {"error": "No hay suficientes datos para calcular frecuencia"}
        
        # Convertir a días
        delta_days = time_deltas.dt.total_seconds() / 86400
        
        # Estadísticas de deltas
        delta_stats = {
            'min_days': float(delta_days.min()),
            'median_days': float(delta_days.median()),
            'max_days': float(delta_days.max()),
            'std_days': float(delta_days.std()),
            'mode_days': float(delta_days.mode()[0]) if not delta_days.mode().empty else float(delta_days.median())
        }
        
        # Clasificar frecuencia
        median_delta = delta_stats['median_days']
        
        if median_delta < 0.5:
            freq_class = "intraday"
        elif median_delta <= 1.5:
            freq_class = "daily"
        elif median_delta <= 10:
            freq_class = "weekly"
        elif median_delta <= 35:
            freq_class = "monthly"
        elif median_delta <= 100:
            freq_class = "quarterly"
        else:
            freq_class = "irregular"
        
        print(f"  - Frecuencia detectada: {freq_class}")
        print(f"  - Delta mediano: {median_delta:.1f} días")
        print(f"  - Rango de deltas: [{delta_stats['min_days']:.1f}, {delta_stats['max_days']:.1f}] días")
        
        # Inferir release lag basado en tipo de datos
        release_lag_days = self._infer_release_lag(df, freq_class)
        
        return {
            'frequency_class': freq_class,
            'delta_median_days': median_delta,
            'delta_stats': delta_stats,
            'release_lag_median_days': release_lag_days,
            'timezone': self.cutoff_timezone
        }
    
    def _infer_release_lag(self, df: pd.DataFrame, freq_class: str) -> float:
        """Infiere el lag de publicación basado en patrones conocidos"""
        # Reglas heurísticas por tipo de dato
        release_lags = {
            'daily': 0,  # Datos diarios típicamente disponibles mismo día
            'monthly': 10,  # Datos mensuales típicamente publicados día 10 del mes siguiente
            'weekly': 2,  # Datos semanales con 2 días de retraso
            'quarterly': 30,  # Datos trimestrales con un mes de retraso
            'intraday': 0,  # Datos intradía disponibles en tiempo real
            'irregular': 5  # Asumir 5 días por defecto
        }
        
        # Ajustes específicos por fuente
        if 'banxico' in str(df.columns).lower():
            if 'inpc' in str(df.columns).lower() or 'sp1' in str(df.columns).lower():
                return 9  # INPC se publica típicamente día 9 del mes siguiente
            elif 'igae' in str(df.columns).lower():
                return 55  # IGAE tiene ~55 días de retraso
        
        return release_lags.get(freq_class, 5)
    
    def propose_features(self, df: pd.DataFrame, freq_class: str, 
                        value_cols: List[str], release_lag: float) -> List[Dict]:
        """Propone features según frecuencia sin fuga de información"""
        features = []
        
        if freq_class == "daily":
            # Features para datos diarios
            for col in value_cols:
                # Nivel con lag por disponibilidad
                if release_lag == 0:
                    features.append({
                        'name': f'{col}_t0',
                        'uses_data_at': 't-0',
                        'transform': 'level',
                        'window': 1,
                        'availability_rule': 'same_day_close'
                    })
                
                # Lags seguros
                for lag in [1, 5, 20]:
                    features.append({
                        'name': f'{col}_lag{lag}',
                        'uses_data_at': f't-{lag}',
                        'transform': 'level',
                        'window': 1,
                        'availability_rule': f'available_at <= cutoff_t-{lag}'
                    })
                
                # Cambios porcentuales
                for window in [5, 20]:
                    features.append({
                        'name': f'{col}_pct_change_{window}d',
                        'uses_data_at': f't-1',
                        'transform': f'pct_change_{window}',
                        'window': window,
                        'availability_rule': 'requires_t-1_to_t-window'
                    })
                
                # Media móvil
                features.append({
                    'name': f'{col}_ma20',
                    'uses_data_at': 't-1',
                    'transform': 'rolling_mean',
                    'window': 20,
                    'availability_rule': 'uses_t-1_to_t-20'
                })
                
        elif freq_class == "monthly":
            # Features para datos mensuales
            for col in value_cols:
                # Último valor publicado (as-of join)
                features.append({
                    'name': f'{col}_last_published',
                    'uses_data_at': f't-{int(release_lag)}',
                    'transform': 'as_of_join',
                    'window': 1,
                    'availability_rule': f'last_value_published_before_t-{int(release_lag)}'
                })
                
                # Cambios mensuales
                features.append({
                    'name': f'{col}_mom_pct',
                    'uses_data_at': 't-1m',
                    'transform': 'month_over_month_pct',
                    'window': 1,
                    'availability_rule': 'requires_two_published_months'
                })
                
                # Cambio trimestral
                features.append({
                    'name': f'{col}_qoq_pct',
                    'uses_data_at': 't-3m',
                    'transform': 'quarter_over_quarter_pct',
                    'window': 3,
                    'availability_rule': 'requires_t-1m_and_t-4m_published'
                })
        
        elif freq_class == "weekly":
            # Features para datos semanales
            for col in value_cols:
                # Último valor (con lag de publicación)
                features.append({
                    'name': f'{col}_last_week',
                    'uses_data_at': f't-{int(release_lag+7)}',
                    'transform': 'as_of_join_weekly',
                    'window': 7,
                    'availability_rule': f'last_weekly_value_before_t-{int(release_lag)}'
                })
                
                # Cambio semanal
                features.append({
                    'name': f'{col}_wow_pct',
                    'uses_data_at': 't-1w',
                    'transform': 'week_over_week_pct',
                    'window': 7,
                    'availability_rule': 'requires_two_published_weeks'
                })
        
        return features
    
    def generate_quality_report(self, df: pd.DataFrame, source_name: str) -> Dict:
        """Genera reporte de calidad de datos"""
        report = {
            'source': source_name,
            'total_records': len(df),
            'date_range': {
                'min': str(df.iloc[:, 0].min()) if len(df) > 0 else None,
                'max': str(df.iloc[:, 0].max()) if len(df) > 0 else None
            },
            'missing_pct_by_col': {},
            'duplicates': {},
            'outliers': {}
        }
        
        # Porcentaje de faltantes por columna
        for col in df.columns:
            missing_pct = (df[col].isna().sum() / len(df) * 100) if len(df) > 0 else 0
            report['missing_pct_by_col'][col] = round(missing_pct, 2)
        
        # Duplicados
        report['duplicates']['exact'] = int(df.duplicated().sum())
        
        # Outliers en columnas numéricas
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col in df.columns and df[col].notna().sum() > 3:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                outliers = ((df[col] < (Q1 - 1.5 * IQR)) | 
                           (df[col] > (Q3 + 1.5 * IQR))).sum()
                report['outliers'][col] = int(outliers)
        
        return report
    
    def analyze_source(self, file_path: str, source_name: str, 
                      value_cols: List[str], units: str) -> Dict:
        """Análisis completo de una fuente"""
        # 1. Cargar y filtrar datos
        df = self.load_and_sample(file_path, source_name)
        
        if len(df) == 0:
            print(f"⚠️ No hay datos en ventana 2024-2025 para {source_name}")
            return None
        
        # 2. Detectar columna temporal
        date_cols = [col for col in df.columns if any(x in col.lower() for x in ['date', 'fecha', 'year', 'año'])]
        primary_time_col = date_cols[0] if date_cols else None
        
        if not primary_time_col:
            print(f"❌ No se pudo detectar columna temporal en {source_name}")
            return None
        
        # 3. Análisis de frecuencia
        freq_analysis = self.infer_frequency(df, primary_time_col)
        
        # 4. Proponer features
        features = self.propose_features(
            df, 
            freq_analysis['frequency_class'],
            value_cols,
            freq_analysis['release_lag_median_days']
        )
        
        # 5. Reporte de calidad
        quality_report = self.generate_quality_report(df, source_name)
        
        # 6. Generar muestra preview
        sample_size = min(20, len(df))
        sample_preview = df.head(sample_size)
        
        # 7. Consolidar resultados
        analysis = {
            'source_name': source_name,
            'file_path': file_path,
            'date_range': quality_report['date_range'],
            'frequency': freq_analysis,
            'data_quality': quality_report,
            'imputation_policy': {
                'method': 'LOCF',
                'max_carry_days': self._get_max_carry(freq_analysis['frequency_class'])
            },
            'anti_leakage': {
                'cutoff_time_tz': f'23:59:59 {self.cutoff_timezone}',
                'available_at_rule': f'primary_time + {freq_analysis["release_lag_median_days"]} days'
            },
            'features': features,
            'units': units,
            'sample_preview': sample_preview.to_dict('records')[:10]  # Primeras 10 filas
        }
        
        return analysis
    
    def _get_max_carry(self, freq_class: str) -> int:
        """Define política de carry forward según frecuencia"""
        carry_policies = {
            'daily': 3,
            'weekly': 7,
            'monthly': 31,
            'quarterly': 93,
            'intraday': 1,
            'irregular': 7
        }
        return carry_policies.get(freq_class, 7)


def main():
    """Función principal de auditoría"""
    analyzer = TemporalAuditAnalyzer()
    
    # Definir fuentes a analizar
    sources_to_analyze = [
        # Banxico
        {
            'file': 'SF43718_data.csv',
            'name': 'BANXICO_USD_MXN',
            'value_cols': ['valor'],
            'units': 'MXN/USD'
        },
        {
            'file': 'SP1_data.csv', 
            'name': 'BANXICO_INPC',
            'value_cols': ['valor'],
            'units': 'Index'
        },
        {
            'file': 'SF43783_data.csv',
            'name': 'BANXICO_TIIE28',
            'value_cols': ['valor'],
            'units': 'Percent'
        },
        # LME
        {
            'file': 'lme_sr_wide.csv',
            'name': 'LME_STEEL_REBAR',
            'value_cols': ['M01', 'M02', 'M03'],
            'units': 'USD/ton'
        },
        {
            'file': 'lme_combined_sr_sc.csv',
            'name': 'LME_COMBINED',
            'value_cols': ['sr_m01', 'sc_m01', 'rebar_scrap_spread'],
            'units': 'USD/ton'
        },
        # EPU
        {
            'file': 'epu_mexico_data.csv',
            'name': 'EPU_MEXICO',
            'value_cols': ['Mexican Policy Uncertainty Index'],
            'units': 'Index'
        },
        # Gas Natural
        {
            'file': 'gas_natural_ipgn.csv',
            'name': 'GAS_NATURAL_IPGN',
            'value_cols': ['Índice (USD/MBtu)'],
            'units': 'USD/MBtu'
        }
    ]
    
    all_results = []
    
    print("="*80)
    print("AUDITORÍA TEMPORAL DE FUENTES DE DATOS")
    print("Predicción de Precio Varilla Corrugada t+1")
    print("="*80)
    
    for source in sources_to_analyze:
        try:
            result = analyzer.analyze_source(
                source['file'],
                source['name'],
                source['value_cols'],
                source['units']
            )
            if result:
                all_results.append(result)
        except Exception as e:
            print(f"\n❌ Error analizando {source['name']}: {e}")
            continue
    
    # Guardar resultados consolidados
    output_path = 'parte_tecnica/03_feature_engineering/temporal_audit_results.json'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n✅ Resultados guardados en: {output_path}")
    
    # Generar resumen ejecutivo
    print("\n" + "="*80)
    print("RESUMEN EJECUTIVO DE AUDITORÍA")
    print("="*80)
    
    usable_sources = 0
    for result in all_results:
        freq = result['frequency']['frequency_class']
        lag = result['frequency']['release_lag_median_days']
        quality = 100 - np.mean(list(result['data_quality']['missing_pct_by_col'].values()))
        
        usability = "✅ APTA" if quality > 95 and lag < 30 else "⚠️ LIMITADA"
        if quality < 90:
            usability = "❌ NO APTA"
        else:
            usable_sources += 1
        
        print(f"\n{result['source_name']}:")
        print(f"  - Frecuencia: {freq}")
        print(f"  - Release lag: {lag:.0f} días")
        print(f"  - Calidad datos: {quality:.1f}%")
        print(f"  - Features propuestos: {len(result['features'])}")
        print(f"  - Usabilidad t+1: {usability}")
    
    print(f"\n\nFUENTES APTAS PARA MODELO: {usable_sources}/{len(all_results)}")
    
    return all_results


if __name__ == "__main__":
    main()
