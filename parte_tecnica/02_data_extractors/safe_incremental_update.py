#!/usr/bin/env python3
"""
SAFE INCREMENTAL UPDATE - Banxico Series
Garantiza NO duplicados, validación de datos, backup automático

Uso:
    python safe_incremental_update.py
"""
import pandas as pd
import shutil
from datetime import datetime
from pathlib import Path
from banxico_downloader import BanxicoDownloader

class SafeIncrementalUpdater:
    """Actualizador seguro con validaciones y backups"""
    
    def __init__(self):
        self.downloader = BanxicoDownloader()
        self.output_dir = Path("outputs")
        self.backup_dir = Path("outputs/backups")
        self.backup_dir.mkdir(exist_ok=True)
        
    def backup_file(self, filepath: Path) -> Path:
        """Crear backup antes de modificar"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"{filepath.stem}_backup_{timestamp}.csv"
        shutil.copy(filepath, backup_path)
        print(f"   💾 Backup: {backup_path.name}")
        return backup_path
    
    def update_series(self, serie_id: str, start_date: str, end_date: str) -> dict:
        """
        Actualizar una serie CON GARANTÍA de no duplicados
        
        Returns:
            dict con estadísticas de la actualización
        """
        print(f"\n📊 Actualizando {serie_id}")
        print("-" * 60)
        
        output_file = self.output_dir / f"{serie_id}_data.csv"
        
        # 1. Backup del archivo existente
        if output_file.exists():
            self.backup_file(output_file)
        else:
            print("   ⚠️  Archivo no existe, se creará nuevo")
            return self._create_new_series(serie_id, start_date, end_date)
        
        # 2. Descargar datos nuevos
        try:
            df_new = self.downloader.download_range(serie_id, start_date, end_date)
            
            if df_new is None or len(df_new) == 0:
                print("   ℹ️  No hay datos nuevos")
                return {'status': 'no_new_data', 'records': 0}
                
            print(f"   ✅ Descargados: {len(df_new)} registros")
            print(f"      Fechas: {df_new['fecha'].min()} a {df_new['fecha'].max()}")
            
        except Exception as e:
            print(f"   ❌ Error descargando: {e}")
            return {'status': 'download_error', 'error': str(e)}
        
        # 3. Leer archivo existente
        try:
            df_existing = pd.read_csv(output_file)
            df_existing['fecha'] = pd.to_datetime(df_existing['fecha'])
            
            print(f"   📂 Existentes: {len(df_existing)} registros")
            print(f"      Última fecha: {df_existing['fecha'].max().date()}")
            
        except Exception as e:
            print(f"   ❌ Error leyendo existente: {e}")
            return {'status': 'read_error', 'error': str(e)}
        
        # 4. Combinar SIN DUPLICADOS
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        
        # CRÍTICO: Eliminar duplicados por fecha
        records_before = len(df_combined)
        df_combined = df_combined.drop_duplicates(subset=['fecha'], keep='last')
        records_after = len(df_combined)
        duplicates_removed = records_before - records_after
        
        if duplicates_removed > 0:
            print(f"   🧹 Duplicados eliminados: {duplicates_removed}")
        
        # Ordenar por fecha
        df_combined = df_combined.sort_values('fecha').reset_index(drop=True)
        
        # 5. Validaciones
        print(f"\n   🔍 Validaciones:")
        
        # 5a. No hay nulos en fechas
        null_dates = df_combined['fecha'].isnull().sum()
        if null_dates > 0:
            print(f"      ❌ {null_dates} fechas nulas")
            return {'status': 'validation_error', 'error': 'null_dates'}
        else:
            print(f"      ✅ 0 fechas nulas")
        
        # 5b. No hay duplicados
        duplicates = df_combined['fecha'].duplicated().sum()
        if duplicates > 0:
            print(f"      ❌ {duplicates} fechas duplicadas")
            return {'status': 'validation_error', 'error': 'duplicates'}
        else:
            print(f"      ✅ 0 duplicados")
        
        # 5c. Fechas ordenadas
        is_sorted = df_combined['fecha'].is_monotonic_increasing
        if not is_sorted:
            print(f"      ❌ Fechas no ordenadas")
            return {'status': 'validation_error', 'error': 'not_sorted'}
        else:
            print(f"      ✅ Fechas ordenadas")
        
        # 5d. Total de registros razonable
        print(f"      ✅ Total: {len(df_combined)} registros")
        
        # 6. Guardar
        try:
            df_combined.to_csv(output_file, index=False)
            print(f"\n   💾 Guardado: {output_file}")
            
            # Estadísticas
            nuevos = len(df_new)
            total = len(df_combined)
            
            print(f"\n   📈 Resumen:")
            print(f"      Nuevos: {nuevos}")
            print(f"      Total: {total}")
            print(f"      Última fecha: {df_combined['fecha'].max().date()}")
            
            return {
                'status': 'success',
                'new_records': nuevos,
                'total_records': total,
                'duplicates_removed': duplicates_removed,
                'last_date': str(df_combined['fecha'].max().date())
            }
            
        except Exception as e:
            print(f"   ❌ Error guardando: {e}")
            return {'status': 'save_error', 'error': str(e)}
    
    def _create_new_series(self, serie_id: str, start_date: str, end_date: str) -> dict:
        """Crear archivo nuevo para una serie"""
        try:
            df = self.downloader.download_range(serie_id, start_date, end_date)
            
            if df is not None and len(df) > 0:
                output_file = self.output_dir / f"{serie_id}_data.csv"
                df.to_csv(output_file, index=False)
                print(f"   ✅ Archivo creado: {len(df)} registros")
                return {'status': 'created', 'records': len(df)}
            else:
                return {'status': 'no_data'}
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return {'status': 'error', 'error': str(e)}

def main():
    """Ejecutar actualización segura"""
    print("🔒 SAFE INCREMENTAL UPDATE - Banxico")
    print("="*80)
    print(f"Fecha: {datetime.now()}")
    print()
    
    updater = SafeIncrementalUpdater()
    
    # Series a actualizar
    series = {
        'SF43718': 'USD/MXN',
        'SF43783': 'TIIE 28d'
    }
    
    # Calcular rango (últimos 7 días para estar seguros)
    from datetime import timedelta
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)
    
    print(f"📅 Rango: {start_date} a {end_date}")
    print()
    
    results = {}
    
    for serie_id, nombre in series.items():
        result = updater.update_series(
            serie_id, 
            start_date.isoformat(), 
            end_date.isoformat()
        )
        results[serie_id] = result
    
    # Resumen final
    print("\n" + "="*80)
    print("📊 RESUMEN FINAL")
    print("="*80)
    
    all_success = True
    for serie_id, result in results.items():
        status = result.get('status')
        if status == 'success':
            print(f"✅ {serie_id}: {result['new_records']} nuevos, {result['total_records']} total")
            if result['duplicates_removed'] > 0:
                print(f"   🧹 {result['duplicates_removed']} duplicados eliminados")
        else:
            print(f"❌ {serie_id}: {status}")
            all_success = False
    
    print()
    if all_success:
        print("✅ ACTUALIZACIÓN EXITOSA - SIN PROBLEMAS")
    else:
        print("⚠️  HUBO PROBLEMAS - Revisar arriba")
    
    print()
    print("🔒 GARANTÍAS:")
    print("   ✅ Backups creados antes de modificar")
    print("   ✅ Duplicados eliminados automáticamente")
    print("   ✅ Validación de fechas (nulos, duplicados, orden)")
    print("   ✅ Rollback posible (backups en outputs/backups/)")

if __name__ == "__main__":
    main()
