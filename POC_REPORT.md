# Parametric Insurance & Disaster Loss Assessment: POC technical report

**Case 100075 · hierachAi Technologies · draft of 2026-10-08**
**Pilot:**
- Kharif: Palnadu, YSR Kadapa, Parvathipuram Manyam.
- Rabi: Chittoor, proposed in place of East Godavari because no East Godavari data was available.

**Status of validation:** the triggers have been tested against **real CCE yields** shared by the Department for YSR Kadapa (26 mandals, Kharif 2019–2025, section 7.4). No CCE or claims were available for Palnadu, Parvathipuram Manyam or Chittoor; validation there is interim (second sensor only).

---

## 1. Summary

- **What we built:** an end-to-end pipeline. It takes department e-Panta and cadastral data plus open satellite and weather data, and produces a per-mandal, per-crop decision for every disaster event and season: **parametric payout**, **field / photo verification**, or **no payout**.
- **Weather trigger:** cited methods only (IMD, ETCCDI, SPI, FAO-56, WBCIS structure, UN-SPIDER, Otsu, Kogan VCI). No hand-picked thresholds.
- **Satellite confirmation:** gated by what the department data says is actually in the field. That is the crop and sowing date per parcel, so we know whether a crop was standing on the event date.

**Main findings**

| Finding | Number |
|---|---|
| Rainfall-trigger premium (pure burn cost), 1-in-5 trigger / 1-in-25 exit | **12.5%** of sum insured (7% to 20% across design choices) |
| Agreement of rainfall triggers with satellite crop condition (MODIS VCI), mandal-season | Spearman **−0.13**: right direction, weak. This is the basis risk of rainfall-only cover. |
| Same, district-year (drought districts) | **−0.35** YSR Kadapa, **−0.30** Palnadu, **0** Manyam (flood-driven) |
| Sentinel-1 image inside 72 h of the event | **8 of 22** events (median 96 h) |
| Sentinel-1 "flood" on dry control dates (false-alarm floor) | median 0.1–0.6% of cropland, up to 9.5% in one mandal |
| Pilot events whose flooded cropland beat that floor within 72 h | **0 of 22** |
| Positive control: Budameru / Krishna floods, Sep 2024 (rule declared in advance) | **PASS:** 5.6% flooded cropland vs 1.4% dry floor; up to 21% in the flooded mandals |
| **Real CCE losses caught by weather triggers alone** (YSR, 166 mandal-crop-years, loss = yield < 80% of normal) | **7%** season trigger only; **37%** with the acute layer on ERA5 (agreement 60%). Below the ≥75% target. |
| Seasons where the rainfall trigger and satellite agree on drought | Gurazala 2023 (cotton, chilli, paddy) |
| False-positive reduction from the standing-crop gate (Michaung 2023, YSR, parcel level) | **60%** of radar-flagged parcels removed (harvested or not yet sown) |

**What this means**
- In these inland, semi-arid and canal-irrigated pilot mandals, radar flood signal at mandal scale **cannot be told apart from routine field water**.
- The system therefore **never auto-pays on radar alone**. It routes those cases to field and photo verification within the 72-hour window.
- Automatic payout happens only where two independent sensors agree.

---

## 2. Data

| Data | Source | Use |
|---|---|---|
| Crop, variety, sowing date, acres per survey number, Kharif 2023–26 (Chittoor also Rabi 2023–25) | e-Panta (Department) | Exposure; crop stage per parcel |
| Parcel polygons, YSR Kadapa | APAIMS cadastral (Department) | Parcel-level satellite analysis |
| Irrigation source, Kharif 2026 | Department | Context only (about 70% unknown in YSR) |
| Daily rainfall 1995 – Aug 2026, 0.05° | CHIRPS v2 (UCSB) | Triggers |
| Daily rainfall to Sep 2026 | ERA5 (ECMWF) | Screening; provisional live events |
| Cyclone tracks | IBTrACS v4 (NOAA) | Cyclone trigger |
| SAR, 10 m | Sentinel-1 GRD (ESA) | Flood extent; radar crop time series |
| Optical, 10 m | Sentinel-2 SR + s2cloudless (ESA) | Crop condition |
| NDVI 250 m, 2001–2026 | MODIS MOD13Q1 (NASA) | Long-record vegetation condition (VCI) |
| Cropland, permanent water, terrain | ESA WorldCover 2021, JRC GSW 1.4, MERIT Hydro HAND | Masks |
| Mandal boundaries | geoBoundaries ADM3 (open) | Aggregation |

