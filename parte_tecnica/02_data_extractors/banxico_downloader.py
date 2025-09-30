#!/usr/bin/env python3
"""
Banxico SIE API Downloader
Implementa la estrategia de descarga de datos macroeconómicos desde Banco de México
Autor: CDO DeAcero Project
Fecha: 2025-09-28
"""

import requests
import pandas as pd
import json
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BanxicoDownloader:
    """
    Clase para descargar datos del Sistema de Información Económica (SIE) de Banco de México
    Implementa la estrategia de descarga con prioridad de periodicidad y límites de API
    """
    
    def __init__(self, token: Optional[str] = None):
        """
        Inicializa el downloader con token de autenticación
        
        Args:
            token: Token de 64 caracteres de Banxico. Si no se proporciona, 
                   intenta cargarlo desde archivo
        """
        if token is None:
            token = self._load_token_from_file()
        
        self.token = token
        self.base_url = "https://www.banxico.org.mx/SieAPIRest/service/v1"
        self.headers = {
            "Accept": "application/json",
            "Bmx-Token": token
        }
        
        # Series objetivo para el proyecto - ACTUALIZADAS con series vigentes
        self.series = {
            "SF43718": "Tipo de cambio FIX peso/dólar (diaria)",
            "SP1": "INPC General - Índice de precios al consumidor",
            "SF43783": "TIIE a 28 días (diaria)",
            "SR16734": "Indicador global de actividad económica (IGAE)",
            "SP74665": "Inflación no subyacente anual"
        }
        
        # Series descontinuadas (para referencia histórica si se necesitan)
        self.series_historicas = {
            "SP9709": "Índice de precios varilla corrugada (hasta 2011)",
            "SP67487": "INPP histórico (hasta 2011)",
            "SP66938": "INPC histórico (hasta 2011)",
            "SP66321": "TIIE histórica (hasta 2011)",
            "SP68002": "Actividad industrial histórica (hasta 2011)"
        }
        
        # Contadores para respetar límites
        self.request_count = 0
        self.last_reset_time = datetime.now()
        
    def _load_token_from_file(self) -> str:
        """Carga el token desde el archivo sie.txt"""
        token_file = "docs/sources/banxico-sie/sie.txt"
        try:
            with open(token_file, "r") as f:
                lines = f.readlines()
                token = lines[0].split(":")[1].strip()
                logger.info(f"Token cargado desde {token_file}")
                return token
        except Exception as e:
            logger.error(f"Error cargando token: {e}")
            raise ValueError("No se pudo cargar el token de autenticación")
    
    def _check_rate_limits(self):
        """
        Verifica y respeta los límites de API
        - Datos históricos: 200 consultas en 5 minutos
        """
        current_time = datetime.now()
        time_diff = (current_time - self.last_reset_time).total_seconds()
        
        # Reset contador cada 5 minutos
        if time_diff > 300:  # 5 minutos
            self.request_count = 0
            self.last_reset_time = current_time
            logger.info("Contador de requests reseteado")
        
        # Si alcanzamos el límite, esperar
        if self.request_count >= 195:  # Margen de seguridad
            wait_time = 300 - time_diff
            logger.warning(f"Límite de API alcanzado. Esperando {wait_time:.0f} segundos...")
            time.sleep(wait_time + 1)
            self.request_count = 0
            self.last_reset_time = datetime.now()
    
    def get_series_metadata(self, serie_id: str) -> Dict:
        """
        Obtiene metadatos de una serie incluyendo periodicidad
        
        Args:
            serie_id: Identificador de la serie (ej: SP9709)
            
        Returns:
            Dict con metadatos de la serie
        """
        self._check_rate_limits()
        
        url = f"{self.base_url}/series/{serie_id}?locale=es"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            self.request_count += 1
            
            data = response.json()
            serie_info = data['bmx']['series'][0]
            
            metadata = {
                'id': serie_info.get('idSerie'),
                'titulo': serie_info.get('titulo'),
                'periodicidad': serie_info.get('periodicidad', 'No especificada'),
                'unidad': serie_info.get('unidad'),
                'fecha_inicio': serie_info.get('fechaInicio'),
                'fecha_fin': serie_info.get('fechaFin')
            }
            
            logger.info(f"Metadatos obtenidos para {serie_id}: {metadata['periodicidad']}")
            return metadata
            
        except Exception as e:
            logger.error(f"Error obteniendo metadatos de {serie_id}: {e}")
            return {}
    
    def download_range(self, serie_id: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Descarga datos de una serie en un rango de fechas
        
        Args:
            serie_id: Identificador de la serie
            start_date: Fecha inicio (YYYY-MM-DD)
            end_date: Fecha fin (YYYY-MM-DD)
            
        Returns:
            DataFrame con los datos descargados
        """
        self._check_rate_limits()
        
        url = f"{self.base_url}/series/{serie_id}/datos/{start_date}/{end_date}"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            self.request_count += 1
            
            data = response.json()
            serie_data = data['bmx']['series'][0]
            
            # Convertir a DataFrame
            df_data = []
            fecha_descarga = datetime.now()
            
            for obs in serie_data['datos']:
                df_data.append({
                    'serie_id': serie_id,
                    'fecha': obs['fecha'],
                    'valor': float(obs['dato']) if obs['dato'] != 'N/E' else None,
                    'fecha_descarga': fecha_descarga
                })
            
            df = pd.DataFrame(df_data)
            
            # Convertir fecha a datetime
            df['fecha'] = pd.to_datetime(df['fecha'], format='%d/%m/%Y')
            
            logger.info(f"Descargados {len(df)} registros para {serie_id}")
            return df
            
        except Exception as e:
            logger.error(f"Error descargando datos de {serie_id}: {e}")
            return pd.DataFrame()
    
    def check_all_periodicities(self) -> pd.DataFrame:
        """
        Verifica la periodicidad de todas las series objetivo
        
        Returns:
            DataFrame con información de periodicidad de cada serie
        """
        periodicidad_info = []
        
        for serie_id, descripcion in self.series.items():
            metadata = self.get_series_metadata(serie_id)
            
            if metadata:
                periodicidad_info.append({
                    'serie_id': serie_id,
                    'descripcion': descripcion,
                    'titulo_oficial': metadata.get('titulo'),
                    'periodicidad': metadata.get('periodicidad'),
                    'unidad': metadata.get('unidad'),
                    'fecha_inicio': metadata.get('fecha_inicio'),
                    'fecha_fin': metadata.get('fecha_fin')
                })
            
            time.sleep(0.5)  # Pausa conservadora entre requests
        
        df_periodicidad = pd.DataFrame(periodicidad_info)
        
        # Guardar reporte
        output_dir = "parte_tecnica/02_data_extractors/outputs"
        os.makedirs(output_dir, exist_ok=True)
        
        df_periodicidad.to_csv(f"{output_dir}/banxico_series_periodicidad.csv", index=False)
        logger.info(f"Reporte de periodicidad guardado en {output_dir}/banxico_series_periodicidad.csv")
        
        return df_periodicidad
    
    def download_strategic(self, full_history: bool = False) -> Dict[str, pd.DataFrame]:
        """
        Implementa la estrategia de descarga según la prioridad definida
        
        Args:
            full_history: Si True, descarga desde 2015. Si False, solo desde 2025
            
        Returns:
            Diccionario con DataFrames por cada serie
        """
        # Definir rangos según estrategia
        if full_history:
            start_date = "2015-01-01"
            logger.info("Descarga COMPLETA: datos desde 2015")
        else:
            start_date = "2025-01-01"
            logger.info("Descarga INICIAL: solo datos desde 2025")
        
        end_date = datetime.now().strftime("%Y-%m-%d")
        
        # Primero verificar periodicidades
        logger.info("Verificando periodicidad de las series...")
        periodicidades = self.check_all_periodicities()
        print("\nPeriodicidad de las series:")
        print(periodicidades[['serie_id', 'descripcion', 'periodicidad']])
        
        # Descargar datos
        results = {}
        
        for serie_id in self.series.keys():
            logger.info(f"\nDescargando {serie_id} - {self.series[serie_id]}")
            
            df = self.download_range(serie_id, start_date, end_date)
            
            if not df.empty:
                results[serie_id] = df
                
                # Guardar CSV individual
                output_file = f"parte_tecnica/02_data_extractors/outputs/{serie_id}_data.csv"
                df.to_csv(output_file, index=False)
                logger.info(f"Datos guardados en {output_file}")
            
            # Pausa entre series
            time.sleep(1.5)
        
        # Crear dataset consolidado
        self._create_consolidated_dataset(results)
        
        return results
    
    def _create_consolidated_dataset(self, data_dict: Dict[str, pd.DataFrame]):
        """
        Crea un dataset consolidado con todas las series alineadas por fecha
        
        Args:
            data_dict: Diccionario con DataFrames de cada serie
        """
        if not data_dict:
            logger.warning("No hay datos para consolidar")
            return
        
        # Preparar DataFrames para merge
        dfs_to_merge = []
        
        for serie_id, df in data_dict.items():
            df_pivot = df.pivot(index='fecha', columns='serie_id', values='valor')
            dfs_to_merge.append(df_pivot)
        
        # Merge todos los DataFrames
        if dfs_to_merge:
            df_consolidated = pd.concat(dfs_to_merge, axis=1)
            
            # Información sobre periodicidad
            df_consolidated_info = pd.DataFrame({
                'total_obs': df_consolidated.count(),
                'primera_fecha': df_consolidated.apply(lambda x: x.first_valid_index()),
                'ultima_fecha': df_consolidated.apply(lambda x: x.last_valid_index()),
                'pct_missing': (df_consolidated.isna().sum() / len(df_consolidated) * 100).round(2)
            })
            
            # Guardar dataset consolidado
            output_file = "parte_tecnica/02_data_extractors/outputs/banxico_consolidated_data.csv"
            df_consolidated.to_csv(output_file)
            logger.info(f"Dataset consolidado guardado en {output_file}")
            
            # Guardar resumen
            info_file = "parte_tecnica/02_data_extractors/outputs/banxico_consolidated_info.csv"
            df_consolidated_info.to_csv(info_file)
            
            print("\nResumen del dataset consolidado:")
            print(df_consolidated_info)
    
    def get_latest_values(self) -> pd.DataFrame:
        """
        Obtiene solo los valores más recientes (dato oportuno) de cada serie
        
        Returns:
            DataFrame con los valores más recientes
        """
        latest_values = []
        
        for serie_id, descripcion in self.series.items():
            self._check_rate_limits()
            
            url = f"{self.base_url}/series/{serie_id}/datos/oportuno"
            try:
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()
                self.request_count += 1
                
                data = response.json()
                serie_data = data['bmx']['series'][0]
                
                if serie_data['datos']:
                    latest_obs = serie_data['datos'][0]
                    latest_values.append({
                        'serie_id': serie_id,
                        'descripcion': descripcion,
                        'fecha': latest_obs['fecha'],
                        'valor': latest_obs['dato'],
                        'fecha_descarga': datetime.now()
                    })
                
            except Exception as e:
                logger.error(f"Error obteniendo dato oportuno de {serie_id}: {e}")
            
            time.sleep(0.5)
        
        df_latest = pd.DataFrame(latest_values)
        
        # Guardar reporte
        output_file = "parte_tecnica/02_data_extractors/outputs/banxico_latest_values.csv"
        df_latest.to_csv(output_file, index=False)
        logger.info(f"Valores más recientes guardados en {output_file}")
        
        return df_latest


def main():
    """Función principal para ejecutar el downloader"""
    print("=== Banxico SIE Data Downloader ===")
    print("Proyecto: Predicción de Precios de Varilla Corrugada")
    print("Fecha:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*40)
    
    # Inicializar downloader
    downloader = BanxicoDownloader()
    
    # Menú de opciones
    print("\nOpciones de descarga:")
    print("1. Verificar periodicidad de las series")
    print("2. Obtener valores más recientes (dato oportuno)")
    print("3. Descarga inicial (solo 2025)")
    print("4. Descarga completa (desde 2015)")
    print("5. Ejecutar todo (recomendado para primera vez)")
    
    opcion = input("\nSeleccione opción (1-5): ")
    
    if opcion == "1":
        print("\nVerificando periodicidad...")
        periodicidades = downloader.check_all_periodicities()
        print("\nResultados guardados en outputs/banxico_series_periodicidad.csv")
        
    elif opcion == "2":
        print("\nObteniendo valores más recientes...")
        latest = downloader.get_latest_values()
        print("\nValores más recientes:")
        print(latest)
        
    elif opcion == "3":
        print("\nIniciando descarga inicial (2025)...")
        data = downloader.download_strategic(full_history=False)
        print(f"\nDescarga completada. {len(data)} series procesadas.")
        
    elif opcion == "4":
        print("\nIniciando descarga completa (desde 2015)...")
        print("ADVERTENCIA: Esto puede tomar varios minutos.")
        confirmar = input("¿Continuar? (s/n): ")
        if confirmar.lower() == 's':
            data = downloader.download_strategic(full_history=True)
            print(f"\nDescarga completada. {len(data)} series procesadas.")
        
    elif opcion == "5":
        print("\nEjecutando análisis completo...")
        
        # 1. Verificar periodicidad
        print("\n[1/3] Verificando periodicidad...")
        periodicidades = downloader.check_all_periodicities()
        
        # 2. Obtener valores recientes
        print("\n[2/3] Obteniendo valores más recientes...")
        latest = downloader.get_latest_values()
        
        # 3. Descarga inicial
        print("\n[3/3] Descargando datos desde 2025...")
        data = downloader.download_strategic(full_history=False)
        
        print("\n✅ Análisis completo finalizado!")
        print(f"Archivos guardados en: parte_tecnica/02_data_extractors/outputs/")
    
    else:
        print("Opción no válida")


if __name__ == "__main__":
    main()
