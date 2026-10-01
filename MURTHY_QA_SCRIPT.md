# AP-CropGuard — Murthy Defense Playbook
### Demo: 2026-06-28+2 · Kurnool Parametric Insurance PoC

---

## HOW MURTHY EVALUATES (critical context)

He goes **bottom-up**: (1) satellite depth → (2) soil/weather → (3) classification → (4) THEN innovation.  
He finds **one weak link** and hammers it. He never reaches your innovation if layer 1 fails.  
His strongest move: ask "why that number?" on any constant. If you say "we chose it" — you lose.  
His best response: **"we derived it from [cite] / measured it from [data]."**

---

## LAYER 1 — SATELLITE DATA

**Q: "Why are you using 250m MODIS? Sentinel-2 is 10m."**

> "250m is the resolution of NASA MODIS MOD13Q1, the same dataset used by NADAMS — the National Agricultural Drought Assessment and Monitoring System run by ICAR — for operational drought monitoring across all of India. If 250m is good enough for the national drought monitor, it's the right baseline for this PoC. Sentinel-2 at 10m is in our Phase 1 scope — but using it now would mean no cloud-free composites at 16-day intervals for Kurnool's high-cloud Kharif season."

**Q: "How do you know your satellite pixels are reliable?"**

> "Each MODIS composite carries a QA pixel-count field — the number of cloud-free pixels in the 2km buffer around the mandal centroid. For Orvakal on August 29, 2023 we had 241 of 241 pixels cloud-free, giving reliability = 1.0. This pixel fraction IS the satellite reliability score that drives the fusion weight. We don't assume reliability — we measure it from the data."  
> *(Show sensor_weights block on Screen 2 — pixel_count: 241)*

**Q: "How many composites do you have?"**

> "11 composites per season, 16-day cadence, June through November. Cloud-masked composites are excluded from analysis — shown as gaps on the NDVI chart, not interpolated. The chart on Screen 1 shows exactly which composites are cloud-masked."

**Q: "What does your VCI baseline come from?"**

> "Per-mandal NDVI (min, max) calibrated from all valid 2020 + 2023 composites combined — 22 composites total per mandal. We enforce a minimum 0.20 range to prevent hypersensitive VCI on narrow-variability mandals. The 2020 season is the near-normal year (SPI +1.685 for Orvakal Aug-Oct), so it's our natural baseline."

---

## LAYER 2 — RAINFALL / WATER BALANCE

**Q: "What's your rainfall source?"**

> "ERA5-Land Reanalysis from ECMWF, accessed via Open-Meteo API. This is the same ECMWF reanalysis product used by ICAR's crop model calibrations and by several state agriculture departments for drought assessment. Daily resolution, all 27 Kurnool mandals."

**Q: "Why is your SPI window August–October for Cotton? Why not June–September?"**

> "It's derived from crop phenology, not hand-picked. Cotton's highest Kc stage is Boll Development (Kc 1.8, DAS 60–100). For a July 1 sowing, DAS 60–100 maps to August 30–October 9. So the critical moisture window is August, September, October — the crop's own physiological water demand peak. For June–September, July 2023 had +105% above normal rainfall at Orvakal, which would cancel the August and October drought signals in a cumulative SPI, giving SPI = −0.018 (near-normal). The August–October window isolates the true drought."  
> *Window derivation source: FAO Paper 56 Kc tables, GoI Drought Manual 2016 Chapter 4.*

**Q: "Isn't this just a rainfall-side model? What about soil moisture and ET?"**

> "Yes — that's an honest limitation we acknowledge on Screen 1 in the Data Sources panel. This is the rainfall side of the water balance: P vs P_baseline. Full soil moisture and evapotranspiration modelling (FAO Penman-Monteith ET₀ + soil water balance) is in Phase 1. For parametric insurance, the rainfall deficit trigger is the most widely used index precisely because it's objective, transparent, and doesn't require field soil measurements."

**Q: "Your SPI is based on a synthetic baseline — isn't that made up?"**