**Linking e-Panta to the cadastral (YSR Kadapa)**
- Villages are matched within each mandal by the share of e-Panta survey numbers found in the cadastral village, which is robust to spelling.
- Booked parcels are then joined at the finest survey level that exists in the polygons.
- About **52%** of booked Kharif acres join to a polygon each year (was 6% with name matching). The cadastral covers 424 of 753 villages, so this is near the ceiling.
- 8.5k APAIMS polygons share an `objectid`; those are excluded from parcel analysis.

**Pilot mandals (written rule)**
- **Eligible:** at least one qualifying event in 2020–2025.
- **Ranked by:** focus-crop acres (e-Panta 2025). YSR also needs ≥50% parcel coverage.
- **Selected:**
  - Parvathipuram and Balijipeta (Manyam, paddy)
  - Gurazala and Sattenapalle (Palnadu, cotton, chilli, paddy)
  - Chapad and Khajipet (YSR, paddy, cotton)
  - Vedurukuppam (Chittoor, Rabi paddy)

---

## 3. Satellite processing

### 3.1 Flood extent (Sentinel-1)
The method follows the UN-SPIDER Recommended Practice for Sentinel-1 flood mapping, with every threshold made data-driven or cited:
- **Geometry:**
  - VH polarisation, IW mode.
  - The post-event image is the first acquisition within 12 days, taken only from an orbit that also has a pre-event image within 60 days.
  - The pre-event reference is the median of that same orbit and pass, so all 22 events are orbit-matched.
  - Speckle is reduced with a 50 m focal median.
- **Water threshold:** Otsu's method on a balanced sample of known permanent water (JRC) and cropland, computed per event. This makes the histogram two-humped by construction. Results ranged from −24.0 to −20.0 dB, against a typical −27 dB for open water and −15 dB for cropland.
- **Change threshold:** a backscatter drop of at least 3 dB, i.e. received power halved (Clement et al. 2018).
- **Masks:** JRC permanent water (seasonality ≥ 10 months); HAND > 15 m (Twele et al. 2016); clusters smaller than 8 pixels.
- **False-alarm floor:** the identical algorithm run on dry dates (15 Feb and 1 Mar 2024, < 21 mm of rain in 45 days) gives each mandal's background "flood" share. An event must beat it.

**What went wrong first, and how it was fixed**
- The first version used Otsu on the change histogram over cropland. That histogram has only one hump, so thresholds came out near 0 dB and 25–41% of cropland was flagged.
- It was replaced by the reference-sampled Otsu above before any results were used.

### 3.2 Crop condition
- Sentinel-2 NDVI is masked with s2cloudless probability below 40% plus the SCL cloud, shadow and cirrus classes.
- Sentinel-1 VH and VV are averaged per 10-day window.
- Values are extracted per YSR parcel and per mandal cropland, Kharif 2023–2026. Windows with no acquisition are recorded as missing; this happens with the 12-day Sentinel-1 repeat in 2022–2024.

### 3.3 Long record
- MODIS MOD13Q1 NDVI (QA good or marginal), Kharif Sep–Oct mean over cropland, 2001–2025.
- VCI = scaled within each mandal's own record (Kogan 1995).
- VCI < 35 = vegetation stress (Kogan; GoI Manual for Drought Management 2016).

---

## 4. Parametric triggers (WBCIS term-sheet structure)

