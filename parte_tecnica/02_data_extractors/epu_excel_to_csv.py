#!/usr/bin/env python3
"""
EPU Excel to CSV Converter
Convierte los archivos Excel de Economic Policy Uncertainty a formato CSV
Autor: CDO DeAcero Project
Fecha: 2025-09-28
"""

import pandas as pd
import os
import sys
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def convert_epu_file(input_file: str, output_dir: str) -> dict:
    """
    Convierte un archivo Excel de EPU a CSV
    
    Args:
        input_file: Ruta al archivo Excel
        output_dir: Directorio donde guardar el CSV
        
    Returns:
        Dict con información de la conversión
    """
    logger.info(f"Procesando: {os.path.basename(input_file)}")
    
    try:
        # Determinar el país basado en el nombre del archivo
        filename = os.path.basename(input_file)
        
        if "Mexico" in filename:
            country = "mexico"
        elif "US_Policy" in filename:
            country = "usa"
        elif "SCMP_China" in filename:
            country = "china"
        elif "ECSU" in filename:
            country = "turkey"
        else:
            country = "unknown"
        
        # Leer el archivo Excel
        # Para archivos .xls antiguos, especificar engine
        if input_file.endswith('.xls'):
            df = pd.read_excel(input_file, engine='xlrd')
        else:
            df = pd.read_excel(input_file)
        
        # Mostrar información del DataFrame
        logger.info(f"  - Forma: {df.shape}")
        logger.info(f"  - Columnas: {list(df.columns)}")
        
        # Limpiar nombres de columnas
        df.columns = [col.strip() for col in df.columns]
        
        # Buscar columna de fecha
        date_cols = [col for col in df.columns if 'date' in col.lower() or 'year' in col.lower() or 'month' in col.lower()]
        if date_cols:
            logger.info(f"  - Columna de fecha detectada: {date_cols[0]}")
        
        # Añadir timestamp de procesamiento
        df['fecha_procesamiento'] = datetime.now()
        df['archivo_origen'] = filename
        
        # Generar nombre de archivo de salida
        output_filename = f"epu_{country}_data.csv"
        output_path = os.path.join(output_dir, output_filename)
        
        # Guardar como CSV
        df.to_csv(output_path, index=False)
        logger.info(f"  - Guardado como: {output_filename}")
        
        # Estadísticas básicas
        stats = {
            'archivo': filename,
            'pais': country,
            'filas': len(df),
            'columnas': len(df.columns),
            'columnas_lista': list(df.columns),
            'archivo_salida': output_filename,
            'primera_fila': df.iloc[0].to_dict() if not df.empty else {},
            'ultima_fila': df.iloc[-1].to_dict() if not df.empty else {}
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error procesando {filename}: {e}")
        return {
            'archivo': filename,
            'error': str(e)
        }


def main():
    """Función principal"""
    print("=== EPU Excel to CSV Converter ===")
    print("Convirtiendo archivos de Economic Policy Uncertainty")
    print("="*50)
    
    # Directorios
    input_dir = "docs/sources/economic_policy_uncertainity"
    output_dir = "parte_tecnica/02_data_extractors/outputs"
    
    # Verificar que existe el directorio de entrada
    if not os.path.exists(input_dir):
        print(f"ERROR: No se encuentra el directorio {input_dir}")
        sys.exit(1)
    
    # Crear directorio de salida si no existe
    os.makedirs(output_dir, exist_ok=True)
    
    # Buscar archivos Excel
    excel_files = [f for f in os.listdir(input_dir) if f.endswith(('.xlsx', '.xls'))]
    
    if not excel_files:
        print("No se encontraron archivos Excel en el directorio")
        sys.exit(1)
    
    print(f"\nArchivos encontrados: {len(excel_files)}")
    for f in excel_files:
        print(f"  - {f}")
    
    print("\nIniciando conversión...")
    print("-"*50)
    
    # Procesar cada archivo
    all_stats = []
    for excel_file in excel_files:
        input_path = os.path.join(input_dir, excel_file)
        stats = convert_epu_file(input_path, output_dir)
        all_stats.append(stats)
        print()
    
    # Resumen final
    print("="*50)
    print("RESUMEN DE CONVERSIÓN")
    print("="*50)
    
    success_count = sum(1 for s in all_stats if 'error' not in s)
    error_count = len(all_stats) - success_count
    
    print(f"\nArchivos procesados exitosamente: {success_count}")
    print(f"Archivos con errores: {error_count}")
    
    if success_count > 0:
        print("\nArchivos CSV generados:")
        for stats in all_stats:
            if 'error' not in stats:
                print(f"  - {stats['archivo_salida']}: {stats['filas']} filas, {stats['columnas']} columnas")
    
    if error_count > 0:
        print("\nErrores encontrados:")
        for stats in all_stats:
            if 'error' in stats:
                print(f"  - {stats['archivo']}: {stats['error']}")
    
    # Generar reporte detallado
    report_file = os.path.join(output_dir, f"epu_conversion_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    with open(report_file, 'w') as f:
        f.write("=== REPORTE DETALLADO DE CONVERSIÓN EPU ===\n")
        f.write(f"Fecha: {datetime.now()}\n")
        f.write(f"Archivos procesados: {len(all_stats)}\n\n")
        
        for stats in all_stats:
            f.write(f"\n{'='*40}\n")
            f.write(f"Archivo: {stats['archivo']}\n")
            if 'error' not in stats:
                f.write(f"País: {stats['pais']}\n")
                f.write(f"Filas: {stats['filas']}\n")
                f.write(f"Columnas: {stats['columnas']}\n")
                f.write(f"Columnas: {', '.join(stats['columnas_lista'][:5])}")
                if len(stats['columnas_lista']) > 5:
                    f.write(f"... (y {len(stats['columnas_lista'])-5} más)")
                f.write("\n")
                f.write(f"Archivo de salida: {stats['archivo_salida']}\n")
            else:
                f.write(f"ERROR: {stats['error']}\n")
    
    print(f"\nReporte detallado guardado en: {report_file}")
    
    # Verificar si necesitamos instalar xlrd para archivos .xls
    try:
        import xlrd
    except ImportError:
        print("\n⚠️  NOTA: Para leer archivos .xls antiguos, instala xlrd:")
        print("    pip install xlrd")


if __name__ == "__main__":
    main()
