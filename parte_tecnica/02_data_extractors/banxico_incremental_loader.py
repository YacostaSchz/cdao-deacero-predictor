#!/usr/bin/env python3
"""
Banxico Incremental Loader
Script para carga incremental de datos del SIE de Banco de México
Detecta últimos datos cargados y descarga solo los nuevos
Autor: CDO DeAcero Project
Fecha: 2025-09-28
"""

import pandas as pd
import os
import json
from datetime import datetime, timedelta
from banxico_downloader import BanxicoDownloader
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BanxicoIncrementalLoader:
    """
    Clase para manejar cargas incrementales de datos de Banxico
    """
    
    def __init__(self, data_dir: str = "parte_tecnica/02_data_extractors/outputs"):
        """
        Inicializa el loader incremental
        
        Args:
            data_dir: Directorio donde se almacenan los datos
        """
        self.data_dir = data_dir
        self.downloader = BanxicoDownloader()
        self.incremental_log_file = os.path.join(data_dir, "incremental_load_log.json")
        self.load_history = self._load_history()
        
    def _load_history(self) -> dict:
        """Carga el historial de cargas incrementales"""
        if os.path.exists(self.incremental_log_file):
            with open(self.incremental_log_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_history(self):
        """Guarda el historial de cargas incrementales"""
        with open(self.incremental_log_file, 'w') as f:
            json.dump(self.load_history, f, indent=2, default=str)
    
    def get_last_date_loaded(self, serie_id: str) -> datetime:
        """
        Obtiene la última fecha cargada para una serie
        
        Args:
            serie_id: ID de la serie
            
        Returns:
            Última fecha cargada o fecha por defecto (2015-01-01)
        """
        # Buscar en archivos existentes
        csv_file = os.path.join(self.data_dir, f"{serie_id}_data.csv")
        
        if os.path.exists(csv_file):
            try:
                df = pd.read_csv(csv_file)
                if not df.empty and 'fecha' in df.columns:
                    # Convertir fecha a datetime
                    df['fecha'] = pd.to_datetime(df['fecha'])
                    last_date = df['fecha'].max()
                    logger.info(f"Última fecha en archivo para {serie_id}: {last_date}")
                    return last_date
            except Exception as e:
                logger.error(f"Error leyendo archivo {csv_file}: {e}")
        
        # Si no hay archivo o error, usar fecha por defecto
        default_date = datetime(2015, 1, 1)
        logger.info(f"No se encontró archivo para {serie_id}. Usando fecha por defecto: {default_date}")
        return default_date
    
    def incremental_download(self, full_reload: bool = False) -> dict:
        """
        Realiza descarga incremental de todas las series
        
        Args:
            full_reload: Si True, recarga todos los datos desde 2015
            
        Returns:
            Dict con estadísticas de la carga
        """
        logger.info("=== INICIANDO CARGA INCREMENTAL ===")
        logger.info(f"Timestamp: {datetime.now()}")
        
        stats = {
            'timestamp': datetime.now(),
            'series_updated': {},
            'total_new_records': 0,
            'errors': []
        }
        
        # Obtener metadatos de todas las series
        logger.info("Verificando periodicidad de series...")
        periodicidades = self.downloader.check_all_periodicities()
        
        for serie_id in self.downloader.series.keys():
            try:
                logger.info(f"\nProcesando serie {serie_id}...")
                
                if full_reload:
                    start_date = datetime(2015, 1, 1)
                    logger.info(f"Full reload solicitado. Descargando desde {start_date}")
                else:
                    # Obtener última fecha cargada
                    last_date = self.get_last_date_loaded(serie_id)
                    # Comenzar desde el día siguiente
                    start_date = last_date + timedelta(days=1)
                
                end_date = datetime.now()
                
                # Si ya tenemos datos hasta hoy, saltar
                if start_date > end_date:
                    logger.info(f"{serie_id}: Ya está actualizado hasta {last_date.date()}")
                    stats['series_updated'][serie_id] = {
                        'status': 'up_to_date',
                        'last_date': last_date,
                        'new_records': 0
                    }
                    continue
                
                # Descargar datos nuevos
                logger.info(f"Descargando desde {start_date.date()} hasta {end_date.date()}")
                df_new = self.downloader.download_range(
                    serie_id, 
                    start_date.strftime("%Y-%m-%d"),
                    end_date.strftime("%Y-%m-%d")
                )
                
                if df_new.empty:
                    logger.info(f"{serie_id}: No hay datos nuevos disponibles")
                    stats['series_updated'][serie_id] = {
                        'status': 'no_new_data',
                        'last_date': last_date if not full_reload else None,
                        'new_records': 0
                    }
                    continue
                
                # Cargar datos existentes si no es full reload
                if not full_reload and os.path.exists(os.path.join(self.data_dir, f"{serie_id}_data.csv")):
                    df_existing = pd.read_csv(os.path.join(self.data_dir, f"{serie_id}_data.csv"))
                    df_existing['fecha'] = pd.to_datetime(df_existing['fecha'])
                    
                    # Combinar datos existentes con nuevos
                    df_combined = pd.concat([df_existing, df_new], ignore_index=True)
                    # Eliminar duplicados por fecha
                    df_combined = df_combined.drop_duplicates(subset=['fecha'], keep='last')
                    df_combined = df_combined.sort_values('fecha')
                else:
                    df_combined = df_new
                
                # Guardar datos actualizados
                output_file = os.path.join(self.data_dir, f"{serie_id}_data.csv")
                df_combined.to_csv(output_file, index=False)
                
                new_records = len(df_new)
                stats['series_updated'][serie_id] = {
                    'status': 'updated',
                    'start_date': start_date,
                    'end_date': end_date,
                    'new_records': new_records,
                    'total_records': len(df_combined)
                }
                stats['total_new_records'] += new_records
                
                logger.info(f"{serie_id}: {new_records} nuevos registros añadidos")
                
            except Exception as e:
                logger.error(f"Error procesando {serie_id}: {e}")
                stats['errors'].append({
                    'serie_id': serie_id,
                    'error': str(e)
                })
        
        # Actualizar dataset consolidado
        try:
            logger.info("\nActualizando dataset consolidado...")
            self._update_consolidated_dataset()
        except Exception as e:
            logger.error(f"Error actualizando dataset consolidado: {e}")
            stats['errors'].append({
                'serie_id': 'consolidated',
                'error': str(e)
            })
        
        # Guardar historial
        self.load_history[datetime.now().isoformat()] = stats
        self._save_history()
        
        # Generar reporte
        self._generate_report(stats)
        
        return stats
    
    def _update_consolidated_dataset(self):
        """Actualiza el dataset consolidado con todos los datos"""
        dfs_to_merge = []
        
        for serie_id in self.downloader.series.keys():
            csv_file = os.path.join(self.data_dir, f"{serie_id}_data.csv")
            if os.path.exists(csv_file):
                df = pd.read_csv(csv_file)
                df['fecha'] = pd.to_datetime(df['fecha'])
                df_pivot = df.pivot(index='fecha', columns='serie_id', values='valor')
                dfs_to_merge.append(df_pivot)
        
        if dfs_to_merge:
            df_consolidated = pd.concat(dfs_to_merge, axis=1)
            output_file = os.path.join(self.data_dir, "banxico_consolidated_data.csv")
            df_consolidated.to_csv(output_file)
            logger.info(f"Dataset consolidado actualizado: {len(df_consolidated)} filas")
    
    def _generate_report(self, stats: dict):
        """Genera reporte de la carga incremental"""
        report_file = os.path.join(self.data_dir, f"incremental_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        
        with open(report_file, 'w') as f:
            f.write("=== REPORTE DE CARGA INCREMENTAL ===\n")
            f.write(f"Timestamp: {stats['timestamp']}\n")
            f.write(f"Total nuevos registros: {stats['total_new_records']}\n\n")
            
            f.write("Series actualizadas:\n")
            for serie_id, info in stats['series_updated'].items():
                f.write(f"\n{serie_id}:\n")
                for key, value in info.items():
                    f.write(f"  {key}: {value}\n")
            
            if stats['errors']:
                f.write("\nErrores encontrados:\n")
                for error in stats['errors']:
                    f.write(f"  - {error['serie_id']}: {error['error']}\n")
        
        logger.info(f"Reporte guardado en: {report_file}")
        
        # Imprimir resumen
        print("\n=== RESUMEN DE CARGA INCREMENTAL ===")
        print(f"Total nuevos registros: {stats['total_new_records']}")
        print(f"Series actualizadas: {sum(1 for s in stats['series_updated'].values() if s['status'] == 'updated')}")
        print(f"Series sin cambios: {sum(1 for s in stats['series_updated'].values() if s['status'] == 'up_to_date')}")
        print(f"Errores: {len(stats['errors'])}")


def main():
    """Función principal"""
    print("=== Banxico Incremental Loader ===")
    print("Sistema de carga incremental de datos")
    print("="*40)
    
    loader = BanxicoIncrementalLoader()
    
    print("\nOpciones:")
    print("1. Carga incremental (solo datos nuevos)")
    print("2. Recarga completa desde 2015")
    print("3. Ver historial de cargas")
    
    opcion = input("\nSeleccione opción (1-3): ")
    
    if opcion == "1":
        print("\nIniciando carga incremental...")
        stats = loader.incremental_download(full_reload=False)
        
    elif opcion == "2":
        print("\nIniciando recarga completa desde 2015...")
        confirmar = input("¿Está seguro? Esto sobrescribirá todos los datos (s/n): ")
        if confirmar.lower() == 's':
            stats = loader.incremental_download(full_reload=True)
        else:
            print("Operación cancelada")
            
    elif opcion == "3":
        print("\n=== HISTORIAL DE CARGAS ===")
        if loader.load_history:
            for timestamp, info in sorted(loader.load_history.items(), reverse=True)[:10]:
                print(f"\n{timestamp}:")
                print(f"  Total registros nuevos: {info.get('total_new_records', 0)}")
                print(f"  Series actualizadas: {len(info.get('series_updated', {}))}")
        else:
            print("No hay historial de cargas disponible")
    
    else:
        print("Opción no válida")


if __name__ == "__main__":
    main()
