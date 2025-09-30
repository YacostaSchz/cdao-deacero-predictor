#!/usr/bin/env python3
"""
Analizador de Días Inhábiles Multi-País para Imputación de Datos
Cubre: México, USA, UK (LME), China, Turquía
Período: 2015-2026
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import logging
from typing import Dict, List, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class HolidayCalendarAnalyzer:
    """Analiza y gestiona días inhábiles para múltiples países"""
    
    def __init__(self):
        self.countries = ['Mexico', 'USA', 'UK', 'China', 'Turkey']
        self.start_date = datetime(2015, 1, 1)
        self.end_date = datetime(2026, 12, 31)
        self.holidays = {}
        
    def get_mexico_holidays(self) -> Dict[int, List[datetime]]:
        """Días festivos oficiales de México (bancarios)"""
        holidays = {}
        
        for year in range(2015, 2027):
            holidays[year] = [
                # Fijos
                datetime(year, 1, 1),    # Año Nuevo
                datetime(year, 2, 5) if year >= 2024 else self._get_first_monday_february(year),  # Constitución
                datetime(year, 3, 18) if year >= 2024 else self._get_third_monday_march(year),    # Benito Juárez
                datetime(year, 5, 1),    # Día del Trabajo
                datetime(year, 9, 16),   # Independencia
                datetime(year, 11, 18) if year >= 2024 else self._get_third_monday_november(year), # Revolución
                datetime(year, 12, 25),  # Navidad
                
                # Variables (aproximados - Semana Santa)
                self._get_good_friday(year),
                self._get_holy_thursday(year),
            ]
            
            # Día de muertos (bancario solo si cae entre semana)
            nov2 = datetime(year, 11, 2)
            if nov2.weekday() < 5:  # Lunes a Viernes
                holidays[year].append(nov2)
                
        return holidays
    
    def get_usa_holidays(self) -> Dict[int, List[datetime]]:
        """Días festivos de USA (mercados cerrados)"""
        holidays = {}
        
        for year in range(2015, 2027):
            holidays[year] = [
                datetime(year, 1, 1),    # New Year
                self._get_mlk_day(year), # MLK Day (3rd Monday Jan)
                self._get_presidents_day(year), # Presidents Day (3rd Monday Feb)
                self._get_good_friday(year),    # Good Friday
                self._get_memorial_day(year),   # Memorial Day (last Monday May)
                datetime(year, 7, 4),    # Independence Day
                self._get_labor_day(year),      # Labor Day (1st Monday Sep)
                self._get_thanksgiving(year),   # Thanksgiving (4th Thursday Nov)
                datetime(year, 12, 25),  # Christmas
            ]
            
            # Ajustes cuando cae en fin de semana
            holidays[year] = self._adjust_weekend_holidays_usa(holidays[year])
            
        return holidays
    
    def get_uk_holidays(self) -> Dict[int, List[datetime]]:
        """Días festivos UK (LME cerrado)"""
        holidays = {}
        
        for year in range(2015, 2027):
            holidays[year] = [
                datetime(year, 1, 1),    # New Year
                self._get_good_friday(year),
                self._get_easter_monday(year),
                self._get_early_may_bank(year),    # First Monday May
                self._get_spring_bank(year),       # Last Monday May
                self._get_summer_bank(year),       # Last Monday August
                datetime(year, 12, 25),  # Christmas
                datetime(year, 12, 26),  # Boxing Day
            ]
            
            # Ajustes especiales (ej. Jubileo de la Reina)
            if year == 2022:
                holidays[year].extend([
                    datetime(2022, 6, 2),  # Spring bank holiday moved
                    datetime(2022, 6, 3),  # Platinum Jubilee
                ])
                
        return holidays
    
    def get_china_holidays(self) -> Dict[int, List[datetime]]:
        """Días festivos de China (aproximados - varían por calendario lunar)"""
        holidays = {}
        
        # Fechas aproximadas del Año Nuevo Chino (Spring Festival)
        chinese_new_year = {
            2015: datetime(2015, 2, 19),
            2016: datetime(2016, 2, 8),
            2017: datetime(2017, 1, 28),
            2018: datetime(2018, 2, 16),
            2019: datetime(2019, 2, 5),
            2020: datetime(2020, 1, 25),
            2021: datetime(2021, 2, 12),
            2022: datetime(2022, 2, 1),
            2023: datetime(2023, 1, 22),
            2024: datetime(2024, 2, 10),
            2025: datetime(2025, 1, 29),
            2026: datetime(2026, 2, 17),
        }
        
        for year in range(2015, 2027):
            holidays[year] = [
                datetime(year, 1, 1),    # New Year
                datetime(year, 5, 1),    # Labour Day
                datetime(year, 10, 1),   # National Day
            ]
            
            # Año Nuevo Chino (típicamente 7 días)
            if year in chinese_new_year:
                cny_start = chinese_new_year[year]
                for i in range(7):
                    holidays[year].append(cny_start + timedelta(days=i))
                    
            # Golden Week (1-7 octubre)
            for i in range(2, 8):
                holidays[year].append(datetime(year, 10, i))
                
        return holidays
    
    def get_turkey_holidays(self) -> Dict[int, List[datetime]]:
        """Días festivos de Turquía"""
        holidays = {}
        
        for year in range(2015, 2027):
            holidays[year] = [
                datetime(year, 1, 1),    # New Year
                datetime(year, 4, 23),   # National Sovereignty Day
                datetime(year, 5, 1),    # Labour Day
                datetime(year, 5, 19),   # Youth Day
                datetime(year, 8, 30),   # Victory Day
                datetime(year, 10, 29),  # Republic Day
            ]
            
            # Festividades religiosas (aproximadas - calendario lunar)
            # Estas fechas son aproximadas y varían cada año
            
        return holidays
    
    def _get_good_friday(self, year: int) -> datetime:
        """Calcula Viernes Santo usando algoritmo de Gauss"""
        # Implementación simplificada - en producción usar biblioteca especializada
        easter_dates = {
            2015: datetime(2015, 4, 3),
            2016: datetime(2016, 3, 25),
            2017: datetime(2017, 4, 14),
            2018: datetime(2018, 3, 30),
            2019: datetime(2019, 4, 19),
            2020: datetime(2020, 4, 10),
            2021: datetime(2021, 4, 2),
            2022: datetime(2022, 4, 15),
            2023: datetime(2023, 4, 7),
            2024: datetime(2024, 3, 29),
            2025: datetime(2025, 4, 18),
            2026: datetime(2026, 4, 3),
        }
        return easter_dates.get(year, datetime(year, 4, 1))
    
    def _get_holy_thursday(self, year: int) -> datetime:
        """Jueves Santo = Viernes Santo - 1 día"""
        return self._get_good_friday(year) - timedelta(days=1)
    
    def _get_easter_monday(self, year: int) -> datetime:
        """Lunes de Pascua = Viernes Santo + 3 días"""
        return self._get_good_friday(year) + timedelta(days=3)
    
    def _get_first_monday_february(self, year: int) -> datetime:
        """Primer lunes de febrero"""
        first_day = datetime(year, 2, 1)
        days_ahead = 0 - first_day.weekday()  # Monday is 0
        if days_ahead <= 0:
            days_ahead += 7
        return first_day + timedelta(days=days_ahead)
    
    def _get_third_monday_march(self, year: int) -> datetime:
        """Tercer lunes de marzo"""
        first_day = datetime(year, 3, 1)
        first_monday = first_day + timedelta(days=(7 - first_day.weekday()) % 7)
        return first_monday + timedelta(days=14)
    
    def _get_third_monday_november(self, year: int) -> datetime:
        """Tercer lunes de noviembre"""
        first_day = datetime(year, 11, 1)
        first_monday = first_day + timedelta(days=(7 - first_day.weekday()) % 7)
        return first_monday + timedelta(days=14)
    
    def _get_mlk_day(self, year: int) -> datetime:
        """MLK Day - Tercer lunes de enero"""
        first_day = datetime(year, 1, 1)
        first_monday = first_day + timedelta(days=(7 - first_day.weekday()) % 7)
        return first_monday + timedelta(days=14)
    
    def _get_presidents_day(self, year: int) -> datetime:
        """Presidents Day - Tercer lunes de febrero"""
        return self._get_first_monday_february(year) + timedelta(days=14)
    
    def _get_memorial_day(self, year: int) -> datetime:
        """Memorial Day - Último lunes de mayo"""
        last_day = datetime(year, 5, 31)
        offset = (last_day.weekday() - 0) % 7
        return last_day - timedelta(days=offset)
    
    def _get_labor_day(self, year: int) -> datetime:
        """Labor Day USA - Primer lunes de septiembre"""
        first_day = datetime(year, 9, 1)
        days_ahead = 0 - first_day.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return first_day + timedelta(days=days_ahead)
    
    def _get_thanksgiving(self, year: int) -> datetime:
        """Thanksgiving - Cuarto jueves de noviembre"""
        first_day = datetime(year, 11, 1)
        first_thursday = first_day + timedelta(days=(3 - first_day.weekday()) % 7)
        return first_thursday + timedelta(days=21)
    
    def _get_early_may_bank(self, year: int) -> datetime:
        """Early May Bank Holiday UK - Primer lunes de mayo"""
        first_day = datetime(year, 5, 1)
        days_ahead = 0 - first_day.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return first_day + timedelta(days=days_ahead)
    
    def _get_spring_bank(self, year: int) -> datetime:
        """Spring Bank Holiday UK - Último lunes de mayo"""
        return self._get_memorial_day(year)  # Mismo cálculo
    
    def _get_summer_bank(self, year: int) -> datetime:
        """Summer Bank Holiday UK - Último lunes de agosto"""
        last_day = datetime(year, 8, 31)
        offset = (last_day.weekday() - 0) % 7
        return last_day - timedelta(days=offset)
    
    def _adjust_weekend_holidays_usa(self, holidays: List[datetime]) -> List[datetime]:
        """Ajusta holidays que caen en fin de semana (reglas USA)"""
        adjusted = []
        for holiday in holidays:
            if holiday.weekday() == 5:  # Saturday
                adjusted.append(holiday - timedelta(days=1))  # Friday
            elif holiday.weekday() == 6:  # Sunday
                adjusted.append(holiday + timedelta(days=1))  # Monday
            else:
                adjusted.append(holiday)
        return adjusted
    
    def analyze_holidays(self):
        """Analiza todos los días inhábiles"""
        logging.info("=== ANÁLISIS DE DÍAS INHÁBILES 2015-2026 ===")
        
        # Recopilar holidays por país
        self.holidays = {
            'Mexico': self.get_mexico_holidays(),
            'USA': self.get_usa_holidays(),
            'UK': self.get_uk_holidays(),
            'China': self.get_china_holidays(),
            'Turkey': self.get_turkey_holidays()
        }
        
        # Análisis por país
        summary = {}
        for country, holidays_by_year in self.holidays.items():
            total_holidays = sum(len(holidays) for holidays in holidays_by_year.values())
            avg_per_year = total_holidays / len(holidays_by_year)
            
            summary[country] = {
                'total_holidays': total_holidays,
                'avg_per_year': round(avg_per_year, 1),
                'years': list(holidays_by_year.keys())
            }
            
            logging.info(f"\n{country}:")
            logging.info(f"  - Total días inhábiles: {total_holidays}")
            logging.info(f"  - Promedio anual: {avg_per_year:.1f}")
            
        # Crear calendario maestro
        self.create_master_calendar()
        
        # Proponer estrategias de imputación
        self.propose_imputation_strategies()
        
        return summary
    
    def create_master_calendar(self):
        """Crea calendario consolidado de días hábiles/inhábiles"""
        logging.info("\n=== CREANDO CALENDARIO MAESTRO ===")
        
        # Crear DataFrame con todos los días
        date_range = pd.date_range(self.start_date, self.end_date, freq='D')
        calendar_df = pd.DataFrame(index=date_range)
        
        # Marcar fines de semana
        calendar_df['is_weekend'] = calendar_df.index.weekday >= 5
        
        # Marcar holidays por país
        for country, holidays_by_year in self.holidays.items():
            country_holidays = []
            for year_holidays in holidays_by_year.values():
                country_holidays.extend(year_holidays)
            
            calendar_df[f'{country}_holiday'] = calendar_df.index.isin(country_holidays)
            calendar_df[f'{country}_business_day'] = ~(calendar_df['is_weekend'] | calendar_df[f'{country}_holiday'])
        
        # Guardar calendario
        output_path = 'parte_tecnica/03_feature_engineering/outputs/holiday_calendar_2015_2026.csv'
        calendar_df.to_csv(output_path)
        logging.info(f"Calendario guardado en: {output_path}")
        
        # Análisis de coincidencias
        logging.info("\n📊 Análisis de Coincidencias:")
        
        # Días donde todos los mercados están cerrados
        all_closed = calendar_df[
            ~calendar_df['Mexico_business_day'] & 
            ~calendar_df['USA_business_day'] & 
            ~calendar_df['UK_business_day']
        ]
        logging.info(f"  - Días con TODOS los mercados cerrados: {len(all_closed)}")
        
        # Días donde México está abierto pero LME cerrado
        mx_open_lme_closed = calendar_df[
            calendar_df['Mexico_business_day'] & 
            ~calendar_df['UK_business_day']
        ]
        logging.info(f"  - México abierto, LME cerrado: {len(mx_open_lme_closed)}")
        
        return calendar_df
    
    def propose_imputation_strategies(self):
        """Propone estrategias de imputación por tipo de dato"""
        logging.info("\n=== ESTRATEGIAS DE IMPUTACIÓN PROPUESTAS ===")
        
        strategies = {
            "LME_STEEL_REBAR": {
                "source": "UK holidays",
                "frequency": "daily",
                "strategy": "LOCF (Last Observation Carried Forward)",
                "justification": "Precios de cierre se mantienen hasta siguiente día hábil",
                "max_carry_days": 4,
                "alternative": "Interpolación lineal si gap > 4 días"
            },
            "BANXICO_FX": {
                "source": "Mexico holidays", 
                "frequency": "daily",
                "strategy": "LOCF para fines de semana, interpolación para holidays largos",
                "justification": "FIX publicado todos los días hábiles bancarios",
                "max_carry_days": 3,
                "weekend_strategy": "Viernes se extiende a sábado/domingo"
            },
            "EPU_INDICES": {
                "source": "Múltiples países",
                "frequency": "monthly",
                "strategy": "No requiere imputación diaria",
                "justification": "Datos mensuales no afectados por días inhábiles",
                "consideration": "Publicación puede retrasarse por holidays"
            },
            "GAS_NATURAL": {
                "source": "Mexico holidays",
                "frequency": "monthly", 
                "strategy": "No requiere imputación diaria",
                "justification": "Índice mensual"
            },
            "CROSS_MARKET": {
                "scenario": "México abierto, LME cerrado",
                "strategy": "Usar último precio LME + ajuste por movimiento FX",
                "formula": "LME_t = LME_t-1 * (1 + β * ΔUSDMXN)",
                "beta_estimated": 0.15,
                "justification": "Captura efecto de movimientos cambiarios en ausencia de precio LME"
            }
        }
        
        # Guardar estrategias
        output_path = 'parte_tecnica/03_feature_engineering/outputs/imputation_strategies.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(strategies, f, indent=2, ensure_ascii=False)
            
        logging.info("Estrategias guardadas en: " + output_path)
        
        # Implementación práctica
        logging.info("\n📋 IMPLEMENTACIÓN PRÁCTICA:")
        logging.info("""
