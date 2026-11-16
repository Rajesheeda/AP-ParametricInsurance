# Parametric Insurance & Disaster Loss Assessment: POC technical report

**Case 100075 · hierachAi Technologies · draft of 2026-10-30, corrected 2026-11-16 (section 0)**
**Pilot:**
- Kharif: Palnadu, YSR Kadapa, Parvathipuram Manyam.
- Rabi: Chittoor, proposed in place of East Godavari because no East Godavari data was available.

**Status of validation:** the triggers have been tested against **real CCE yields** shared by the Department for YSR Kadapa (26 mandals, Kharif 2019–2025, section 7.4). No CCE or claims were available for Palnadu, Parvathipuram Manyam or Chittoor; validation there is interim (second sensor only).

---

## 0. Correction of 14–16 Nov 2026: each mandal scored with its own radar pass

**What was wrong.** The radar step scored a whole district with the first orbit-matched Sentinel-1 pass. Mandals outside that pass's footprint read **0% flooded instead of "not imaged"**: Palnadu 26 of 28 mandals in 5 of 7 events; YSR CCE windows 19 of 40 mandals in 11 of 17. Found by the footprint check in `poc/SAR_DEPTH_STUDY.md` (amendment 1, committed `d975cc9` before any accuracy was scored).
**Fix (not tuning).** Each mandal is scored by the earliest orbit-matched pass in the 12-day window that covers at least half of its cropland; flood share is over imaged cropland only; a mandal with no such pass is NOT IMAGED. Detection physics, thresholds and masks are unchanged. Old outputs are kept in `gee_out/v1_district_pass/` and `data/derived_v1_snapshot/`.

| Result | As originally run | Corrected |
|---|---|---|
| Lane 1 product vs CCE (YSR, 80% indemnity) | 9 payouts, 7 real (78%, CI 45–94), catches 12% | **17 payouts, 14 real (82%, CI 59–94), catches 24%**; 13 of 14 hits are Nivar 2020 |
| Same at 70% / 90% indemnity | – | 17 / 9 (53%, 31–74) · 17 / 16 (94%, 73–99) |
| Sentinel-1 flood alone vs the gate (80%) | 33% (22–46): fails | **61 fired, 30 real, 49% (37–61) vs 36% base: passes** |
| ERA5 × SAR (80%) | – | 16 / 13, 81% (57–93) |
| Declared consensus × SAR | 17 / 2 | 17 / 3, 18% (6–41): still fails |
| Cover B radar confirmation rate | 30% | 59% (16 of 27) |
| Premium, YSR both covers (pure burn cost) | 5.9% (4.3–8.2) | **9.4% (7.2–11.4)** vs 24.9% rainfall-only |
| CCE mandal-seasons with radar inside 72 h | 94 of 147 | 68 of 147 |
| Positive control (Budameru 2024) | PASS | **PASS, unchanged** (5.61% vs 1.41%; 19 of 19 imaged) |
| Cyclone Arnab index payouts | 0 | **1: Salur 34.5%** (not imaged on 30 Oct; 4 Nov pass, T+172 h: 0.60% vs 0.07% floor) |

**Two things we say plainly.** (a) The Arnab change is a bug fix made after the pre-registration, dated and committed before any scoring. (b) A 0.6% radar signal unlocking a 34.5% payout is a design weakness: radar confirms, rainfall sets the amount. A minimum-signal rule is a candidate for next season and can enter only through the qualification gate.
**Revisit (acquisition metadata, 2021–2026).** Sentinel-1 repeats every 12 days over the pilot mandals for the whole record: P(image within 72 h) = 24% (single-track mandals) to 49% (two tracks).
**Flooded vegetation (declared test).** VV rise ≥ 3 dB: Budameru 5.4% of cropland vs 3.5% on a dry control date, ratio 1.55 < 2: no usable signal at C-band; the drop-only rule stays.
**Coast-wide cyclone test (declared rules, `poc/CYCLONE_TEST_2026.md`).** Arnab "where": **FAILED**. Our top three old districts by net flooded cropland were Guntur, Srikakulam and West Godavari, against the official East Godavari, West Godavari and Krishna; the delta's first usable pass (4 Nov) came after Murasu's 3 Nov rain, so the two storms cannot be separated there. Murasu "where": passed (Prakasam and Guntur above Nellore), but Prakasam reads about 73,000 ha against 3,151 ha reported with little rain. November is Rabi land preparation and the dry-date floors are from Feb/Mar, the wrong season, so this pass is not evidence of skill. A seasonal floor (same weeks, non-event years) is the candidate fix through the gate; the same caveat applies to Salur.
**Not yet scored:** flood-map accuracy against Sentinel-2 (only 2 events have a clear optical view so far).
Tables in sections 7.4–7.13 marked *as originally run* keep the first-run values for the record; the corrected values are the ones above.

---

## 1. Summary

**Design: two lanes, never mixed.**
- **Lane 1, parametric insurance:** the payout is a formula on objective indices only, with no claim, no loss adjustment and no field visit, and no photo can change it. Each cover is a **dual trigger**: a rainfall index *and* an independent satellite index must both cross pre-agreed levels.
  - **Cover A, season:** WBCIS term-sheet structure (FAO-56 stages; deficit, excess, dry spell) AND MODIS VCI < 35.
  - **Cover B, catastrophe:** ERA5 3-day rain from the mandal's own 1-in-5 to 1-in-25 level AND Sentinel-1 flood on standing crops above the measured false-alarm level.
  - **Each farmer's own calendar:** stages start at that booking's e-Panta sowing week, not at a mandal-wide date.
  - **Index qualification gate:** a candidate index enters the contract only if it beats the base loss rate on the Department's own CCE yields (lower 95% bound of precision). The gate is re-run every season.
