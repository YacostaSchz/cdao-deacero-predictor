# 📦 Guía para Subir el Proyecto a GitHub

**Fecha**: 2025-09-30  
**Proyecto**: Prueba Técnica CDO DeAcero - API Predicción Varilla Corrugada  
**Autor**: Yazmín Acosta

---

## 🎯 Objetivo

Subir el proyecto completo a GitHub para compartirlo con el equipo evaluador de DeAcero.

---

## ⚠️ IMPORTANTE: Archivos a Incluir vs Excluir

### ✅ INCLUIR (Importantes para la Entrega)

1. **Documentación Principal**:
   - README.md
   - DOCUMENTACION_COMPLETA_ENTREGA.md
   - ENTREGA_FINAL.md
   - CORREO_ENTREGA.md
   - VALIDACION_CORREO_VS_RETO.md
   - COMPLETION_CERTIFICATE.md

2. **Código Fuente**:
   - Todo en `parte_tecnica/` (Python, Terraform)
   - Todo en `parte_estrategica/`

3. **Datos Críticos**:
   - `parte_tecnica/03_feature_engineering/outputs/TWO_STAGE_MODEL.pkl` ⭐
   - `parte_tecnica/03_feature_engineering/outputs/features_dataset_latest.csv` ⭐
   - `parte_tecnica/02_data_extractors/outputs/*.csv` (datos procesados)
   - `docs/sources/` (fuentes de datos originales)

4. **Configuración**:
   - requirements.txt
   - Dockerfile
   - .env.example
   - Terraform files

### ❌ EXCLUIR (No necesarios)

- `venv/` (entorno virtual)
- `__pycache__/` (cache Python)
- `.git/` (si existe ya)
- Archivos temporales
- Logs grandes
- APM framework files (`.sanctum/`, `.cursor/`)

---

## 📝 PASO 1: Modificar .gitignore (TEMPORAL para la entrega)

Voy a crear un `.gitignore` especial para esta entrega que permite subir archivos importantes.

**Acción**: Renombrar tu .gitignore actual y crear uno nuevo temporal
