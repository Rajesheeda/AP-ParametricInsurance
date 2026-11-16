# Demo Guide — Parametric Insurance & Disaster Loss Assessment (Case 100075)

**Demo:** 17 Nov 2026, morning · **10 min demo + 5 min Q&A** · **Dashboard:** http://127.0.0.1:8010/
**How to use this file:**
- **Part A** explains the ideas in plain English. Read it once tonight.
- **Part B** is the story: our approach and the 7 innovations.
- **Part C** goes screen by screen: what is on screen, what we are proving, what to say (Telugu with English terms), and what it means for you.
- **Part D** is Murthy's likely questions with answers.
- **Part E** is the morning checklist.

All numbers come from the 16 Nov rebuild, with the corrected radar method. Say only what is on the screen.

---

## Part A — Understand it first (plain English)

### A1. The problem in one paragraph
- When a cyclone or drought hits, two different things must happen.
- **(1) Insurance** must pay farmers who bought a policy.
- **(2) Government relief** (SDRF "input subsidy") must reach farmers who lost at least 33% of their crop.
- Today both are slow. Officers visit fields, and claims take months.
- Weather-only insurance (WBCIS) pays on rainfall alone, so it often pays the wrong people. Heavy rain does not always destroy a crop, and irrigation hides droughts.
- The hackathon asks for a faster, more objective system: satellites, rainfall data, phone photos, and loss assessment within 72 hours.

### A2. Words you will hear (and what they really mean)
| Word | Plain meaning |
|---|---|
| **Kharif / Rabi** | Monsoon crop season (Jun–Nov) / winter crop season (Nov–Mar). |
| **Mandal** | Sub-district (like a taluk). Our pilot is 7 mandals. |
| **e-Panta** | AP's crop-booking app: for every survey number, the crop, variety, **sowing date** and acres. Our "who grows what, where, since when". |
| **Survey number / cadastral** | Land-parcel ID / the parcel boundary map. We have boundaries only for YSR Kadapa. |
| **CCE (crop-cutting experiment)** | Officials harvest a small sample plot and weigh the grain: the **official measured yield**. Our ground truth. We have it for YSR Kadapa only, 2019–2025. |
| **PMFBY** | The national crop insurance scheme; pays when the CCE yield falls below a threshold. |
| **WBCIS** | Weather-based insurance: pays when rainfall crosses levels. Fast, but often wrong (pays without loss, misses real loss). |
| **Parametric insurance** | Pays automatically by a **formula on an index** (rain, satellite); no claim, no field visit. Fast and objective, but only as good as the index. |
| **Index / trigger / exit** | The measured number / the level where payout starts / the level where it reaches 100%. Ours: trigger = 1-in-5-year level, exit = 1-in-25-year level of that mandal. |
| **"1-in-5 year level"** | A rainfall amount reached in about 1 year out of 5 in that mandal's own history (1995–2024). Every mandal gets its own level. |
| **Sum insured** | The rupees per acre the policy covers (notified "scale of finance"). We were not given it, so we show payout as **% of sum insured**. |
| **Basis risk** | The gap between what the index says and what really happened in the field: the farmer lost a crop and the index didn't pay, or the reverse. The central weakness of all index insurance. |
| **Dual trigger** | Pay only when **two independent indices both** agree (rain AND satellite). Cuts wrong payouts. |
| **SDRF input subsidy** | State disaster relief for ≥33% crop loss: ₹8,500/ha rainfed, ₹17,000/ha irrigated, up to 2 ha per farmer (MHA norms, 10 Oct 2022). Reduced if insurance already paid for the same disaster. |
| **AEO** | Agriculture Extension Officer: the field officer who verifies damage. |
| **Sentinel-1 (SAR radar)** | European radar satellite. It **sees through clouds**, which matters in cyclones. Calm water reflects radar away, so flooded land looks **dark**: the signal **drops**. |
| **dB, VH, VV** | Radar brightness in decibels; VH and VV are two polarisations (how the radar wave is sent and received). We use VH for flood. |
| **Orbit-matched** | Compare before/after images taken from the **same satellite track**, so viewing geometry is identical and only the ground changed. |
| **Speckle** | Grainy noise in radar images; we smooth it (50 m median filter). |
| **Otsu threshold** | A standard automatic way to pick the dark/bright cut-off from the image itself, not by hand. |
| **False-alarm floor** | We run the flood detector on **dry dates** (no flood). Whatever it "finds" there is noise. A real flood must beat that floor. |
| **Positive control** | Test the method on a **known** flood first (Budameru/Vijayawada, Sep 2024). It passed: 5.6% flooded vs 1.4% floor. |
| **Revisit** | How often the satellite passes. Sentinel-1 passes our mandals every **12 days**, so there is only a 24–49% chance of an image within 72 hours. |
| **Sentinel-2 / NDVI** | Optical satellite (blocked by clouds) / a greenness index. |
| **MODIS VCI** | Vegetation Condition Index: how green the crop is compared with that place's own history, 0–100. **VCI < 35 = stressed** (Kogan's standard). Our drought cross-check. |
| **ERA5 / CHIRPS / IMERG** | Three global rainfall datasets (model reanalysis / satellite+gauge / satellite). ERA5 is published about 6 days late. |
| **ECMWF, GFS, ICON** | Weather **forecast** models, available immediately; used only as a provisional reading during an event. |
| **FAO-56 crop stages** | The UN FAO standard for crop growth stages (initial, development, mid, late) and their lengths; tells us **when** rain hurts most. |
| **Precision** | Of the times we paid, how many were real losses. |
| **POD (detection rate)** | Of all real losses, how many we caught. |
| **Base rate (36%)** | How often a loss happens anyway. An index must beat this, or it is no better than paying at random. |
| **Wilson 95% CI** | The honest uncertainty range around a percentage from a small sample. |
| **Qualification gate** | Our rule: an index enters the contract only if the **lower end** of its precision CI is above the 36% base rate. |
| **ICC / independent observations** | Losses in one season hit many mandals together, so 166 mandal-years behave like only ~14 independent data points. |
| **Pre-registration** | Writing the prediction and scoring rule **before** seeing the result, so nobody can say we tuned to the answer. |
| **BPH (brown plant hopper)** | A paddy pest that thrives after floods. |

