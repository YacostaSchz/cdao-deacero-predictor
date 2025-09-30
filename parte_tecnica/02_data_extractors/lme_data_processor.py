#!/usr/bin/env python3
"""
LME Data Processor
Procesa archivos de precios de cierre LME (Steel Rebar y Steel Scrap)
con estructura de contratos de futuros M01-M15
Autor: CDO DeAcero Project
Fecha: 2025-09-28
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os
import logging
from typing import Dict, List, Tuple

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LMEDataProcessor:
    """Procesador para datos LME con contratos de futuros"""
    
    def __init__(self, input_dir: str = "docs/sources/lme_closing prices",
                 output_dir: str = "parte_tecnica/02_data_extractors/outputs"):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.contract_columns = [f'M{i:02d}' for i in range(1, 16)]  # M01 a M15
        
    def process_lme_file(self, filename: str, commodity_type: str) -> pd.DataFrame:
        """
        Procesa un archivo individual de LME
        
        Args:
            filename: Nombre del archivo
            commodity_type: 'SR' para Steel Rebar o 'SC' para Steel Scrap
            
        Returns:
            DataFrame procesado
        """
        logger.info(f"\nProcesando archivo LME: {filename}")
        filepath = os.path.join(self.input_dir, filename)
        
        try:
            # Leer el archivo Excel
            df = pd.read_excel(filepath)
            logger.info(f"  - Forma original: {df.shape}")
            logger.info(f"  - Columnas encontradas: {list(df.columns)[:10]}...")
            
            # Buscar la columna de fecha
            date_col = None
            for col in df.columns:
                if 'date' in str(col).lower() or 'fecha' in str(col).lower():
                    date_col = col
                    break
            
            if date_col is None:
                # Si no hay columna con 'date', asumir que es la primera
                date_col = df.columns[0]
                logger.warning(f"  - No se encontró columna 'date', usando: {date_col}")
            
            logger.info(f"  - Columna de fecha: {date_col}")
            
            # Identificar columnas de contratos
            contract_cols_found = []
            for col in df.columns:
                if col in self.contract_columns:
                    contract_cols_found.append(col)
            
            logger.info(f"  - Contratos encontrados: {len(contract_cols_found)} ({contract_cols_found[:5]}...)")
            
            # Crear DataFrame limpio
            df_clean = pd.DataFrame()
            df_clean['date'] = pd.to_datetime(df[date_col], errors='coerce')
            
            # Copiar datos de contratos
            for contract in contract_cols_found:
                df_clean[contract] = pd.to_numeric(df[contract], errors='coerce')
            
            # Eliminar filas sin fecha válida
            df_clean = df_clean.dropna(subset=['date'])
            
            # Ordenar por fecha
            df_clean = df_clean.sort_values('date')
            
            # Añadir metadatos
            df_clean['commodity'] = commodity_type
            df_clean['year'] = df_clean['date'].dt.year
            df_clean['month'] = df_clean['date'].dt.month
            df_clean['fecha_procesamiento'] = datetime.now()
            
            # Calcular estadísticas de la curva de futuros
            df_clean['front_month'] = df_clean['M01']  # Contrato más cercano
            df_clean['back_month'] = df_clean['M03']   # Contrato a 3 meses
            
            # Contango/Backwardation
            df_clean['contango_3m'] = ((df_clean['M03'] - df_clean['M01']) / df_clean['M01'] * 100).round(2)
            df_clean['contango_6m'] = ((df_clean['M06'] - df_clean['M01']) / df_clean['M01'] * 100).round(2) if 'M06' in df_clean.columns else None
            
            # Spread entre contratos
            df_clean['spread_m1_m2'] = df_clean['M02'] - df_clean['M01'] if 'M02' in df_clean.columns else None
            df_clean['spread_m1_m3'] = df_clean['M03'] - df_clean['M01'] if 'M03' in df_clean.columns else None
            
            logger.info(f"  - Registros procesados: {len(df_clean)}")
            logger.info(f"  - Período: {df_clean['date'].min()} a {df_clean['date'].max()}")
            logger.info(f"  - Precio M01 promedio: ${df_clean['front_month'].mean():.2f} USD/ton")
            
            return df_clean
            
        except Exception as e:
            logger.error(f"Error procesando {filename}: {e}")
            raise
    
    def create_long_format(self, df_wide: pd.DataFrame, commodity_type: str) -> pd.DataFrame:
        """
        Convierte datos de formato ancho a largo para análisis temporal
        """
        # Columnas a mantener
        id_vars = ['date', 'commodity', 'year', 'month', 'fecha_procesamiento']
        
        # Columnas de contratos
        value_vars = [col for col in df_wide.columns if col.startswith('M') and len(col) == 3]
        
        # Reshape a formato largo
        df_long = pd.melt(
            df_wide,
            id_vars=id_vars,
            value_vars=value_vars,
            var_name='contract',
            value_name='price_usd_ton'
        )
        
        # Añadir meses hasta vencimiento
        df_long['months_to_maturity'] = df_long['contract'].str.extract('M(\d+)').astype(int)
        
        # Eliminar valores nulos
        df_long = df_long.dropna(subset=['price_usd_ton'])
        
        return df_long
    
    def analyze_term_structure(self, df: pd.DataFrame) -> Dict:
        """
        Analiza la estructura temporal de los futuros
        """
        # Obtener última fecha
        latest_date = df['date'].max()
        latest_data = df[df['date'] == latest_date].iloc[0]
        
        # Extraer curva de futuros
        contracts = [col for col in df.columns if col.startswith('M') and len(col) == 3]
        curve = []
        
        for contract in sorted(contracts):
            if contract in latest_data and pd.notna(latest_data[contract]):
                curve.append({
                    'contract': contract,
                    'months': int(contract[1:]),
                    'price': float(latest_data[contract])
                })
        
        # Calcular pendiente de la curva (regresión lineal simple)
        if len(curve) >= 2:
            x = [c['months'] for c in curve]
            y = [c['price'] for c in curve]
            slope = np.polyfit(x, y, 1)[0]
        else:
            slope = 0
        
        analysis = {
            'date': latest_date.strftime('%Y-%m-%d'),
            'front_month_price': float(latest_data['M01']) if 'M01' in latest_data else None,
            'curve_slope': slope,
            'contango': slope > 0,
            'term_structure': curve
        }
        
        return analysis
    
    def process_all(self):
        """Procesa todos los archivos LME"""
        logger.info("="*60)
        logger.info("PROCESADOR DE DATOS LME")
        logger.info("="*60)
        
        # Archivos a procesar
        files_to_process = [
            ("SR Closing Prices.xlsx", "SR", "Steel Rebar"),
            ("SC Closing Prices.xlsx", "SC", "Steel Scrap")
        ]
        
        all_results = {}
        
        for filename, commodity_code, commodity_name in files_to_process:
            logger.info(f"\nProcesando {commodity_name} ({commodity_code})")
            logger.info("-"*40)
            
            try:
                # Procesar archivo
                df_wide = self.process_lme_file(filename, commodity_code)
                
                # Guardar formato ancho
                output_wide = os.path.join(self.output_dir, f"lme_{commodity_code.lower()}_wide.csv")
                df_wide.to_csv(output_wide, index=False)
                logger.info(f"  ✅ Formato ancho guardado: {output_wide}")
                
                # Crear y guardar formato largo
                df_long = self.create_long_format(df_wide, commodity_code)
                output_long = os.path.join(self.output_dir, f"lme_{commodity_code.lower()}_long.csv")
                df_long.to_csv(output_long, index=False)
                logger.info(f"  ✅ Formato largo guardado: {output_long}")
                
                # Analizar estructura temporal
                term_analysis = self.analyze_term_structure(df_wide)
                logger.info(f"\n  📊 Análisis de estructura temporal (última fecha: {term_analysis['date']}):")
                logger.info(f"    - Precio front month (M01): ${term_analysis['front_month_price']:.2f} USD/ton")
                logger.info(f"    - Pendiente de la curva: {term_analysis['curve_slope']:.2f}")
                logger.info(f"    - Estado del mercado: {'Contango' if term_analysis['contango'] else 'Backwardation'}")
                
                # Guardar análisis
                all_results[commodity_code] = {
                    'df_wide': df_wide,
                    'df_long': df_long,
                    'term_analysis': term_analysis,
                    'stats': {
                        'total_records': len(df_wide),
                        'date_range': f"{df_wide['date'].min()} to {df_wide['date'].max()}",
                        'avg_front_month': df_wide['M01'].mean(),
                        'volatility_front_month': df_wide['M01'].std()
                    }
                }
                
                # Mostrar muestra de datos
                logger.info(f"\n  📋 Muestra de datos procesados:")
                print(df_wide[['date', 'M01', 'M03', 'M06', 'contango_3m']].tail())
                
            except Exception as e:
                logger.error(f"❌ Error procesando {filename}: {e}")
                continue
        
        # Crear dataset combinado SR-SC
        if 'SR' in all_results and 'SC' in all_results:
            logger.info("\n" + "="*60)
            logger.info("CREANDO DATASET COMBINADO SR-SC")
            logger.info("="*60)
            
            df_sr = all_results['SR']['df_wide'][['date', 'M01']].rename(columns={'M01': 'sr_m01'})
            df_sc = all_results['SC']['df_wide'][['date', 'M01']].rename(columns={'M01': 'sc_m01'})
            
            # Merge por fecha
            df_combined = pd.merge(df_sr, df_sc, on='date', how='inner')
            
            # Calcular spread Rebar-Scrap
            df_combined['rebar_scrap_spread'] = df_combined['sr_m01'] - df_combined['sc_m01']
            df_combined['rebar_scrap_ratio'] = df_combined['sr_m01'] / df_combined['sc_m01']
            
            # Guardar
            output_combined = os.path.join(self.output_dir, "lme_combined_sr_sc.csv")
            df_combined.to_csv(output_combined, index=False)
            logger.info(f"✅ Dataset combinado guardado: {output_combined}")
            logger.info(f"   - Registros: {len(df_combined)}")
            logger.info(f"   - Spread promedio SR-SC: ${df_combined['rebar_scrap_spread'].mean():.2f} USD/ton")
            
            # Mostrar últimos registros
            logger.info("\n📋 Últimos registros del dataset combinado:")
            print(df_combined.tail())
        
        # Generar reporte final
        self.generate_report(all_results)
        
        return all_results
    
    def generate_report(self, results: Dict):
        """Genera reporte de procesamiento"""
        report_path = os.path.join(self.output_dir, f"lme_processing_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        
        with open(report_path, 'w') as f:
            f.write("=== REPORTE DE PROCESAMIENTO LME ===\n")
            f.write(f"Fecha: {datetime.now()}\n")
            f.write(f"Archivos procesados: {len(results)}\n\n")
            
            for commodity, data in results.items():
                f.write(f"\n{'='*40}\n")
                f.write(f"Commodity: {commodity}\n")
                f.write(f"Registros: {data['stats']['total_records']}\n")
                f.write(f"Período: {data['stats']['date_range']}\n")
                f.write(f"Precio M01 promedio: ${data['stats']['avg_front_month']:.2f} USD/ton\n")
                f.write(f"Volatilidad M01: ${data['stats']['volatility_front_month']:.2f}\n")
                f.write(f"Último precio M01: ${data['term_analysis']['front_month_price']:.2f}\n")
                f.write(f"Estado del mercado: {'Contango' if data['term_analysis']['contango'] else 'Backwardation'}\n")
        
        logger.info(f"\n📄 Reporte guardado en: {report_path}")


def main():
    """Función principal"""
    processor = LMEDataProcessor()
    results = processor.process_all()
    
    logger.info("\n" + "="*60)
    logger.info("PROCESAMIENTO COMPLETADO")
    logger.info("="*60)
    
    # Resumen final
    for commodity, data in results.items():
        logger.info(f"\n{commodity}: {data['stats']['total_records']} registros procesados")
        logger.info(f"  - Último precio: ${data['term_analysis']['front_month_price']:.2f} USD/ton")


if __name__ == "__main__":
    main()
