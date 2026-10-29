# AP Parametric Insurance & Disaster Loss Assessment — POC (case 100075)

> Bridge file for Claude Code and Claude Chat. For Claude Chat, paste this file plus `COMMON_DATA.md` at the start of the chat.
> The Kurnool demo (June 2026) is archived in `DEMO_KURNOOL_NOTES.md`. **Do not reuse the demo numbers.**

## Where we are
- **Stage:** POC. hierachAi was given a chance to prove the solution after the demo did not fully convince the judges.
- **Window:** POC build 2026-09-25 to about 2026-10-10. **Demo: 30 October 2026.**
- **Judges:** Murthy (remote-sensing and agri-science expert, hostile, works bottom-up) and Kalyan / Mohiuddin (Crop Insurance Section).
- **Scope:**
  - Kharif: Palnadu (22), YSR Kadapa (11), Parvathipuram Manyam (14).
  - Rabi: Chittoor (10), which we proposed instead of East Godavari because no East Godavari data exists.
  - Pilot: 5–7 mandals. Live season: Kharif 2026.
- **Success criteria (PPT):**
  - ≥75% correlation between triggers and actual losses.
  - ≥80% flood-mapping accuracy vs APSDMA.
  - Loss assessment within 72 hours.
  - 5-year back-test vs PMFBY claims and CCE yields.
- **Department ask:** 2 items, `C:\AP-Agri-Common\requests\parametric_100075_data_request.md`, with the reasoning in `POC_DATA_ASK.md`. **Build without assuming the department replies.** When their data arrives, swap it in.

## Approach
0. **Two lanes, never mixed (2026-10-30, answers Murthy Q6/Q7/Q9).**
   - **Lane 1, parametric insurance:** index only; photos and field visits never change a payout. Each cover is a dual trigger:
     - Cover A, season: WBCIS-structure rainfall AND VCI<35.
     - Cover B, catastrophe: ERA5 3-day RP5→RP25 AND Sentinel-1 flood on standing crops above the false-alarm floor.
     - FAO-56 stages run from each booking's own e-Panta sowing week.
   - **Index qualification gate:** an index enters the contract only if the lower Wilson 95% bound of its CCE precision is above the base loss rate. Re-run every season.
   - **Lane 2, SDRF relief (≥33% damage):** 72-hour radar map, CCE-calibrated loss estimate, quality-gated photo / AEO enumeration.
   - **Basis-risk log:** records cases where the two lanes disagree.
   - **Honest result:** the declared 3-source consensus × SAR design FAILED on CCE (17 payouts, 2 real). ERA5 × SAR was chosen after seeing the data (hits mostly Nivar 2020). Lane 1 product: 9 payouts, 7 real (78%, CI 45–94), catches 12% of losses. Rainfall-only WBCIS-style: 24 payouts, 20 false.