**Season structure**
- Each crop season is split into the four FAO-56 stages (Allen et al. 1998, Table 11).
- The stages start from the **median e-Panta sowing date** of that crop in that mandal.
- Each stage carries three covers:
  - **deficit:** total rainfall
  - **excess:** maximum 3-day rainfall
  - **dry spell:** longest run of days below 2.5 mm (IMD rainy-day threshold)

**Turning covers into a payout**
- Each cover value becomes a percentile within the mandal's own 1995–2024 CHIRPS record, then a standard normal score with higher meaning worse, as in SPI.
- Stage stress = the worst of its three covers.
- Season stress S = the stage stresses summed, weighted by each stage's share of crop water demand (FAO-56 Kc × days).
- **Trigger** = the 1-in-5-year value of S; **exit** = the 1-in-25-year value. Payout rises linearly between them.

**Why not twelve separate triggers.** Applying the return period once, to S, keeps payout frequency at **20%** (measured 0.20). Twelve separate 1-in-5 triggers made almost every year pay, with a burn cost of about 30%, and were rejected.

**Pure premium (burn cost)**
- 12.0–12.9% of sum insured for every district and crop.
- The near-uniformity is a property of return-period design: each mandal's trigger is its own 1-in-5 level.
- Differences between crops and areas must come from **calibration against actual losses (claims, CCE)**, which is the purpose of the data request.

| Trigger / exit return period | 1-in-3 / 1-in-15 | 1-in-5 / 1-in-25 | 1-in-10 / 1-in-50 |
|---|---|---|---|
| Mean burn cost | ~20% | ~12.5% | ~7% |

**Acute events (heavy rain, unseasonal rain, cyclone)**
- **Weather trigger:** the event's 3-day rainfall in the mandal beats the mandal's own 99th percentile (CHIRPS 1995–2024), or an IBTrACS cyclone ≥ 34 kt (IMD cyclonic storm) passed within 150 km.
- The return period of the 3-day total is reported with each event.

---

## 5. Decision logic

| Weather trigger | Satellite confirmation | Action |
|---|---|---|
| yes | yes | **Parametric payout** |
| yes | no | **Field / photo verification** |
| no | yes | **Field / photo verification** (basis-risk catch) |
| no | no | **No payout** |

**Satellite confirmation, acute events.** All of these must hold:
- Flooded cropland share is above the mandal's dry-control floor.
- The radar image is **within 72 h** of the event.
- The crop is **standing** on the event date: e-Panta sowing date ≤ event ≤ sowing date + FAO-56 duration.
- No paddy is being planted around the event (e-Panta paddy sowing within −30/+15 days). Otherwise the radar "flood" may be puddling water.

**Satellite confirmation, seasons:** VCI < 35.

**Photo verification (Module B).** Cases routed to field / photo verification are resolved with a geotagged photo, which counts as evidence only if every check passes:

| Check | How |
|---|---|
| Geotag | GPS from the photo's EXIF; manual coordinates are accepted but marked lower trust |
| Location | Point in pilot mandal; in YSR Kadapa, point in APAIMS parcel, compared with the claimed survey number |
| Booking | e-Panta crop booked on that parcel for every season that can be standing on the photo date |
| Timing | Taken between event start and 30 days after event end (policy setting) |
| Vision | Crop seen, damage class and confidence from a zero-shot vision-language model (Gemini); **not yet validated against field truth** |
| Crop match | Crop seen agrees with the e-Panta booking |

- **Outcome:** photo confirms loss → the case can close for payment. Photo shows no damage → closed without payment.
- **Basis-risk catch:** a photo confirming loss where the system said "no payout" is referred for field verification.
- **Fallback rule:** the demo engine's rule-based fallback, used when no vision service answers, is never counted as evidence.
- **Test:** a plain-colour image with a valid geotag inside parcel 24/A (Chapad) was rejected as "crop mismatch → field visit".

