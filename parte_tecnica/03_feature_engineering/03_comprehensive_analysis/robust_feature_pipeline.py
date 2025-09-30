#!/usr/bin/env python3
"""
ROBUST FEATURE PIPELINE - CDO DeAcero
Predicción Precio Varilla Corrugada t+1

Implementa estrategia robusta con 15 features core en 3 tiers
Autor: Sistema Sr Data Scientist "CausalOps"
Fecha: 2025-09-28
"""

import pandas as pd
import numpy as np
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Union
import json
import logging
from pathlib import Path

# Configuración
warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RobustFeaturePipeline:
    """Pipeline robusto para generar 15 features core con sistema de fallbacks"""
    
    def __init__(self, data_path: str = "../../02_data_extractors/outputs/"):
        self.data_path = Path(data_path)
        self.holiday_path = Path("../outputs/holiday_calendar_2015_2026.csv")
        # Ruta corregida desde 03_comprehensive_analysis/
        self.events_path = Path(__file__).parent.parent.parent.parent / "docs/sources/99_custom/scores_formatted.md"
        
        # Parámetros del modelo
        self.MEXICO_PREMIUM = 1.157  # 15.7% spread calibrado
        self.FALLBACK_PRICE = 625.0  # Último precio conocido USD/ton
        
        # Configuración de features
        self.feature_config = self._setup_feature_config()
        
        # Cache para datos
        self._data_cache = {}
        
        logger.info("🛡️ RobustFeaturePipeline inicializado")
        
    def _setup_feature_config(self) -> Dict:
        """Configuración de los 15 features core en 3 tiers"""
        return {
            'tier_1_critical': {
                'lme_sr_m01_lag1': {'source': 'lme', 'weight': 0.40, 'fallback': 'last_known'},
                'usdmxn_lag1': {'source': 'banxico', 'weight': 0.20, 'fallback': 'last_known'},
                'mexico_premium': {'value': self.MEXICO_PREMIUM, 'weight': 0.20, 'fallback': 'fixed'},
                'lme_volatility_5d': {'source': 'lme', 'weight': 0.10, 'fallback': 'historical_avg'},
                'lme_momentum_5d': {'source': 'lme', 'weight': 0.10, 'fallback': 0.0}
            },
            'tier_2_important': {
                'contango_indicator': {'source': 'lme', 'fallback': 0},
                'rebar_scrap_spread_norm': {'source': 'lme', 'fallback': 'historical_median'},
                'trade_events_impact_7d': {'source': 'events', 'fallback': 0},
                'weekday_effect': {'source': 'calendar', 'fallback': 0},
                'seasonality_simple': {'source': 'calendar', 'fallback': 0}
            },
            'tier_3_contextual': {
                'real_interest_rate': {'source': 'banxico', 'lag': 30, 'fallback': 'last_known'},
                'uncertainty_indicator': {'source': 'epu', 'fallback': 'medium'},
                'market_regime': {'source': 'lme', 'fallback': 'neutral'},
                'days_to_holiday': {'source': 'calendar', 'fallback': 30},
                'model_confidence': {'source': 'computed', 'fallback': 0.7}
            }
        }

    def load_data(self) -> Dict[str, pd.DataFrame]:
        """Cargar todos los datasets necesarios con manejo de errores"""
        logger.info("📊 Cargando datos...")
        
        datasets = {}
        
        try:
            # 1. LME Data (crítico)
            lme_file = self.data_path / "lme_combined_sr_sc.csv"
            if lme_file.exists():
                datasets['lme'] = pd.read_csv(lme_file, parse_dates=['date'], index_col='date')
                logger.info(f"✅ LME data: {len(datasets['lme'])} registros")
            else:
                logger.error("❌ LME data no encontrado - CRÍTICO")
                raise FileNotFoundError("LME data es crítico para el modelo")
            
            # 2. Banxico Data (crítico)
            fx_file = self.data_path / "SF43718_data.csv"  # USD/MXN
            if fx_file.exists():
                fx_data = pd.read_csv(fx_file, parse_dates=['fecha'], index_col='fecha')
                fx_data.rename(columns={'valor': 'usdmxn'}, inplace=True)
                datasets['banxico_fx'] = fx_data
                logger.info(f"✅ FX data: {len(datasets['banxico_fx'])} registros")
            
            tiie_file = self.data_path / "SF43783_data.csv"  # TIIE28
            if tiie_file.exists():
                tiie_data = pd.read_csv(tiie_file, parse_dates=['fecha'], index_col='fecha')
                tiie_data.rename(columns={'valor': 'tiie28'}, inplace=True)
                datasets['banxico_tiie'] = tiie_data
                logger.info(f"✅ TIIE data: {len(datasets['banxico_tiie'])} registros")
            
            inpc_file = self.data_path / "SP1_data.csv"  # INPC
            if inpc_file.exists():
                inpc_data = pd.read_csv(inpc_file, parse_dates=['fecha'], index_col='fecha')
                inpc_data.rename(columns={'valor': 'inpc'}, inplace=True)
                datasets['banxico_inpc'] = inpc_data
                logger.info(f"✅ INPC data: {len(datasets['banxico_inpc'])} registros")
            
            # 3. EPU Data (importante)
            for country in ['mexico', 'usa', 'china', 'turkey']:
                epu_file = self.data_path / f"epu_{country}_data.csv"
                if epu_file.exists():
                    epu_data = pd.read_csv(epu_file)
                    # Crear columna de fecha a partir de Year y Month
                    if 'Year' in epu_data.columns and 'Month' in epu_data.columns:
                        epu_data['date'] = pd.to_datetime(epu_data[['Year', 'Month']].assign(day=1))
                        epu_data = epu_data.set_index('date')
                        # Renombrar columna EPU
                        epu_cols = [col for col in epu_data.columns if 'Policy Uncertainty' in col or 'EPU' in col or 'Index' in col]
                        if epu_cols:
                            epu_data.rename(columns={epu_cols[0]: 'epu_index'}, inplace=True)
                    datasets[f'epu_{country}'] = epu_data
                    logger.info(f"✅ EPU {country}: {len(epu_data)} registros")
            
            # 4. Holiday Calendar
            if self.holiday_path.exists():
                datasets['holidays'] = pd.read_csv(self.holiday_path, index_col=0, parse_dates=True)
                logger.info(f"✅ Holiday calendar: {len(datasets['holidays'])} registros")
            
            # 5. Trade Events
            if self.events_path.exists():
                datasets['events'] = self._parse_trade_events()
                logger.info(f"✅ Trade events: {len(datasets['events'])} eventos")
            
        except Exception as e:
            logger.error(f"❌ Error cargando datos: {e}")
            raise
        
        self._data_cache = datasets
        return datasets
    
    def _parse_trade_events(self) -> pd.DataFrame:
        """
        Parsear eventos comerciales del markdown
        Formato: | Fecha | Descripción | Impacto (-3 a +3) | Referencia |
        """
        events = []
        
        try:
            with open(self.events_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extraer tabla de eventos
            lines = content.split('\n')
            for line in lines:
                # Buscar líneas que tienen fecha 2025 y son parte de la tabla
                if '2025-' in line and '|' in line and not line.strip().startswith('||'):
                    parts = [p.strip() for p in line.split('|')]
                    # Formato: ['', 'Fecha', 'Descripción', 'Impacto', 'Referencia', '']
                    if len(parts) >= 5:
                        try:
                            date_str = parts[1]
                            date = pd.to_datetime(date_str)
                            description = parts[2]
                            impact_str = parts[3]
                            
                            # Extraer impacto numérico (-3 a +3)
                            if '+3' in impact_str:
                                impact = 3
                            elif '+2' in impact_str:
                                impact = 2
                            elif '+1' in impact_str:
                                impact = 1
                            elif '-3' in impact_str:
                                impact = -3
                            elif '-2' in impact_str:
                                impact = -2
                            elif '-1' in impact_str:
                                impact = -1
                            else:
                                impact = 0
                            
                            events.append({
                                'date': date,
                                'impact': impact,
                                'description': description[:100]  # Truncar descripción
                            })
                        except Exception as e:
                            continue
            
            if events:
                df = pd.DataFrame(events).set_index('date')
                logger.info(f"✅ Trade events parseados: {len(df)} eventos con impactos {df['impact'].min()} a {df['impact'].max()}")
                return df
            else:
                logger.warning("⚠️ No se encontraron eventos en el archivo")
                return pd.DataFrame(columns=['impact', 'description'])
            
        except Exception as e:
            logger.warning(f"⚠️ Error parsing trade events: {e}")
            return pd.DataFrame(columns=['impact', 'description'])

    def align_temporal_data(self, datasets: Dict) -> pd.DataFrame:
        """Alinear temporalmente todos los datos en frecuencia diaria"""
        logger.info("🔄 Alineando datos temporalmente...")
        
        # Crear índice diario desde 2015 hasta hoy
        start_date = '2015-01-01'
        end_date = pd.Timestamp.now().strftime('%Y-%m-%d')
        daily_index = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # DataFrame base
        aligned_df = pd.DataFrame(index=daily_index)
        
        # 1. LME data (diario, base principal)
        if 'lme' in datasets:
            lme = datasets['lme']
            aligned_df['sr_m01'] = lme['sr_m01']
            # Solo agregar columnas que existen
            if 'sr_m02' in lme.columns:
                aligned_df['sr_m02'] = lme['sr_m02']
            if 'sr_m03' in lme.columns:
                aligned_df['sr_m03'] = lme['sr_m03']
            aligned_df['sc_m01'] = lme['sc_m01']
            logger.info(f"✅ LME data alineado: {aligned_df['sr_m01'].notna().sum()} días válidos")
        
        # 2. FX data (diario)
        if 'banxico_fx' in datasets:
            aligned_df['usdmxn'] = datasets['banxico_fx']['usdmxn']
            logger.info(f"✅ FX data alineado: {aligned_df['usdmxn'].notna().sum()} días válidos")
        
        # 3. TIIE data (diario)
        if 'banxico_tiie' in datasets:
            aligned_df['tiie28'] = datasets['banxico_tiie']['tiie28']
        
        # 4. INPC data (mensual - forward fill)
        if 'banxico_inpc' in datasets:
            inpc_monthly = datasets['banxico_inpc']['inpc'].resample('M').last()
            aligned_df['inpc'] = inpc_monthly.reindex(daily_index, method='ffill')
        
        # 5. EPU data (mensual - forward fill)
        for country in ['mexico', 'usa', 'china', 'turkey']:
            if f'epu_{country}' in datasets:
                epu_data = datasets[f'epu_{country}']
                if 'epu_index' in epu_data.columns:
                    epu_monthly = epu_data['epu_index'].resample('M').last()
                    aligned_df[f'epu_{country}'] = epu_monthly.reindex(daily_index, method='ffill')
        
        # 6. Holiday indicators
        if 'holidays' in datasets:
            holidays = datasets['holidays']
            # Buscar columnas correctas
            mx_holiday_col = None
            weekend_col = None
            
            for col in holidays.columns:
                if 'mexico' in col.lower() or 'Mexico' in col:
                    mx_holiday_col = col
                if 'weekend' in col.lower():
                    weekend_col = col
            
            if mx_holiday_col is not None:
                aligned_df['is_holiday_mx'] = holidays[mx_holiday_col].astype(int)
            else:
                aligned_df['is_holiday_mx'] = 0
                
            if weekend_col is not None:
                aligned_df['is_weekend'] = holidays[weekend_col].astype(int)
            else:
                aligned_df['is_weekend'] = (aligned_df.index.weekday >= 5).astype(int)
        else:
            # Fallback: calcular weekends básicos
            aligned_df['is_weekend'] = (aligned_df.index.weekday >= 5).astype(int)
            aligned_df['is_holiday_mx'] = 0
        
        logger.info(f"✅ Datos alineados: {len(aligned_df)} días, periodo {aligned_df.index.min()} a {aligned_df.index.max()}")
        
        return aligned_df

    def apply_holiday_imputation(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aplicar estrategia de imputación por días inhábiles
        GARANTÍA: 0 nulos en series críticas para que lags no tengan nulos
        """
        logger.info("🏖️ Aplicando imputación por días inhábiles...")
        
        df_imputed = df.copy()
        
        # Columnas críticas a imputar con LOCF
        # IMPORTANTE: Estas columnas NO pueden tener nulos porque se usarán en lags
        critical_columns = ['sr_m01', 'sr_m02', 'sr_m03', 'sc_m01', 'usdmxn', 'tiie28']
        
        for col in critical_columns:
            if col in df_imputed.columns:
                nulls_before = df_imputed[col].isnull().sum()
                
                # Marcar imputaciones ANTES de imputar
                df_imputed[f'{col}_imputed'] = df_imputed[col].isna()
                
                # Paso 1: LOCF con límite 3 días (weekends normales)
                df_imputed[col] = df_imputed[col].fillna(method='ffill', limit=3)
                
                # Paso 2: Si aún hay nulos, LOCF sin límite (gaps largos)
                remaining_nulls = df_imputed[col].isnull().sum()
                if remaining_nulls > 0:
                    df_imputed[col] = df_imputed[col].fillna(method='ffill')
                
                # Paso 3: Si TODAVÍA hay nulos al inicio, backfill
                remaining_nulls = df_imputed[col].isnull().sum()
                if remaining_nulls > 0:
                    df_imputed[col] = df_imputed[col].fillna(method='bfill')
                
                # Paso 4: Último recurso - media de la serie
                remaining_nulls = df_imputed[col].isnull().sum()
                if remaining_nulls > 0:
                    df_imputed[col] = df_imputed[col].fillna(df_imputed[col].mean())
                
                nulls_after = df_imputed[col].isnull().sum()
                n_imputed = df_imputed[f'{col}_imputed'].sum()
                
                status = "✅" if nulls_after == 0 else "❌"
                logger.info(f"   {status} {col}: {nulls_before} nulos → {n_imputed} imputados → {nulls_after} restantes")
                
                if nulls_after > 0:
                    logger.error(f"      ⛔ CRÍTICO: {col} aún tiene {nulls_after} nulos")
        
        # Para datos mensuales, permitir forward fill más largo
        monthly_columns = [col for col in df_imputed.columns if col.startswith(('inpc', 'epu_'))]
        for col in monthly_columns:
            if col in df_imputed.columns:
                df_imputed[col] = df_imputed[col].fillna(method='ffill', limit=31)
                # Si aún hay nulos (inicio de serie), backfill
                df_imputed[col] = df_imputed[col].fillna(method='bfill')
        
        return df_imputed

    def create_tier1_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Crear features Tier 1 - Críticos (5 features)
        PRE-REQUISITO: df debe tener 0 nulos en sr_m01 y usdmxn
        """
        logger.info("🔴 Creando features Tier 1 - Críticos...")
        
        # VALIDACIÓN PREVIA: Verificar que no hay nulos en columnas base
        critical_base = ['sr_m01', 'usdmxn']
        for col in critical_base:
            if col in df.columns:
                nulls = df[col].isnull().sum()
                if nulls > 0:
                    logger.error(f"❌ CRÍTICO: {col} tiene {nulls} nulos ANTES de calcular lags")
                    raise ValueError(f"{col} debe estar limpio antes de calcular features")
        
        features = pd.DataFrame(index=df.index)
        
        # 1. LME SR M01 lag-1 (40% weight) - MÁS IMPORTANTE
        features['lme_sr_m01_lag1'] = df['sr_m01'].shift(1)
        
        # 2. USD/MXN lag-1 (20% weight)
        features['usdmxn_lag1'] = df['usdmxn'].shift(1)
        
        # 3. Mexico premium (20% weight) - FIJO 15.7%
        features['mexico_premium'] = self.MEXICO_PREMIUM
        
        # 4. LME volatility 5d (10% weight)
        returns_5d = df['sr_m01'].pct_change().rolling(window=5, min_periods=3)
        features['lme_volatility_5d'] = returns_5d.std()
        
        # 5. LME momentum 5d (10% weight)
        features['lme_momentum_5d'] = (df['sr_m01'].shift(1) - df['sr_m01'].shift(5)) / df['sr_m01'].shift(5)
        
        # Fallbacks solo para features derivados (NO para lags)
        # Los lags tienen 1 null al inicio por el shift(1) - esto es esperado
        features['lme_volatility_5d'] = features['lme_volatility_5d'].fillna(0.02)  # ~2% histórico
        features['lme_momentum_5d'] = features['lme_momentum_5d'].fillna(0.0)  # 0 al inicio
        
        # VALIDACIÓN POST-FEATURE: Contar nulos
        for col in ['lme_sr_m01_lag1', 'usdmxn_lag1']:
            nulls = features[col].isnull().sum()
            # Solo debe haber 1 null (primera fila por shift)
            if nulls > 1:
                logger.error(f"❌ {col}: {nulls} nulos (esperado: 1 por shift)")
            else:
                logger.info(f"✅ {col}: {nulls} nulos (correcto - solo primer día)")
        
        logger.info(f"✅ Tier 1 features: {features.notna().sum().sum()}/{len(features)*5} valores válidos")
        
        return features

    def create_tier2_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Crear features Tier 2 - Importantes (5 features)"""
        logger.info("🟡 Creando features Tier 2 - Importantes...")
        
        features = pd.DataFrame(index=df.index)
        
        # 6. Contango indicator (simple: +1, 0, -1)
        # Usar M03 si está disponible, sino usar M02, sino usar proxy simple
        if 'sr_m03' in df.columns and 'sr_m01' in df.columns:
            spread = df['sr_m03'] - df['sr_m01']
            features['contango_indicator'] = np.sign(spread)
        elif 'sr_m02' in df.columns and 'sr_m01' in df.columns:
            spread = df['sr_m02'] - df['sr_m01']
            features['contango_indicator'] = np.sign(spread)
        else:
            # Proxy basado en momentum como indicador de estructura
            if 'sr_m01' in df.columns:
                momentum = df['sr_m01'].pct_change(5)
                features['contango_indicator'] = np.sign(momentum)
            else:
                features['contango_indicator'] = 0
        
        # 7. Rebar-scrap spread normalizado
        if 'sc_m01' in df.columns:
            spread = df['sr_m01'] - df['sc_m01']
            features['rebar_scrap_spread_norm'] = spread / df['sr_m01']
        else:
            features['rebar_scrap_spread_norm'] = 0.25  # Spread típico histórico
        
        # 8. Trade events impact próximos 7 días
        features['trade_events_impact_7d'] = self._calculate_trade_events_impact(df.index)
        
        # 9. Weekday effect
        weekday_effects = {0: -0.02, 1: 0.01, 2: 0.00, 3: 0.00, 4: 0.01, 5: 0.00, 6: 0.00}  # Mon=0
        features['weekday_effect'] = df.index.weekday.map(weekday_effects)
        
        # 10. Seasonality simple (por quarter)
        quarter_effects = {1: -0.01, 2: 0.02, 3: 0.01, 4: -0.02}
        features['seasonality_simple'] = df.index.quarter.map(quarter_effects)
        
        # Fallbacks
        features['contango_indicator'] = features['contango_indicator'].fillna(0)
        features['rebar_scrap_spread_norm'] = features['rebar_scrap_spread_norm'].fillna(0.25)
        features['trade_events_impact_7d'] = features['trade_events_impact_7d'].fillna(0)
        
        logger.info(f"✅ Tier 2 features: {features.notna().sum().sum()}/{len(features)*5} valores válidos")
        
        return features

    def create_tier3_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Crear features Tier 3 - Contextuales (5 features)"""
        logger.info("🟢 Creando features Tier 3 - Contextuales...")
        
        features = pd.DataFrame(index=df.index)
        
        # 11. Real interest rate (TIIE - inflation)
        if 'tiie28' in df.columns and 'inpc' in df.columns:
            inflation_yoy = df['inpc'].pct_change(252)  # Aprox anual
            features['real_interest_rate'] = df['tiie28'] - inflation_yoy
        else:
            features['real_interest_rate'] = 4.0  # Valor histórico típico
        
        # 12. Uncertainty indicator (simple high/medium/low)
        uncertainty_score = 0.5  # Default medium
        if 'lme_volatility_5d' in df.columns:
            # Basado en volatilidad
            vol_data = df['sr_m01'].pct_change().rolling(20).std()
            uncertainty_score = np.where(vol_data > vol_data.quantile(0.75), 0.8,
                                       np.where(vol_data < vol_data.quantile(0.25), 0.2, 0.5))
        features['uncertainty_indicator'] = uncertainty_score
        
        # 13. Market regime (bull=1, neutral=0, bear=-1)
        if 'sr_m01' in df.columns:
            ma_5 = df['sr_m01'].rolling(5).mean()
            ma_20 = df['sr_m01'].rolling(20).mean()
            features['market_regime'] = np.where(ma_5 > ma_20, 1,
                                               np.where(ma_5 < ma_20, -1, 0))
        else:
            features['market_regime'] = 0
        
        # 14. Days to holiday (aproximado)
        features['days_to_holiday'] = self._calculate_days_to_holiday(df.index)
        
        # 15. Model confidence
        features['model_confidence'] = self._calculate_model_confidence(df)
        
        # Fallbacks
        features['real_interest_rate'] = features['real_interest_rate'].fillna(4.0)
        features['uncertainty_indicator'] = features['uncertainty_indicator'].fillna(0.5)
        features['market_regime'] = features['market_regime'].fillna(0)
        features['days_to_holiday'] = features['days_to_holiday'].fillna(30)
        features['model_confidence'] = features['model_confidence'].fillna(0.7)
        
        logger.info(f"✅ Tier 3 features: {features.notna().sum().sum()}/{len(features)*5} valores válidos")
        
        return features

    def _calculate_trade_events_impact(self, date_index: pd.DatetimeIndex) -> pd.Series:
        """Calcular impacto de eventos comerciales próximos 7 días"""
        impact_series = pd.Series(0.0, index=date_index)
        
        if 'events' in self._data_cache:
            events = self._data_cache['events']
            
            for date in date_index:
                # Buscar eventos en próximos 7 días
                future_events = events[
                    (events.index >= date) & 
                    (events.index <= date + timedelta(days=7))
                ]
                
                if not future_events.empty:
                    # Sumar impactos con decay exponencial
                    total_impact = 0
                    for event_date, event in future_events.iterrows():
                        days_ahead = (event_date - date).days
                        decay_factor = np.exp(-days_ahead / 3)  # Decay 3 días
                        total_impact += event['impact'] * decay_factor
                    
                    impact_series[date] = total_impact
        
        return impact_series

    def _calculate_days_to_holiday(self, date_index: pd.DatetimeIndex) -> pd.Series:
        """Calcular días hasta próximo festivo"""
        days_series = pd.Series(30, index=date_index)  # Default 30 días
        
        if 'holidays' in self._data_cache:
            holidays = self._data_cache['holidays']
            # Buscar columna de holidays de México
            mx_holiday_col = None
            for col in holidays.columns:
                if 'mexico' in col.lower() or 'Mexico' in col:
                    mx_holiday_col = col
                    break
            
            if mx_holiday_col is not None:
                holiday_dates = holidays[holidays[mx_holiday_col] == True].index
            else:
                holiday_dates = pd.DatetimeIndex([])
            
            for date in date_index:
                future_holidays = holiday_dates[holiday_dates > date]
                if not future_holidays.empty:
                    days_to_next = (future_holidays[0] - date).days
                    days_series[date] = min(days_to_next, 30)  # Cap en 30 días
        
        return days_series

    def _calculate_model_confidence(self, df: pd.DataFrame) -> pd.Series:
        """Calcular confianza del modelo basada en disponibilidad de datos"""
        confidence_series = pd.Series(0.7, index=df.index)  # Default medium
        
        # Factores que afectan confianza
        for date in df.index:
            confidence = 0.7  # Base
            
            # +0.2 si datos LME frescos (no más de 1 día)
            if 'sr_m01' in df.columns and pd.notna(df.loc[date, 'sr_m01']):
                confidence += 0.15
            
            # +0.1 si datos FX frescos
            if 'usdmxn' in df.columns and pd.notna(df.loc[date, 'usdmxn']):
                confidence += 0.1
            
            # -0.2 si fin de semana o festivo
            if date.weekday() >= 5:
                confidence -= 0.1
            
            # -0.3 si alta volatilidad
            if 'sr_m01' in df.columns:
                recent_vol = df['sr_m01'].pct_change().rolling(5).std().loc[date]
                if pd.notna(recent_vol) and recent_vol > 0.03:  # >3% vol diaria
                    confidence -= 0.2
            
            confidence_series[date] = np.clip(confidence, 0.3, 0.95)
        
        return confidence_series

    def create_features_dataset(self, datasets: Dict) -> pd.DataFrame:
        """Pipeline completo: crear dataset final con 15 features"""
        logger.info("🚀 Iniciando pipeline completo de features...")
        
        # 1. Alinear datos temporalmente
        aligned_df = self.align_temporal_data(datasets)
        
        # 2. Aplicar imputación por días inhábiles
        imputed_df = self.apply_holiday_imputation(aligned_df)
        
        # 3. Crear features por tiers
        tier1_features = self.create_tier1_features(imputed_df)
        tier2_features = self.create_tier2_features(imputed_df)
        tier3_features = self.create_tier3_features(imputed_df)
        
        # 4. Combinar todos los features
        features_df = pd.concat([tier1_features, tier2_features, tier3_features], axis=1)
        
        # 5. Agregar columnas de holidays y transparencia
        holiday_cols = [c for c in imputed_df.columns if 'holiday' in c.lower() or 'weekend' in c.lower() or 'business_day' in c.lower()]
        if holiday_cols:
            features_df = features_df.join(imputed_df[holiday_cols])
            logger.info(f"✅ Columnas de calendario añadidas: {len(holiday_cols)}")
        
        # Agregar columnas _imputed para transparencia
        imputed_cols = [c for c in imputed_df.columns if '_imputed' in c]
        if imputed_cols:
            features_df = features_df.join(imputed_df[imputed_cols])
            logger.info(f"✅ Columnas de imputación añadidas: {len(imputed_cols)}")
        
        # 6. Agregar target (para entrenamiento)
        # Target = precio México día siguiente
        if 'sr_m01' in imputed_df.columns:
            features_df['target_mexico_price'] = (imputed_df['sr_m01'].shift(-1) * self.MEXICO_PREMIUM)
        
        # 7. Agregar metadata de calidad
        features_df['data_quality_score'] = self._calculate_data_quality_score(imputed_df)
        
        # 7. Eliminar filas con demasiados NaNs
        min_features_required = 10  # Al menos 10 de 15 features
        valid_rows = features_df.iloc[:, :15].notna().sum(axis=1) >= min_features_required
        features_df = features_df[valid_rows]
        
        logger.info(f"🎯 Dataset final creado:")
        logger.info(f"   - Período: {features_df.index.min()} a {features_df.index.max()}")
        logger.info(f"   - Registros válidos: {len(features_df)}")
        logger.info(f"   - Features: {features_df.columns.tolist()[:15]}")
        logger.info(f"   - Completitud promedio: {features_df.iloc[:, :15].notna().mean().mean():.2%}")
        
        return features_df

    def _calculate_data_quality_score(self, df: pd.DataFrame) -> pd.Series:
        """Calcular score de calidad de datos por día"""
        critical_columns = ['sr_m01', 'usdmxn']
        important_columns = ['tiie28', 'sc_m01']
        
        quality_score = pd.Series(0.0, index=df.index)
        
        for date in df.index:
            score = 0.0
            
            # 60% peso a columnas críticas
            for col in critical_columns:
                if col in df.columns and pd.notna(df.loc[date, col]):
                    score += 0.3  # 30% cada una
            
            # 40% peso a columnas importantes
            for col in important_columns:
                if col in df.columns and pd.notna(df.loc[date, col]):
                    score += 0.2  # 20% cada una
            
            quality_score[date] = score
        
        return quality_score

    def validate_features_quality(self, features_df: pd.DataFrame) -> Dict:
        """Validar calidad del dataset de features"""
        logger.info("🔍 Validando calidad de features...")
        
        validation_results = {
            'timestamp': datetime.now().isoformat(),
            'total_records': len(features_df),
            'date_range': {
                'start': features_df.index.min().isoformat(),
                'end': features_df.index.max().isoformat()
            },
            'feature_stats': {},
            'quality_summary': {}
        }
        
        # Estadísticas por feature
        feature_cols = features_df.columns[:15]  # Primeros 15 features
        
        for col in feature_cols:
            validation_results['feature_stats'][col] = {
                'completeness': features_df[col].notna().mean(),
                'mean': features_df[col].mean() if pd.api.types.is_numeric_dtype(features_df[col]) else None,
                'std': features_df[col].std() if pd.api.types.is_numeric_dtype(features_df[col]) else None,
                'outliers_pct': self._detect_outliers(features_df[col]) if pd.api.types.is_numeric_dtype(features_df[col]) else 0
            }
        
        # Resumen de calidad
        validation_results['quality_summary'] = {
            'avg_completeness': features_df[feature_cols].notna().mean().mean(),
            'critical_features_ok': all(features_df[col].notna().mean() > 0.8 for col in ['lme_sr_m01_lag1', 'usdmxn_lag1']),
            'recommended_for_training': validation_results['quality_summary'].get('avg_completeness', 0) > 0.75
        }
        
        logger.info(f"✅ Validación completada:")
        logger.info(f"   - Completitud promedio: {validation_results['quality_summary']['avg_completeness']:.2%}")
        logger.info(f"   - Features críticos OK: {validation_results['quality_summary']['critical_features_ok']}")
        
        return validation_results

    def _detect_outliers(self, series: pd.Series, method: str = 'iqr') -> float:
        """Detectar porcentaje de outliers usando IQR"""
        if series.empty or not pd.api.types.is_numeric_dtype(series):
            return 0.0
        
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outliers = (series < lower_bound) | (series > upper_bound)
        return outliers.mean()

    def save_features_dataset(self, features_df: pd.DataFrame, validation_results: Dict) -> str:
        """Guardar dataset de features con metadata"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Guardar dataset principal
        output_file = f"../outputs/features_dataset_{timestamp}.csv"
        features_df.to_csv(output_file)
        logger.info(f"💾 Dataset guardado: {output_file}")
        
        # Guardar validation report
        report_file = f"../outputs/features_validation_{timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump(validation_results, f, indent=2)
        logger.info(f"📊 Reporte validación: {report_file}")
        
        # Crear también versión latest
        latest_file = "../outputs/features_dataset_latest.csv"
        features_df.to_csv(latest_file)
        logger.info(f"💾 Latest version: {latest_file}")
        
        return output_file

def main():
    """Función principal para ejecutar el pipeline"""
    logger.info("🚀 Iniciando Robust Feature Pipeline...")
    
    try:
        # Inicializar pipeline
        pipeline = RobustFeaturePipeline()
        
        # Cargar todos los datos
        datasets = pipeline.load_data()
        
        # Crear dataset de features
        features_df = pipeline.create_features_dataset(datasets)
        
        # Validar calidad
        validation_results = pipeline.validate_features_quality(features_df)
        
        # Guardar resultados
        output_file = pipeline.save_features_dataset(features_df, validation_results)
        
        logger.info("✅ Pipeline completado exitosamente!")
        logger.info(f"📁 Archivo principal: {output_file}")
        logger.info(f"📊 Registros procesados: {len(features_df)}")
        
        # Preview del dataset
        print("\n🔍 PREVIEW DEL DATASET:")
        print("="*60)
        print(f"Período: {features_df.index.min()} a {features_df.index.max()}")
        print(f"Total registros: {len(features_df)}")
        print(f"Features: {list(features_df.columns[:15])}")
        print("\nÚltimos 5 registros (features críticos):")
        critical_features = ['lme_sr_m01_lag1', 'usdmxn_lag1', 'mexico_premium', 'lme_volatility_5d', 'model_confidence']
        print(features_df[critical_features].tail())
        
        return features_df, validation_results
        
    except Exception as e:
        logger.error(f"❌ Error en pipeline: {e}")
        raise

if __name__ == "__main__":
    features_df, validation_results = main()
