#!/usr/bin/env python3
"""
VERIFICACIÓN DE ORGANIZACIÓN DE ARCHIVOS
Confirmar que todos los archivos están en las carpetas correctas
"""

import os
from pathlib import Path

def verify_organization():
    """Verificar organización de archivos"""
    
    print("📁 VERIFICACIÓN DE ORGANIZACIÓN DE ARCHIVOS")
    print("="*80)
    
    base_path = Path(".")
    
    # Estructura esperada
    expected_structure = {
        "01_baseline_analysis": {
            "purpose": "Análisis exploratorio inicial",
            "key_files": ["temporal_audit_analyzer.py", "TEMPORAL_AUDIT_REPORT.md"]
        },
        "02_premium_models": {
            "purpose": "Análisis de premium México/LME",
            "key_files": ["focused_2025_model.py", "SIMPLE_PREMIUM_ANALYSIS.py", 
                         "COMPLETE_DATA_AUDIT.py", "PREMIUM_VALIDATION_FRAMEWORK.py"]
        },
        "03_comprehensive_analysis": {
            "purpose": "Feature engineering robusto",
            "key_files": ["robust_feature_pipeline.py", "ROBUST_FEATURE_STRATEGY.md"]
        },
        "05_final_models": {
            "purpose": "Modelo final de producción",
            "key_files": ["TWO_STAGE_FINAL_MODEL.py", "OVERFITTING_VALIDATION.py", 
                         "TWO_STAGE_MODEL_SUMMARY.md"]
        },
        "archives": {
            "purpose": "Análisis históricos",
            "key_files": ["FINAL_CONSOLIDATED_MODEL.py", "PREMIUM_DEFINITION_VERIFICATION.py",
                         "FILE_ORGANIZATION_PLAN.md"]
        },
        "outputs": {
            "purpose": "Datasets y modelos entrenados",
            "key_files": ["TWO_STAGE_MODEL.pkl", "features_dataset_latest.csv",
                         "overfitting_validation_report.json"]
        }
    }
    
    # Verificar cada carpeta
    all_good = True
    
    for folder, info in expected_structure.items():
        folder_path = base_path / folder
        
        print(f"\n📂 {folder}/")
        print(f"   Propósito: {info['purpose']}")
        
        if folder_path.exists():
            print(f"   ✅ Carpeta existe")
            
            # Verificar archivos clave
            existing_files = [f.name for f in folder_path.iterdir() if f.is_file()]
            
            for key_file in info['key_files']:
                if key_file in existing_files:
                    print(f"   ✅ {key_file}")
                else:
                    print(f"   ❌ {key_file} - FALTANTE")
                    all_good = False
            
            # Mostrar archivos adicionales
            additional = [f for f in existing_files if f not in info['key_files']]
            if additional:
                print(f"   📄 Archivos adicionales: {len(additional)}")
                for f in additional[:3]:  # Mostrar solo primeros 3
                    print(f"      - {f}")
                if len(additional) > 3:
                    print(f"      - ... y {len(additional)-3} más")
        else:
            print(f"   ❌ Carpeta NO EXISTE")
            all_good = False
    
    # Verificar archivos sueltos en raíz
    print(f"\n📄 ARCHIVOS EN RAÍZ:")
    root_files = [f.name for f in base_path.iterdir() if f.is_file() and f.suffix == '.py']
    
    if root_files:
        print(f"   ⚠️ Archivos Python sueltos: {len(root_files)}")
        for f in root_files:
            print(f"      - {f}")
        all_good = False
    else:
        print(f"   ✅ Sin archivos Python sueltos")
    
    # Resumen final
    print(f"\n\n🎯 RESUMEN DE ORGANIZACIÓN")
    print("="*60)
    
    if all_good:
        print("✅ ORGANIZACIÓN PERFECTA")
        print("   - Todas las carpetas existen")
        print("   - Archivos clave en su lugar")
        print("   - Sin archivos sueltos")
    else:
        print("⚠️ ORGANIZACIÓN INCOMPLETA")
        print("   - Revisar archivos faltantes arriba")
        print("   - Mover archivos sueltos a carpetas apropiadas")
    
    return all_good

def show_production_guide():
    """Mostrar guía para usar archivos de producción"""
    
    print(f"\n\n🚀 GUÍA DE ARCHIVOS PARA PRODUCCIÓN")
    print("="*70)
    
    production_files = {
        "MODELO PRINCIPAL": {
            "file": "05_final_models/TWO_STAGE_FINAL_MODEL.py",
            "description": "Modelo de dos etapas para producción",
            "output": "outputs/TWO_STAGE_MODEL.pkl"
        },
        "VALIDACIÓN": {
            "file": "05_final_models/OVERFITTING_VALIDATION.py", 
            "description": "Validación de overfitting (4 tests)",
            "output": "outputs/overfitting_validation_report.json"
        },
        "DOCUMENTACIÓN": {
            "file": "05_final_models/TWO_STAGE_MODEL_SUMMARY.md",
            "description": "Resumen ejecutivo completo",
            "output": "Documentación técnica"
        },
        "DATASET": {
            "file": "outputs/features_dataset_latest.csv",
            "description": "Features completas 2025 (271 obs)",
            "output": "Input para entrenamiento"
        }
    }
    
    for category, info in production_files.items():
        print(f"\n🎯 {category}:")
        print(f"   Archivo: {info['file']}")
        print(f"   Descripción: {info['description']}")
        print(f"   Output: {info['output']}")
    
    print(f"\n📋 COMANDOS PARA PRODUCCIÓN:")
    print("```bash")
    print("# 1. Entrenar modelo final")
    print("cd 05_final_models/")
    print("python TWO_STAGE_FINAL_MODEL.py")
    print("")
    print("# 2. Validar overfitting")
    print("python OVERFITTING_VALIDATION.py")
    print("")
    print("# 3. Implementar API")
    print("# (próximo paso)")
    print("```")

if __name__ == "__main__":
    print("🔍 VERIFICACIÓN COMPLETA DE ORGANIZACIÓN")
    print("="*80)
    
    # Verificar organización
    is_organized = verify_organization()
    
    # Mostrar guía de producción
    show_production_guide()
    
    if is_organized:
        print(f"\n\n🎉 ¡ORGANIZACIÓN COMPLETA!")
        print("   ✅ Todos los archivos en su lugar")
        print("   ✅ Estructura limpia y documentada")
        print("   ✅ Listo para implementación API")
    else:
        print(f"\n\n⚠️ ORGANIZACIÓN PENDIENTE")
        print("   📋 Revisar archivos faltantes arriba")
        print("   📋 Completar movimientos de archivos")
