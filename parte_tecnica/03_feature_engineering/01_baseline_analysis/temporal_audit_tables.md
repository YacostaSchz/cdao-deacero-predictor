# 📊 TABLAS DE AUDITORÍA TEMPORAL

## Tabla 1: sample_preview_2024_2025

### LME Steel Rebar (10 registros representativos)
| date | M01 | M03 | M06 | contango_3m | spread_m1_m2 | rebar_scrap_spread |
|------|-----|-----|-----|-------------|--------------|-------------------|
| 2024-01-02 | 615.00 | 612.50 | 615.00 | -0.41% | 2.50 | 155.00 |
| 2024-03-15 | 628.50 | 635.00 | 642.00 | 1.03% | -2.50 | 168.50 |
| 2024-06-20 | 592.00 | 598.50 | 608.00 | 1.10% | -4.00 | 142.00 |
| 2024-09-10 | 580.00 | 585.00 | 595.50 | 0.86% | -2.00 | 135.00 |
| 2024-12-15 | 565.50 | 570.00 | 582.00 | 0.80% | -3.50 | 128.50 |
| 2025-02-14 | 552.00 | 558.50 | 570.00 | 1.18% | -4.00 | 122.00 |
| 2025-05-20 | 545.00 | 550.00 | 562.50 | 0.92% | -2.50 | 118.00 |
| 2025-07-15 | 542.50 | 547.00 | 558.50 | 0.83% | -2.00 | 115.50 |
| 2025-08-28 | 540.00 | 540.00 | 561.50 | 0.00% | 0.00 | 196.00 |
| 2025-08-29 | 540.48 | 545.00 | 561.50 | 0.84% | 4.52 | 194.08 |

### USD/MXN (10 registros)
| fecha | valor | serie_id |
|-------|-------|----------|
| 2024-01-02 | 16.9823 | SF43718 |
| 2024-03-15 | 16.6845 | SF43718 |
| 2024-06-20 | 18.2156 | SF43718 |
| 2024-09-10 | 19.8234 | SF43718 |
| 2024-12-16 | 20.1532 | SF43718 |
| 2025-02-14 | 20.3421 | SF43718 |
| 2025-05-20 | 17.8923 | SF43718 |
| 2025-07-15 | 17.6234 | SF43718 |
| 2025-09-25 | 18.3421 | SF43718 |
| 2025-09-26 | 18.3856 | SF43718 |

---

## Tabla 2: frequency_report

| source_name | frequency_class | delta_median_days | variance_delta | release_lag_median | release_lag_p95 | timezone | calendar_rule |
|-------------|-----------------|-------------------|----------------|-------------------|-----------------|----------|---------------|
| BANXICO_USD_MXN | daily | 1.0 | 0.89 | 0 | 0 | America/Mexico_City | weekdays |
| BANXICO_INPC | monthly | 31.0 | 2.1 | 9 | 10 | America/Mexico_City | month_start |
| BANXICO_TIIE28 | daily | 1.0 | 0.89 | 0 | 0 | America/Mexico_City | weekdays |
| LME_STEEL_REBAR | daily | 1.0 | 0.91 | 0 | 1 | Europe/London | weekdays |
| LME_COMBINED | daily | 1.0 | 0.91 | 0 | 1 | Europe/London | weekdays |
| EPU_MEXICO | monthly | 31.0 | 1.8 | 30 | 35 | UTC | month_end |
| EPU_USA | monthly | 31.0 | 1.8 | 30 | 35 | UTC | month_end |
| EPU_CHINA | monthly | 31.0 | 1.8 | 30 | 35 | UTC | month_end |
| EPU_TURKEY | monthly | 31.0 | 1.8 | 30 | 35 | UTC | month_end |
| GAS_NATURAL_IPGN | monthly | 31.0 | 2.0 | 15 | 20 | America/Mexico_City | month_mid |
| BANXICO_IGAE | monthly | 31.0 | 2.1 | 55 | 60 | America/Mexico_City | month_start |

---

## Tabla 3: data_quality_report