### A3. Our idea in 60 seconds (memorise this)
1. **Separate insurance from relief, never mix them.**
   - Insurance = an automatic formula on indices (fast, objective).
   - Relief = real damage checked in the field (fair).
   - Mixing them makes insurance slow and arguable.
2. **Insurance pays only when rain AND satellite agree** (dual trigger), and only with indices that **proved themselves against the State's own crop-cutting yields** (qualification gate).
3. **Each farmer's payout uses his own sowing date** from e-Panta, not one date for the whole mandal.
4. **Relief starts within 72 hours** from rainfall, radar and quality-checked phone photos, and computes the SDRF amount from official norms.
5. **Where insurance and relief disagree, we log it** (basis risk) and fix the index between seasons.
6. **We show our failures and limits ourselves.**

---

## Part B — Solution approach and the 7 innovations

| # | Innovation | Problem it solves | Proof (number on screen) |
|---|---|---|---|
| 1 | **Two lanes, never mixed** | Insurance becomes slow and disputed when photos and visits decide payouts | Photo verification always says "Insurance is unchanged" |
| 2 | **Dual trigger (rain AND satellite)** | Rainfall-only cover pays the wrong people | YSR CCE: rainfall-only paid 24 times, **20 wrong**; our product paid 17 times, **14 real (82%, CI 59–94%)** |
| 3 | **Index qualification gate** | Anyone can claim "our index works" | An index enters only if its precision lower bound is above 36%. Our own first design **failed** this gate (17 payouts, 3 real) and we show it |
| 4 | **Farmer's own sowing calendar** | One mandal date pays early and late sowers wrongly | **1,09,039 of 5,22,208** bookings would flip paid/unpaid under a mandal calendar |
| 5 | **e-Panta gate on radar** | Radar cannot tell a flood from paddy fields filled with water for planting | Michaung 2023: **60%** of radar flags removed (no standing crop) |
| 6 | **Measured, not hand-picked** | Hand-picked thresholds are easy to attack | False-alarm floor from dry dates; photo limits from **982** Department photos; GPS limit **51 m** = median parcel radius; positive control **PASS** |
| 7 | **Tested live on real cyclones** | Back-tests can be tuned to the past | Arnab and Murasu run with the same code as the back-tests; misses published (Salur weakness, coast-wide ranking failed) |

