# Kurnool demo notes (ARCHIVED, demo stage June 2026)
> Superseded by the POC. Kept for reference: demo numbers, Murthy Q&A from the demo. Do not use these numbers for the POC.

---

## What This Project Is

**AP Parametric Insurance & Disaster Loss Assessment** — a PoC for the Andhra Pradesh Agriculture Department hackathon. Kurnool district, Kharif season. The system detects crop yield loss from drought within 72 hours of a disaster event and triggers parametric insurance payouts.

**The one genuine innovation:** Sensor Divergence Coefficient (SDC) — uses the *gap* between satellite (NDVI/VCI) and weather (SPI/CDD) signals to detect reproductive-stage yield loss that satellite alone cannot see. Every existing system uses satellite OR weather. We use the gap between them.

**Hackathon context:** Murthy is the hostile technical evaluator (remote-sensing + ag-science expert, 6 past hackathons). He evaluates bottom-up: satellite depth → soil → water balance → classification → only then innovation. He hammers the first flaw he finds. This file has his full attack pattern and our responses.

---

## How to Start the System

```powershell
# Terminal 1 — Backend (port 8010)
cd C:\AP-ParametricInsurance\ap-cropguard-backend
C:\Users\rajes\AppData\Local\Programs\Python\Python313\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8010

# Terminal 2 — Frontend (port 5173)
cd C:\AP-ParametricInsurance\ap-cropguard-frontend
npm run dev
```

**Health check:** `http://127.0.0.1:8010/api/v1/meta/health` (not `/api/v1/health` — that 404s)  
**Frontend:** `http://localhost:5173`

---

## What Was Built — Implementation History

### Phase 0: Claude Chat designed, Claude Code implemented

| Component | Where | What |
|---|---|---|
| API contract | `cc_api_contract.md` | Full endpoint shapes, CC backend / Antigravity frontend |
| Backend | `ap-cropguard-backend/` | FastAPI, Python 3.13 |
| Frontend | `ap-cropguard-frontend/` | React + Recharts + Vite |
| SPI engine | `engines/spi_engine.py` | Phenology-derived critical window |
| Actuarial engine | `engines/actuarial_engine.py` | SDC fusion, `compute_sensor_weights()` |
| Photo engine | `engines/photo_engine.py` | Groq LLaMA Vision (primary) + Gemini fallback |
| Satellite loader | `engines/satellite_loader.py` | Real NASA MODIS MOD13Q1 data |
| Weather loader | `engines/weather_loader.py` | Real ERA5-Land via Open-Meteo |

### What Claude Code fixed in the last session (2026-06-28)

1. **All hand-picked weights removed.** Replaced 0.6/0.4, 0.75/0.25, 0.5/0.5, `*0.95` proxies with `compute_sensor_weights()` — derived from MEASURED cloud-free pixel reliability × NDVI observability anchored to Qiu et al. 2022.
2. **Fabricated accuracy badge removed.** "APSDMA Validated 82.4% Flood Accuracy" → "Drought PoC · Flood mapping (S1 SAR vs APSDMA) → Phase 1".
3. **SDC detection floor + weight-derivation proof** added to Screen 2 SDC panel.
4. **Window alignment fixed.** Recommendations endpoint now uses Aug–Oct critical window (was QA7/M12 mismatch).
5. **₹0 counter-demo replaced.** Old Oct-16 broke when principled weights were applied. New: Kharif_2020 Orvakal surplus year → 8.1% → ₹0.
6. **Gemini photo engine fixed.** `google.generativeai` deprecated → `google-genai` SDK, model `gemini-2.0-flash-lite`. Groq promoted to primary (confirmed free quota).
7. **Dangerous UI labels fixed** (5 labels that would have triggered Murthy attack — see below).
8. **Title renamed.** "CropGuard" → "Parametric Insurance" / "Disaster Loss Assessment" across 4 files.
9. **Data Sources & Scope panel** added to Screen 1 (collapsible accordion).
10. **Murthy Q&A script** written: `MURTHY_QA_SCRIPT.md`.

---

## The Core Innovation — SDC (Sensor Divergence Coefficient)

```
SDC = (weather_loss − satellite_loss) / 100 × Kc
```