1. **Parcel-aware.** e-Panta gives crop, variety, sowing date and acres per survey number. Joining to APAIMS cadastral gives a per-parcel satellite series, and each parcel's crop stage comes from its own sowing date instead of an assumed one.
2. **Cohort-normalized change detection.** A parcel is compared with parcels of the same crop and sowing week outside the event footprint. This removes the phenology-timing confound (the demo's weak spot).
3. **Multi-peril triggers from published definitions only:**
   - IMD rain classes and seasonal-departure categories.
   - ETCCDI-style 99th-percentile extremes.
   - SPI (McKee 1993).
   - IMD cyclone ≥34 kt (IBTrACS).
   - UN-SPIDER Sentinel-1 flood change detection.
4. **Satellite:**
   - Sentinel-1 SAR (sees through monsoon cloud), orbit-matched pre/post for flood.
   - Sentinel-2 NDVI with s2cloudless and SCL masking.
   - Every result carries the date of the image it came from and a confidence level, because the revisit gap can miss the 72-hour window.
5. **Photo layer:** geotag must fall inside the claimed parcel polygon, and the crop must match the e-Panta booking.

## Pipeline (`poc/`; outputs in `poc/data/`, gitignored, never commit department data)
| Step | File | Output / status |
|---|---|---|
| YSR e-Panta ↔ cadastral join | `pipeline/p01_ysr_parcel_join.py` | Share of booked acres joined: exact + base about 52% (was 6%). Cadastral covers only 424 of 753 villages, which is the ceiling. |
| Mandal boundaries | `pipeline/p02_mandal_boundaries.py` | geoBoundaries ADM3 (open). 115 of 116 mandals matched; Telugu names transliterated; Sadum unmatched. |
| Rainfall screening | `pipeline/p03_rainfall.py` | ERA5-Land daily at mandal centroid, 1995 onward (Open-Meteo). |
| GEE upload files | `pipeline/p04_gee_assets.py` | `data/derived/gee_upload/poc_mandals.zip`, `ysr_parcels.zip` (89k parcels, dominant crop, purity and sowing date per Kharif season). |
| Event catalogue | `pipeline/p05_event_catalogue.py` | Flood / unseasonal rain / drought / cyclone per mandal, 2020–2026 (ERA5 screening; rerun on CHIRPS). Matches known events: Sep 2024 Palnadu floods, Michaung, Nivar, Gulab, Montha; live Manyam events Jul and Sep 2026. |
| Exposure | `pipeline/p06_exposure.py` | Focus-crop acres per mandal (e-Panta 2025), plus YSR parcel coverage. |
| Pilot mandals | `pipeline/p07_pilot_selection.py` | Written rule → 7 mandals: Parvathipuram, Balijipeta (Manyam); Gurazala, Sattenapalle (Palnadu); Chapad, Khajipet (YSR); Vedurukuppam (Chittoor Rabi). |
| GEE-3 event list | `pipeline/p08_flood_event_list.py` | 22 events written into `gee/GEE3_s1_flood_events.js` (4 rainiest per district, all named cyclones, all 2026 events). |
| Earth Engine runner | `gee_py/ee_run.py <project> <cmd>` | Runs everything from Python in project `ap-early-warning` (upload, chirps, ts, flood, modis, status, download); outputs are saved to `data/gee_out/`. The `gee/*.js` files are the earlier Code Editor versions. |
| CHIRPS daily | `pipeline/p09_chirps_long.py` | CHIRPS mandal means 1995 – Aug 2026 (it lags about a month). Event catalogue rerun on CHIRPS: 2023 drought shows (El Niño); ERA5 instead flags 2025. |
| Triggers & premium | `pipeline/p10_triggers.py` | WBCIS-style: FAO-56 stages × deficit/excess/dry-spell → percentile z → season stress S; trigger 1-in-5, exit 1-in-25. Burn cost about 12.5% of sum insured (7% at 1-in-10/50, 20% at 1-in-3/15). |
| Interim validation | `pipeline/p11_validate_modis.py` | Rainfall stress vs MODIS VCI (Kogan, VCI<35): mandal-season Spearman −0.13; district-year −0.35 YSR, −0.30 Palnadu, 0 Manyam. Rainfall alone has high basis risk. |
| Parcel cross-check | `pipeline/p12_parcel_crosscheck.py` | Michaung 2023 YSR: the standing-crop gate removed 60% of SAR-flagged parcels (harvested / Rabi land preparation); the remaining ones show no NDVI loss vs cohort, so this tests false positives, not loss. |
| Pilot assessment | `pipeline/p13_assessment.py` | Two lanes: `lane1_payout_pct`/`lane1_decision` (dual trigger), `lane2_action` (PRIORITY ENUMERATION: RADAR-MAPPED / ENUMERATION: PHOTO / AEO / MONITOR), `evidence_grade` A/B/C, `basis_risk_flag`, rain from CHIRPS / ERA5 / IMERG. `action` = INDEX PAYOUT / RELIEF ENUMERATION / NO PAYOUT. |
| GPM IMERG | `gee_py/imerg.py <project>` | Daily mandal means Jun 2000 – Sep 2026 (113 mandals); catalogue `p05 rain_imerg_daily.parquet`. CCE: catches 47% of losses but 67% false alarms; nobody catches Nov 2021 (report 7.8). |
| SAR for CCE years | `gee_py/sar_cce.py <project>` | Frozen flood method on 17 YSR acute windows 2019–25 × 40 mandals → `gee_out/out_sarcce_*.parquet`. |
| Dual trigger / gate | `pipeline/p22_dual_trigger.py` | Candidate indices vs CCE with Wilson CI and gate; writes `cat_cover_levels.parquet`, `dual_trigger_validation.json` (report 7.9). |
| Per-farmer payouts | `pipeline/p23_farmer_payouts.py` | 221,555 e-Panta bookings (Chapad, Khajipet, Gurazala, Sattenapalle; K2023–25) on own sowing-week cohorts; 21,289 flip vs the mandal calendar; Gurazala 2023 pays 13,096. API `GET /api/v1/poc/farmer/{villages,payouts}` (`routers/poc_farmer.py`). |
| **CCE validation** | `pipeline/p15_validate_cce.py` | Real Department CCE yields (4 CSVs in `C:\AP-Agri-Common\data`, Oct 2026), YSR Kadapa, 166 mandal-crop-years 2019–2025. Loss = yield < 70/80/90% of the mandal's leave-one-out normal. Season trigger catches 7% of losses; + acute layer on ERA5 37% (agreement 60%); CHIRPS misses Nivar 2020; both miss Nov 2021 floods. Below the 75% target; reported as basis risk. |
| Fused loss model | `pipeline/p16_loss_model.py` | Tested leave-one-year-out vs CCE: AUC 0.53/0.50, i.e. no skill, so it is **not used** (report 7.7). |
| Soil moisture | `gee_py/soil_moisture.py`, `pipeline/p17_soil_moisture.py` | ERA5-Land root zone (2000–25) + SMAP surface (2016–25), mid-stage percentile. In YSR, dry soil does NOT mean loss (irrigation); drought trigger + dry soil precision 0–11% vs 36% base. Evidence only. |
| Yield-loss calibration | `pipeline/p18_loss_calibration.py` | Median CCE loss by trigger type: acute 25% (n=30), drought 10% (n=11), none 0% (n=115); attached to every decision. |
| Alerts | `pipeline/p19_alerts.py` | Telugu + English alerts from decisions (machine-drafted Telugu, needs Department review); dashboard tab. |
| Live refresh / one command | `pipeline/p20_live_refresh.py`, `poc/run_all.py [--live <ee-project>]` | ERA5 to about yesterday−5, CHIRPS where published, new events mapped with the frozen radar method. |
| Pest classifier | `poc/photo/pest_train.py` | Trained on Department images, held-out 60% (53–66%) vs Gemini 47% on the same images (McNemar p=0.02); top-3 suggestion in photo verification. |
| Dashboard images | `pipeline/p21_dashboard_images.py <ee-project>` | Real images only: Sentinel-2 views of each pilot mandal and the Krishna delta (hero), Sentinel-1 before/after with detected flood for Budameru 2024 and Manyam Sep 2026, Department field photos with the trained model's prediction. Saved to `data/dashboard/img/` and embedded by p14. |
| Dashboard | `pipeline/p14_dashboard_data.py` + `dashboard_src/index.html` | Dark AI-style redesign (2026-10-29): sidebar, satellite hero, mandal image cards, radar before/after slider, field photo gallery, CCE chart. Two-lane rewrite (2026-10-30): tabs Disasters & relief (Lane 2), Insurance product (term sheet + qualification gate), Farmer payouts (backend look-up). One self-contained file (~4 MB): `poc/data/dashboard/index.html`. Opened via the backend at `http://127.0.0.1:8010/poc/` it also has the photo tab. |
| Photo verification (Module B) | `poc/photo/verify.py`, `poc/photo/quality.py`, `ap-cropguard-backend/routers/poc_photo.py` | Lane 2 evidence only. `POST /api/v1/poc/photo/verify`, `GET /api/v1/poc/photo/log`. Quality gate first (Laplacian blur, exposure, clipping, resolution; percentiles of 982 Department photos; 91% genuine accepted, 100% degraded refused → RETAKE PHOTO). Then checks EXIF geotag, pilot mandal, YSR cadastral parcel and survey number, e-Panta booking (all seasons standing on that date), timing vs event, vision crop/damage, crop match → verdict + case resolution (incl. basis-risk catch). The demo engine's rule-based fallback is **never** counted as evidence. Log: `poc/data/photo_evidence.jsonl`. |

Flood method (current, in `ee_run.py`): VH, orbit-matched pre/post, 50 m focal median; water threshold = Otsu on a balanced sample of JRC permanent water + cropland (about −21 to −24 dB); change ≥ 3 dB drop (Clement et al. 2018); JRC permanent water, HAND > 15 m and < 8-pixel clusters masked. Radar was within 72 h for only about 8 of 20 events.
**Positive control** (`poc/POSITIVE_CONTROL.md`, `gee_py/pc_run.py`, rule declared before running): Budameru/Krishna floods, Sep 2024, 19 mandals within 30 km of Vijayawada → PASS. Flooded cropland 5.61% vs 1.41% dry floor; 18–22% in Vijayawada Rural/Urban and Mangalagiri. The image was 265 h after the event (outside 72 h).
Second Earth Engine project: `ap-parametricinsurance` (registered 2026-10-08; its asset root wasn't provisioned yet, so `pc_run.py direct` computes without assets).
Report: `POC_REPORT.md` (methods, results, validation, limits, references).
Earth Engine project `ap-early-warning` went into **restricted mode** (noncommercial quota exhausted) on 2026-10-08, so queued tasks run slowly.
APAIMS `objectid` is not unique (8.5k duplicates); `p04` now issues a row-based `pid` for any re-upload, and current parcel outputs exclude ambiguous IDs.

## Known data limits (state these before Murthy finds them)
- Parcel boundaries exist only for YSR (about 56% of villages). Palnadu and Manyam run at mandal/village level until cadastral is shared.
- Palnadu and Manyam e-Panta names are in Telugu only; they are joined by transliteration and fuzzy matching, with reviewed exceptions listed in the script.
- Irrigation source is unknown for about 70% of YSR acreage and exists for Kharif 2026 only.
- ERA5-Land underestimates convective extremes, so it is used for screening only; triggers use CHIRPS (and IMD if reachable; imdpune.gov.in times out from here).
- CCE yields exist for YSR Kadapa only (received Oct 2026); no PMFBY claim amounts and nothing for Palnadu, Manyam or Chittoor. The department said no further data will come.

## Murthy rules
1. Never present a proxy as actuals; every number carries its source.
2. State limits first: revisit, cloud, parcel size, irrigation unknowns.
3. No hand-picked constants. Use a citation or a value measured from our data.
4. Name methods correctly. Don't call something "AI" without a trained model evaluated on a held-out test.
5. Satellite depth first: SAR physics for flooded paddy, speckle filtering, orbit matching and cloud masking, then payouts.

## Environment
- Python: `py -3.13` (plain `python` is not on PATH). Libraries: geopandas, rapidfuzz, indic-transliteration, earthengine-api (this machine is not signed in to Earth Engine; the user runs GEE scripts in the Code Editor).
- Start the backend with the `poc-backend` entry in `.claude/launch.json` (uvicorn on 127.0.0.1:8010), then open `http://127.0.0.1:8010/poc/`.
- Vision (`engines/photo_engine.py`): order from `VISION_ORDER` (default `gemini,groq`). Models: `GEMINI_MODEL` (default `gemini-3.5-flash-lite`), `GROQ_VISION_MODEL` (default `qwen/qwen3.8-27b`; llama-4-scout was withdrawn). Groq key replaced 2026-10-09.
- Lessons: a prompt that names the claimed crop or lists local crops made models "see" that crop in a plain green image, so the POC check is blind (no crop named) and the prompt asks for "none" when no crop is visible. Both models then return "none" for non-crop images.
- Pest/disease benchmark (`poc/photo/pest_sample.py`, `pest_benchmark.py`; images in `poc/data/pest_benchmark/`, gitignored): Department Label Studio repo (`C:\AP-Agri-Common\data\LabelStudio`, 79k images / 28k labelled; its script holds an API key, never copy it). 8 post-flood classes × 30, blind: Gemini crop 100%, any pest/disease 90%, correct name 47% (41–54%); Groq Qwen 20% (rate-limited). So vision = crop check + suggestion only; dedicated detector is post-POC work.
- The old Kurnool demo screens in `ap-cropguard-frontend/` are unchanged.

## Shared department data (C:\AP-Agri-Common)

@COMMON_DATA.md