**Plus, for the requirements:**
- **A (automated pipeline + compensation):** trigger → per-farmer payout → settlement batch; relief case → AEO verification → sanction from the MHA norms; audit log.
- **B (photo module):**
  - quality gate, geotag, crop check;
  - Healthy / Partially / Severely damaged with confidence;
  - a trained pest model (60% held-out) plus cited interventions;
  - a photo loss %;
  - a phone capture page.

---

## Part C — Screen by screen (10 minutes)

> **Format per screen:** 🖥 what is on screen · 🎯 what we are proving · 🗣 say (Telugu) · 💡 for you (plain meaning)

### 1. Opening (0:30) — no click
🎯 Frame the problem and our core idea before any screen.
🗣 "నమస్కారం సార్. Disaster తర్వాత రెండు పనులు జరగాలి — **insurance payout** మరియు **SDRF relief**. ఈ రెండింటినీ కలిపితే రెండూ slow అవుతాయి. మేము వాటిని **రెండు lanes** గా విడదీశాం: Lane 1 insurance — index మీద formula, claim లేదు, visit లేదు. Lane 2 relief — నిజమైన నష్టం 72 గంటల్లో, radar, e-Panta, photo, AEO తో. ప్రతి index ని Department **CCE yields** మీద test చేశాం — fail అయినవి కూడా చూపిస్తాం. Arnab, Murasu cyclones మీద live గా run చేశాం."
💡 You are saying: "insurance = automatic formula; relief = field truth; we proved our indices on government yield data and we are honest about failures."

### 2. Overview (1:00) — Sidebar → *Overview*
🖥 Satellite hero; KPI tiles (7 pilot mandals, 22 disasters, 20 → 0, 6,25,401 bookings, 60%); the two-lane diagram.
🎯 Innovations 1, 2, 4: the architecture, and why rainfall-only fails.
🗣 "ఈ diagram మా solution. పైన Lane 1: rainfall index **మరియు** satellite index — రెండూ దాటితేనే pay. ప్రతి రైతు **సొంత e-Panta sowing date** నుండి crop stages. కింద Lane 2: radar damage map → e-Panta gate (ఆ రోజు నిలబడిన పంట మాత్రమే) → CCE-calibrated loss → photo/AEO enumeration.
'20 → 0' tile: rainfall-only cover YSR లో 24 సార్లు pay చేసింది, 20 తప్పు; dual trigger తో తప్పు season payouts 0.
Mandal calendar వాడితే 1,09,039 bookings paid/unpaid మారిపోతాయి — అదే basis risk; మేము ప్రతి booking ని దాని సొంత sowing week తో price చేశాం."
💡 Point at the diagram while talking. "20 → 0" means: of 24 rainfall-only payouts, 20 went to farmers who had no real loss (by CCE), and adding the satellite check removed those wrong season payouts.

### 3. Live: Cyclone Arnab (2:30) ⭐ — Sidebar → *Live: Cyclone Arnab*
🖥 LIVE badge; KPIs **15** relief mandals, **6** above the rain trigger, **1** index payout (Salur), **T+69 h**; the timeline cards; the mandal table; "Reading" and "Limits" cards.
🎯 Innovation 7: the whole system worked on a real cyclone, both lanes, with our weakness stated.
🗣
- "Arnab 28 Oct న Yanam దగ్గర తీరం దాటింది. Back-test చేసిన **అదే code**, ఏమీ tune చేయలేదు.
- **Relief lane:** landfall తర్వాత **69 గంటల్లో** relief list, Telugu/English alerts. Final ERA5 తో **15 Manyam mandals**, 1.22 లక్షల standing acres.
- **Insurance lane:** rainfall మాత్రమే చూస్తే 6 mandals కి **22% నుండి 80%** pay చేయాల్సి వచ్చేది. Radar ఒక్క **Salur** ని మాత్రమే confirm చేసింది — 34.5%. మిగతా 5 hold.
- **మనమే చెప్పాల్సింది:** Salur లో radar signal 0.60% మాత్రమే, payout 34.5%. Radar confirm మాత్రమే చేస్తుంది, amount rain నిర్ణయిస్తుంది — ఇది weakness. ఇంకా: మా false-alarm floor February/March dry dates నుండి; November లో Rabi land preparation వల్ల signal రావచ్చు. **Seasonal floor + minimum-signal rule** ని next season gate ద్వారా test చేస్తాం.
- **Bug fix (14 Nov):** మా code district మొత్తానికి ఒకే radar pass వాడింది; ఆ pass కవర్ చేయని mandals ని '0% flood' అని చదివింది. Fix చేశాం, పాత-కొత్త results రెండూ ఉంచాం.
- **Radar timing:** 15 లో 5 మాత్రమే 72 గంటల్లో imaged — Sentinel-1 ఇక్కడ 12 రోజులకు ఒకసారి. అందుకే relief radar కోసం ఆగదు."

