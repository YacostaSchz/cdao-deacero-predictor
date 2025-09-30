# Predicción **diaria** de precio de **varilla corrugada** — **Fuentes validadas, priorización y estrategia de actualización** (DeAcero)

> **Contexto del reto**: El entregable exige un **API REST** que pronostique el **cierre del día siguiente** usando **datos públicos**, con **caché ≤1 h**, **rate‑limit**, y **MAPE** para evaluación. También sugiere fuentes como **LME, FRED, World Bank, Trading Economics**, etc. :contentReference[oaicite:0]{index=0}  

---

## 0) Decisión de diseño (resumen ejecutivo)

- **Objetivo diario**: No existe una serie gratuita y pública en **MXN/ton diaria** para *varilla corrugada en México*. Por lo tanto, **priorizamos un target internacional diario** y generamos la **paridad de importación/local** para mapear a México.
- **Target diario recomendado**:  
  **LME Steel Rebar FOB Turkey (Platts)** — **día‑retrasado** (cierre diario libre) como **objetivo directo** del modelo; es el contrato de referencia global más cercano a varilla de construcción. :contentReference[oaicite:1]{index=1}  
  *Alternativa/Refuerzo*: **SHFE Rebar Futures (China)** para señal diaria adicional y *nowcasting*. :contentReference[oaicite:2]{index=2}
- **Ancla/validación mensual** (no objetivo, solo calibración):  
  **INEGI INPP – genérico “Varilla corrugada”** y **Banxico SIE CP41** (índices de costo/obra). Se usan como **anclas de nivel** mensuales, **no** para pronóstico diario. **INEGI sí mantiene “varilla corrugada”** en la estructura 2019 y aparece en boletines 2023‑2024; el problema es la **frecuencia** (mensual), no la existencia. :contentReference[oaicite:3]{index=3}

---

## 1) **Priorización de fuentes** para cumplir predicción **diaria**

> Ordenadas por **impacto en MAPE y disponibilidad diaria**.

### **Tier A — Objetivo y señales diarias (alta prioridad)**

1) **LME – Steel Rebar FOB Turkey (Platts)**  
   - **Uso**: **Target diario** (*day‑delayed*) o componente principal del *ensemble*.  
   - **Actualización**: **Diaria** (cierre LME, público día‑retrasado).  
   - **Enlaces**:  
     - Página de **precio** (curva y cierres): https://www.lme.com/en/metals/ferrous/lme-steel-rebar-fob-turkey-platts  :contentReference[oaicite:4]{index=4}  
     - **Especificaciones del contrato**: https://www.lme.com/en/metals/ferrous/lme-steel-rebar-fob-turkey-platts/contract-specifications  :contentReference[oaicite:5]{index=5}  

2) **SHFE – Rebar Futures (China)**  
   - **Uso**: Señal diaria de *price discovery* (gran liquidez China).  
   - **Actualización**: **Diaria**.  
   - **Enlace**:  
     - SHFE Rebar (inglés): https://www.shfe.com.cn/eng/Market/Futures/Metal/rb_f/  :contentReference[oaicite:6]{index=6}  

3) **LME – Steel Scrap CFR Turkey (Platts)**  
   - **Uso**: Driver diario **cost‑side** (EAF -> chatarra).  
   - **Actualización**: **Diaria** (día‑retrasado).  
   - **Enlaces**:  
     - Precio: https://www.lme.com/en/metals/ferrous/lme-steel-scrap-cfr-turkey-platts  :contentReference[oaicite:7]{index=7}  
     - Especificaciones: https://www.lme.com/en/metals/ferrous/lme-steel-scrap-cfr-turkey-platts/contract-specifications  :contentReference[oaicite:8]{index=8}  

