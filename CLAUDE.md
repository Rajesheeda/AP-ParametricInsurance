# AP Parametric Insurance & Disaster Loss Assessment — POC (case 100075)

> Bridge file for Claude Code and Claude Chat. For Claude Chat, paste this file plus `COMMON_DATA.md` at the start of the chat.
> The Kurnool demo (June 2026) is archived in `DEMO_KURNOOL_NOTES.md`. **Do not reuse the demo numbers.**

## Where we are
- **Stage:** POC. hierachAi was given a chance to prove the solution after the demo did not fully convince the judges.
- **Window:** 15 days from 2026-09-25, ending about 2026-10-10.
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
| Pilot assessment | `pipeline/p13_assessment.py` | Acute: event's own trigger (CHIRPS p99 / IBTrACS) + SAR flood above the dry-control noise floor, within 72 h, on standing crops, with a paddy-planting gate → payout / field verification / none. Season: trigger + VCI<35. |
| Dashboard | `pipeline/p14_dashboard_data.py` + `dashboard_src/index.html` | One self-contained file: `poc/data/dashboard/index.html` (open in a browser). |

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
- No PMFBY claims or CCE yield data yet, so any interim validation is labelled "interim", **never** "PMFBY".

## Murthy rules
1. Never present a proxy as actuals; every number carries its source.
2. State limits first: revisit, cloud, parcel size, irrigation unknowns.
3. No hand-picked constants. Use a citation or a value measured from our data.
4. Name methods correctly. Don't call something "AI" without a trained model evaluated on a held-out test.
5. Satellite depth first: SAR physics for flooded paddy, speckle filtering, orbit matching and cloud masking, then payouts.

## Environment
- Python: `py -3.13` (plain `python` is not on PATH). Libraries: geopandas, rapidfuzz, indic-transliteration, earthengine-api (this machine is not signed in to Earth Engine; the user runs GEE scripts in the Code Editor).
- The demo app in `ap-cropguard-backend/` (port 8010) and `ap-cropguard-frontend/` (port 5173) is still intact and will be reworked for the POC.

## Shared department data (C:\AP-Agri-Common)

@COMMON_DATA.md