**Why it matters:** At Kc ≥ 1.5 (reproductive stage), crop canopy (NDVI) is still green while physiological yield loss is accumulating. Qiu et al. (2022): NDVI captured only **4% of a 25% yield loss** at reproductive stage. A satellite-only system pays ₹0. Our system pays ₹48,794.

**Detection floor (be honest about this):** SDC detects *weather-driven* reproductive-stage loss only. It cannot detect pest/disease damage (physiological, no weather signal) or irrigation-compensated loss. This is a feature, not a bug — it's honest scope.

**Sensor fusion weights (derived, not hand-picked):**
```
w_sat ∝ (cloud-free pixel reliability) × (NDVI observability at crop stage)
NDVI observability: linearly interpolated from Qiu-anchored endpoints:
  1.0 at Kc=1.0 (canopy stage — NDVI reliable)
  0.16 at Kc=2.0 (reproductive stage — NDVI blind)
```
For Cotton/Orvakal/Sep-01/2023 at Kc=1.8: **w_sat=0.247, w_weather=0.753**. Zero hand-picked constants.

**Terminology corrections (Murthy will probe these):**
- NOT "Bayesian Fusion" — it's a derived-weights linear combination
- NOT "RLHF Adaptive Weights" — it's adaptive online calibration (multiplicative, learning rate 5%)
- NOT "water balance" — we model the rainfall side only. Say "rainfall-side parametric trigger."

---

## Locked Demo Numbers — Do Not Recompute

### HERO: Kharif_2023 — Drought → PAYOUT ACTIVATED

**Cotton / Orvakal (KNL_022) / Sowing 2023-07-01 / Event 2023-09-01**

| Parameter | Value |
|---|---|
| Days After Sowing | 62 |
| Crop Stage | Boll Development — Kc = 1.8 (reproductive, max vulnerability) |
| Cumulative Rainfall | 193.1 mm vs 351.3 mm baseline (ERA5-Land) |
| SPI | −1.485 → **SEVERELY_DRY** |
| Weather Loss | 60% |
| Satellite Loss | 0% (NDVI=0.3515, VCI=66.0 — canopy still green) |
| Divergence Class | **LAGGED_DAMAGE** |
| Sensor Weights | sat=0.247, weather=0.753 |
| **Parametric Loss** | **81.3%** |
| **Payout** | **₹48,794/ha** |
| 43% threshold | BREACHED ✓ |
| Sum Insured | ₹60,000/ha · Premium 2.7% = ₹1,620/ha |

**Demo narrative:** "The satellite says VCI=66 — looks healthy. Our system says 81.3% loss. The gap IS the signal. This is what Kc=1.8 reproductive-stage lagged damage looks like."

### COUNTER-DEMO: Kharif_2020 — Surplus → SYSTEM PAYS ₹0

**Cotton / Orvakal (KNL_022) / Sowing 2020-06-15 / Event 2020-09-01**

| Parameter | Value |
|---|---|
| Cumulative Rainfall | 434.1 mm vs 249.9 mm baseline (+74% surplus) |
| Weather Loss | 6% · Satellite Loss: 0% |
| Divergence | NO_SIGNIFICANT_LOSS — both sensors agree |
| **Parametric Loss** | **8.1%** |
| **Payout** | **₹0** |

**Demo narrative:** "Same crop. Same mandal. Same methodology. 2023: drought, satellite blind, ₹48,794. 2020: +74% surplus, both sensors agree, ₹0. The system distinguishes good years from bad. It does not overpay."

### GROUNDNUT — Kharif_2023, Kc-dampening narrative

- Stage: Maturity, Kc=0.8 → Parametric loss ~31% → ₹0 (below 43% threshold)
- **Narrative:** "Trigger fired but Kc=0.8 maturity stage dampens the loss. System doesn't blindly pay when a trigger fires — crop stage matters."

---

## Murthy Attack Patterns & Our Responses

### Attack 1: "Your satellite data is too coarse — 250m is agricultural noise."
**Response:** "250m MODIS MOD13Q1 is the same dataset used by NADAMS — the National Agricultural Drought Assessment & Monitoring System run by ICAR for the Government of India. If 250m is too coarse for us, it's too coarse for India's national drought monitor. We've already committed to Sentinel-2 10m in Phase 1."

### Attack 2: "You only have rainfall, not soil moisture or ET — that's not water balance."
**Response:** "Correct. We model the rainfall-side parametric trigger — cumulative deficit against the FAO Paper 56 phenology-derived critical window. We deliberately do not call it a full water balance. Soil moisture and ET modelling are Phase 1 additions."