🗣 **Murasu (15 sec):** "3 Nov Murasu: Palnadu లో 20 mandals relief, insurance 0. Chilakaluripet లో radar 22.4% flood చూపించింది, కానీ rain contract level కి రాలేదు — relief pay చేస్తుంది, insurance చేయదు, case **basis-risk log** లోకి."
💡
- **Relief opened fast** on rainfall alone (no need to wait for radar).
- **Insurance waited** for the second index.
- **Salur paid**, but on a weak signal. Admitting this before Murthy finds it earns credibility.
- **"T+69 h"** = 69 hours after landfall, under the 72-hour target.
- **Basis-risk example:** Murasu's Chilakaluripet shows the lanes disagreeing, and that is exactly what the log is for.

### 4. Insurance product (1:30) — Sidebar → *Insurance product*
🖥 Term sheet; qualification-gate table (each index: payouts, real, precision CI, pass/fail); premium.
🎯 Innovations 2 and 3: the index had to prove itself on government yields, and our own first design failed.
🗣 "ఇది **qualification gate**: CCE లో loss rate 36%. ఏ index అయినా దాని precision యొక్క 95% lower bound 36% కంటే ఎక్కువ ఉంటేనే contract లోకి.
- Rainfall-only: precision 17% — **fail**.
- మేము ముందే declare చేసిన 3-source consensus × radar: 17 payouts, 3 real — **fail**. అది కూడా screen మీద ఉంచాం.
- మా Lane 1 product: **17 payouts, 14 real — 82% (CI 59–94%)**. Honest గా: 14 లో 13 hits 2020 **Nivar** cyclone ఒక్కటే, ERA5 × radar ని data చూసిన తర్వాత ఎంచుకున్నాం — అందుకే Kharif 2026 CCE తో మళ్ళీ test.
- Premium (pure burn cost, YSR): rainfall-only **24.9%** vs మా dual **9.4%** of sum insured — premium తక్కువ అంటే రైతు share, State subsidy రెండూ తగ్గుతాయి."
💡
- **Precision 82%** means about 8 in 10 payouts went to real losses. The range 59–94% is wide because the data is small.
- The Nivar point is a weakness: most hits come from one storm. Saying it first protects you.
- **Burn cost** = the average yearly payout. It is the "pure" premium before the insurer's margin.

### 5. Photo verification — Module B (2:00) — Sidebar → *Photo verification* (live)
🖥 Upload form; results with ✓/✗ per check; verdict; recommended interventions; the "Insurance unchanged" line.
🎯 Requirement B: a quality-gated, location-checked photo with damage class, confidence, pest ID and interventions, and it never changes insurance.
🗣 **(a) `2_blurry_shaken.jpg`:** "Blur photo — మొదటి check లోనే **RETAKE PHOTO**; analysis run కాదు. Limits Department యొక్క 982 field photos నుండి measure చేశాం: genuine 91% accept, degraded 100% refuse."
🗣 **(b) `1_clear_paddy_brown_plant_hopper.jpg`:** "ప్రతి check వేరుగా: quality ✓, location Balijipeta ✓, event timing ✓, vision — Paddy, **Severely damaged**, confidence, photo loss %, crop match ✓. మా **trained pest model** — **brown plant hopper**, తర్వాత **DPPQS / ICAR / ANGRAU** నుండి interventions, source తో. చివరి line: **insurance మారదు**. Location type చేశాం కాబట్టి 'MANUAL GPS, OFFICER TO VERIFY'.
Pest model Department images మీద train — held-out **60%** vs Gemini 47%. ఇది officer కి suggestion మాత్రమే."
🗣 **Phone (10 sec):** "`/poc/capture.html` — phone camera, తీసిన క్షణంలో phone GPS; accuracy 51 m లోపు ఉంటేనే geotag — అది YSR median parcel size నుండి."
💡
- **The first photo** shows that a bad photo is rejected before anyone wastes time on it.
- **The second** shows every check, the pest, and what the farmer should do.
- **"Insurance unchanged"** is the two-lane rule in action.
- **"60% held-out"** means the model was tested on photos it never saw in training, which is the honest way to measure a model.

