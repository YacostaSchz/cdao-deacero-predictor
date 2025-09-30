# 📅 Estrategia de Actualización de Datos

**Fecha**: 2025-09-29 18:45  
**Pregunta**: ¿Diario tendría que actualizar las series?

---

## 🎯 RESPUESTA CORTA

**SÍ - Actualización diaria de 3 series críticas**:
1. LME Steel Rebar (Excel)
2. USD/MXN (Banxico API)
3. TIIE 28d (Banxico API)

**Frecuencia**: Lunes a Viernes (días hábiles)

---

## 📊 ESTRATEGIA COMPLETA POR FUENTE

### 🔴 ACTUALIZACIÓN DIARIA (Business Days)

#### 1. LME Steel Rebar & Scrap

**Fuente**: Excel files (SR Closing Prices.xlsx, SC Closing Prices.xlsx)  
**Frecuencia**: **Diaria** (Lunes-Viernes)  
**Horario**: 2:00 PM Mexico City  
**Razón**: LME cierra 17:00 London (12:00 PM Mexico), datos disponibles 1-2h después

**Automatización** (Terraform):
```hcl
google_cloud_scheduler_job.data_ingestion_schedules["lme_excel_processor"]
  schedule: "0 14 * * 1-5"  # 2PM Mon-Fri
```

**Proceso**:
1. Cloud Scheduler dispara Cloud Function
2. Function descarga/procesa Excel files
3. Actualiza BigQuery table: lme_steel_rebar_daily
4. Trigger: Model prediction update

**CRÍTICO**: ✅ **SÍ, actualización diaria obligatoria**

---

#### 2. USD/MXN (Tipo de Cambio)

**Fuente**: Banxico API (Serie SF43718)  
**Frecuencia**: **Diaria** (Lunes-Viernes)  
**Horario**: 8:30 AM Mexico City  
**Razón**: Banxico publica FIX a las 12:00, tomamos con buffer

**Automatización**:
```hcl
google_cloud_scheduler_job.data_ingestion_schedules["banxico_daily_updater"]
  schedule: "30 8 * * 1-5"  # 8:30AM Mon-Fri
```

**CRÍTICO**: ✅ **SÍ, actualización diaria obligatoria** (afecta premium)

---

#### 3. TIIE 28 días

**Fuente**: Banxico API (Serie SF43783)  
**Frecuencia**: **Diaria** (Lunes-Viernes)  
**Horario**: 8:30 AM Mexico City  
**Razón**: Publicado diario junto con FIX

**Automatización**: Mismo job que USD/MXN

**IMPORTANTE**: ✅ **SÍ, actualización diaria obligatoria** (afecta real_interest_rate)

---

### 🟡 ACTUALIZACIÓN MENSUAL

#### 4. INPC (Inflación)

**Fuente**: Banxico API (Serie SP1)  
**Frecuencia**: **Mensual**  
**Horario**: Día 3 del mes, 10:00 AM  
**Razón**: Publicado ~día 10 de cada mes

**Automatización**:
```hcl
google_cloud_scheduler_job.data_ingestion_schedules["banxico_monthly_updater"]
  schedule: "0 10 3 * *"  # 3rd of month, 10AM
```

**NO DIARIO**: ❌ Solo mensual

---

#### 5. IGAE (Actividad Económica)

**Fuente**: Banxico API (Serie SR16734)  
**Frecuencia**: **Mensual**  
**Horario**: Día 3 del mes  
**Razón**: Publicado con retraso de 2 meses

**NO DIARIO**: ❌ Solo mensual

---

#### 6. EPU Indices (Incertidumbre)

**Fuente**: Excel files (Mexico, USA, China, Turkey)  
**Frecuencia**: **Mensual**  
**Horario**: Día 1 del mes, 11:00 AM  
**Razón**: Publicados con 1-5 días de retraso

**Automatización**:
```hcl
google_cloud_scheduler_job.data_ingestion_schedules["epu_excel_processor"]
  schedule: "0 11 1 * *"  # 1st of month, 11AM
```

**NO DIARIO**: ❌ Solo mensual

---

#### 7. Gas Natural IPGN

**Fuente**: Excel (Índice de Precios de Gas Natural.xlsx)  
**Frecuencia**: **Mensual**  
**Horario**: Día 5 del mes, 12:00 PM  
**Razón**: CRE publica ~día 5

**NO DIARIO**: ❌ Solo mensual

---

## 📅 CALENDARIO DE ACTUALIZACIÓN

### Diaria (Lunes-Viernes)

| Serie | Hora Mexico | Proceso | Crítico |
|-------|-------------|---------|---------|
| **LME SR/SC** | 2:00 PM | Excel processor | ✅ SÍ |
| **USD/MXN** | 8:30 AM | Banxico API | ✅ SÍ |
| **TIIE 28d** | 8:30 AM | Banxico API | ✅ SÍ |

---

### Mensual

| Serie | Día del Mes | Hora | Crítico |
|-------|-------------|------|---------|
| **INPC** | 3 | 10:00 AM | ⚠️ Medio |
| **IGAE** | 3 | 10:00 AM | ⚠️ Bajo |
| **Inflación** | 3 | 10:00 AM | ⚠️ Medio |
| **EPU** | 1 | 11:00 AM | ⚠️ Bajo |
| **Gas Natural** | 5 | 12:00 PM | ⚠️ Bajo |

---

## 🤖 AUTOMATIZACIÓN COMPLETA

### Cloud Scheduler Jobs Configurados (Terraform)