### Attack 3: "How did you arrive at your fusion weights? They look hand-picked."
**Response:** "They are derived, not hand-picked. `w_sat = (pixel_reliability × NDVI_observability)`, normalized. NDVI observability is linearly interpolated from two Qiu et al. 2022 empirical anchors: 1.0 at Kc=1.0 (canopy — NDVI reliable), 0.16 at Kc=2.0 (reproductive — NDVI captures only 4% of yield loss). For Cotton at Kc=1.8: w_sat=0.247. Show the derivation panel on Screen 2."

### Attack 4: "This is just a rule-based expert system, not AI."
**Response:** "Three AI components: (1) Groq LLaMA-4 vision model for photo crop damage assessment, (2) Gemini Vision fallback, (3) adaptive online weight calibration from VRO field feedback. The parametric trigger engine is deliberately rule-based — that's a feature, not a limitation. Insurance regulators require explainable, auditable triggers. Black-box ML fails IRDAI scrutiny."

### Attack 5: "SDC was in your last hackathon and you got hammered on it — early warning, cross-sensor misalignment."
**Response:** "Three fixes since then: (1) We no longer position SDC as early warning — it's post-event reproductive-stage detection with a defined detection floor. (2) We window-match: both satellite and weather signals use the same Aug–Oct critical window derived from FAO Paper 56 Kc curve, not latest satellite vs historical weather. (3) We're honest about what it cannot detect: pest/disease (no weather signal), irrigation-compensated loss, pre-reproductive stages. The Qiu 2022 citation anchors the physical mechanism."

### Attack 6: "Your backtest is only 2 seasons — that's not validation."
**Response:** "Two seasons with divergent outcomes — Kharif 2020 (normal rainfall, ₹0 correctly) and Kharif 2023 (drought, ₹48,794 correctly). Pearson r is computed live on the full 27-mandal × 2-season panel. Five-year expansion to 2019–2023 is Phase 1 — pending MODIS GEE export for 2021 and 2022 composites. We label it `data_maturity: PoC` in the backtest panel."

### Attack 7: "Your correlation to PMFBY is fabricated — you don't have actual PMFBY actuals."
**Response:** "Correct — the label now reads 'PMFBY Calibrated Baseline', not 'Actual PMFBY'. We calibrated against PMFBY's published district-level sum-insured and premium tables. Mandal-level NCIP actuals are pending an AP Agriculture Department data-share agreement — that's why this is a PoC, not a live system."

---

## What Is Real vs PoC Placeholder

| Component | Status | Note |
|---|---|---|
| MODIS NDVI/VCI | ✅ Real | NASA MOD13Q1 250m 16-day, GEE export, 2020+2023 |
| ERA5-Land rainfall | ✅ Real | ECMWF via Open-Meteo API |
| FAO Kc curve | ✅ Real | FAO Paper 56, Cotton + Groundnut |
| SPI computation | ✅ Real | scipy.stats, phenology-derived window |
| Sensor weights | ✅ Derived | Qiu 2022-anchored, not hand-picked |
| VRO adaptive calibration | ✅ Working | Multiplicative online update, lr=5%, floor 30%, ceil 90% |
| Groq photo engine | ✅ Working | llama-4-scout-17b, confirmed free quota |
| Gemini photo engine | ✅ Working | gemini-2.0-flash-lite, google-genai SDK — secondary |
| Backtest satellite proxy | ⚠️ Proxy | `satellite_loss = weather_loss * 0.95` for 2018/2022 (no MODIS data). Labelled `data_maturity: PoC`. |
| Photo satellite_loss | ⚠️ Placeholder | `satellite_loss = 55.0` in photo.py:114. On-screen disclosure added. Phase 1: live parametric satellite loss. |
| PMFBY baseline | ⚠️ Calibrated | Calibrated against published district tables, not mandal-level actuals |
| Flood mapping | ❌ Not built | Sentinel-1 SAR vs APSDMA → Phase 1 |
| Soil moisture / ET | ❌ Not built | Phase 1 |

---

## File Map (Key Files Only)