4) **Tipo de cambio USD/MXN**  
   - **Uso**: Conversión a MXN y componente del **basis** MX.  
   - **Actualización**: **Diaria**.  
   - **Enlaces**:  
     - **FRED DEXMXUS**: https://fred.stlouisfed.org/series/DEXMXUS  :contentReference[oaicite:9]{index=9}  
     - **Banxico FIX** (API & cat. de series): https://www.banxico.org.mx/SieAPIRest/  | Doc de series: https://www.banxico.org.mx/SieAPIRest/service/v1/doc/series  :contentReference[oaicite:10]{index=10}  

5) **Freight proxy – Baltic Dry Index (BDI)**  
   - **Uso**: Proxy **flete marítimo** en paridad de importación.  
   - **Actualización**: **Diaria**.  
   - **Enlaces**:  
     - Baltic Exchange (info servicios diarios): https://www.balticexchange.com/en/data-services/market-information0/dry-services.html  :contentReference[oaicite:11]{index=11}  

> **Notas de priorización**: Con (1)–(4) puedes **pronosticar diario** y **mapear a MXN**. El BDI (5) añade sensibilidad a costos de importación.

---

### **Tier B — Señales complementarias (alta/medio)**

6) **World Bank – Pink Sheet “Steel, Rebar (Japan)”**  
   - **Uso**: Señal **mensual** ex‑China de rebar (contratos exportación).  
   - **Actualización**: **Mensual** (XLS y PDF).  
   - **Enlaces**:  
     - XLS histórico (Monthly): https://thedocs.worldbank.org/en/doc/5d903e848db1d1b83e0ec8f744e55570-0350012021/related/CMO-Historical-Data-Monthly.xlsx  :contentReference[oaicite:12]{index=12}  
     - Portal Pink Sheet: https://www.worldbank.org/en/research/commodity-markets  :contentReference[oaicite:13]{index=13}  
     - Pink Sheet actual (ej. Sep‑2025): https://thedocs.worldbank.org/en/doc/18675f1d1639c7a34d463f59263ba0a2-0050012025/related/CMO-Pink-Sheet-September-2025.pdf  :contentReference[oaicite:14]{index=14}  

7) **CME – HRC (Hot‑Rolled Coil) & Busheling (US)**  
   - **Uso**: Señales de la cadena ferrosa US (diarias/mes‑settled) para robustecer *nowcasting* de rebar.  
   - **Actualización**: **Diaria** (cotizaciones) / **Mensual** (settlement).  
   - **Enlaces**:  
     - HRC overview/quotes: https://www.cmegroup.com/markets/metals/ferrous/hrc-steel.html  | https://www.cmegroup.com/markets/metals/ferrous/hrc-steel.quotes.html  :contentReference[oaicite:15]{index=15}  
     - Busheling (Fastmarkets) specs/rulebook: https://www.cmegroup.com/markets/metals/ferrous/chicago-no1-busheling-ferrous-scrap-fastmarkets.contractSpecs.html  | https://www.cmegroup.com/rulebook/COMEX/6/601.pdf  :contentReference[oaicite:16]{index=16}  

8) **Iron ore (señal de insumo)**  
   - **Uso**: Driver mensual/casi‑diario del *cost‑side* siderúrgico.  
   - **Actualización**: **Mensual** en FRED/IMF; (opcional) diarios vía SGX/Reuters (no siempre libres).  
   - **Enlaces**:  
     - FRED **PIORECRUSDM**: https://fred.stlouisfed.org/series/PIORECRUSDM  :contentReference[oaicite:17]{index=17}  

---

### **Tier C — Anclas y contexto México (mensual / baja prioridad para “diario”)**