### 6. Compensation (1:30) — Sidebar → *Compensation*
🖥 KPIs: **15** relief cases, budget **₹12.6–25.2 cr**, **13,096** settlement lines, audit ✓. Relief-case table with states; the insurance batch with its SHA-256; the audit log.
🎯 Requirement A: the compensation workflow, from trigger to money, with official norms and an audit trail.
🗣 "Requirement A — compensation workflow.
- **Relief:** Arnab 15 mandals = 15 cases. OPENED → photo వస్తే EVIDENCE RECEIVED → AEO ≥33% hectares enter → sanction **MHA SDRF norms** నుండి ఆటోమేటిక్ (₹8,500/ha rainfed, ₹17,000 irrigated) → PAID. Budget **₹12.6–25.2 కోట్లు** — planning number, payment list కాదు.
- MHA norms లోనే: **insurance claim వస్తే input subsidy తగ్గుతుంది** — Salur లో అదే link.
- **Insurance:** Gurazala 2023 — 13,096 bookings ఒక settlement batch; file SHA-256 తో lock, approve చేసిన file నే insurer కి.
- Rupees కి notified sum insured కావాలి — ఇవ్వలేదు, invent చేయలేదు.
- ప్రతి action officer role తో, hash-chain audit log — ఒక line మార్చినా 'broken' చూపిస్తుంది."
💡
- **The budget** is an estimate for the government's planning. Who actually gets paid is decided by the AEO's verified hectares.
- **SHA-256** is a digital fingerprint: if anyone edits the payout file after approval, the fingerprint changes and the system refuses it.
- (Optional live click: Balijipeta → "AEO verify ≥33%" → 120 rainfed + 30 irrigated → Sanction → ₹15,30,000. Delete `poc\data\compensation_log.jsonl` afterwards.)

### 7. Limits + close (1:00) — Sidebar → *Validation & limits* (or no click)
🎯 Say the limits before Murthy does, then make one clear ask.
🗣 "Limits, మీరు అడగకముందే:
1. **≥75% correlation:** CCE ఒక district, 7 seasons; losses season-wise cluster — ~14 independent observations. ఈ data తో 75% ని prove చేయలేం, reject కూడా చేయలేం; ~25 seasons కావాలి.
2. **≥80% flood accuracy vs APSDMA:** APSDMA maps ఇవ్వలేదు. Budameru positive control PASS. Sentinel-2 comparison ఇంకా score కాలేదు.
3. Coast-wide Arnab test లో delta districts ని మా radar సరిగ్గా rank చేయలేదు — declared test **fail**: delta first pass Murasu rain తర్వాత వచ్చింది, November land preparation కూడా signal ఇస్తుంది. Seasonal floor దానికి fix.
4. Cadastral YSR కి మాత్రమే; irrigation 70% unknown; radar 72 h లో 24–49% chance.
**ఒకే request:** Arnab, Murasu mandal-level crop-damage enumeration — మా predictions score చేయడానికి. ధన్యవాదాలు."
💡 Saying failures first is our strategy: Murthy respects honest concessions and hammers hidden flaws.

| Screen | Time |
|---|---|
| Opening | 0:30 |
| Overview | 1:00 |
| **Live: Cyclone Arnab** | 2:30 |
| Insurance product | 1:30 |
| Photo verification (live) | 2:00 |
| Compensation | 1:30 |
| Limits + close | 1:00 |
| **Total** | **10:00** |

Short on time? Cut Overview to 0:30 and Compensation to 1:00. Never cut Arnab or the Photo demo.

---

## Part D — Questions (Murthy first), with answers