| source_name | total_records | missing_pct | duplicates_exact | duplicates_temporal | outliers_count | quality_score |
|-------------|---------------|-------------|------------------|---------------------|----------------|---------------|
| BANXICO_USD_MXN | 437 | 0.0% | 0 | 0 | 2 | 99.5% |
| BANXICO_INPC | 20 | 0.0% | 0 | 0 | 0 | 100.0% |
| BANXICO_TIIE28 | 437 | 0.0% | 0 | 0 | 1 | 99.8% |
| LME_STEEL_REBAR | 421 | 0.0% | 0 | 0 | 5 | 98.8% |
| LME_COMBINED | 421 | 0.0% | 0 | 0 | 8 | 98.1% |
| EPU_MEXICO | 20 | 0.0% | 0 | 0 | 1 | 95.0% |
| EPU_USA | 20 | 0.0% | 0 | 0 | 2 | 90.0% |
| EPU_CHINA | 0 | N/A | 0 | 0 | 0 | N/A |
| EPU_TURKEY | 12 | 0.0% | 0 | 0 | 1 | 91.7% |
| GAS_NATURAL_IPGN | 140 | 0.0% | 0 | 0 | 3 | 97.9% |

---

## Tabla 4: feature_catalog

| feature_name | uses_data_at | transform | window | availability_rule | source |
|--------------|--------------|-----------|---------|-------------------|---------|
| lme_sr_m01_lag1 | t-1 | level | 1 | available_at <= cutoff_t-1 | LME_SR |
| lme_sr_m01_lag5 | t-5 | level | 1 | available_at <= cutoff_t-5 | LME_SR |
| lme_sr_pct_5d | t-1 | pct_change | 5 | requires_t-1_to_t-5 | LME_SR |
| lme_sr_ma20 | t-1 | rolling_mean | 20 | uses_t-1_to_t-20 | LME_SR |
| lme_contango_3m | t-1 | spread_pct | 1 | (M03-M01)/M01 at t-1 | LME_SR |
| usdmxn_t0 | t-0 | level | 1 | if_runtime > 14:00_MX | BANXICO |
| usdmxn_lag1 | t-1 | level | 1 | available_at <= cutoff_t-1 | BANXICO |
| usdmxn_pct_5d | t-1 | pct_change | 5 | requires_t-1_to_t-5 | BANXICO |
| spread_sr_sc_lag1 | t-1 | difference | 1 | sr_m01 - sc_m01 at t-1 | LME_COMB |
| ratio_sr_sc_lag1 | t-1 | ratio | 1 | sr_m01 / sc_m01 at t-1 | LME_COMB |
| inpc_last_pub | t-60 | as_of_join | 1 | last_published_before_t-9 | BANXICO |
| inpc_yoy_pct | t-60 | yoy_change | 12 | requires_t-1y_published | BANXICO |
| tiie28_lag1 | t-1 | level | 1 | available_at <= cutoff_t-1 | BANXICO |
| epu_mx_last | t-30 | as_of_join | 1 | last_value_before_t-30 | EPU_MX |
| epu_mx_ma3 | t-30 | rolling_mean | 3 | uses_last_3_months | EPU_MX |
| gas_usd_last | t-15 | as_of_join | 1 | last_value_before_t-15 | GAS_NAT |

---

## Políticas de Imputación Detalladas

### LOCF (Last Observation Carried Forward) con límites:
```
if missing_days <= max_carry_days:
    value = last_valid_observation
else:
    value = NaN  # No imputable, excluir del dataset
```

### Max Carry por Fuente:
| Fuente | Max Carry | Justificación |
|--------|-----------|---------------|
| Datos diarios (LME, FX) | 3 días | Fines de semana + 1 festivo |
| TIIE28 | 3 días | Mismo que FX |
| INPC | 31 días | Publicación mensual |
| EPU indices | 31 días | Publicación mensual |
| Gas Natural | 31 días | Publicación mensual |
| IGAE | No usar | Lag > 50 días |

---

## Test de No-Fuga (Gap Tests)

### Metodología:
1. Crear gaps artificiales de 5, 10, 20 días
2. Aplicar política de imputación
3. Comparar predicciones con/sin imputación
4. Verificar que MAPE no se degrade > 1%

### Resultados:
| Gap Size | MAPE sin gap | MAPE con LOCF | Degradación | Status |
|----------|--------------|---------------|-------------|---------|
| 5 días | 12.3% | 12.5% | +0.2% | ✅ Aceptable |
| 10 días | 12.3% | 13.1% | +0.8% | ✅ Aceptable |
| 20 días | 12.3% | 14.8% | +2.5% | ❌ Rechazar |

**Conclusión**: LOCF funciona bien hasta 10 días de gap

---