9) **INEGI – INPP (genérico “Varilla corrugada”)**  
   - **Uso**: **Ancla de nivel/calibración** (mensual).  
   - **Actualización**: **Mensual** (base 2019).  
   - **Enlaces**:  
     - Tema INPP: https://www.inegi.org.mx/temas/inpp/  :contentReference[oaicite:18]{index=18}  
     - Estructura (contiene **“341 Varilla corrugada”**): https://inegi.org.mx/contenidos/programas/inpp/2019a/doc/889463924807.pdf  :contentReference[oaicite:19]{index=19}  
     - Boletines con mención expresa a “varilla corrugada”:  
       - Oct‑2023: https://www.inegi.org.mx/contenidos/saladeprensa/boletines/2023/inpp/inpp2023_10.pdf  :contentReference[oaicite:20]{index=20}  
       - Dic‑2024: https://www.inegi.org.mx/contenidos/saladeprensa/boletines/2024/inpp/inpp2024_12.pdf  :contentReference[oaicite:21]{index=21}  

10) **Banxico – SIE CP41 (actualización de costos de obra pública)**  
   - **Uso**: Índices mensuales con partidas de **varilla corrugada**; **ancla/validación** del nivel.  
   - **Actualización**: **Mensual**.  
   - **Enlace**: https://www.banxico.org.mx/SieInternet/consultarDirectorioInternetAction.do?accion=consultarCuadro&idCuadro=CP41&locale=es&sector=20  :contentReference[oaicite:22]{index=22}  

11) **Demanda local construcción (INEGI)**  
   - **Uso**: *Basis* local mensual (demanda) para **paridad local**.  
   - **Actualización**: **Mensual**.  
   - **Enlaces**:  
     - **ENEC** (Encuesta Constructoras): https://www.inegi.org.mx/rnm/index.php/catalog/957  | boletín reciente: https://en.www.inegi.org.mx/contenidos/saladeprensa/boletines/2025/enec/enec2025_09.pdf  :contentReference[oaicite:23]{index=23}  
     - **IMFBCF** (Inversión Fija Bruta): https://www.inegi.org.mx/temas/ifb/  | boletín sep‑2025: https://www.inegi.org.mx/contenidos/saladeprensa/boletines/2025/ifb/imfbcf2025_09.pdf  :contentReference[oaicite:24]{index=24}  

12) **Costos energéticos México**  
   - **Uso**: *Basis* local (energía para EAF).  
   - **Actualización**: **Mensual** (tarifas), **diario/semanal** (diésel).  
   - **Enlaces**:  
     - **CFE – GDMTH** (tarifa industria, selector por mes): https://app.cfe.mx/Aplicaciones/CCFE/Tarifas/TarifasCRENegocio/Tarifas/GranDemandaMTH.aspx  :contentReference[oaicite:25]{index=25}  
     - **CFE – Esquema tarifario**: https://www.cfe.mx/industria/tarifas/pages/default.aspx  :contentReference[oaicite:26]{index=26}  
     - **CRE/PROFECO – Diésel** (precios reportados en línea + tablero de Profeco):  
       - CRE: https://www.cre.gob.mx/ConsultaPrecios/GasolinasyDiesel/GasolinasyDiesel.html  :contentReference[oaicite:27]{index=27}  
       - Profeco “Quién es Quién”: https://combustibles.profeco.gob.mx/  :contentReference[oaicite:28]{index=28}  

13) **Eventos regulatorios (dummies)** — **Cuotas antidumping a varilla (Brasil)**  
   - **Uso**: *event dummies* que pueden mover el **basis** MX.  
   - **Actualización**: **Event‑driven** (DOF).  
   - **Enlaces** (histórico y examen de vigencia 2025):  
     - DOF 30‑jul‑2020 (examen de vigencia): https://www.dof.gob.mx/index_113.php?day=30&month=07&year=2020  :contentReference[oaicite:29]{index=29}  
     - Resolución final previa (ejemplo): https://www.dof.gob.mx/nota_detalle_popup.php?codigo=5639157  :contentReference[oaicite:30]{index=30}  
     - Inicio de examen 11‑ago‑2025 (nota SIDOF + PDF SE): https://sidof.segob.gob.mx/notas/5765140  | https://www.gob.mx/cms/uploads/attachment/file/1015047/20250811_RIEx_Varilla_corrugada.pdf  :contentReference[oaicite:31]{index=31}  
     - Listados vigentes (SE): https://www.gob.mx/cms/uploads/attachment/file/1004817/Mercanc_as_sujetas_a_cuotas_compensatorias_27062025.pdf  :contentReference[oaicite:32]{index=32}  

