#!/usr/bin/env python3
"""
Macro Data Fetcher - Descargador Consolidado de Datos Macroeconómicos
Integra todas las fuentes disponibles para el modelo de predicción de precios de varilla corrugada
Autor: CDO DeAcero Project
Fecha: 2025-09-28
"""

import os
import sys
import time
import json
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

# Importar el downloader de Banxico existente
from banxico_downloader import BanxicoDownloader

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MacroDataFetcher:
    """
    Clase consolidadora para descargar todos los datos macroeconómicos necesarios
    para el modelo de predicción de precios de varilla corrugada
    """
    
    def __init__(self):
        """Inicializa el fetcher con configuraciones de APIs"""
        # Tokens y configuraciones
        self.fred_key = os.getenv('FRED_API_KEY', '')
        self.banxico_downloader = BanxicoDownloader()
        
        # Directorios de salida
        self.output_dir = "parte_tecnica/02_data_extractors/outputs"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Calibración crítica del proyecto
        self.MEXICO_LME_SPREAD = 1.157  # 15.7% premium confirmado Sept 2025
        self.REFERENCE_PRICE_MEXICO = 625  # USD/ton (26-sep-2025)
        self.REFERENCE_PRICE_LME = 540.50  # USD/ton (26-sep-2025)
    
    def download_banxico_data(self, start_date: str = "2025-01-01") -> Dict[str, pd.DataFrame]:
        """
        Descarga datos de Banxico usando el downloader existente
        
        Returns:
            Dict con DataFrames de cada serie
        """
        logger.info("=== Descargando datos de Banxico ===")
        
        # Usar el downloader existente
        try:
            # Verificar periodicidad primero
            periodicidades = self.banxico_downloader.check_all_periodicities()
            logger.info(f"Periodicidades verificadas: {len(periodicidades)} series")
            
            # Descargar datos
            data = self.banxico_downloader.download_strategic(
                full_history=(start_date < "2025-01-01")
            )
            
            logger.info(f"✅ Banxico: {len(data)} series descargadas")
            return data
            
        except Exception as e:
            logger.error(f"Error descargando Banxico: {e}")
            return {}
    
    def download_epu_indices(self) -> Dict[str, pd.DataFrame]:
        """
        Descarga índices de incertidumbre económica (EPU)
        
        Returns:
            Dict con DataFrames de cada país
        """
        logger.info("=== Descargando índices EPU ===")
        
        epu_sources = {
            'mexico': "https://www.policyuncertainty.com/media/Mexico_Policy_Uncertainty_Data.xlsx",
            'usa': "https://www.policyuncertainty.com/media/US_Policy_Uncertainty_Data.xlsx",
            'china': "https://www.policyuncertainty.com/media/China_Policy_Uncertainty_Data.xlsx",
            'turkey': "https://www.policyuncertainty.com/media/Turkey_EPU_Data.xlsx"
        }
        
        epu_data = {}
        
        for country, url in epu_sources.items():
            try:
                logger.info(f"Descargando EPU {country}...")
                df = pd.read_excel(url)
                
                # Guardar localmente
                output_file = f"{self.output_dir}/epu_{country}.csv"
                df.to_csv(output_file, index=False)
                
                epu_data[f'epu_{country}'] = df
                logger.info(f"✅ EPU {country}: {len(df)} observaciones")
                
            except Exception as e:
                logger.error(f"Error descargando EPU {country}: {e}")
            
            time.sleep(1)  # Ser cortés con los servidores
        
        return epu_data
    
    def download_world_bank_commodities(self) -> pd.DataFrame:
        """
        Descarga Pink Sheet del World Bank con precios de commodities
        
        Returns:
            DataFrame con precios mensuales de commodities
        """
        logger.info("=== Descargando World Bank Commodities ===")
        
        wb_url = "https://thedocs.worldbank.org/en/doc/5d903e848db1d1b83e0ec8f744e55570-0350012021/related/CMO-Historical-Data-Monthly.xlsx"
        
        try:
            logger.info("Descargando Pink Sheet...")
            df = pd.read_excel(wb_url, sheet_name='Monthly Prices')
            
            # Filtrar commodities relevantes
            relevant_commodities = [
                'Steel rebar',
                'Iron ore, cfr spot',
                'Crude oil, Brent',
                'Coal, Australian',
                'Natural gas, US',
                'Natural gas, Europe',
                'Copper',
                'Aluminum'
            ]
            
            # Buscar columnas que contengan estos nombres
            cols_to_keep = ['Month']
            for commodity in relevant_commodities:
                matching_cols = [col for col in df.columns if commodity.lower() in col.lower()]
                cols_to_keep.extend(matching_cols)
            
            # Filtrar DataFrame
            df_filtered = df[cols_to_keep].copy()
            
            # Guardar
            output_file = f"{self.output_dir}/world_bank_commodities.csv"
            df_filtered.to_csv(output_file, index=False)
            
            logger.info(f"✅ World Bank: {len(df_filtered)} meses, {len(df_filtered.columns)} series")
            return df_filtered
            
        except Exception as e:
            logger.error(f"Error descargando World Bank commodities: {e}")
            return pd.DataFrame()
    
    def download_fred_data(self) -> Dict[str, pd.DataFrame]:
        """
        Descarga datos de FRED API (requiere API key)
        
        Returns:
            Dict con series de FRED
        """
        logger.info("=== Descargando datos de FRED ===")
        
        if not self.fred_key:
            logger.warning("⚠️ FRED_API_KEY no configurada. Saltando descarga de FRED.")
            logger.info("Para obtener una key gratuita: https://fred.stlouisfed.org/docs/api/api_key.html")
            return {}
        
        try:
            from fredapi import Fred
            fred = Fred(api_key=self.fred_key)
            
            fred_series = {
                'DFF': 'Federal Funds Rate',
                'CPIAUCSL': 'Consumer Price Index USA',
                'DGS10': '10-Year Treasury Rate',
                'DEXMXUS': 'Mexico/US Exchange Rate'
            }
            
            fred_data = {}
            start_date = '2015-01-01'
            
            for series_id, description in fred_series.items():
                try:
                    logger.info(f"Descargando {series_id}: {description}")
                    data = fred.get_series(series_id, start_date=start_date)
                    
                    # Convertir a DataFrame
                    df = pd.DataFrame({
                        'date': data.index,
                        series_id: data.values
                    })
                    
                    # Guardar
                    output_file = f"{self.output_dir}/fred_{series_id}.csv"
                    df.to_csv(output_file, index=False)
                    
                    fred_data[series_id] = df
                    logger.info(f"✅ FRED {series_id}: {len(df)} observaciones")
                    
                except Exception as e:
                    logger.error(f"Error descargando {series_id}: {e}")
                
                time.sleep(0.5)  # Respetar límites de API
            
            return fred_data
            
        except ImportError:
            logger.error("❌ fredapi no instalado. Ejecutar: pip install fredapi")
            return {}
        except Exception as e:
            logger.error(f"Error con FRED API: {e}")
            return {}
    
    def load_lme_data(self) -> Dict[str, pd.DataFrame]:
        """
        Carga datos LME desde archivos Excel locales
        
        Returns:
            Dict con datos de contratos SR y SC
        """
        logger.info("=== Cargando datos LME locales ===")
        
        lme_files = {
            'rebar': 'docs/sources/lme_closing prices/SR Closing Prices.xlsx',
            'scrap': 'docs/sources/lme_closing prices/SC Closing Prices.xlsx'
        }
        
        lme_data = {}
        
        for metal, filepath in lme_files.items():
            try:
                if os.path.exists(filepath):
                    logger.info(f"Cargando LME {metal.upper()}...")
                    df = pd.read_excel(filepath)
                    
                    # Guardar como CSV para fácil acceso
                    output_file = f"{self.output_dir}/lme_{metal}.csv"
                    df.to_csv(output_file, index=False)
                    
                    lme_data[f'lme_{metal}'] = df
                    logger.info(f"✅ LME {metal}: {len(df)} observaciones, {len(df.columns)} columnas")
                else:
                    logger.warning(f"⚠️ Archivo LME no encontrado: {filepath}")
                    
            except Exception as e:
                logger.error(f"Error cargando LME {metal}: {e}")
        
        return lme_data
    
    def create_consolidated_dataset(self, all_data: Dict) -> pd.DataFrame:
        """
        Crea dataset consolidado alineando todas las fuentes por fecha
        
        Args:
            all_data: Diccionario con todos los DataFrames descargados
            
        Returns:
            DataFrame consolidado
        """
        logger.info("=== Creando dataset consolidado ===")
        
        # Identificar columnas de fecha en cada dataset
        date_columns = {
            'banxico': 'fecha',
            'epu': 'Date',
            'world_bank': 'Month',
            'fred': 'date',
            'lme': 'Date'
        }
        
        # TODO: Implementar lógica de consolidación compleja
        # Por ahora, crear resumen de disponibilidad
        
        summary = []
        for source_name, df_dict in all_data.items():
            if isinstance(df_dict, dict):
                for series_name, df in df_dict.items():
                    if isinstance(df, pd.DataFrame) and not df.empty:
                        summary.append({
                            'fuente': source_name,
                            'serie': series_name,
                            'observaciones': len(df),
                            'columnas': len(df.columns),
                            'primera_fecha': df.iloc[0, 0] if len(df.columns) > 0 else 'N/A',
                            'ultima_fecha': df.iloc[-1, 0] if len(df.columns) > 0 else 'N/A'
                        })
        
        df_summary = pd.DataFrame(summary)
        
        # Guardar resumen
        summary_file = f"{self.output_dir}/data_availability_summary.csv"
        df_summary.to_csv(summary_file, index=False)
        
        logger.info(f"✅ Resumen de disponibilidad guardado: {summary_file}")
        print("\nResumen de datos disponibles:")
        print(df_summary)
        
        return df_summary
    
    def generate_download_report(self, all_data: Dict) -> Dict:
        """
        Genera reporte de descarga con estadísticas y validaciones
        
        Args:
            all_data: Todos los datos descargados
            
        Returns:
            Dict con métricas del reporte
        """
        logger.info("=== Generando reporte de descarga ===")
        
        report = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'calibracion': {
                'precio_mexico_referencia': self.REFERENCE_PRICE_MEXICO,
                'precio_lme_referencia': self.REFERENCE_PRICE_LME,
                'spread_confirmado': self.MEXICO_LME_SPREAD,
                'fecha_referencia': '2025-09-26'
            },
            'fuentes_descargadas': {},
            'archivos_generados': []
        }
        
        # Contar datos por fuente
        for source_name, data in all_data.items():
            if isinstance(data, dict):
                report['fuentes_descargadas'][source_name] = {
                    'series': len(data),
                    'total_observaciones': sum(len(df) for df in data.values() if isinstance(df, pd.DataFrame))
                }
        
        # Listar archivos generados
        if os.path.exists(self.output_dir):
            report['archivos_generados'] = [
                f for f in os.listdir(self.output_dir) 
                if f.endswith(('.csv', '.json'))
            ]
        
        # Guardar reporte
        report_file = f"{self.output_dir}/download_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Reporte guardado: {report_file}")
        
        return report
    
    def fetch_all_macro_data(self, include_fred: bool = True) -> Dict:
        """
        Descarga todos los datos macro necesarios para el modelo
        
        Args:
            include_fred: Si incluir datos de FRED (requiere API key)
            
        Returns:
            Dict con todos los datos descargados
        """
        logger.info("=== INICIANDO DESCARGA COMPLETA DE DATOS MACRO ===")
        logger.info(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Calibración: México {self.REFERENCE_PRICE_MEXICO} vs LME {self.REFERENCE_PRICE_LME} = {self.MEXICO_LME_SPREAD}")
        
        all_data = {}
        
        # 1. Banxico (siempre disponible)
        banxico_data = self.download_banxico_data()
        if banxico_data:
            all_data['banxico'] = banxico_data
        
        # 2. LME (archivos locales)
        lme_data = self.load_lme_data()
        if lme_data:
            all_data['lme'] = lme_data
        
        # 3. EPU indices (descarga directa)
        epu_data = self.download_epu_indices()
        if epu_data:
            all_data['epu'] = epu_data
        
        # 4. World Bank commodities
        wb_data = self.download_world_bank_commodities()
        if not wb_data.empty:
            all_data['world_bank'] = {'commodities': wb_data}
        
        # 5. FRED (opcional, requiere API key)
        if include_fred:
            fred_data = self.download_fred_data()
            if fred_data:
                all_data['fred'] = fred_data
        
        # 6. Crear dataset consolidado
        self.create_consolidated_dataset(all_data)
        
        # 7. Generar reporte
        report = self.generate_download_report(all_data)
        
        logger.info("=== DESCARGA COMPLETA FINALIZADA ===")
        logger.info(f"Total fuentes: {len(all_data)}")
        logger.info(f"Archivos generados: {len(report['archivos_generados'])}")
        
        return all_data


def main():
    """Función principal para ejecutar el fetcher"""
    print("=== Macro Data Fetcher - CDO DeAcero ===")
    print("Descargador consolidado de datos macroeconómicos")
    print("Fecha:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*50)
    
    # Verificar configuración
    print("\n📋 Verificando configuración...")
    fred_configured = bool(os.getenv('FRED_API_KEY'))
    print(f"FRED API Key: {'✅ Configurada' if fred_configured else '❌ No configurada'}")
    
    if not fred_configured:
        print("\n💡 Para obtener una FRED API key gratuita:")
        print("1. Visitar: https://fred.stlouisfed.org/docs/api/api_key.html")
        print("2. Registrarse (instantáneo)")
        print("3. Ejecutar: export FRED_API_KEY='tu_key_aqui'")
    
    # Menú de opciones
    print("\n🔧 Opciones de descarga:")
    print("1. Descarga completa (todas las fuentes)")
    print("2. Solo Banxico + LME (sin FRED)")
    print("3. Solo EPU indices")
    print("4. Solo World Bank commodities")
    print("5. Verificar archivos LME locales")
    
    opcion = input("\nSeleccione opción (1-5): ")
    
    # Inicializar fetcher
    fetcher = MacroDataFetcher()
    
    if opcion == "1":
        print("\n🚀 Iniciando descarga completa...")
        if not fred_configured:
            print("⚠️ FRED se omitirá (no hay API key)")
        data = fetcher.fetch_all_macro_data(include_fred=fred_configured)
        print(f"\n✅ Descarga completa. {len(data)} fuentes procesadas.")
        
    elif opcion == "2":
        print("\n🚀 Descargando Banxico + LME...")
        data = {}
        data['banxico'] = fetcher.download_banxico_data()
        data['lme'] = fetcher.load_lme_data()
        fetcher.create_consolidated_dataset(data)
        fetcher.generate_download_report(data)
        print("\n✅ Descarga Banxico + LME completada.")
        
    elif opcion == "3":
        print("\n🚀 Descargando EPU indices...")
        epu_data = fetcher.download_epu_indices()
        print(f"\n✅ {len(epu_data)} índices EPU descargados.")
        
    elif opcion == "4":
        print("\n🚀 Descargando World Bank commodities...")
        wb_data = fetcher.download_world_bank_commodities()
        if not wb_data.empty:
            print(f"\n✅ World Bank: {len(wb_data)} observaciones descargadas.")
        
    elif opcion == "5":
        print("\n🔍 Verificando archivos LME locales...")
        lme_data = fetcher.load_lme_data()
        if lme_data:
            print("\n✅ Archivos LME encontrados y procesados:")
            for name, df in lme_data.items():
                print(f"  - {name}: {len(df)} filas, {len(df.columns)} columnas")
        else:
            print("\n❌ No se encontraron archivos LME")
    
    else:
        print("Opción no válida")
    
    print(f"\n📁 Archivos guardados en: {fetcher.output_dir}/")
    print("\n🎯 Próximos pasos:")
    print("1. Revisar archivos en outputs/")
    print("2. Validar calibración con spread 15.7%")
    print("3. Integrar en pipeline de features para modelo")


if __name__ == "__main__":
    main()
