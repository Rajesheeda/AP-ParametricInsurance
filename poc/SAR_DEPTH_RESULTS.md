# SAR depth study: results against the rules in `SAR_DEPTH_STUDY.md`

Computed 2026-11-14 to 16, `gee_py/sar_depth.py` and `gee_py/flood_passes.py`, Earth Engine project
`ap-parametricinsurance`. Result files (gitignored): `data/derived/sar_depth_accuracy.json`, `sar_depth_events.json`,
`sar_depth_revisit.csv`, `sar_depth_fv.json`; samples `data/gee_out/out_depth_*.parquet`; coverage
`out_depth_cov_*.parquet`. The cyclone test is in `CYCLONE_TEST_RESULTS.md`.

## 0. Bug found and fixed first (amendment 1)
`ee_run.flood_event` scored a whole district with the district's first orbit-matched pass. Mandals outside that
pass's footprint read 0 ha flooded instead of "not imaged":

| Events | Mandals not imaged by the first pass |
|---|---|
| Palnadu, 5 of 7 events | 26 of 28 |
| YSR CCE windows, 11 of 17 | 19 of 40 |
| Parvathipuram Manyam, 4 of 7 events and Cyclone Arnab | 10 of 15 |
| Chittoor Michaung 2023 | 20 of 30 |

**Fix (`flood_passes.py`):** every orbit-matched pass in the 12-day window is mapped with the unchanged detection;
each mandal takes the earliest pass covering at least half of its cropland; the flood share is over imaged cropland;
a mandal with no such pass is NOT IMAGED. Where the old and new runs used the same pass, flooded area agrees to
0.00-0.03 ha (2.4 ha for Arnab, from boundary simplification). Old outputs: `data/gee_out/v1_district_pass/`.

Effect on the CCE test (166 YSR mandal-crop-years, loss = yield below 80% of normal; `dual_trigger_validation.json`):
| Test | As run (bug) | Corrected |
|---|---|---|
| Lane 1 product, both covers | 9 payouts, 7 real, 78% (CI 45-94), catches 12% | 17 payouts, 14 real, **82% (CI 59-94), catches 24%** |
| Sentinel-1 flood alone | 52 fired, 33% (22-46): fails the gate | 61 fired, **49% (37-61): passes** (base 36%) |
| ERA5 AND Sentinel-1 | 8 fired, 75% (41-93) | 16 fired, 81% (57-93) |
| Mandal-seasons with radar within 72 h | 94 of 147 | **68 of 147** |
13 of the 14 real Lane 1 payouts are 2020 (Nivar), 1 is 2023: the evidence is still essentially one storm.
Positive control (Budameru 2024): unchanged, PASS (5.61% vs 1.41%, 19 of 19 mandals imaged).

## A. Accuracy against Sentinel-2 (PPT: >= 80%)
24 events assessed: **5 scored**; 2 sampled but below 30 reference-flood points (Asani 2022: 1, Palnadu Jul 2023: 4);
17 unscorable: 7 without a Sentinel-2 image within 1 day (incl. Budameru), 10 without clear cropland inside the radar
footprint (incl. Arnab, Montha).

| Pooled, 5 events | Value (95% CI) |
|---|---|
| Overall accuracy (PPT metric) | **96.4% (95.0-97.9): criterion met** |
| Flood precision (user's accuracy) | 68% (65-70) |
| Flood recall (producer's accuracy) | 9% (6-13) |
| Flood F1 | 0.16 |

| Event | Reference-flood points | OA | Precision | Recall | F1 |
|---|---|---|---|---|---|
| Chittoor, Nov 2021 | 328 | 88.2% | 97% | 15% | 0.26 |
| Chittoor, Mandous Dec 2022 | 223 | 96.0% | 71% | 36% | 0.48 |
| Manyam, 9 Sep 2026 | 235 | 97.0% | 75% | 3% | 0.07 |
| Manyam, 20 Sep 2026 | 253 | 96.3% | 81% | 5% | 0.09 |
| Palnadu, Sep 2020 | 78 | 97.7% | 25% | 47% | 0.33 |

**Reading.** Overall accuracy is high because most land is dry (declared in advance). When the radar says flood,
optical sees water about two times in three; but the radar finds only about one in ten of the new water optical
sees. In the paddy season optical "new water" includes water standing in growing paddy, which C-band VH under a
canopy does not show as a drop (see C). This is why relief never depends on radar, and why in insurance a radar
miss holds the payout and becomes a basis-risk case that relief covers.

## B. Processing sensitivity (same points; nothing adopted this season)
| Variant | Precision | Recall | F1 |
|---|---|---|---|
| `v1` frozen | 68% | 9% | 0.16 |
| `lee` Lee 7x7, ENL 4.4 | 71% | 10% | 0.17 |
| `d2` / `d4` change 2 / 4 dB | 64% / 71% | 9% / 8% | 0.16 / 0.15 |
| `tm1` / `tp1` Otsu -1 / +1 dB | 72% / 77% | 7% / 16% | 0.12 / 0.26 |
| `single` no change detection | 33% | 10% | 0.15 |
The frozen 3 dB change and the 50 m median are not fragile (2-4 dB and a Lee filter change little). Change detection
matters: without it precision halves. A water threshold 1 dB higher doubles recall, a candidate for next season,
through the gate.

## C. Flooded vegetation (double bounce)
Budameru 2024: VV rise >= 3 dB on 5.4% of cropland vs 3.5% and 1.6% on the dry control dates: ratio 1.55, below the
declared factor of 2. **No usable signal**: at C-band a VV rise is as common from crop growth and soil change as from
flood under canopy. The drop-only rule stays.

## D. Probability of a radar image within 72 h
Over the pilot mandals Sentinel-1 has imaged on a 12-day repeat for the whole record: S1B never imaged here
systematically, S1C appeared once, and S1D took over S1A's track in mid-2026.
| Mandal | P(within 72 h), 2021 / 2022-24 / 2025-26 | Median wait, 2025-26 |
|---|---|---|
| Balijipeta, Chapad, Khajipet (two tracks) | 49% / 47-48% / 49% | 73-74 h |
| Gurazala, Sattenapalle, Parvathipuram, Vedurukuppam (one track) | 24-25% / 23-24% / 24-25% | 143-149 h |
72 hours is not a radar promise here. The 72-hour assessment is carried by rain, photos and AEO visits; radar
confirms later.