```
✅ lme-excel-processor-schedule       (Diario 2PM Mon-Fri)
✅ banxico-daily-updater-schedule     (Diario 8:30AM Mon-Fri)
✅ banxico-monthly-updater-schedule   (Mensual día 3)
✅ epu-excel-processor-schedule       (Mensual día 1)
✅ gas-natural-processor-schedule     (Mensual día 5)
✅ model-retraining-schedule          (Semanal Lunes 2AM)
✅ update-steel-prediction            (Diario 6AM)
```

**Total**: 7 jobs automatizados

---

## 🔄 FLUJO DIARIO AUTOMATIZADO

### Día Hábil Normal (Lun-Vie)

```
8:30 AM - Banxico API updater
   ↓
   Updates: USD/MXN, TIIE → BigQuery
   
2:00 PM - LME Excel processor
   ↓
   Downloads: SR/SC Excel → Procesa → BigQuery
   
6:00 AM (Siguiente día) - Prediction update
   ↓
   Reads: Latest data from BigQuery
   ↓
   Runs: TWO_STAGE_MODEL.pkl
   ↓
   Writes: predictions/current.json → GCS
   ↓
   API: Serves fresh prediction
```

---

### Fin de Semana (Sáb-Dom)

```
NO hay jobs programados
API: Retorna última predicción del viernes
Razón: Mercados cerrados, no hay datos nuevos
```

---

## ❓ RESPUESTA A TU PREGUNTA

### ¿Diario tendría que actualizar las series?

**RESPUESTA DETALLADA**:

**Actualización Manual**: ❌ **NO**  
**Automatización**: ✅ **SÍ** (Cloud Scheduler + Cloud Functions)

**Series que cambian diario**:
- ✅ **LME**: Precio cierre diario (crítico para modelo)
- ✅ **USD/MXN**: Tipo de cambio diario (crítico para conversión)
- ✅ **TIIE**: Tasa interés diaria (afecta premium)

**Series que cambian mensual**:
- ⚠️ INPC, IGAE, Inflación (menores, forward-fill ok)
- ⚠️ EPU indices (menor impacto, coef ~0)
- ⚠️ Gas Natural (muy bajo impacto)

---

## 🛠️ OPCIONES DE IMPLEMENTACIÓN

### Opción A: Automatización Completa (Terraform)

**Pro**:
- ✅ Cero intervención manual
- ✅ Confiable y reproducible
- ✅ Logs automáticos

**Con**:
- Requiere terraform apply completo
- Cloud Functions adicionales

**Costo**: $0 (dentro free tier)

---

### Opción B: Manual Diaria (Simplificada)

**Proceso**:
```bash
# Ejecutar cada día hábil (10 minutos)

1. Actualizar LME:
   - Descargar SR/SC Closing Prices.xlsx
   - gsutil cp a gs://cdo-yacosta-excel-files/

2. Actualizar Banxico:
   - python banxico_downloader.py SF43718 SF43783
   
3. Regenerar predicción:
   - python generate_prediction.py
   - gsutil cp prediction.json gs://cdo-yacosta-models/predictions/
```

**Pro**: Simple, control total  
**Con**: Requiere intervención manual diaria

---

### Opción C: Híbrido (Durante Evaluación)

**Para los 5 días de evaluación**:
- Actualizar manual cada mañana (30 min)
- Verificar predicción generada
- Monitorear que API sirva correctamente

**Post-evaluación**:
- Terraform apply para automatización completa

**Recomendado**: ✅ **Esta opción para la evaluación**

---

## 📋 CHECKLIST ACTUALIZACIÓN DIARIA MANUAL

### Cada Mañana (Lun-Vie durante evaluación)

**7:00 AM - 7:30 AM**:
- [ ] Verificar que LME publicó precios cierre día anterior
- [ ] Actualizar USD/MXN desde Banxico
- [ ] Regenerar features con datos nuevos
- [ ] Ejecutar modelo TWO_STAGE_MODEL.pkl
- [ ] Generar predicción para hoy
- [ ] Subir a GCS: predictions/current.json
- [ ] Verificar: curl al API retorna predicción correcta

**Tiempo**: ~15-30 minutos

---

## 🎯 RECOMENDACIÓN PARA EVALUACIÓN

### Días 1-5 de Evaluación

**Estrategia Híbrida**:
1. **Actualización manual** cada mañana (30 min)
   - Garantiza control total
   - Permite validar cada predicción
   - Evita problemas de automatización

2. **Predicción generada** antes de 6 AM
   - Evaluadores hacen llamadas durante el día
   - Siempre tienen predicción fresca

3. **Monitoreo diario**:
   - Verificar logs de Cloud Run
   - Validar costo = $0
   - Confirmar requests funcionando

---

### Post-Evaluación (Opcional)

Si DeAcero decide usar el servicio:
- `terraform apply` completo
- Automatización 100% con Cloud Scheduler
- Cero intervención manual

---

## ✅ GARANTÍA DE DATOS FRESCOS

### Durante Evaluación

**Compromiso**:
- ✅ Predicción actualizada ANTES de 6 AM cada día hábil
- ✅ Usa datos más recientes disponibles (cierre día anterior)
- ✅ Monitoreo diario de calidad

**Contingencia**:
- Si falla actualización: API retorna última predicción válida
- Confidence score baja si datos >24h
- Logs alertan de problema

---

## 🎯 RESUMEN

### ¿Necesitas actualizar diario?

**Durante Evaluación (5 días)**: ✅ **SÍ** - Manual recomendado (30 min/día)

**Post-Evaluación**: ⚠️ **OPCIONAL** - Automatización completa disponible

**Series críticas diarias**:
- LME (más importante)
- USD/MXN (crítico para conversión)
- TIIE (afecta premium)

**Series mensuales**: No requieren actualización diaria

---

*Documentado: 2025-09-29 18:45*
