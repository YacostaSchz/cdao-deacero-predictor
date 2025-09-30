#!/usr/bin/env python3
"""
Limpiador específico para datos EPU de Turquía
Procesa el archivo ECSU_Index.xls con formato especial
Autor: CDO DeAcero Project
Fecha: 2025-09-28
"""

import pandas as pd
import numpy as np
from datetime import datetime
import logging
import os

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def clean_turkey_epu():
    """
    Limpia y procesa el archivo EPU de Turquía con formato especial
    """
    logger.info("=== Limpieza de datos EPU Turquía ===")
    
    # Rutas
    input_file = "docs/sources/economic_policy_uncertainity/ECSU_Index.xls"
    output_file = "parte_tecnica/02_data_extractors/outputs/epu_turkey_clean.csv"
    
    try:
        # Leer el archivo Excel con xlrd
        logger.info(f"Leyendo archivo: {input_file}")
        df_raw = pd.read_excel(input_file, engine='xlrd')
        
        # Mostrar las primeras filas para entender la estructura
        logger.info("Primeras 5 filas del archivo:")
        for i in range(min(5, len(df_raw))):
            logger.info(f"  Fila {i}: {df_raw.iloc[i].values}")
        
        # El archivo tiene estructura especial:
        # - Primera fila contiene "date" y "ECSU" en las primeras columnas
        # - Las siguientes filas contienen los datos
        
        # Buscar la fila donde empiezan los datos reales
        data_start_row = None
        for i, row in df_raw.iterrows():
            if pd.notna(row.iloc[0]) and str(row.iloc[0]).strip().lower() == 'date':
                data_start_row = i + 1
                break
        
        if data_start_row is None:
            logger.warning("No se encontró la fila de encabezados 'date'. Intentando método alternativo...")
            # Buscar primera fecha válida
            for i, row in df_raw.iterrows():
                try:
                    # Si la primera columna parece una fecha
                    if pd.to_datetime(str(row.iloc[0]), errors='coerce') is not pd.NaT:
                        data_start_row = i
                        break
                except:
                    continue
        
        if data_start_row is None:
            raise ValueError("No se pudo encontrar el inicio de los datos")
        
        logger.info(f"Los datos empiezan en la fila {data_start_row}")
        
        # Extraer solo las primeras dos columnas relevantes (fecha y valor ECSU)
        df_clean = pd.DataFrame({
            'date': df_raw.iloc[data_start_row:, 0],
            'ecsu_index': df_raw.iloc[data_start_row:, 1]
        })
        
        # Limpiar datos
        df_clean = df_clean.dropna(subset=['date', 'ecsu_index'])
        
        # Convertir fecha a datetime
        df_clean['date'] = pd.to_datetime(df_clean['date'], errors='coerce')
        df_clean = df_clean.dropna(subset=['date'])
        
        # Convertir índice a numérico
        df_clean['ecsu_index'] = pd.to_numeric(df_clean['ecsu_index'], errors='coerce')
        df_clean = df_clean.dropna(subset=['ecsu_index'])
        
        # Ordenar por fecha
        df_clean = df_clean.sort_values('date')
        
        # Extraer componentes de fecha
        df_clean['year'] = df_clean['date'].dt.year
        df_clean['month'] = df_clean['date'].dt.month
        df_clean['year_month'] = df_clean['date'].dt.strftime('%Y-%m')
        
        # Añadir metadata
        df_clean['country'] = 'turkey'
        df_clean['source'] = 'ECSU'
        df_clean['fecha_procesamiento'] = datetime.now()
        
        # Reordenar columnas
        df_clean = df_clean[['date', 'year', 'month', 'year_month', 
                           'ecsu_index', 'country', 'source', 'fecha_procesamiento']]
        
        # Estadísticas
        logger.info(f"\nEstadísticas del dataset limpio:")
        logger.info(f"  - Registros totales: {len(df_clean)}")
        logger.info(f"  - Período: {df_clean['date'].min()} a {df_clean['date'].max()}")
        logger.info(f"  - Valor mínimo: {df_clean['ecsu_index'].min():.2f}")
        logger.info(f"  - Valor máximo: {df_clean['ecsu_index'].max():.2f}")
        logger.info(f"  - Valor promedio: {df_clean['ecsu_index'].mean():.2f}")
        logger.info(f"  - Desviación estándar: {df_clean['ecsu_index'].std():.2f}")
        
        # Verificar consistencia temporal
        df_clean['date_diff'] = df_clean['date'].diff()
        mode_diff = df_clean['date_diff'].mode()[0] if not df_clean['date_diff'].mode().empty else None
        if mode_diff:
            logger.info(f"  - Frecuencia de datos: {mode_diff.days} días (aprox.)")
        
        # Guardar archivo limpio
        df_clean.to_csv(output_file, index=False)
        logger.info(f"\n✅ Archivo limpio guardado en: {output_file}")
        
        # Mostrar muestra de datos
        logger.info("\nMuestra de datos limpios:")
        print(df_clean.head())
        print("\nÚltimos registros:")
        print(df_clean.tail())
        
        return df_clean
        
    except Exception as e:
        logger.error(f"Error procesando archivo: {e}")
        raise


def process_gas_natural():
    """
    Procesa el archivo de Índice de Precios de Gas Natural si existe
    """
    logger.info("\n=== Procesando archivo de Gas Natural ===")
    
    gas_file = "docs/sources/gas_natural_ipgn/Índice de Precios de Gas Natural.xlsx"
    
    if os.path.exists(gas_file):
        try:
            logger.info(f"Leyendo archivo: {gas_file}")
            
            # Intentar leer el archivo
            df_gas = pd.read_excel(gas_file)
            
            logger.info(f"  - Forma: {df_gas.shape}")
            logger.info(f"  - Columnas: {list(df_gas.columns)}")
            
            # Guardar como CSV
            output_gas = "parte_tecnica/02_data_extractors/outputs/gas_natural_ipgn.csv"
            df_gas['fecha_procesamiento'] = datetime.now()
            df_gas.to_csv(output_gas, index=False)
            
            logger.info(f"✅ Gas Natural guardado en: {output_gas}")
            
            # Mostrar muestra
            logger.info("\nMuestra de datos de Gas Natural:")
            print(df_gas.head())
            
        except Exception as e:
            logger.error(f"Error procesando Gas Natural: {e}")
    else:
        logger.info("No se encontró archivo de Gas Natural")


def main():
    """Función principal"""
    print("="*60)
    print("LIMPIEZA DE DATOS ESPECIALES")
    print("="*60)
    
    # Limpiar EPU Turquía
    try:
        df_turkey = clean_turkey_epu()
        print(f"\n✅ EPU Turquía: {len(df_turkey)} registros procesados")
    except Exception as e:
        print(f"\n❌ Error con EPU Turquía: {e}")
    
    # Procesar Gas Natural si existe
    process_gas_natural()
    
    print("\n" + "="*60)
    print("PROCESO COMPLETADO")
    print("="*60)


if __name__ == "__main__":
    main()
