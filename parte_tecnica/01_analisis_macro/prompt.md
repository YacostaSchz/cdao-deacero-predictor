Objetivo

Estimar y explicar el impacto de variables sobre el precio de la varilla corrugada (Steel rebar [STL_JP_REBAR], $/mt) usando el archivo CMOHistoricalDataMonthly.xlsx.

Entregar evidencia estadística de:
a) correlaciones y lead‑lag;
b) causalidad de Granger;
c) relaciones de largo plazo (cointegración) y efectos dinámicos vía IRFs y FEVD.

Alcance y datos

Usa estas hojas:

Monthly Prices (principal, 1960M01–2016M06, USD nominales);

Monthly Indices (índices 2010=100: iENERGY, iBASEMET, iMETMIN, etc.);

Index Weights (documentación/pesos para interpretar índices);

Description (diccionario de series/códigos).

Variable objetivo: Steel rebar [STL_JP_REBAR] ($/mt).

Trabaja la muestra 1979‑01 a 2012‑06, que es donde hay datos de rebar.

Variables candidatas (drivers exógenos): prioriza

Iron ore, cfr spot [IRON_ORE] (cobertura completa);

Energía: Crude oil, Brent [CRUDE_BRENT], Coal, Australian [COAL_AUS], Natural gas (US/EUR/JP);

Índices: iENERGY, iBASEMET, iMETMIN.

Variables colineales/“intra‑acero” (para análisis separado o control, no como “drivers exógenos” principales):

Steel Index, Steel, hot/cold rolled, Steel wire rod.

Preparación

Parsear las fechas YYYYMmm → fecha mensual (primero de mes).

Reemplazar valores no numéricos (..) por NA; tipar a float.

Trabajar en USD nominales; replicar el análisis en reales (deflactando por CPI o PPI Metals) solo como robustez.

Alinear frecuencias/fechas; construir dataset compacto para 1979–2012.

EDA + correlaciones

Graficar niveles y log‑niveles de Rebar + drivers.

Calcular correlaciones en niveles y en Δlog (mensual y YoY), con matrices ordenadas por |ρ|.

Estimar cross‑correlations (Δlog) a ±12 meses para identificar rezagos líderes (p. ej., Iron ore ~ +2m).

Pruebas de estacionariedad y quiebres

ADF/PP/KPSS en cada serie (niveles y Δlog).

Detectar quiebres estructurales (Bai–Perron o Chow) alrededor de 2008–2009 y 2011.

Documentar implicaciones sobre el modelado.

Causalidad y cointegración

Granger (1–12 lags) de drivers → Rebar (y bidireccional para contraste); reportar p‑values por lag y mejor lag (criterio AIC/BIC+significancia).

Engle–Granger bivariado (Rebar ~ Iron ore, Rebar ~ Brent, Rebar ~ Coal).

Johansen multivariado (Rebar + Iron ore + Brent + Coal ± iBASEMET) para verificar rank y vectores de cointegración.

Si hay cointegración: estimar VECM; si no: VAR en Δlog.

Reportar IRFs (choques 1 desviación estándar) y FEVD (horizontes 1, 3, 6, 12 meses) sobre Rebar.

Modelos y cuantificación de impacto

Modelo base: VECM (o VAR si no hay cointegración) con lags seleccionados por AIC/BIC y testeos de diagnóstico (autocorrelación, normalidad, heterocedasticidad).

Alternativa de predictores con lags exógenos (Lasso/Elastic Net en Δlog con 0–12 lags por variable) para selección de rezagos; interpretar contribuciones con coeficientes estandarizados y, si aplicable, SHAP sobre un modelo lineal/GBM de apoyo (solo para ranking de importancia, no para inferencia causal).

Entregar elasticidades aproximadas: efecto % en Rebar ante 1% shock en cada driver a distintos horizontes (a partir de IRFs / coeficientes).

Validación

Backtesting con ventana rodante (por ejemplo, entrenamiento 1979–2004, validación 2005–2012) para MAE/MAPE/RMSE de Δlog(Rebar).

Tests post‑estimación (residuos blancos, estabilidad de parámetros—CUSUM/CUSUMSQ).

Entregables

Notebook reproducible (Python: pandas, statsmodels, linearmodels opcional, scikit‑learn) con semillas fijas y entorno documentado.

Resumen ejecutivo (2–4 páginas) con hallazgos clave (drivers, rezagos, IRFs/FEVD, implicaciones).

Gráficos: series, heatmaps de correlación, cross‑corr a ±12m, IRFs y FEVD, importancia de variables (si se usa Lasso/GBM).

Tablas: resultados de Granger, cointegración, selección de lags, métricas de validación.

Criterios de aceptación

Reproducibilidad 100%, código limpio y comentado.

Reporte incluye por qué se escoge VECM/VAR, diagnóstico de supuestos, intervalos de confianza en IRFs y conclusiones claras sobre quién lidera a qué y en cuánto tiempo.

🚫 Prompt negativo (qué evitar)

No mezclar o usar como “drivers exógenos” variables que son prácticamente el mismo mercado (p. ej., Steel Index, hot/cold rolled, wire rod) para “explicar” Rebar sin advertir la endogeneidad/colinealidad. Úsalas solo en un análisis separado de co‑movimiento o como controles cuidadosamente justificados.

No introducir fugas de información (look‑ahead): la ingeniería de rezagos debe garantizar que los predictores estén disponibles en t‑k para explicar Rebar_t.

No concluir “causalidad económica” solo con Granger; debe complementarse con cointegración/IRFs y razonamiento económico.

No ignorar quiebres estructurales (2008–2009, 2011) ni métricas de diagnóstico de modelos.

No imputar huecos con métodos que distorsionen dinámicas (p. ej., forward‑fill prolongado en precios) sin análisis de sensibilidad.

No mezclar bases/deflactores de forma inconsistente (los índices son 2010=100; precios están en USD nominales). Si deflactas, deja ambas versiones y documenta.

No evaluar el modelo solo por ajuste in‑sample; exige backtesting con ventanas rodantes.

No usar correlaciones en niveles como evidencia causal sin probar estacionariedad/cointegración.

No exportar conclusiones sin intervalos de confianza ni cuantificar la incertidumbre de impactos.

Sugerencia de variables/etiquetas (para el notebook)

Objetivo: Steel rebar [STL_JP_REBAR] (log y Δlog).

Drivers exógenos (prioridad):

IRON_ORE, CRUDE_BRENT, COAL_AUS, NGAS_US/NGAS_EUR/NGAS_JP, iENERGY, iBASEMET, iMETMIN.

Horizontes/rezagos a examinar: 0–12 meses; especial atención a Iron ore (+2m) y Coal (+1m) observados preliminarmente.