Murthy works bottom-up: satellite physics → validation → method choices → innovation.
- Answer in 20–30 seconds.
- Admit what is weak, then give the number.
- **Never guess.** If you don't know, say "we haven't measured that; here is how we would."

### D1. Satellite / radar physics
| Question | Answer to say | 💡 For you |
|---|---|---|
| "Why radar, not optical?" | "Cyclone days are cloudy; Sentinel-1 C-band SAR sees through cloud. Optical (Sentinel-2) is used only for cloud-masked crop views and as an independent accuracy check." | Radar works in clouds. |
| "How do you detect flood?" | "VH, orbit-matched pre/post; a water threshold by Otsu on a balanced sample of JRC permanent water and cropland (about −21 to −24 dB); a change of at least 3 dB drop (Clement et al. 2018); masks: JRC permanent water, HAND > 15 m (high ground), clusters < 8 pixels." | Calm water = dark; we need dark **and** a darkening vs before. |
| "Speckle filtering?" | "50 m focal median. A Lee (1980) filter and 2/4 dB variants are in a sensitivity study declared beforehand; not scored yet." | Smoothing the grainy noise. |
| "Incidence angle / geometry?" | "Pre and post are from the same relative orbit, so the geometry is identical; we compare like with like and don't need angle normalisation." | Same satellite track before and after. |
| "Flooded paddy raises backscatter (double bounce). Your drop-only rule misses it." | "We tested it with a rule declared first: a VV rise ≥ 3 dB is 5.4% of cropland after Budameru, but 3.5% on a dry February date; ratio 1.55, below the 2× we declared. No usable signal at C-band here, so the drop rule stays." | Water under standing plants can make radar brighter; we checked, and here it isn't reliable. |
| "Paddy puddling looks like flood." | "Yes. The e-Panta gate counts only crops already standing on that date; inside a paddy planting window radar does not confirm. Michaung 2023: 60% of radar flags removed." | Farmers flood fields to plant rice; we use sowing dates to ignore those. |
| "How do you know radar works at all?" | "Positive control declared before running: Budameru 2024, 19 mandals, 5.61% flooded cropland vs 1.41% dry floor: PASS (18–22% in the worst mandals)." | Tested on a flood everyone knows happened. |
| "False alarms?" | "Each mandal's floor comes from the same detector on two dry dates (Feb/Mar 2024). Weakness: wrong season for November; a seasonal floor is the next-season fix through the gate." | Noise level measured, not guessed. |
| "72 hours with a 12-day satellite?" | "From acquisition metadata 2021–2026: P(image within 72 h) is 24–49% per pilot mandal. So relief runs on rain and photos inside 72 h; radar confirms when it arrives. Arnab: 5 of 15 relief mandals inside 72 h." | We measured how often radar comes in time. |
| "MODIS 250 m on small parcels?" | "VCI is used only at mandal level as the drought cross-check, never per parcel. Median YSR parcel is 0.82 ha." | One MODIS pixel is bigger than most fields, so we use it only for the whole mandal. |
| "Clouds in Sentinel-2?" | "s2cloudless probability plus SCL masking; every image carries its date." | Cloudy pixels removed. |
| "Did radar find the delta damage for Arnab?" | "No, and we declared that test before computing: it failed. The delta's first usable pass (4 Nov) came after Murasu's rain, and November is Rabi land preparation; our floors are from Feb/Mar. A seasonal floor is the fix, through the gate." | Honest failure; the reason is timing and season. |