**Vision benchmark on the Department's labelled images.**
- **Data:** Label Studio pest and disease repository, about 79k images, 28k of them labelled.
- **Sample:** 30 random labelled images from each of 8 post-flood / excess-moisture classes (paddy BLB, sheath blight, blast, brown spot, false smut, brown plant hopper; cotton bacterial blight, Alternaria).
- **Protocol:** each image was sent to the model **blind**, without naming the crop or label, and scored against the label using a keyword list fixed before scoring (`poc/photo/pest_benchmark.py`).

| Gemini (n = 218) | Result (95% CI) |
|---|---|
| Crop identified correctly | **100%** (97–100%) |
| Any pest / disease detected | **90%** (85–93%) |
| Correct pest / disease named | **47%** (41–54%) |

- Correct naming by class: false smut 92%, Alternaria 62%, brown spot 60%, blast 47%, sheath blight / BLB / cotton bacterial blight about 30–33%, brown plant hopper 7% (n = 14).
- The Groq Qwen model, on the 132 calls not rate-limited, named the correct pest or disease 20% of the time.

**Use in the POC:**
- The vision model is reliable for the **crop-consistency check** (crop seen vs e-Panta booking).
- It is **not** reliable enough to diagnose pests and diseases on its own, so its pest and disease output is shown as a suggestion for the agriculture officer, never as a decision.
- The Department's 28k labelled images are enough to train and test a dedicated detector (YOLO-OBB, the format they export). That is the next step after the POC.

---

## 6. Results for the pilot mandals

| | Parametric payout | Field / photo verification | No payout |
|---|---|---|---|
| Acute events (22 events × pilot mandals × crops) | 0 | 63 | 19 |
| Drought seasons 2020–2025 | 3 | 9 | 35 |

**Acute events**
- Radar flood on cropland ranged from 0.02% to 3.4% per district, which is inside the dry-control range.
- The radar image arrived within 72 h for 8 of 22 events.
- Where the weather trigger fired, cases went to verification, not to automatic payout.

**Drought**
- **Gurazala, Kharif 2023:** the mid-season deficit trigger fired, with payouts of 29% (cotton), 22% (chilli) and 62% (paddy), and VCI was 30. The two sensors agree, so it pays.
- **Chapad, Sattenapalle and Khajipet, 2023:** the trigger fired but crops stayed greener (VCI 45–53), so these go to verification. That is consistent with irrigation buffering the deficit, and is exactly where rainfall-only cover would have over-paid.

**Live season, Kharif 2026 (Manyam)**
- Heavy rain on 2–7 Jul, 9–13 Sep and 20–25 Sep 2026.
- The last event is ERA5-provisional, rated 1-in-30 years in Balijipeta.
- Status: pending season close, with field verification flagged where radar or rainfall fired.

---

## 7. Validation

### 7.1 Second sensor (interim, not losses)

| Scope | n | Spearman (S vs VCI) | POD | FAR |
|---|---|---|---|---|
| All Kharif mandal-seasons 2001–2025 | 1,975 | −0.13 (p < 0.001) | 0.39 | 0.78 |
| Deficit / dry-spell driven | 1,275 | −0.13 (p < 0.001) | 0.38 | 0.76 |
| District-year, YSR Kadapa | 25 | −0.35 (p 0.09) | – | – |
| District-year, Palnadu | 25 | −0.30 (p 0.15) | – | – |
| District-year, Parvathipuram Manyam | 25 | 0.00 (p 0.99) | – | – |

POD = share of VCI-stress seasons the trigger caught. FAR = share of trigger seasons without VCI stress.

**Reading**
- Rainfall-only triggers have the right direction but weak skill.
- This is the documented basis risk of weather-index insurance, and it is the reason the POC requires a second sensor before paying.

### 7.2 Parcel-level cross-check (cyclone Michaung, Dec 2023, YSR)
- 31,108 parcels with a single dominant crop; each is compared with its cohort of the same crop and sowing fortnight.
- Radar flagged 716 parcels as flooded.
- The standing-crop gate removed 432 (60%). These were mostly canal-irrigated fields sown in May–July, harvested before December and being prepared for Rabi paddy.
- The remaining 284 showed **no greenness loss** relative to their cohort.
- Michaung's main damage was further east, so this event tests false positives, not loss detection.