```
ap-cropguard-backend/
  main.py                          — FastAPI app, port 8010
  engines/
    actuarial_engine.py            — SDC, compute_sensor_weights(), payout calc
    spi_engine.py                  — SPI, CDD, phenology-derived critical window
    photo_engine.py                — Groq (primary) + Gemini (secondary) + rule fallback
    satellite_loader.py            — MODIS VCI loader
    weather_loader.py              — ERA5-Land rainfall loader
  routers/
    district.py                    — /district/* endpoints incl. /recommendations
    parametric.py                  — /parametric/calculate, /simulate
    photo.py                       — /photo/assess, /feedback, /weight-history
    backtest.py                    — /backtest/results
    meta.py                        — /meta/health, /meta/crops, /meta/mandals
  .env                             — GEMINI_API_KEY, GROQ_API_KEY (not committed)

ap-cropguard-frontend/src/
  components/
    Screen1_Overview.jsx           — District map, mandal grid, DataScopePanel, Field Dispatch
    Screen2_Insurance.jsx          — Parametric engine, SDC panel, backtest, premium table
    Screen3_Photo.jsx              — Photo upload, VRO feedback, weight history
    Sidebar.jsx                    — "Parametric Insurance / Disaster Loss Assessment / Kurnool District"
    TopBar.jsx                     — Screen titles, season toggle, 72hr badge
  utils/
    constants.js                   — THRESHOLD_LOSS_PCT=43, CROPS, SEASONS

data/
  satellite/                       — MODIS MOD13Q1 CSVs (GEE export)
  weather/                         — ERA5-Land per-mandal rainfall CSVs

MURTHY_QA_SCRIPT.md               — Full Murthy Q&A defense playbook
cc_api_contract.md                 — API contract (CC backend / Antigravity frontend)
prompt.md                          — Prompt-driven workflow: edit this, say "run the prompt"
```

---

## API Base URL & Key Endpoints

Base: `http://127.0.0.1:8010/api/v1`

| Endpoint | Purpose |
|---|---|
| GET `/meta/health` | Health check |
| GET `/district/overview?season=Kharif_2023` | District header stats |
| GET `/district/mandals?season=Kharif_2023` | Per-mandal data |
| GET `/district/recommendations?season=Kharif_2023&crop=Cotton` | SDC field dispatch intelligence |
| POST `/parametric/calculate` | Full insurance calculation (hero demo) |
| POST `/parametric/simulate` | Real-time slider simulation |
| GET `/backtest/results?season=Kharif_2023` | Historical backtest panel |
| POST `/photo/assess` | Photo crop damage (Groq/Gemini vision) |
| POST `/photo/feedback` | VRO agree/dispute → adaptive weight update |

---

## For Claude Chat (Demo Day Q&A Mode)

If you are Claude Chat being opened during a demo — read this file, then you know everything. Key things to be ready for:

1. **"What innovation does this have?"** → SDC lagged-damage detection. Satellite says ₹0, we say ₹48,794. The gap between sensors IS the signal.
2. **"Show me the ₹0 case."** → Kharif_2020, surplus year, both sensors agree, 8.1% → ₹0. Same crop, same mandal, different year.
3. **"Are these weights hand-picked?"** → No. Derived from Qiu 2022 empirical NDVI observability endpoints. Show the weight derivation proof on Screen 2.
4. **"What's real data vs mock?"** → MODIS and ERA5-Land are real. Backtest satellite proxy and photo satellite_loss are PoC placeholders (both labelled on screen).
5. **"Why 43% threshold?"** → AP Agriculture Department PMFBY standard threshold. We didn't choose it.
6. **"Can this scale statewide?"** → Roadmap on Screen 2. Same MODIS + ERA5 pipeline, 670+ mandals, just expand the GEE export polygon.

---

## For Claude Code (Implementation Mode)

- Read `prompt.md` before doing anything — that's the workflow file.
- Python command on this Windows machine: full path `C:\Users\rajes\AppData\Local\Programs\Python\Python313\python.exe` (not `python` or `py` — PATH unreliable).
- Port 8010 backend, 5173 frontend.
- Never recompute the hero demo numbers — they are locked in this file.
- The `satellite_loss = 55.0` placeholder in `photo.py` is intentional PoC — do not remove, it has on-screen disclosure.
- Do not rename "Adaptive Online Calibration" back to "Bayesian" or "RLHF" — those are wrong terminology and Murthy will attack them.


## Shared department data (C:\AP-Agri-Common)

@COMMON_DATA.md