### D2. Validation and statistics
| Question | Answer | 💡 |
|---|---|---|
| "You didn't reach 75%." | "It can't be tested with this data: one district, 7 seasons, losses clustered by season (ICC 0.47), so about 14 independent observations. A true r = 0.75 has a 95% CI of −0.01 to 0.96. What we can show: rainfall-only 20 of 24 wrong; dual 14 of 17 right." | The sample is too small to prove or disprove 75%. |
| "82% sounds good, but how many events?" | "13 of 14 hits are Nivar 2020. We say so; the index re-runs the gate on Kharif 2026 CCE." | Mostly one storm, so we test again. |
| "You chose ERA5 after seeing the data." | "Yes, on screen. Our declared consensus design failed (17 payouts, 3 real). ERA5 is on probation until new CCE tests it." | We admit post-hoc choice. |
| "You changed numbers after the bug." | "The bug: a district was scored with one radar pass, so mandals outside it read 0% instead of 'not imaged'. Fixed 14 Nov before scoring; old and new both kept. Lane 1 went from 9 / 7 (78%) to 17 / 14 (82%); the positive control is unchanged." | Fixing a bug openly is not tuning. |
| "Why 80% indemnity?" | "PMFBY offers 70/80/90%; we report all three: 53% / 82% / 94% precision." | Standard options, all shown. |
| "Why 1-in-5 trigger, 1-in-25 exit?" | "A standard return-period design; sensitivity shown: burn cost 7% at 1-in-10/50, 20% at 1-in-3/15. Each mandal uses its own history." | A design choice, with its effect shown. |
| "Hand-picked constants?" | "None hidden: 33% and the rupee rates are MHA norms; 3 dB is Clement 2018; VCI 35 is Kogan; photo limits are percentiles of 982 Department photos; 51 m is the measured median parcel radius." | Every number has a source. |

### D3. Soil, water, crop
| Question | Answer | 💡 |
|---|---|---|
| "Soil moisture?" | "Tested: ERA5-Land root zone and SMAP surface. In YSR, dry soil does not mean loss, because of irrigation; drought plus dry-soil precision was 0–11% vs a 36% base. Evidence only, not in the contract." | We checked, and it didn't help here. |
| "Water balance?" | "We do not claim a water balance. FAO-56 is used for crop-stage timing only." | Don't over-claim. |
| "Irrigation?" | "Unknown for about 70% of YSR acreage and only for Kharif 2026. That is why rainfall-only fails in YSR and why we need the satellite second trigger." | Irrigated crops survive dry spells. |
| "Wind lodging in Manyam?" | "Radar sees water, not flattened plants. Lodging goes to relief enumeration and the basis-risk log; a lodging index can enter only through the gate." | Wind damage is invisible to a flood index. |

### D4. AI, photos, workflow (Kalyan / Mohiuddin too)
| Question | Answer | 💡 |
|---|---|---|
| "Where is the AI?" | "One trained model we claim: the pest classifier, held-out 60% vs Gemini 47% (McNemar p = 0.02). The vision model is general; we call it a suggestion. Our fused loss model had AUC 0.53, no skill, so we didn't use it." | Claim AI only where tested. |
| "Is the damage class validated?" | "Partly: 90% of 218 Department diseased photos called damaged (CI 85–93%). False alarms on healthy crop can't be measured, because there are no healthy labels. The officer confirms 33%." | Half-measured; we say which half. |
| "Phone GPS can be faked." | "So can EXIF. Defences: crop booking, timing, crop seen, AEO sampling. A photo never changes insurance." | Photos are evidence, not money. |
| "How much money?" | "Relief: MHA rate × verified ha, computed automatically. Insurance: needs the notified sum insured; one table fill gives rupees." | We didn't invent rupees. |
| "What does the Department get tomorrow?" | "A ranked relief list with standing acres inside 72 h, Telugu/English alerts, a photo check, SDRF sanction workflow, and an insurance decision from a written rule." | The practical value. |
| "Can it scale to all districts?" | "Yes: e-Panta, boundaries, ERA5 and Sentinel-1 are statewide. With cadastral and CCE for a district, the same gate re-runs." | Same code, more data. |

---

## Part E — Morning checklist (20 minutes before)

1. Start the backend (`poc-backend`) and **wait 1 minute**.
2. Run the preflight; the last line must say **ALL CLEAR**:
   ```
   py -3.13 C:\AP-ParametricInsurance\poc\preflight.py
   ```
3. Photos are in `poc\data\demo_photos\`: `2_blurry_shaken.jpg` first, then `1_clear_paddy_brown_plant_hopper.jpg`. Form: Event *LIVE · Cyclone Arnab* · Lat 18.5999 · Lon 83.5119 · Taken 2026-10-30 10:00 · Crop Paddy.
4. After any rehearsal, delete `poc\data\compensation_log.jsonl`.
5. Have a phone hotspot as backup. Without internet the photo shows "VISION UNAVAILABLE" and the map is blank; everything else works.
6. Browser full screen at zoom 100%; click every tab once before the judges arrive.