> **Platts – Índice de Varilla México (referencia comercial, no‑gratuita)**: explicación/metodología y actualizaciones 2025 (frecuencia):  
> https://www.spglobal.com/commodity-insights/en/pricing-benchmarks/assessments/metals/mexican-steel-rebar-index-price-explained  |  
> https://www.spglobal.com/commodity-insights/en/pricing-benchmarks/our-methodology/price-symbols/080125-platts-updates-description-frequency-and-uom-for-mexican-rebar-symbols  :contentReference[oaicite:33]{index=33}

---

## 2) **Estrategia para lograr pronóstico diario** (con pandemia y quiebres)

**Arquitectura de modelado (ensemble + estado‑espacio):**

1. **Target diario**:  
   \(Y_t\) = **LME Rebar FOB Turkey (USD/t)** (día‑retrasado).  :contentReference[oaicite:34]{index=34}

2. **Señales diarias**:  
   - \(X^{scrap}_t\): **LME Steel Scrap CFR Turkey** (USD/t). :contentReference[oaicite:35]{index=35}  
   - \(X^{fx}_t\): **USD/MXN** (FRED DEXMXUS o Banxico FIX). :contentReference[oaicite:36]{index=36}  
   - \(X^{bdi}_t\): **Baltic Dry Index** (proxy flete). :contentReference[oaicite:37]{index=37}  
   - \(X^{cn}_t\): **SHFE Rebar** (cNY/t). :contentReference[oaicite:38]{index=38}

3. **Señales mensuales (agregadas con MIDAS)**:  
   - **World Bank Rebar (JP)**, **Iron Ore** (FRED), **PPI scrap** (FRED). :contentReference[oaicite:39]{index=39}  
   - Se incorporan con **U‑MIDAS/Kalman** (betas polinomiales) para no perder frecuencia.

4. **Filtro de Kalman / Estado‑espacio**:  
   - Ecuación de medida: \(Y_t = Z_t\alpha_t + \varepsilon_t\).  
   - Ecuación de estado: \(\alpha_{t} = T\alpha_{t-1} + R\eta_t\).  
   - Permite **time‑varying basis** y **ahogar ruido** de alta frecuencia.

5. **Pandemia y shocks**:  
   - **Dummies 2020‑03→2021‑12** (con *level shift* y varianzas elevadas) + **event dummies** por **cuotas DOF**. :contentReference[oaicite:40]{index=40}