- **Lane 2, disaster relief (SDRF input subsidy, ≥33% damage):** a 72-hour provisional assessment. Radar-mapped flooding on standing crops, a CCE-calibrated loss estimate, and enumeration by quality-gated, parcel-locked photo or AEO visit.
- **Basis-risk log:** every case where the lanes disagree is recorded. Index levels change only between seasons.
- **Methods:** cited published methods only (IMD, ETCCDI, SPI, FAO-56, WBCIS structure, UN-SPIDER, Otsu, Kogan VCI). No hand-picked thresholds.

**PoC success criteria: status**

| Target (PPT) | Status | Why |
|---|---|---|
| ≥75% correlation, triggers vs actual losses | **Not measurable with the data shared** | CCE exists for 1 of 4 districts and 7 seasons, and there are no PMFBY claims. Losses cluster by season, so 166 mandal-crop-years carry about 14 independent observations. A true r = 0.75 over 7 seasons has a 95% CI of −0.01 to 0.96; testing it needs about 25 seasons (section 7.13). |
| ≥80% flood accuracy vs APSDMA | **No reference data shared** | Replaced by a positive control declared in advance (Budameru 2024: PASS) and a measured false-alarm floor per mandal. |
| Loss assessment within 72 h | **Met for relief (Lane 2)** | Daily rainfall inside 72 h, plus radar when it arrives: P(Sentinel-1 image within 72 h) 24–49% per pilot mandal (12-day repeat); every result carries its image time. |
| 5-year back-test vs PMFBY and CCE | **Done on what exists** | CCE 2019–2025 (YSR); premium back-test 2001–2024 for all Kharif pilot districts; no PMFBY claim amounts shared. |

**Main findings**