### 7.3 Positive control (declared before running; see `poc/POSITIVE_CONTROL.md`)
- **Test:** the Budameru / Krishna floods of 31 Aug – 2 Sep 2024, 19 mandals within 30 km of Vijayawada, same frozen method.
- **Pass rule:** event flooded-cropland share exceeds the dry-control share.

**Result: PASS.**
- Flooded cropland was **5.61%** for the event against **1.41%** on the dry control dates, about 4× the floor.
- The excess is concentrated where flooding was reported:

| Mandal | Event | Dry control |
|---|---|---|
| Vijayawada (Urban) | 21.6% | 1.6% |
| Mangalagiri | 20.8% | 0.4% |
| Vijayawada (Rural) | 18.3% | 0.7% |
| Ibrahimpatnam | 9.9% | 1.2% |

- Most outer mandals stay within 1–4 points of their control.
- Water threshold was −23.5 dB; the image pair was orbit-matched.

**Caveat:** the first orbit-matched post-event image was on 13 Sep 2024, **265 h** after the rain ended. The flood was still standing and so was detected, but outside the 72-hour window.

**Conclusion:**
- The detector sees real cropland flooding clearly above its false-alarm floor.
- The pilot events did not produce flooding above routine field water, so the system's refusal to pay on them was correct, not a blind spot.
- The 72-hour window still needs the rainfall trigger and field verification whenever radar timing does not cooperate.

### 7.4 Validation against real CCE yields (YSR Kadapa)

**Data:** Department CCE records (plot yields of two experiments per village, 5 × 5 m or 10 × 10 m plots), Kharif 2019–2025, YSR Kadapa. After matching mandals and requiring at least 3 CCE years per mandal-crop: **166 mandal-crop-years** (26 mandals; paddy 114, cotton 52). This includes the pilot mandals Chapad and Khajipet.

**Method (declared before computing; `poc/pipeline/p15_validate_cce.py`):**
- Actual yield = mean CCE yield per mandal, crop and year (kg/ha).
- Normal = mean of the same mandal and crop over its **other** CCE years, so a year is never part of its own baseline.
- Loss event = actual yield below normal × indemnity level, reported for the three PMFBY levels (70, 80, 90%).
- Trigger = the season payout from section 4, alone and combined with the acute-event layer (section 4, same qualifying rule as the pilot assessment).

**Results** (loss = yield below 80% of normal; 70% and 90% give the same picture):

| Trigger system | Agreement | CCE losses caught (POD) | False alarms (FAR) |
|---|---|---|---|
| Season trigger only (CHIRPS) | 55% | 7% | 83% |
| Season + acute event, acute on CHIRPS | 44% | 10% | 87% |
| Season + acute event, acute on ERA5 | **60%** | **37%** | **57%** |

Spearman between season stress and CCE loss: −0.12 (p = 0.12).

| Kharif | Mean CCE loss | Season trigger fired | + acute (CHIRPS) | + acute (ERA5) |
|---|---|---|---|---|
| 2019 | 5% | 0% | 0% | 0% |
| 2020 (cyclone Nivar) | 39% | 0% | 5% | **100%** |
| 2021 (November floods) | 41% | 0% | 10% | 0% |
| 2022 | 20% | 0% | 0% | 0% |
| 2023 (deficit year) | 14% | 54% | 81% | 81% |
| 2024 | 2% | 37% | 82% | 41% |
| 2025 | 7% | 0% | 0% | 0% |