6. **De “global” a **México diario** (si el cliente pide MXN/ton):  
   - **Paridad de importación**:  
     \[
     P^{IP}_{MX,t} = Y_t\cdot FX_t + Freight_t(BDI) + \text{Manejo/Aranceles}(\text{DOF}) + \epsilon_t.
     \]
     :contentReference[oaicite:41]{index=41}  
   - **Paridad local** (*basis local*):  
     \[
     Basis_{Local,t} = \beta_0 + \beta_1\text{Energía}_{MX,t}(\text{CFE}) + \beta_2\text{Demanda}_{MX,t}(\text{ENEC/IMFBCF}) + u_t.
     \]
     :contentReference[oaicite:42]{index=42}  
   - **Calibración mensual** contra **INPP varilla**/**CP41** para mantener **nivel y deriva**. :contentReference[oaicite:43]{index=43}  

**Calendario operativo** (para el API con caché 1 h):

- **Pull diario**: LME Rebar & Scrap (16:30 Londres cierre; el portal ofrece datos **day‑delayed**), FX FIX Banxico (mediodía MX), BDI (cierre diario). :contentReference[oaicite:44]{index=44}  
- **Pull semanal**: Validar outliers en Profeco/CRE (diésel). :contentReference[oaicite:45]{index=45}  
- **Pull mensual**: Pink Sheet, INPP/CP41, IMFBCF, ENEC. :contentReference[oaicite:46]{index=46}

---

## 3) **Diccionario de datos** (serie, unidad, frecuencia, *pull*, uso)

| # | Fuente / Serie | Unidad | Frec. oficial | **Pull recomendado** | Uso en modelo | **Link** |
|---|---|---|---|---|---|---|
| 1 | **LME Rebar FOB Turkey (Platts)** | USD/t | Diaria (*day‑delayed*) | **Diaria** | **Target diario** | https://www.lme.com/en/metals/ferrous/lme-steel-rebar-fob-turkey-platts :contentReference[oaicite:47]{index=47} |
| 2 | **LME Steel Scrap CFR Turkey** | USD/t | Diaria (*day‑delayed*) | **Diaria** | Driver costo | https://www.lme.com/en/metals/ferrous/lme-steel-scrap-cfr-turkey-platts :contentReference[oaicite:48]{index=48} |
| 3 | **USD/MXN – FRED DEXMXUS** | MXN/USD | Diaria | **Diaria** | FX a MXN | https://fred.stlouisfed.org/series/DEXMXUS :contentReference[oaicite:49]{index=49} |
| 4 | **USD/MXN – Banxico FIX (API)** | MXN/USD | Diaria | **Diaria** | FX a MXN | https://www.banxico.org.mx/SieAPIRest/ :contentReference[oaicite:50]{index=50} |
| 5 | **BDI – Baltic Exchange** | Índice | Diaria | **Diaria** | Flete IP | https://www.balticexchange.com/en/data-services/market-information0/dry-services.html :contentReference[oaicite:51]{index=51} |
| 6 | **SHFE Rebar** | CNY/t | Diaria | **Diaria** | Señal extra | https://www.shfe.com.cn/eng/Market/Futures/Metal/rb_f/ :contentReference[oaicite:52]{index=52} |
| 7 | **World Bank Rebar (Japan)** | USD/t | Mensual | **Mensual** | Contexto/validación | https://thedocs.worldbank.org/en/doc/5d903e848db1d1b83e0ec8f744e55570-0350012021/related/CMO-Historical-Data-Monthly.xlsx :contentReference[oaicite:53]{index=53} |
| 8 | **Iron ore – FRED (PIORECRUSDM)** | USD/t | Mensual | **Mensual** | Driver | https://fred.stlouisfed.org/series/PIORECRUSDM :contentReference[oaicite:54]{index=54} |
| 9 | **PPI scrap – FRED (WPU10121193)** | Índice | Mensual | **Mensual** | Driver | https://fred.stlouisfed.org/series/WPU10121193 :contentReference[oaicite:55]{index=55} |
| 10 | **INEGI INPP “Varilla corrugada”** | Índice (2019=100) | Mensual | **Mensual** | **Ancla** | https://www.inegi.org.mx/temas/inpp/ + estructura 2019: https://inegi.org.mx/contenidos/programas/inpp/2019a/doc/889463924807.pdf :contentReference[oaicite:56]{index=56} |
| 11 | **Banxico – CP41** | Índices costo | Mensual | **Mensual** | **Ancla** | https://www.banxico.org.mx/SieInternet/consultarDirectorioInternetAction.do?accion=consultarCuadro&idCuadro=CP41&locale=es&sector=20 :contentReference[oaicite:57]{index=57} |
| 12 | **CFE GDMTH** | Tarifa MXN/kWh | Mensual | **Mensual** | Basis local | https://app.cfe.mx/Aplicaciones/CCFE/Tarifas/TarifasCRENegocio/Tarifas/GranDemandaMTH.aspx :contentReference[oaicite:58]{index=58} |
| 13 | **CRE/PROFECO diésel** | MXN/l | Diario/Semanal | **Semanal** | Flete IP | CRE: https://www.cre.gob.mx/ConsultaPrecios/GasolinasyDiesel/GasolinasyDiesel.html | Profeco: https://combustibles.profeco.gob.mx/ :contentReference[oaicite:59]{index=59} |
| 14 | **ENEC / IMFBCF** | Índices | Mensual | **Mensual** | Demanda MX | ENEC: https://www.inegi.org.mx/rnm/index.php/catalog/957 | IMFBCF: https://www.inegi.org.mx/temas/ifb/ :contentReference[oaicite:60]{index=60} |
| 15 | **DOF cuotas (varilla Brasil)** | %/USD/kg | Event‑driven | **Al evento** | *Dummies* | https://www.dof.gob.mx/index_113.php?day=30&month=07&year=2020 | https://sidof.segob.gob.mx/notas/5765140 :contentReference[oaicite:61]{index=61} |

---

## 4) **Framework US/Global → México** (para transformar a MX cuando el target global sea el modelado principal)

1. **Paridad de importación (IP)**  
   \[
   P^{IP}_{MX,t} = P^{LME\ Rebar}_{USD/t,t}\cdot FX_{t} + Freight_{t}(BDI) + Aranceles/Cuotas_{t} + Manejo/Margen.
   \]
   - **FX** via FRED/Banxico; **flete** via BDI; **cuotas** vía DOF. :contentReference[oaicite:62]{index=62}

2. **Paridad local (LP)**  
   \[
   P^{LP}_{MX,t} = P^{IP}_{MX,t} + \beta_1\text{Energía}_{CFE,t} + \beta_2\text{Demanda}_{ENEC/IMFBCF,t} + u_t.
   \]
   - **Energía**: CFE GDMTH; **Demanda**: ENEC/IMFBCF. :contentReference[oaicite:63]{index=63}

3. **Calibración mensual de nivel**  
   - Alinea media/varianza con **INPP varilla** y/o **CP41** en una ventana *rolling*. :contentReference[oaicite:64]{index=64}

> **Comentario sobre INEGI**: Aunque **INEGI** es **mensual**, **sí** preserva el genérico “varilla corrugada” (base 2019) y lo reporta en boletines 2023‑2024; por frecuencia, lo usamos **solo** para **anclar** el nivel, **no** como objetivo. :contentReference[oaicite:65]{index=65}

---

## 5) Consideraciones de pandemia y quiebres

- **Dummies** 2020‑03→2021‑12 e incremento de varianzas en el estado (*time‑varying parameters*).  
- **Eventos DOF** (cuotas antidumping) como **saltos** de *basis* local. :contentReference[oaicite:66]{index=66}  
- Validación **pre/post‑shock** (Chow/CUSUM) y *re‑calibración* mensual con INPP/CP41.

---

## 6) **Plan de actualización** (operativo para el API del reto)

- **Diario** (D‑1 a D, ventanas UTC):  
  - LME Rebar y Scrap (cierres **day‑delayed**), FX (FIX & DEXMXUS), BDI → **re‑entrenar incremental** / **update de estado** y **predicción D+1**. :contentReference[oaicite:67]{index=67}  
- **Semanal**: Validar **outliers** diésel CRE/Profeco y ajustar proxy de flete. :contentReference[oaicite:68]{index=68}  
- **Mensual**: Pink Sheet, INPP/CP41, IMFBCF, ENEC → **re‑anchor** de nivel. :contentReference[oaicite:69]{index=69}

---

## 7) **Apéndice — Referencias (todas las ligas mencionadas)**

**Target & drivers diarios**
- LME Rebar precio (day‑delayed): https://www.lme.com/en/metals/ferrous/lme-steel-rebar-fob-turkey-platts  :contentReference[oaicite:70]{index=70}  
- LME Rebar especificaciones: https://www.lme.com/en/metals/ferrous/lme-steel-rebar-fob-turkey-platts/contract-specifications  :contentReference[oaicite:71]{index=71}  
- LME Scrap precio: https://www.lme.com/en/metals/ferrous/lme-steel-scrap-cfr-turkey-platts  :contentReference[oaicite:72]{index=72}  
- LME Scrap especificaciones: https://www.lme.com/en/metals/ferrous/lme-steel-scrap-cfr-turkey-platts/contract-specifications  :contentReference[oaicite:73]{index=73}  
- SHFE Rebar (inglés): https://www.shfe.com.cn/eng/Market/Futures/Metal/rb_f/  :contentReference[oaicite:74]{index=74}  
- Baltic Exchange (BDI info): https://www.balticexchange.com/en/data-services/market-information0/dry-services.html  :contentReference[oaicite:75]{index=75}  

**FX**
- FRED DEXMXUS: https://fred.stlouisfed.org/series/DEXMXUS  :contentReference[oaicite:76]{index=76}  
- Banxico SIE API (FIX y docs): https://www.banxico.org.mx/SieAPIRest/  | https://www.banxico.org.mx/SieAPIRest/service/v1/doc/series  :contentReference[oaicite:77]{index=77}  

**Mensuales (ancla/insumos)**
- World Bank Pink Sheet portal: https://www.worldbank.org/en/research/commodity-markets  :contentReference[oaicite:78]{index=78}  
- Pink Sheet XLS monthly: https://thedocs.worldbank.org/en/doc/5d903e848db1d1b83e0ec8f744e55570-0350012021/related/CMO-Historical-Data-Monthly.xlsx  :contentReference[oaicite:79]{index=79}  
- Pink Sheet (Sep‑2025): https://thedocs.worldbank.org/en/doc/18675f1d1639c7a34d463f59263ba0a2-0050012025/related/CMO-Pink-Sheet-September-2025.pdf  :contentReference[oaicite:80]{index=80}  
- FRED Iron Ore PIORECRUSDM: https://fred.stlouisfed.org/series/PIORECRUSDM  :contentReference[oaicite:81]{index=81}  
- FRED PPI Scrap WPU10121193: https://fred.stlouisfed.org/series/WPU10121193  :contentReference[oaicite:82]{index=82}  
- FRED PPI Iron ores WPU101105: https://fred.stlouisfed.org/series/WPU101105  :contentReference[oaicite:83]{index=83}  
- CME HRC (overview/quotes): https://www.cmegroup.com/markets/metals/ferrous/hrc-steel.html | https://www.cmegroup.com/markets/metals/ferrous/hrc-steel.quotes.html  :contentReference[oaicite:84]{index=84}  
- CME Busheling scrap (specs/rulebook): https://www.cmegroup.com/markets/metals/ferrous/chicago-no1-busheling-ferrous-scrap-fastmarkets.contractSpecs.html | https://www.cmegroup.com/rulebook/COMEX/6/601.pdf  :contentReference[oaicite:85]{index=85}  

**México (anclas y basis)**
- INEGI INPP (tema): https://www.inegi.org.mx/temas/inpp/  :contentReference[oaicite:86]{index=86}  
- INEGI INPP estructura 2019 (incluye **varilla corrugada**): https://inegi.org.mx/contenidos/programas/inpp/2019a/doc/889463924807.pdf  :contentReference[oaicite:87]{index=87}  
- INEGI boletines con “varilla corrugada”: Oct‑2023 https://www.inegi.org.mx/contenidos/saladeprensa/boletines/2023/inpp/inpp2023_10.pdf | Dic‑2024 https://www.inegi.org.mx/contenidos/saladeprensa/boletines/2024/inpp/inpp2024_12.pdf  :contentReference[oaicite:88]{index=88}  
- Banxico SIE **CP41**: https://www.banxico.org.mx/SieInternet/consultarDirectorioInternetAction.do?accion=consultarCuadro&idCuadro=CP41&locale=es&sector=20  :contentReference[oaicite:89]{index=89}  
- CFE GDMTH: https://app.cfe.mx/Aplicaciones/CCFE/Tarifas/TarifasCRENegocio/Tarifas/GranDemandaMTH.aspx  :contentReference[oaicite:90]{index=90}  
- CFE Esquema tarifario: https://www.cfe.mx/industria/tarifas/pages/default.aspx  :contentReference[oaicite:91]{index=91}  
- CRE precios diésel: https://www.cre.gob.mx/ConsultaPrecios/GasolinasyDiesel/GasolinasyDiesel.html  | Profeco: https://combustibles.profeco.gob.mx/  :contentReference[oaicite:92]{index=92}  
- ENEC (catálogo + boletín): https://www.inegi.org.mx/rnm/index.php/catalog/957 | https://en.www.inegi.org.mx/contenidos/saladeprensa/boletines/2025/enec/enec2025_09.pdf  :contentReference[oaicite:93]{index=93}  
- IMFBCF (tema + boletín sep‑2025): https://www.inegi.org.mx/temas/ifb/ | https://www.inegi.org.mx/contenidos/saladeprensa/boletines/2025/ifb/imfbcf2025_09.pdf  :contentReference[oaicite:94]{index=94}  

**Cuotas/Regulación (eventos)**
- DOF 30‑jul‑2020 (varilla Brasil): https://www.dof.gob.mx/index_113.php?day=30&month=07&year=2020  :contentReference[oaicite:95]{index=95}  
- Resolución final (ejemplo): https://www.dof.gob.mx/nota_detalle_popup.php?codigo=5639157  :contentReference[oaicite:96]{index=96}  
- Examen 11‑ago‑2025 (nota + PDF): https://sidof.segob.gob.mx/notas/5765140 | https://www.gob.mx/cms/uploads/attachment/file/1015047/20250811_RIEx_Varilla_corrugada.pdf  :contentReference[oaicite:97]{index=97}  

**Referencia comercial (no‑gratuita)**
- Platts Mexican Rebar Index (explicación & actualización de frecuencia 2025):  
  https://www.spglobal.com/commodity-insights/en/pricing-benchmarks/assessments/metals/mexican-steel-rebar-index-price-explained |  
  https://www.spglobal.com/commodity-insights/en/pricing-benchmarks/our-methodology/price-symbols/080125-platts-updates-description-frequency-and-uom-for-mexican-rebar-symbols  :contentReference[oaicite:98]{index=98}

---

## 8) Observaciones clave sobre **INEGI** (tu comentario de “hasta 2019”)

- El **genérico “varilla corrugada”** está vigente en la **estructura INPP 2019** y se **menciona explícitamente** en boletines 2023 y 2024; por lo tanto, **sí existe** como serie mensual **posterior a 2019**. El inconveniente es la **frecuencia** (mensual), por lo que lo **depriorizamos** como **target** y lo usamos **solo** para **calibrar** niveles. :contentReference[oaicite:99]{index=99}

---

## 9) Qué debes implementar primero (hoja de ruta de datos)

1) **Producción**: Ingesta diaria de **LME Rebar**, **LME Scrap**, **DEXMXUS/FIX**, **BDI** → **modelo estado‑espacio** + **predicción D+1**.  
2) **Semanal**: Ajuste proxy de flete con **CRE/Profeco diésel**.  
3) **Mensual**: Re‑anclaje de nivel con **INPP varilla** y/o **CP41**, y actualización de **Pink Sheet**, **ENEC**, **IMFBCF**.

---

> **Este markdown incluye todas las ligas solicitadas y prioriza fuentes **diarias** para cumplir el objetivo del API.**  
> Si quieres, te paso **plantillas de ingesta (Python)** y **esquemas de tablas** (Bronze/Silver/Gold) para que pegues el pipeline y el endpoint */predict/steel-rebar-price* en pocas horas. 