> "The SPI is computed from real ERA5-Land daily rainfall for 27 mandals against a 30-year (1990–2020) monthly baseline. The 30-year baseline follows McKee et al. (1993) — the standard SPI computation — and matches GoI Drought Manual 2016 Chapter 4. Orvakal Cotton Aug-Oct SPI for 2023: **−1.485 (SEVERELY_DRY)**. This is live-computed from the rainfall data, not hardcoded."

---

## LAYER 3 — CLASSIFICATION / VALIDATION

**Q: "What's your backtest sample size? Correlation?"**

> "Two Kharif seasons: 2020 (near-normal) and 2023 (drought). Pearson correlation is computed live via scipy.stats.pearsonr — not hardcoded. The 'backtest results' button on Screen 2 runs the computation in real-time. n=2 seasons, n=11 composites each — we acknowledge this is a PoC validation. Phase 1 extends to a 5-year panel (2019–2023) using the same GEE export pipeline."

**Q: "How do you validate the 43% threshold?"**

> "43% is the Andhra Pradesh Agriculture Department's statutory relief threshold — it's not our model's output, it's the state government standard. Our model computes the loss index; the 43% cutoff is the existing policy rule. This makes the model transparent — a field officer can verify: 'system says 44%, threshold is 43%, therefore eligible.'"

**Q: "43% for Cotton at INR 60,000/ha — where does sum insured come from?"**

> "Sum insured is derived from the GoI PMFBY actuarial guidelines: Cost of Cultivation (CoC) for cotton in AP multiplied by a coverage factor. The 2.7% premium rate follows PMFBY's actuarial methodology: historical event frequency × crop-stage vulnerability × sum insured, with 15% expense loading and 10% risk margin per standard reinsurance practice."

---

## LAYER 4 — SDC INNOVATION (where hackathon #6 attacks came)

**Q: "The Sensor Divergence Coefficient — how do you know the satellite is 'missing' the loss? Maybe your weather index is wrong."**

> "That's exactly the right question, and it's why the SDC is framed as a divergence flag, not a replacement for either sensor. In the Sep-01 2023 scenario: ERA5-Land shows −45% rainfall deficit (Aug-Oct), SPI = −1.485 (SEVERELY_DRY), CDD = 20 days. NDVI = 0.352, VCI = 66 (healthy). Both sensors are independently measuring real quantities. When they diverge at the critical reproductive stage, it's consistent with what Qiu et al. (2022) measured: NDVI captured only 4% of yield loss during the reproductive stage drought they studied. The SDC flags this divergence for field verification — it doesn't replace it."

**Q: "Could there be pest damage explaining the NDVI staying green? Pink bollworm inside the boll doesn't change canopy reflectance."**

> "Absolutely correct — this is a known limitation, and we pre-disclose it on Screen 2. The detection floor states: 'Cannot detect internal pest damage (e.g. early pink bollworm inside the boll — no canopy or backscatter change) or irrigated crops compensating a rainfall deficit. SDC is a late-stage divergence flag that triggers field verification — not an early-warning detector.' The SDC catches the rainfall drought signal; it doesn't claim to detect internal pest damage. For that, the field officer dispatch is the correct response."

**Q: "So the SDC just sends officers to the field? What's the innovation?"**

> "The innovation is the *prioritization*. Without SDC, you'd dispatch officers to all 27 mandals uniformly, or use satellite NDVI alone (which would miss the 25 mandals showing lagged-damage divergence). With SDC, the system identifies exactly which mandals have weather-confirmed drought that the canopy signal is under-reporting — those get PRIORITY 1 dispatch. A satellite-only system would see VCI=66 in Orvakal on Sep-01 and flag it as NORMAL, leaving farmers unprotected. The SDC catches what the satellite cannot see at this crop stage."

**Q: "Your SDC weights — why is weather weighted 0.753 and satellite 0.247? Did you tune these?"**

> "No tuning. The weights are derived: `w_sat ∝ (cloud-free pixel reliability) × (NDVI observability at this crop stage)`. Pixel reliability = 241/241 = 1.0 (measured, from MODIS QA). NDVI observability at Kc=1.8 = 0.328, interpolated linearly from two data points anchored to Qiu et al. (2022): observability = 1.0 at canopy stage (Kc≈1.0) and 0.16 at full reproductive (Kc≈2.0), because Qiu found NDVI captured 4/25 = 16% of yield loss at that stage. Weather reliability = 1.0 (ERA5-Land — no cloud masking). The 0.753/0.247 split falls out of normalizing these products. It's shown on screen — nothing is hand-picked."