1. **Fin de Semana Estándar**:
   - LME: Viernes → Sábado, Domingo, Lunes
   - Banxico: Viernes → Sábado, Domingo
   - Imputación: LOCF (carry forward)

2. **Holidays Largos (>3 días)**:
   - Interpolación lineal entre último conocido y primer valor post-holiday
   - Validar contra movimientos extremos (>2σ)

3. **Asincronía de Mercados**:
   - Si México abierto y LME cerrado: 
     * Usar modelo de ajuste por FX
     * Flag en dataset: 'lme_imputed' = True
   
4. **Validación Post-Imputación**:
   - Comparar valores imputados vs reales cuando estén disponibles
   - Calcular RMSE de imputación para calibrar modelos
        """)
        
        return strategies
    
    def create_imputation_example(self):
        """Crea ejemplo práctico de imputación"""
        logging.info("\n=== EJEMPLO DE IMPUTACIÓN ===")
        
        # Caso: Semana Santa 2024
        example_dates = pd.date_range('2024-03-25', '2024-04-01', freq='D')
        example_df = pd.DataFrame(index=example_dates)
        
        # Datos simulados
        example_df['LME_SR_actual'] = [540.5, 541.2, 542.0, np.nan, np.nan, np.nan, np.nan, 545.0]
        example_df['USDMXN_actual'] = [16.80, 16.82, 16.85, 16.83, np.nan, np.nan, np.nan, 16.90]
        
        # Aplicar LOCF
        example_df['LME_SR_imputed'] = example_df['LME_SR_actual'].fillna(method='ffill')
        example_df['USDMXN_imputed'] = example_df['USDMXN_actual'].fillna(method='ffill')
        
        # Interpolación alternativa
        example_df['LME_SR_interpolated'] = example_df['LME_SR_actual'].interpolate(method='linear')
        
        logging.info("\nEjemplo Semana Santa 2024:")
        logging.info(example_df)
        
        return example_df


def main():
    analyzer = HolidayCalendarAnalyzer()
    
    # Analizar holidays
    summary = analyzer.analyze_holidays()
    
    # Crear ejemplo
    analyzer.create_imputation_example()
    
    # Resumen ejecutivo
    logging.info("\n=== RESUMEN EJECUTIVO ===")
    logging.info("""
📅 CALENDARIO DE DÍAS INHÁBILES 2015-2026

Mercados Principales:
- México: ~12 días festivos/año + fines de semana
- USA: ~10 días festivos/año + fines de semana  
- UK (LME): ~8 días festivos/año + fines de semana
- China: ~21 días festivos/año (incluye Golden Weeks)

Estrategia Recomendada:
1. LOCF para gaps ≤ 3 días
2. Interpolación lineal para gaps > 3 días
3. Ajuste por FX cuando hay asincronía México/LME
4. Flags de imputación para transparencia

Archivos Generados:
- holiday_calendar_2015_2026.csv
- imputation_strategies.json
    """)


if __name__ == "__main__":
    main()