| Finding | Number |
|---|---|
| Rainfall-trigger premium (pure burn cost), 1-in-5 trigger / 1-in-25 exit | **12.5%** of sum insured (7% to 20% across design choices) |
| Agreement of rainfall triggers with satellite crop condition (MODIS VCI), mandal-season | Spearman **−0.13**: right direction, weak. This is the basis risk of rainfall-only cover. |
| Same, district-year (drought districts) | **−0.35** YSR Kadapa, **−0.30** Palnadu, **0** Manyam (flood-driven) |
| Sentinel-1 image inside 72 h of the event | P = **24–49%** per pilot mandal (12-day repeat, metadata 2021–2026); 8 of 22 events as originally run |
| Sentinel-1 "flood" on dry control dates (false-alarm floor) | median 0.1–0.6% of cropland, up to 9.5% in one mandal |
| Pilot events whose flooded cropland beat that floor within 72 h | **0 of 22** |
| Positive control: Budameru / Krishna floods, Sep 2024 (rule declared in advance) | **PASS:** 5.6% flooded cropland vs 1.4% dry floor; up to 21% in the flooded mandals |
| **Real CCE losses caught by weather triggers alone** (YSR, 166 mandal-crop-years, loss = yield < 80% of normal) | **7%** season trigger only; **37%** with the acute layer on ERA5 (agreement 60%). Below the ≥75% target. |
| Seasons where the rainfall trigger and satellite agree on drought | Gurazala 2023 (cotton, chilli, paddy) |
| **Lane 1 product vs real CCE** (YSR, both covers dual-triggered; corrected, section 0) | **17 payouts, 14 to real losses** (82%, 95% CI 59–94%), against a 36% base rate; catches 24% of losses; 13 of 14 hits are Nivar 2020 |
| Same years, rainfall-only season cover (today's WBCIS structure) | 24 payouts, **20 with no real loss** (precision 17%) |
| Rainfall source test: CHIRPS / ERA5 / GPM IMERG / 2-of-3 consensus (acute layer) | losses caught 10% / 37% / 47% / 37%; none catches the Nov 2021 floods (section 7.8) |
| Per-farmer cover, 6 pilot mandals, Kharif 2023–25 | **522,208** e-Panta bookings priced on their own sowing week; **109,039** would flip between paid and not paid under a mandal calendar (21,289 of 221,555 in YSR and Palnadu; section 7.10) |
| **Premium, pure burn cost 2001–2024** (section 7.12) | Season cover **13.2% → 2.5%** of sum insured with the dual trigger; YSR both covers **9.4%** (7.2–11.4%, corrected) vs 24.9% rainfall-only |
| **Live events: Cyclones Arnab and Murasu** (28 Oct, 3 Nov 2026; section 7.14) | Arnab: relief list and alerts at **T+69 h** (16 mandals; **15** on final ERA5); rainfall-only cover would pay **22–80%** in 6 Manyam mandals; radar confirms **1 (Salur 34.5%)**, holds 5; 5 of 15 relief mandals imaged inside 72 h. Murasu: **20** Palnadu mandals to relief, **0** index payouts (all below the 1-in-5 level); Chilakaluripet 22.4% flooded vs 2.0% floor is the basis-risk example |
| Photo quality gate (thresholds from 982 Department photos) | **91%** of held-out genuine photos accepted, **100%** of blurred / dark / overexposed / low-resolution copies refused |
| False-positive reduction from the standing-crop gate (Michaung 2023, YSR, parcel level) | **60%** of radar-flagged parcels removed (harvested or not yet sown) |

**What this means**
- In YSR Kadapa, rainfall indices alone are a poor proxy for loss: irrigation buffers deficits, and much heavy rain does no damage. This is the basis risk of today's weather-index insurance, measured with the State's own yields.
- So insurance pays only what two independent indices agree on, and only indices that pass the qualification gate. This removes most false payouts, at the price of detection.
- The losses the index cannot see (2021 floods, 2022) are left to Lane 2 relief and PMFBY area-yield. They are logged as basis risk, not hidden.
- Radar alone is never a payout signal: at mandal scale it cannot be told apart from routine field water without the e-Panta crop and planting gates.

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

## 5. Decision logic: two lanes

| | Lane 1: parametric insurance | Lane 2: disaster relief (SDRF) |
|---|---|---|
| Question | Did the pre-agreed indices cross their levels? | Was this farmer's crop really damaged ≥33%? |
| Inputs | Rainfall index AND satellite index, only indices that passed the qualification gate | Radar map, e-Panta standing crops, CCE-calibrated loss estimate, photo / AEO |
| Output | % of sum insured, by formula, per booking | Enumeration list, radar-flooded villages first |
| Time | When the second index is observed (radar revisit 6–12 days; season end for Cover A) | 72-hour provisional, then enumeration |
| Field evidence | **Never** used | Required |

**Lane 1, Cover B satellite trigger.** All of these must hold:
- The flooded cropland share is above the mandal's dry-control floor.
- The crop is **standing** on the event date: e-Panta sowing date ≤ event ≤ sowing + FAO-56 duration.
- No paddy is being planted around the event (e-Panta paddy sowing within −30/+15 days). Otherwise the radar "flood" may be puddling water.

**Lane 1, Cover A satellite trigger:** VCI < 35 in the same mandal and season.

**Lane 2 priority:** "radar-mapped" when the Lane 1 satellite conditions hold on an image within 72 h; otherwise photo / AEO enumeration whenever any rainfall product or the radar shows a signal. Each case carries an **evidence grade**:
- **A:** at least 2 of 3 rainfall products above their own 1-in-5 level, and an orbit-matched radar image within 72 h.
- **B:** one of those two holds.
- **C:** neither holds.

**Basis-risk flags:** the lanes disagree, for example "relief signal, no index payout".

**Photo verification (Module B), Lane 2 only.** A geotagged photo is relief evidence and feeds the basis-risk log; it never changes an insurance payout. It counts as evidence only if every check passes:

| Check | How |
|---|---|
| Quality | Blur (variance of Laplacian), exposure, clipping, resolution; thresholds = percentiles of 982 Department field photos (section 7.11). A failing photo is refused before any other check ("retake") |
| Geotag | GPS from the photo's EXIF; manual coordinates are accepted but marked lower trust |
| Location | Point in pilot mandal; in YSR Kadapa, point in APAIMS parcel, compared with the claimed survey number |
| Booking | e-Panta crop booked on that parcel for every season that can be standing on the photo date |
| Timing | Taken between event start and 30 days after event end (policy setting) |
| Vision | Crop seen, damage class and confidence from a zero-shot vision-language model (Gemini); **not yet validated against field truth** |
| Crop match | Crop seen agrees with the e-Panta booking |

- **Outcome:** photo confirms loss → recorded for SDRF enumeration. Photo shows no damage → no relief evidence. Either way the insurance payout is unchanged.
- **Basis-risk catch:** a photo confirming loss where the index did not pay (or showing no loss where it did) is logged for the season-end recalibration.
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
- **Trained classifier (done):**
  - EfficientNet-B0 (ImageNet-pretrained, frozen) plus multinomial logistic regression, trained on 1,124 further Department images from the same 8 classes.
  - The test images' task IDs were excluded, and 109 near-duplicates were removed by image fingerprint (`poc/photo/pest_train.py`).
  - **Held-out test accuracy 60%** (95% CI 53–66%) on the same 240 test images.
  - On the 218 images Gemini also answered: **58% vs Gemini 47%**. Exact McNemar test p = 0.02 (57 images right only for the trained model, 34 right only for Gemini).
  - Strong on Alternaria (100%), false smut (93%), BLB (73%) and sheath blight (67%).
  - Weak on cotton bacterial blight (13%, confused with Alternaria; 68 training images) and brown spot (30%).
  - It runs inside photo verification as a top-3 suggestion for the officer, never as a diagnosis.
  - More images per class, and the YOLO-OBB boxes the Department exports, are the route to a stronger detector.
- **Manual coordinates:** a photo whose location is typed in by hand cannot confirm a loss. It is marked "officer to verify before enumeration", because coordinates can be copied from any parcel.

---

## 6. Results for the pilot mandals

| Pilot mandals × crops | Lane 1: index payout | Lane 2: relief enumeration only | Monitor only |
|---|---|---|---|
| Acute events (22 events) | 0 | 61 | 21 |
| Drought seasons 2020–2025 | 3 | 9 | 35 |

**Acute events**
- Radar flood on cropland ranged from 0.02% to 3.4% per district, which is inside the dry-control range.
- The radar image arrived within 72 h for 8 of 22 events.
- No acute event met the Lane 1 satellite trigger on standing, non-planting crops, so there was no index payout. Relief enumeration opened wherever rainfall or radar showed a signal.

**Drought**
- **Gurazala, Kharif 2023:** the mid-season deficit trigger fired, with payouts of 29% (cotton), 22% (chilli) and 62% (paddy), and VCI was 30. Both indices agree, so the index pays.
  - Per farmer, on own sowing dates: 13,096 bookings paid (section 7.10).
- **Chapad, Sattenapalle and Khajipet, 2023:** the rainfall trigger fired but crops stayed greener (VCI 45–53), so there is no index payout and relief enumeration stays open.
  - This is consistent with irrigation buffering the deficit, and is exactly where rainfall-only cover would have over-paid.

**Live season, Kharif 2026 (Manyam)**
- Heavy rain on 2–7 Jul, 9–13 Sep and 20–25 Sep 2026.
- 20–25 Sep: all three rainfall products are above their own 1-in-5 level, and at least two are at or above their 1-in-25 level (CHIRPS 266–296 mm over 3 days).
- Radar 96 h later showed flooded cropland below the false-alarm level, during paddy planting, so there is no index payout. Relief enumeration is open (evidence grade B).

---|---|---|---|
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

### 7.5 Soil moisture (root zone and satellite) against CCE

**Why:** a rainfall deficit only becomes crop stress through the soil, so a drought cover should be checked against soil water.

**Data:** ERA5-Land root-zone soil moisture (0–100 cm, depth-weighted layers 1–3, 2000–2025) and SMAP L3 enhanced surface soil moisture (satellite L-band radiometer, 2016–2025). Both are monthly means per mandal over the crop's FAO-56 mid (reproductive) stage window, expressed as a percentile of the mandal's own record (`gee_py/soil_moisture.py`, `pipeline/p17_soil_moisture.py`).

**Rule (declared before computing):** a drought trigger counts as "soil-confirmed" only if soil moisture is at or below its 20th percentile, the same 1-in-5 return period as the trigger.

| YSR Kadapa, 166 mandal-crop-years (36% had a CCE loss below 80% of normal) | Fired | Share with real loss |
|---|---|---|
| Drought trigger alone | 14 | 29% |
| Drought trigger + dry root zone (ERA5-Land) | 6 | 0% |
| Drought trigger + dry surface (SMAP) | 9 | 11% |
| Dry root zone alone | 13 | 8% |
| Dry surface alone (SMAP) | 17 | 12% |

**Reading:**
- In YSR Kadapa, dry soil did **not** coincide with lost yield; dry seasons had fewer losses than average.
- Irrigation (canal-fed paddy, drip cotton) decouples soil water from yield there, and the large losses of 2019–2025 came from excess rain and cyclones.
- Soil moisture is therefore reported alongside each season decision as evidence, but it does not change payouts.
- **Product implication for YSR:** build the cover around excess rain and cyclones, and restrict drought cover to rainfed parcels using an irrigation mask (e-Panta irrigation source).

### 7.6 Estimated yield loss per decision (CCE-calibrated)

The problem statement asks for *estimated yield loss* within 72 hours. Each decision now carries the distribution of real CCE losses observed when the same trigger type fired (`pipeline/p18_loss_calibration.py`):

| When this fired (YSR, 2019–2025) | Median CCE loss | Middle 50% | Cases with >20% loss | n |
|---|---|---|---|---|
| Acute event (cyclone / extreme rain, ERA5) | 25% | 0–39% | 60% | 30 |
| Drought trigger only | 10% | 0–39% | 36% | 11 |
| Nothing fired | 0% | 0–28% | 32% | 115 |

**Caveats:**
- The samples are small: acute is mostly Nivar 2020, and drought is 2023.
- The calibration is from YSR Kadapa only.
- These figures are a first-day estimate for relief planning. Field and photo verification and CCE remain the basis for payment where the sensors disagree.

### 7.7 Fused weather + satellite loss model (tested, not used)

**What was tested:**
- A logistic-regression and a gradient-boosted model combining rainfall stress, extreme-rain indices from both sources, cyclone, and MODIS VCI.
- Tested leave-one-year-out against the CCE loss events, with normal yields recomputed inside each fold (`pipeline/p16_loss_model.py`).

**Result:** out-of-sample AUC was **0.53 and 0.50**, no better than chance.

**Why:** with seven years, the loss years are dominated by causes the features cannot see:
- the under-read November 2021 floods
- non-weather losses in 2022

**Decision:** the model is not used, and no machine-learning claim is made for loss prediction.

### 7.8 Rainfall source: is the sensor the problem? (GPM IMERG added)

**Why:** CHIRPS and ERA5 both missed the November 2021 YSR floods. If the miss were only a sensor problem, a better product should catch them.

**Data:** GPM IMERG V07 (NASA; passive-microwave and IR retrievals merged with GPCC gauges, 0.1°, half-hourly), daily areal means for all 113 POC mandals, June 2000 to September 2026 (`gee_py/imerg.py`). The event catalogue uses the same p05 rules against IMERG's own record.

**Rule (declared 2026-10-30 before computing):** the same acute-layer rule as section 7.4 on IMERG, plus "any of 3" and "2 of 3" products.

| Acute layer source (with season trigger), loss = yield < 80% of normal | Losses caught | False alarms | Fired |
|---|---|---|---|
| CHIRPS | 10% | 87% | 46 |
| ERA5 | 37% | 57% | 51 |
| GPM IMERG | 47% | 67% | 86 |
| Any of 3 | 49% | 70% | 96 |
| 2 of 3 | 37% | 60% | 55 |

**Reading:**
- IMERG raises detection but also false alarms.
- In 2021 (mean loss 41%), even the union of all three products fired in only 14% of mandal-crops.
- The sensor is not the bottleneck: heavy rain is not the same as loss.

### 7.9 Dual trigger and the index qualification gate

**Data:** Sentinel-1 flood index for every acute-rain window flagged by any product in YSR during the crop season, 2019–2025 (17 windows × 40 mandals, `gee_py/sar_cce.py`, frozen method). VCI as in 7.1. Script: `pipeline/p22_dual_trigger.py`.

**Declared 2026-10-30 before computing:**
- Catastrophe cover = consensus (median of the CHIRPS / ERA5 / IMERG payouts, each linear from its own 1-in-5 to 1-in-25 level of the seasonal 3-day maximum) AND Sentinel-1 flood above the floor.
- Season cover dual = season payout AND VCI < 35.

| Candidate (YSR, n = 166, base loss rate 36%) | Paid | To real loss | Precision (95% CI) | Losses caught |
|---|---|---|---|---|
| Season cover, rainfall only (WBCIS structure) | 24 | 4 | 17% (7–36) | 7% |
| MODIS VCI < 35 alone | 6 | 3 | 50% (19–81) | 5% |
| Season cover dual: rainfall AND VCI | 1 | 1 | 100% (21–100) | 2% |
| Cat cover, CHIRPS / ERA5 / IMERG alone | 41 / 27 / 34 | 5 / 20 / 6 | 12% / **74% (55–87)** / 18% | 8% / 34% / 10% |
| Cat cover, 3-source consensus | 25 | 4 | 16% (6–35) | 7% |
| Sentinel-1 flood alone | 52 | 17 | 33% (22–46) | 29% |
| Dual: consensus AND Sentinel-1 (declared design) | 17 | 2 | 12% (3–34) | 3% |
| **Dual: ERA5 AND Sentinel-1** | 8 | 6 | 75% (41–93) | 10% |
| **Lane 1 product: season dual OR ERA5 × Sentinel-1** *(as originally run; corrected 17 / 14, 82% (59–94), 24%: section 0)* | 9 | 7 | **78% (45–94)** | 12% |

**What happened, in order:**
1. **The declared consensus design failed.** CHIRPS and IMERG flag October 2024, a season with about 2% loss.
2. **Only ERA5 beat the base rate.** After seeing this, we set the **index qualification gate**: an index may enter the contract only if the lower bound of the Wilson 95% interval of its precision exceeds the base loss rate. The gate is re-applied every season on new CCE.
3. **The contract's catastrophe cover is therefore ERA5 × Sentinel-1.** The choice was made after seeing the data. ERA5's hits are mostly cyclone Nivar 2020 (17 of 20), so Kharif 2026 CCE is its out-of-sample test.
4. **The season dual trigger stays on probation.** It paid once in YSR, correctly; that is too few to judge, but it made no false payout. In Palnadu (Gurazala 2023) both its indices agreed.

**Reading:** requiring a second, independent index cuts false payouts from 20 of 24 to 2 of 9, at the cost of detection. Losses with no weather or satellite signal (2021 harvest-stage damage, 2022) stay with relief and PMFBY area-yield.

### 7.10 Each farmer's own sowing calendar

**Method:** `pipeline/p23_farmer_payouts.py`.
- Every e-Panta booking of the focus crops in Chapad and Khajipet (YSR), Gurazala and Sattenapalle (Palnadu) and Parvathipuram and Balijipeta (Manyam, paddy), Kharif 2023–25, gets its FAO-56 stages from its own sowing week. Kharif 2026 bookings carry the live-event status (section 7.14).
- Bookings are grouped into cohorts (mandal × crop × sowing week). Each cohort's 1-in-5 trigger and 1-in-25 exit come from 1995–2024 CHIRPS over that cohort's own stage windows, so early and late sowers have the same payout frequency by design.
- The result is compared with the mandal-median calendar a WBCIS term sheet would use. 90 bookings sown outside 1 May – 28 Sep are outside the Kharif window.

**Results:**
- **522,208 bookings** were priced (221,555 in YSR and Palnadu, 300,653 in Manyam).
- **109,039** cross the rainfall trigger under one calendar but not the other (21,289 in YSR and Palnadu). For example:
  - Balijipeta 2023 paddy: 27,401 bookings trigger on their own calendar, none on the mandal calendar. VCI was 100 (the greenest season on record), so the dual trigger pays none of them.
  - Chapad 2023 paddy: 2,838 bookings trigger on their own calendar, none on the mandal calendar.
  - Gurazala 2023 cotton: 2,798 would be paid on the mandal calendar only.
- With the satellite trigger applied, **Gurazala 2023 pays 13,096 bookings** (cotton, chilli, paddy; VCI 30), about 39% of sum insured acre-weighted.
- YSR pilot mandals pay nothing in 2023–25: VCI was 45–95, and real CCE losses in those years were small.
- **Look-up:** per-booking statements come from `GET /api/v1/poc/farmer/payouts`. Sum insured is an input, the notified scale of finance. No farmer names are used.

### 7.11 Photo quality gate

**Method (`poc/photo/quality.py`):**
- **Measures:** sharpness = variance of the Laplacian (Pech-Pacheco et al. 2000); mean brightness; share of clipped pixels; shorter side in pixels. All are measured after resizing to 1024 px.
- **Thresholds:** percentiles of 982 Department Label Studio field photos. Sharpness at the 5th percentile, which is **33**. Brightness between the 1st and 99th percentiles, **90–160**. Clipping at the 99th percentile, **1.5%**. Resolution at the 1st percentile, **716 px**.

**Test on 491 held-out photos:**
- **91%** of genuine photos were accepted.
- **100%** of their blurred (radius 2 and 4), motion-blurred, darkened, overexposed and quarter-resolution copies were refused.
- A refused photo is never judged: the farmer is asked to retake it.

### 7.12 Premium of the Lane 1 product

**Method:** `pipeline/p24_premium_power.py`. Pure burn cost = mean annual payout, % of sum insured; the insurer adds loading.
- **Cover A:** 2001–2024, the MODIS record, all mandals of the three Kharif districts. Rainfall-only payout (p10) is compared with the dual trigger, which pays only if VCI < 35.
- **Cover B, YSR:** Sentinel-1 has no record before 2015. So the ERA5 rainfall-side payout (2001–2024) is multiplied by the measured radar confirmation rate: 8 of 27 ERA5 events, 30% (Wilson 95% CI 16–48%). This assumes payout size is independent of confirmation.

| District | Crop | Rainfall only | Dual trigger | Payout years (rain only → dual) |
|---|---|---|---|---|
| YSR Kadapa | Cotton / Groundnut / Paddy | 13.5 / 11.8 / 13.8% | 2.5 / 2.4 / 2.3% | about 1 in 5 → 1 in 20–25 |
| Palnadu | Cotton / Paddy / Chilli | 12.8 / 14.2 / 14.0% | 3.0 / 2.7 / 1.9% | about 1 in 5 → 1 in 20–30 |
| Parvathipuram Manyam | Paddy | 11.4% | 2.7% | about 1 in 5 → 1 in 25 |
| YSR Kadapa | Catastrophe cover (B) | 11.9% | 3.5% (1.9–5.8) | – |
| **YSR, both covers** *(as originally run; corrected 9.4% (7.2–11.4))* | | **24.9%** | **5.9% (4.3–8.2)** | |

**Reading:**
- The dual trigger pays in about one season in twenty-five instead of one in five. Its premium is a fifth of rainfall-only cover.
- The farmer share and the State's subsidy are both paid on this premium.
- The other side of the trade-off is the low detection in 7.9: the product pays rarely, and only when two independent indices agree.

### 7.13 Why the ≥75% target can neither be met nor tested with this data

**Method:** `pipeline/p24_premium_power.py`.

1. **Clustering.** One cyclone or flood hits every mandal in the same season, so mandal-crop-years are not independent.
   - The intra-class correlation of the loss indicator by season is **0.47**, giving a design effect of **11.7** (Kish 1965).
   - So the 166 mandal-crop-years carry about **14 independent observations** and about **5 independent loss events**.
2. **Season bootstrap.** Resampling whole seasons (5,000 draws):

| System | Losses caught | 95% CI | Precision | 95% CI |
|---|---|---|---|---|
| Season cover, rainfall only | 7% | 0–29% | 17% | 0–29% |
| Season + ERA5 acute layer | 37% | **0–82%** | 43% | 0–95% |
| Lane 1 product (dual) *(as originally run; corrected POD 24%, CI to 55%)* | 12% | 0–27% | 78% | 50–86% |

3. **Correlation over seasons.** A true r = 0.75 measured over 7 seasons has a Fisher-z 95% interval of **−0.01 to 0.96**, which cannot be distinguished from zero. About **25 seasons** are needed before a true 0.75 has a lower bound above 0.5.
4. **Detection.** Estimating a 75% detection rate to ±10 points needs about **73 independent loss events**. YSR supplies under one per season, so pooling CCE across the State's districts is the route.

**Conclusion:**
- The ≥75% target is not a question this data can answer either way. The ERA5 system's detection interval contains 75%.
- What the data can show, it shows clearly: rainfall-only cover pays mostly in the wrong seasons, and a second independent index removes most false payouts.
- The qualification gate (7.9) is built to re-run as each season's CCE arrives, so the evidence accumulates instead of being re-argued.

### 7.14 Live event: Cyclone Arnab, October 2026

**Event.** Very severe cyclonic storm (IMD). It crossed the Andhra Pradesh / Yanam coast near Yanam early on 28 Oct 2026, then moved north-west towards south Odisha. Hours below are counted from 02:00 IST on 28 Oct, the earliest landfall time IMD gives, so every "T+" is an upper bound.

**What was run.** `pipeline/p25_live_event.py`, with the contract, levels and radar method exactly as frozen before the storm. The relief list and first predictions were written at T+69 h (`poc/ARNAB_PREREGISTRATION.md`); figures update as new radar passes and ERA5 days arrive.

**Rainfall.**
- ERA5, the contract index, is published about 5–6 days late; it reached only 24 Oct when this was run.
- So the rainfall side is **provisional**: ECMWF IFS 0.25°, the operational model ERA5 is built from, read against the ERA5 1-in-5 / 1-in-25 levels. GFS and ICON give the spread.
- Six Manyam mandals cross the 1-in-5 level: Balijipeta and Parvathipuram (both pilot), Salur, Makkuva, Palakonda and Pachipenta. Their rainfall sides are 5.6–15.4% of sum insured.
- The three models disagree widely: 126–262 mm over 3 days at Balijipeta.

**Radar (Lane 1 second trigger, Lane 2 priority).**
- Sentinel-1, relative orbit 121, 30 Oct 00:13 UTC (T+52 h), orbit-matched with 5 pre-event images. Corrected per-mandal pass selection (section 0): this pass covers 5 of the 15 relief mandals; the other 10 were first imaged on 4 Nov (T+172 h).
- Otsu water threshold −21.3 dB from 551 known-water samples, within the usual −21 to −24 dB.
- Flooded cropland is 0–0.9% in 14 of 15 Manyam mandals, each below its own dry-date floor. Palakonda shows 2.8%, below its 6.7% floor.
- **No mandal is confirmed, so there are no index payouts.**
- Palnadu had no post-event pass by the time of the run.

**Relief (Lane 2).**
- 16 mandals (13 Manyam, 3 Palnadu; about 1.2 lakh standing acres in e-Panta 2026) were opened for photo / AEO enumeration inside 72 hours. The 31 Oct update of the provisional ECMWF rain lifted 4 more Palnadu mandals (Sattenapalle, Amaravathi, Pedakurapadu, Krosuru) just above their 99th percentile (81.6 vs 80.9 mm): 20 mandals, 1.62 lakh standing acres. No new radar pass: Manyam still T+52 h, Palnadu none. Index payouts remain 0.
- Telugu and English alerts were issued, with the insurance status stated separately.
- The expected loss attached (median 25%, IQR 0–39%) is calibrated on YSR CCE, not on Manyam.

**Comparison with first official figures.** These are preliminary press figures, 28 Oct (Deccan Chronicle), not a score:
- Crop damage of 2.24 lakh ha in 14 districts, heaviest in the Godavari delta, mostly submerged paddy: West Godavari 76,176 ha, Konaseema 44,232, Kakinada 42,222, East Godavari 29,866, Krishna 22,339.
- Parvathipuram Manyam is not among the districts named.
- The absence of flooded cropland in our Manyam radar map is consistent with this.
- The delta lies outside the POC districts. Its next Sentinel-1 pass is 4 Nov (orbit 19, 12-day revisit).

**How it will be scored.** Against the Department's / APSDMA's mandal-level SDRF enumeration for Arnab, if shared, using the rule in `poc/ARNAB_PREREGISTRATION.md`:
- the share of damaged mandals that our relief list named;
- the share of our index payouts that went to damaged mandals.

**What Arnab shows.**
1. **The dual trigger held.** Rainfall-only cover would have paid 6 mandals on a storm whose crop damage was reported elsewhere.
2. **Relief did not wait for insurance.**
3. **The flood index cannot see wind-lodged paddy.** If enumeration finds lodging losses in Manyam, they are paid by relief and logged as basis risk. A lodging index can enter the contract only through the qualification gate, between seasons.

### 7.15 Compensation workflow and the phone capture page

**Compensation workflow** (`pipeline/p26_compensation.py`, backend `routers/poc_compensation.py`, dashboard tab "Compensation").
- **Lane 1 settlement batches.**
  - One batch per mandal × season, built from the per-booking payouts (7.10). Each line is an e-Panta booking (survey × crop) with its index evidence. No farmer names.
  - Amount = payout % × sum insured × acres. Sum insured is the notified scale of finance (DLTC / SLCCCI). No AP value was shared or found, so it is a Department input (`poc/config/sum_insured.csv`). Until it is filled, batches are stated in sum-insured acres, never in invented rupees.
  - Gurazala K2023: 13,096 lines, 16,324 acres, 8,695 sum-insured acres. It is the only settled pilot mandal-season that paid.
  - States: CALCULATED → APPROVED → SENT TO INSURER → PAID. Approval is refused if the batch file's SHA-256 has changed since calculation.
- **Lane 2 SDRF relief cases** (live event: Cyclone Arnab, 15 mandals on final ERA5).
  - States: OPENED → EVIDENCE RECEIVED (an accepted photo) → AEO VERIFIED ≥33% (rainfed / irrigated ha) or CLOSED: BELOW 33% → SANCTIONED → PAID.
  - The sanction is computed from the norms: MHA F.No.33-03/2020-NDM-I, 10 Oct 2022, item 5. Rates: ₹8,500/ha rainfed, ₹17,000/ha assured irrigation, ≥33% loss, ceiling 2 ha per farmer. The same item says input subsidy is adjusted for any PMFBY claim for the same calamity, which is exactly the Lane 1 / Lane 2 link.
- **Relief budget estimate for Arnab.**
  - Formula: standing acres × share of acute-trigger CCE mandal-years with loss ≥33% × rate.
  - Share ≥33%: 30%, Wilson CI 17–48%, n=30, YSR. With no trigger, 24% of mandal-years also reach 33%. The trigger separates weakly, and mandal-years of one event are correlated (7.13), so the CI is optimistic.
  - Result: **₹12.6 cr (all rainfed) to ₹25.2 cr (all irrigated)** at the central share, CI range ₹7.0–40.3 cr (15 mandals, 1.22 lakh standing acres). Salur also has a Lane 1 payout, so its SDRF input subsidy is reduced by the insurance claim at disbursement (MHA note to item 5)..
  - It sizes the SDRF memorandum. Who is paid is decided by the AEO's verified hectares.
  - Not applied, because the extracts carry no farmer ID: the 2 ha ceiling and the ₹1,000 / ₹2,000 minimum.
- **Audit.** Every action is appended to a log with the SHA-256 of the previous entry. Editing or deleting a line shows as "chain broken". Officers are recorded by role, not by name.

**Phone capture page** (`/poc/capture.html`, installable from the browser; Telugu / English).
- Opens the phone camera directly (`capture="environment"`). Reads the phone's GPS at the moment of capture and posts to the same verification API.
- Why device GPS:
  - Android browsers strip EXIF location from uploaded photos, so EXIF-only geotagging fails for most farmers.
  - A device fix counts as a geotag only if its accuracy is within the **equivalent radius of the median YSR cadastral parcel (51 m; median parcel 0.82 ha, measured from APAIMS)**. Coarser fixes are treated as manual coordinates: officer to verify.
  - Both EXIF and device GPS can be spoofed by fake-GPS apps. The defences are the parcel, crop-booking and timing checks plus AEO sampling.
- No name or phone number is collected.

**Vision damage class: what is measured.**
- On the 218 Department photos of diseased paddy and cotton (the blind benchmark, 7.11 / Environment), the general vision model called 90% damaged (196/218, CI 85–93%).
- Its false-alarm rate on healthy crop and its loss % are **not measured**: no healthy or severity labels exist in the Department's Label Studio (projects checked 31 Oct 2026).
- The officer therefore confirms the ≥33% line. The photo loss % is shown, never used for a payment.

## 8. Known limits

1. Real CCE yields exist for YSR Kadapa only (2019–2025); none for Palnadu, Manyam or Chittoor, and no PMFBY claim amounts. Against CCE, weather triggers alone catch at most about a third of loss events (section 7.4). The dual-trigger Lane 1 product is precise (7 of 9 payouts to real losses) but catches only 12% of losses, and its catastrophe index was chosen after seeing 2019–25 data (section 7.9).
2. Parcel boundaries exist only for YSR (about 56% of villages). Palnadu and Manyam run at mandal level; mandal-level flood is spread over cropland in proportion to crop area.
3. Sentinel-1 meets 72 h with probability 24–49% per pilot mandal (12-day repeat; 8 of 22 events as originally run). Lane 2 relief responds inside 72 h with rainfall and photos; Lane 1 insurance settles when the radar image arrives. Every result carries its image date.
4. SAR cannot tell disaster flooding from paddy puddling or Rabi irrigation. The e-Panta planting gate and the dry-control floor handle this, at the cost of blocking most acute index payouts in paddy (cases go to relief enumeration instead).
5. FAO-56 stage lengths are generic: AP chilli runs longer than FAO "peppers", and local variety durations differ. Satellite phenology per parcel can replace them (data in hand for YSR 2023–26).
6. Irrigation source is unknown for about 70% of YSR acreage and exists for Kharif 2026 only.
7. CHIRPS lags about a month; September 2026 events use ERA5, marked provisional.
8. Earth Engine noncommercial quota limited reprocessing; six parcel chunks (about 4,000 parcels each) timed out in individual years.

---

## 9. Operations: alerts and automation

- **Farmer and officer alerts (Telugu / English):** generated from every non-"no payout" decision (`pipeline/p19_alerts.py`; dashboard tab "Farmer alerts").
  - **Index payout (Lane 1):** both indices crossed their levels, % of sum insured paid automatically, no claim or visit.
  - **Relief enumeration (Lane 2):** upload a geotagged field photo or meet the AEO; radar-flooded villages first.
  - Mandal names come in Telugu from e-Panta.
  - The Telugu text is machine-drafted and must be reviewed by the Department before farmer use. No SMS gateway is connected in this POC.
- **One command:** `py -3.13 poc/run_all.py` rebuilds triggers, validation, decisions, alerts and the dashboard from local data.
- **Live refresh:** `py -3.13 poc/run_all.py --live <earth-engine-project>` first pulls this season's ERA5, CHIRPS and GPM IMERG rainfall, rebuilds the event catalogues, and maps any new event with Sentinel-1 using the same frozen method.

## 10. Scaling

- **Everything runs from open data plus e-Panta:** CHIRPS, Sentinel-1/2, MODIS, IBTrACS and geoBoundaries.
- **Adding a district** needs only its e-Panta extract and, for parcel level, its APAIMS cadastral.
- **Triggers recalibrate per mandal** from that mandal's own rainfall record, so no thresholds need hand-tuning.

---

## 11. References
- Allen R.G. et al. (1998) *Crop evapotranspiration*, FAO Irrigation and Drainage Paper 56.
- Clement M.A., Kilsby C.G., Moore P. (2018) Multi-temporal SAR flood mapping using change detection. *J. Flood Risk Management* 11(2).
- Funk C. et al. (2015) The CHIRPS dataset. *Scientific Data* 2.
- Government of India (2016) *Manual for Drought Management*.
- Government of India, Ministry of Home Affairs (2022) *Items and norms of assistance from SDRF / NDRF, 2022–26* (input subsidy where crop loss is 33% or more).
- Kish L. (1965) *Survey Sampling*. Wiley (design effect).
- Huffman G.J. et al. (2023) *NASA GPM IMERG V07 Algorithm Theoretical Basis Document*.
- Kogan F.N. (1995) Application of vegetation index and brightness temperature for drought detection. *Adv. Space Res.* 15(11).
- McKee T.B., Doesken N.J., Kleist J. (1993) The relationship of drought frequency and duration to time scales. 8th Conf. Applied Climatology.
- Otsu N. (1979) A threshold selection method from gray-level histograms. *IEEE Trans. SMC* 9(1).
- Pech-Pacheco J.L. et al. (2000) Diatom autofocusing in brightfield microscopy: a comparative study. *Proc. 15th ICPR* 3.
- Wilson E.B. (1927) Probable inference, the law of succession, and statistical inference. *JASA* 22(158).
- Twele A. et al. (2016) Sentinel-1-based flood mapping: a fully automated processing chain. *Int. J. Remote Sensing* 37(13).
- UN-SPIDER Recommended Practice: Flood mapping and damage assessment using Sentinel-1 SAR data in Google Earth Engine.
- Zhang X. et al. (2011) Indices for monitoring changes in extremes (ETCCDI). *WIREs Climate Change* 2(6).
