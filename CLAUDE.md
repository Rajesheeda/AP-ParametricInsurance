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
| GEE-1 CHIRPS areal rainfall | `gee/GEE1_chirps_mandal_daily.js` | User runs it; replaces the ERA5 point series for triggers. |
| GEE-2 season time series | `gee/GEE2_season_timeseries.js` | User runs it: NDVI + VH/VV every 10 days per YSR parcel and per mandal cropland. |

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