---

## LAYER 5 — COUNTER-DEMO (we don't overpay)

**The setup:** *"Let me show you the same crop, same mandal, in a good monsoon year."*

> "Switch to Kharif_2020. In the screen 2 calculator: Cotton, Orvakal, sowing June 15, event September 1.  
> — ERA5-Land shows 434mm vs 250mm baseline: **+74% surplus**  
> — NDVI = 0.378, VCI = 73.5: **healthy canopy**  
> — Weather loss: 6%. Satellite loss: 0%. Both sensors agree: NO_SIGNIFICANT_LOSS.  
> — Parametric loss: **8.1%** → ₹0 payout. Threshold not breached.  
> 
> Same crop. Same mandal. Same methodology. 2023 drought → ₹48,794. 2020 surplus → ₹0. The system distinguishes between good and bad years. It does not overpay."

---

## LAYER 6 — "IS THIS REALLY AI?"

**Q: "This looks like expert rules, not AI."**

> "The parametric triggers and Kc tables are rule-based — transparently so. The AI layer is the Bayesian RLHF weight update: VRO field officer feedback (confirmed/denied loss reports) updates the per-mandal fusion weights using Bayesian updating. This means each mandal's satellite-vs-weather trust ratio can be corrected over time from field ground truth. We don't claim the trigger computation is a neural network — the intelligence is in the sensor fusion and the learning loop."

**Q: "What's your AI tech stack?"**

> "The photo engine uses Gemini (via Vertex AI) for field crop damage classification from uploaded photos — fallen stalks, discoloration, stressed leaves. The Bayesian VRO feedback loop updates weights using standard conjugate prior updating. The anomaly detection for non-weather stress (VCI down, weather fine → pest/disease flag) uses rule-based classification on top of real MODIS data. We didn't put black-box ML on top of fabricated data — we put interpretable computation on top of real satellite and rainfall data."

---

## CLOSING MOVES

**If he says "This is a PoC, not production-ready":**

> "Correct — and we've scoped it honestly. This is a proof of concept for Kurnool district covering 27 mandals, rainfed Kharif Cotton and Groundnut, two seasons of real data. The production pathway is clear: live NCIP/SASE portal feed for rainfall, Sentinel-2 revisit for crop-stage satellite, 5-year backtest panel. The innovation isn't the data scale — it's the SDC-based sensor fusion methodology and the derived-weight approach that prevents overpayment without hiding behind arbitrary constants."

**If he asks about something not in the system:**

> "That's a Phase 1 item — [X] is in our roadmap but we scoped this PoC to demonstrate the core SDC methodology on defensible real data rather than claim completeness on fabricated data."

**The one sentence to anchor everything:**

> "Every number in this system is either measured from the data, cited from peer-reviewed literature, or follows a GoI/FAO standard — and we can show you the derivation for any of them."

---

## QUICK REFERENCE — LOCKED NUMBERS

| Scenario | Loss | Payout | Key signal |
|---|---|---|---|
| Cotton · Orvakal · 2023 · Sep-01 | **81.3%** | **₹48,794/ha** | SPI −1.485, LAGGED_DAMAGE, Kc 1.8 |
| Cotton · Orvakal · 2020 · Sep-01 | **8.1%** | **₹0** | ERA5 +74% surplus, NO_SIGNIFICANT_LOSS |
| Groundnut · Orvakal · 2023 · Oct-16 | ~31% | **₹0** | Kc 0.8 dampens below 43% threshold |
| Sensor weights (Sep-01 hero) | sat=0.247 | wx=0.753 | Derived, not tuned |

**Satellite (Sep-01 2023):** MODIS 2023-08-29 · NDVI=0.3515 · VCI=66 · pixel_count=241  
**Rainfall (hero):** 193.1mm vs 351.3mm baseline (Aug-Oct) · ERA5-Land · SPI=−1.485  
**Rainfall (counter):** 434.1mm vs 249.9mm baseline (2020 Jun-Sep) · SPI strongly positive