**Reading**
- **Nivar 2020** was caught in every mandal by the ERA5 acute layer. CHIRPS, a 0.05° satellite–gauge blend, smooths the cyclone's rainfall below each mandal's 99th percentile.
- **The November 2021 floods** were missed by both sources, which under-read the extreme rainfall recorded by gauges. IMD gridded or station data would be needed; `imdpune.gov.in` was not reachable from our environment.
- **2022 (20% loss)** shows no weather signal. This is likely non-weather loss (for example pests), which no rainfall index can see.
- **2023–2024:** deficit triggers fired while CCE losses stayed small. Irrigated paddy buffered the rainfall deficit, so rainfall cover over irrigated land over-pays.
- **Both rainfall sources were chosen before the CCE data arrived** (ERA5 for screening on 2026-10-01, CHIRPS for triggers on 2026-10-07). Neither was tuned to this test, and both are reported.

**Against the ≥75% criterion:**
- Weather triggers alone **do not reach it**. They catch about a third of real loss events at best, which is the basis risk of index insurance measured on the Department's own data.
- This is the reason the POC design never pays or refuses on a weather trigger alone. Every disagreement with satellite evidence goes to field and photo verification.
- **Next steps that address the misses directly:**
  - gauge-based rainfall (IMD) for extreme events
  - an irrigation mask from e-Panta irrigation source to stop deficit cover running over canal-fed paddy
  - CCE-calibrated trigger levels per mandal once a longer CCE record is available

## 8. Known limits

1. Real CCE yields exist for YSR Kadapa only (2019–2025); none for Palnadu, Manyam or Chittoor, and no PMFBY claim amounts. Against CCE, weather triggers alone catch at most about a third of loss events (section 7.4).
2. Parcel boundaries exist only for YSR (about 56% of villages). Palnadu and Manyam run at mandal level; mandal-level flood is spread over cropland in proportion to crop area.
3. Sentinel-1 meets 72 h for 8 of 22 events. The system responds with the daily rainfall trigger plus field verification, and every result carries its image date.
4. SAR cannot tell disaster flooding from paddy puddling or Rabi irrigation. The e-Panta planting gate and the dry-control floor handle this, at the cost of sending most acute cases to verification.
5. FAO-56 stage lengths are generic: AP chilli runs longer than FAO "peppers", and local variety durations differ. Satellite phenology per parcel can replace them (data in hand for YSR 2023–26).
6. Irrigation source is unknown for about 70% of YSR acreage and exists for Kharif 2026 only.
7. CHIRPS lags about a month; September 2026 events use ERA5, marked provisional.
8. Earth Engine noncommercial quota limited reprocessing; six parcel chunks (about 4,000 parcels each) timed out in individual years.

---

## 9. Scaling

- **Everything runs from open data plus e-Panta:** CHIRPS, Sentinel-1/2, MODIS, IBTrACS and geoBoundaries.
- **Adding a district** needs only its e-Panta extract and, for parcel level, its APAIMS cadastral.
- **Triggers recalibrate per mandal** from that mandal's own rainfall record, so no thresholds need hand-tuning.

---

## 10. References
- Allen R.G. et al. (1998) *Crop evapotranspiration*, FAO Irrigation and Drainage Paper 56.
- Clement M.A., Kilsby C.G., Moore P. (2018) Multi-temporal SAR flood mapping using change detection. *J. Flood Risk Management* 11(2).
- Funk C. et al. (2015) The CHIRPS dataset. *Scientific Data* 2.
- Government of India (2016) *Manual for Drought Management*.
- Kogan F.N. (1995) Application of vegetation index and brightness temperature for drought detection. *Adv. Space Res.* 15(11).
- McKee T.B., Doesken N.J., Kleist J. (1993) The relationship of drought frequency and duration to time scales. 8th Conf. Applied Climatology.
- Otsu N. (1979) A threshold selection method from gray-level histograms. *IEEE Trans. SMC* 9(1).
- Twele A. et al. (2016) Sentinel-1-based flood mapping: a fully automated processing chain. *Int. J. Remote Sensing* 37(13).
- UN-SPIDER Recommended Practice: Flood mapping and damage assessment using Sentinel-1 SAR data in Google Earth Engine.
- Zhang X. et al. (2011) Indices for monitoring changes in extremes (ETCCDI). *WIREs Climate Change* 2(6).
