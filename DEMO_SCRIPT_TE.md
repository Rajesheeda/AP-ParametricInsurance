# Demo Guide — Parametric Insurance & Disaster Loss Assessment (Case 100075)

**Demo:** 17 Nov 2026, morning · **10 min demo + 5 min Q&A** · **Dashboard:** http://127.0.0.1:8010/
**How to use this file:**
- **Part A** explains the ideas in plain English. Read it once tonight.
- **Part B** is the story: my approach and the 7 innovations.
- **Part C** is the 10-minute script, word for word: solution → how I used the data → what is new → live proof → the two modules.
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
| **Mandal** | Sub-district (like a taluk). My pilot is 7 mandals. |
| **e-Panta** | AP's crop-booking app: for every survey number, the crop, variety, **sowing date** and acres. My "who grows what, where, since when". |
| **Survey number / cadastral** | Land-parcel ID / the parcel boundary map. I have boundaries only for YSR Kadapa. |
| **CCE (crop-cutting experiment)** | Officials harvest a small sample plot and weigh the grain: the **official measured yield**. My ground truth. I have it for YSR Kadapa only, 2019–2025. |
| **PMFBY** | The national crop insurance scheme; pays when the CCE yield falls below a threshold. |
| **WBCIS** | Weather-based insurance: pays when rainfall crosses levels. Fast, but often wrong (pays without loss, misses real loss). |
| **Parametric insurance** | Pays automatically by a **formula on an index** (rain, satellite); no claim, no field visit. Fast and objective, but only as good as the index. |
| **Index / trigger / exit** | The measured number / the level where payout starts / the level where it reaches 100%. Mine: trigger = 1-in-5-year level, exit = 1-in-25-year level of that mandal. |
| **"1-in-5 year level"** | A rainfall amount reached in about 1 year out of 5 in that mandal's own history (1995–2024). Every mandal gets its own level. |
| **Sum insured** | The rupees per acre the policy covers (notified "scale of finance"). I was not given it, so I show payout as **% of sum insured**. |
| **Basis risk** | The gap between what the index says and what really happened in the field: the farmer lost a crop and the index didn't pay, or the reverse. The central weakness of all index insurance. |
| **Dual trigger** | Pay only when **two independent indices both** agree (rain AND satellite). Cuts wrong payouts. |
| **SDRF input subsidy** | State disaster relief for ≥33% crop loss: ₹8,500/ha rainfed, ₹17,000/ha irrigated, up to 2 ha per farmer (MHA norms, 10 Oct 2022). Reduced if insurance already paid for the same disaster. |
| **AEO** | Agriculture Extension Officer: the field officer who verifies damage. |
| **Sentinel-1 (SAR radar)** | European radar satellite. It **sees through clouds**, which matters in cyclones. Calm water reflects radar away, so flooded land looks **dark**: the signal **drops**. |
| **dB, VH, VV** | Radar brightness in decibels; VH and VV are two polarisations (how the radar wave is sent and received). I use VH for flood. |
| **Orbit-matched** | Compare before/after images taken from the **same satellite track**, so viewing geometry is identical and only the ground changed. |
| **Speckle** | Grainy noise in radar images; I smooth it (50 m median filter). |
| **Otsu threshold** | A standard automatic way to pick the dark/bright cut-off from the image itself, not by hand. |
| **False-alarm floor** | I run the flood detector on **dry dates** (no flood). Whatever it "finds" there is noise. A real flood must beat that floor. |
| **Positive control** | Test the method on a **known** flood first (Budameru/Vijayawada, Sep 2024). It passed: 5.6% flooded vs 1.4% floor. |
| **Revisit** | How often the satellite passes. Sentinel-1 passes the pilot mandals every **12 days**, so there is only a 24–49% chance of an image within 72 hours. |
| **Sentinel-2 / NDVI** | Optical satellite (blocked by clouds) / a greenness index. |
| **MODIS VCI** | Vegetation Condition Index: how green the crop is compared with that place's own history, 0–100. **VCI < 35 = stressed** (Kogan's standard). My drought cross-check. |
| **ERA5 / CHIRPS / IMERG** | Three global rainfall datasets (model reanalysis / satellite+gauge / satellite). ERA5 is published about 6 days late. |
| **ECMWF, GFS, ICON** | Weather **forecast** models, available immediately; used only as a provisional reading during an event. |
| **FAO-56 crop stages** | The UN FAO standard for crop growth stages (initial, development, mid, late) and their lengths; tells me **when** rain hurts most. |
| **Precision** | Of the times the index paid, how many were real losses. |
| **POD (detection rate)** | Of all real losses, how many the index caught. |
| **Base rate (36%)** | How often a loss happens anyway. An index must beat this, or it is no better than paying at random. |
| **Wilson 95% CI** | The honest uncertainty range around a percentage from a small sample. |
| **Qualification gate** | My rule: an index enters the contract only if the **lower end** of its precision CI is above the 36% base rate. |
| **ICC / independent observations** | Losses in one season hit many mandals together, so 166 mandal-years behave like only ~14 independent data points. |
| **Pre-registration** | Writing the prediction and scoring rule **before** seeing the result, so nobody can say I tuned to the answer. |
| **BPH (brown plant hopper)** | A paddy pest that thrives after floods. |

### A3. My idea in 60 seconds (memorise this)
1. **Separate insurance from relief, never mix them.**
   - Insurance = an automatic formula on indices (fast, objective).
   - Relief = real damage checked in the field (fair).
   - Mixing them makes insurance slow and arguable.
2. **Insurance pays only when rain AND satellite agree** (dual trigger), and only with indices that **proved themselves against the State's own crop-cutting yields** (qualification gate).
3. **Each farmer's payout uses his own sowing date** from e-Panta, not one date for the whole mandal.
4. **Relief starts within 72 hours** from rainfall, radar and quality-checked phone photos, and computes the SDRF amount from official norms.
5. **Where insurance and relief disagree, I log it** (basis risk) and fix the index between seasons.
6. **I show my failures and limits myself.**

---

## Part B — Solution approach and the 7 innovations

| # | Innovation | Problem it solves | Proof (number on screen) |
|---|---|---|---|
| 1 | **Two lanes, never mixed** | Insurance becomes slow and disputed when photos and visits decide payouts | Photo verification always says "Insurance is unchanged" |
| 2 | **Dual trigger (rain AND satellite)** | Rainfall-only cover pays the wrong people | YSR CCE: rainfall-only paid 24 times, **20 wrong**; my product paid 17 times, **14 real (82%, CI 59–94%)** |
| 3 | **Index qualification gate** | Anyone can claim "my index works" | An index enters only if its precision lower bound is above 36%. My own first design **failed** this gate (17 payouts, 3 real) and I show it |
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

## Part C — The demo script (10 minutes): solution, data, innovation

> **Rule:** solution first, data second, innovation third, proof last. No stories. Limits only when asked: the answers are in Part D.
> **Format per screen:** 🖥 click · 🗣 what I say (word for word) · 💡 for me

### 1. The solution in one minute (1:00) — Sidebar → *Overview* (hero)
🗣 **Say:**
> "Sir, I built a complete system for crop insurance and disaster relief, running on the Department's own data.
> It does three things automatically.
> One, after a flood or cyclone, it finds which mandals and which crops were hit within 72 hours; for drought, it tracks the whole season.
> Two, it decides the insurance payout for every e-Panta booking, by formula, with no claim and no field visit.
> Three, it runs the relief process: phone photo verification, AEO verification, and the SDRF sanction amount.
> Insurance and relief are kept as two separate lanes, so insurance stays fast and objective, and relief stays fair."

### 2. How I used the data (2:00) — stay on *Overview*, point at the data chips, then the two-lane diagram
🗣 **Say:**
> "Every decision comes from real data. Here is what each source does.
> **e-Panta**, 6.25 lakh bookings in the pilot mandals: for every survey number I know the crop, the acres and the exact sowing date. So every farmer's crop stage is calculated from his own sowing date.
> **Cadastral maps**, 2.23 lakh parcels in YSR Kadapa: they give each parcel its boundary, so satellite readings and photo locations are checked parcel by parcel.
> **CCE yields from the Department**, YSR Kadapa 2019 to 2025: this is the ground truth. I used it to test every index, and to calibrate how much loss each type of event causes.
> **Sentinel-1 radar**: it sees through cyclone clouds and maps flooded standing crops, comparing the same orbit before and after the event.
> **Sentinel-2 and MODIS**: crop condition, used as the drought check.
> **Rainfall from ERA5, CHIRPS and GPM**, daily for every mandal for about 30 years: each mandal gets its own 1-in-5 and 1-in-25 year levels from its own history.
> **The Department's field photos**: 982 photos set the photo quality limits, and 1,124 labelled pest images trained my pest model.
> All of it flows through one pipeline: rain and radar trigger, e-Panta decides which crops were standing, CCE says how much loss to expect, and the result is a payout or a relief case."

💡 This is the "how we used the data" answer they asked for. Point at each chip as you name it.

### 3. What is new (2:00) — Sidebar → *Insurance product*
🗣 **Say:**
> "Five things in this design are new.
> **First, a dual trigger.** Insurance pays only when rainfall and satellite both agree. Rainfall-only cover in YSR paid 24 times and 20 of those had no real loss. My product paid 17 times and 14 were real losses: 82%.
> **Second, a qualification gate.** No index enters the contract on opinion. It must beat chance on the Department's own crop-cutting yields. This table shows every index I tested: the ones that failed are rejected automatically. And it works crop by crop: it passes for paddy, but for cotton it is not yet good enough, so cotton stays with PMFBY until it is.
> **Third, each farmer's own calendar.** Crop stages start from each booking's sowing date. With one mandal calendar, 1 lakh 9 thousand bookings would get the wrong answer.
> **Fourth, e-Panta on top of radar.** Radar cannot tell a flood from a paddy field filled with water for planting. e-Panta tells us what was standing that day; in Cyclone Michaung this removed 60% of radar flags on fields with no standing crop.
> **Fifth, the premium falls.** Because wrong payouts are removed, the YSR premium drops from 24.9% to 9.4% of the sum insured. That saves money for both the farmer and the State."

💡 Numbers to point at: 20 wrong → 0, 82% real, the pass/fail column, 24.9% → 9.4%.

### 4. It works live: Cyclone Arnab (1:45) — Sidebar → *Live: Cyclone Arnab*
🗣 **Say:**
> "This is not a back-test. Cyclone Arnab hit on 28 October and I ran the same system on it, live.
> Within 69 hours, it produced the relief list: 15 mandals and 1.22 lakh acres of standing crop, with Telugu and English alerts.
> On the insurance side, rainfall alone would have paid 6 mandals up to 80% of the sum insured. The radar confirmed one, Salur, and held the other five. That is the dual trigger protecting the scheme, in a real storm.
> I also ran Cyclone Murasu on 3 November: 20 mandals in Palnadu were opened for relief within the same process."

💡 Point at the four numbers on top: 15 · 6 · 1 · T+69 h.

### 5. Module B — phone photos (1:45) — Sidebar → *Photo verification* (live)
🗣 **(a) Upload `2_blurry_shaken.jpg`:**
> "A farmer sends a blurred photo. It is rejected at once: retake photo. The limits come from 982 Department photos."

🗣 **(b) Upload `1_clear_paddy_brown_plant_hopper.jpg`:**
> "Now a clear photo. In one step the system checks the photo quality, the location, the timing against the cyclone, the crop against the e-Panta booking, and the damage: severely damaged, with a confidence score and a loss estimate.
> My trained pest model identifies brown plant hopper and shows the recommended actions from ICAR, DPPQS and ANGRAU.
> The photo goes to relief. It never changes the insurance payout.
> The same check runs from a phone page that captures the photo with the phone's GPS."

### 6. Module A — compensation workflow (1:15) — Sidebar → *Compensation*
🗣 **Say:**
> "Finally, the money.
> For relief, each affected mandal is a case: opened, evidence received, verified by the AEO, sanctioned, paid. The sanction is calculated from the MHA disaster-relief norms: 8,500 rupees per hectare rainfed, 17,000 irrigated. For Arnab, the system estimates a relief budget of 12.6 to 25.2 crore.
> For insurance, the payouts become a settlement batch for the insurer, 13,096 bookings for Gurazala 2023, locked with a digital fingerprint so it cannot be changed after approval.
> Every step is logged with the officer's role."

### 7. Close (0:15)
🗣 **Say:**
> "So: one system, on the Department's own data, from the disaster to the payout. Insurance that pays the right farmers, and relief within 72 hours. Thank you, I'm happy to take questions."

| Screen | Time |
|---|---|
| 1. The solution (Overview) | 1:00 |
| 2. How I used the data (Overview) | 2:00 |
| 3. What is new (Insurance product) | 2:00 |
| 4. Live: Cyclone Arnab | 1:45 |
| 5. Module B: photos (live) | 1:45 |
| 6. Module A: compensation | 1:15 |
| 7. Close | 0:15 |
| **Total** | **10:00** |

Short on time? Drop the Murasu sentence and the phone-page sentence. Never cut screens 2 and 3: they are what the judges asked for.

---|---|
| Opening | 0:45 |
| Overview | 1:00 |
| **Live: Cyclone Arnab** | 2:20 |
| Insurance product | 1:15 |
| Photo verification (live, incl. upload time) | 2:00 |
| Compensation | 1:20 |
| Limits + close | 1:20 |
| **Total** | **10:00** |

Short on time? Skip the Murasu lines and the phone-page line, and cut Compensation to its first two paragraphs. Never cut Arnab or the photo demo. Speak slowly: about 130 words a minute is right.

---

## Part D — Questions (Murthy first), with answers

> Limits and weaknesses are **not** in the talk. Give them here, only when asked: briefly, with the number, then move on.

Murthy works bottom-up: satellite physics → validation → method choices → innovation.
- Answer in 20–30 seconds.
- Admit what is weak, then give the number.
- **Never guess.** If you don't know, say "I haven't measured that; here is how I would."

### D1. Satellite / radar physics
| Question | Answer to say | 💡 For you |
|---|---|---|
| "Why radar, not optical?" | "Cyclone days are cloudy; Sentinel-1 C-band SAR sees through cloud. Optical (Sentinel-2) is used only for cloud-masked crop views and as an independent accuracy check." | Radar works in clouds. |
| "How do you detect flood?" | "VH, orbit-matched pre/post; a water threshold by Otsu on a balanced sample of JRC permanent water and cropland (about −21 to −24 dB); a change of at least 3 dB drop (Clement et al. 2018); masks: JRC permanent water, HAND > 15 m (high ground), clusters < 8 pixels." | Calm water = dark; I need dark **and** a darkening vs before. |
| "Speckle filtering?" | "50 m focal median. Declared sensitivity study against Sentinel-2: a Lee (1980) filter gives F1 0.17 vs 0.16, no real gain; 2 / 4 dB change criteria 0.16 / 0.15. Without change detection (single image) precision falls to 33%, so change detection is needed. A water threshold 1 dB higher gives F1 0.26; it can enter only through the gate." | Smoothing the grainy noise. |
| "Incidence angle / geometry?" | "Pre and post are from the same relative orbit, so the geometry is identical; I compare like with like and don't need angle normalisation." | Same satellite track before and after. |
| "Flooded paddy raises backscatter (double bounce). Your drop-only rule misses it." | "I tested it with a rule declared first: a VV rise ≥ 3 dB is 5.4% of cropland after Budameru, but 3.5% on a dry February date; ratio 1.55, below the 2× I declared. No usable signal at C-band here, so the drop rule stays." | Water under standing plants can make radar brighter; I checked, and here it isn't reliable. |
| "Paddy puddling looks like flood." | "Yes. The e-Panta gate counts only crops already standing on that date; inside a paddy planting window radar does not confirm. Michaung 2023: 60% of radar flags removed." | Farmers flood fields to plant rice; I use sowing dates to ignore those. |
| "How do you know radar works at all?" | "Positive control declared before running: Budameru 2024, 19 mandals, 5.61% flooded cropland vs 1.41% dry floor: PASS (18–22% in the worst mandals)." | Tested on a flood everyone knows happened. |
| "False alarms?" | "Each mandal's floor comes from the same detector on two dry dates (Feb/Mar 2024). Weakness: a different season from the event; next season the floor comes from the same calendar weeks of calm years, plus a minimum margin above it, through the gate." | Noise level measured, not guessed; season-matching is the fix. |
| "72 hours with a 12-day satellite?" | "From acquisition metadata 2021–2026: P(image within 72 h) is 24–49% per pilot mandal. So relief runs on rain and photos inside 72 h; radar confirms when it arrives. Arnab: 5 of 15 relief mandals inside 72 h." | I measured how often radar comes in time. |
| "MODIS 250 m on small parcels?" | "VCI is used only at mandal level as the drought cross-check, never per parcel. Median YSR parcel is 0.82 ha." | One MODIS pixel is bigger than most fields, so I use it only for the whole mandal. |
| "Clouds in Sentinel-2?" | "s2cloudless probability plus SCL masking; every image carries its date." | Cloudy pixels removed. |
| "Flood accuracy ≥80%?" | "APSDMA maps weren't shared, so the reference is Sentinel-2, an independent optical sensor, within 1 day, rules declared in advance (24 events assessed; 5 scorable; the rest had no clear optical view within 1 day, no clear cropland in the radar footprint, or too few flood points: monsoon cloud). Overall accuracy 96% (CI 95–98): criterion met. But I declared in advance that overall accuracy is inflated when most land is dry. Flood-class precision 68%, recall only 9%: when radar says flood it is usually right, but it misses most of the water optical sees, much of it water standing in growing paddy that C-band VH under a canopy doesn't show as a drop." | 96% sounds great, but the honest numbers are 'right 2 of 3 times when it says flood, finds 1 in 10'. Say both. |
| "Recall 9%: your dual trigger denies farmers insurance." | "Yes, that's the trade-off: I chose precision, so Lane 1 catches only 24% of losses but 82% of its payouts are real. Every radar miss is a basis-risk case paid by relief. A 1 dB higher water threshold raised F1 from 0.16 to 0.26 in sensitivity; it can enter only through the gate." | Insurance is strict on purpose; relief is the safety net. |
| "Did radar find the delta damage for Arnab?" | "No. The scoring rule was committed before computing, and it failed: my top three were Guntur, Srikakulam, West Godavari; the State's are East Godavari, West Godavari, Krishna. In the delta, radar water is 3–8% of reported damage. ERA5 rain peaked in Vizianagaram / Srikakulam (~200 mm) while the delta got 80–96 mm; ERA5 wind ranks the delta districts in the damage order, so the likely loss is **wind lodging** of mature paddy, which radar can't see. The delta's first image (4 Nov) also came after Murasu's rain. Next season: a wind trigger relative to each mandal's history, through the gate." | Radar sees water; this damage was mostly wind. |
| "And Murasu?" | "Passed: Prakasam 73,451 > Guntur 19,042 > Nellore 14,496 ha. Seasonal check: Prakasam 9.6% water vs 0.9% in the same weeks of 2024, so it is real; Nellore 3.0% vs 7.7%, no signal, which fits 'largely escaped'. Radar caught what ERA5 rain missed at Prakasam." | A real success, checked against its own season. |

### D2. Validation and statistics
| Question | Answer | 💡 |
|---|---|---|
| "You didn't reach 75%." | "It can't be tested with this data: one district, 7 seasons, losses clustered by season (ICC 0.47), so about 14 independent observations. A true r = 0.75 has a 95% CI of −0.01 to 0.96. What I can show: rainfall-only 20 of 24 wrong; dual 14 of 17 right." | The sample is too small to prove or disprove 75%. |
| "82% sounds good, but how many events?" | "13 of 14 hits are Nivar 2020. I say so; the index re-runs the gate on Kharif 2026 CCE." | Mostly one storm, so I test again. |
| "You chose ERA5 after seeing the data." | "Yes, on screen. My declared consensus design failed (17 payouts, 3 real). ERA5 is on probation until new CCE tests it." | I admit post-hoc choice. |
| "You changed numbers after the bug." | "The bug: a district was scored with one radar pass, so mandals outside it read 0% instead of 'not imaged'. Fixed 14 Nov before scoring; old and new both kept. Lane 1 went from 9 / 7 (78%) to 17 / 14 (82%); the positive control is unchanged." | Fixing a bug openly is not tuning. |
| "Why 80% indemnity?" | "PMFBY offers 70/80/90%; I report all three: 53% / 82% / 94% precision." | Standard options, all shown. |
| "Why 1-in-5 trigger, 1-in-25 exit?" | "A standard return-period design; sensitivity shown: burn cost 7% at 1-in-10/50, 20% at 1-in-3/15. Each mandal uses its own history." | A design choice, with its effect shown. |
| "Hand-picked constants?" | "None hidden: 33% and the rupee rates are MHA norms; 3 dB is Clement 2018; VCI 35 is Kogan; photo limits are percentiles of 982 Department photos; 51 m is the measured median parcel radius." | Every number has a source. |

### D3. Soil, water, crop
| Question | Answer | 💡 |
|---|---|---|
| "Soil moisture?" | "Tested: ERA5-Land root zone and SMAP surface. In YSR, dry soil does not mean loss, because of irrigation; drought plus dry-soil precision was 0–11% vs a 36% base. Evidence only, not in the contract." | I checked, and it didn't help here. |
| "Water balance?" | "I do not claim a water balance. FAO-56 is used for crop-stage timing only." | Don't over-claim. |
| "Irrigation?" | "Unknown for about 70% of YSR acreage and only for Kharif 2026. That is why rainfall-only fails in YSR and why I need the satellite second trigger." | Irrigated crops survive dry spells. |
| "Wind lodging in Manyam?" | "Radar sees water, not flattened plants. Lodging goes to relief enumeration and the basis-risk log; a lodging index can enter only through the gate." | Wind damage is invisible to a flood index. |

### D4. AI, photos, workflow (Kalyan / Mohiuddin too)
| Question | Answer | 💡 |
|---|---|---|
| "Where is the AI?" | "One trained model I claim: the pest classifier, held-out 60% vs Gemini 47% (McNemar p = 0.02). The vision model is general; I call it a suggestion. My fused loss model had AUC 0.53, no skill, so I didn't use it." | Claim AI only where tested. |
| "Is the damage class validated?" | "Partly: 90% of 218 Department diseased photos called damaged (CI 85–93%). False alarms on healthy crop can't be measured, because there are no healthy labels. The officer confirms 33%." | Half-measured; I say which half. |
| "Phone GPS can be faked." | "So can EXIF. Defences: crop booking, timing, crop seen, AEO sampling. A photo never changes insurance." | Photos are evidence, not money. |
| "How much money?" | "Relief: MHA rate × verified ha, computed automatically. Insurance: needs the notified sum insured; one table fill gives rupees." | I didn't invent rupees. |
| "What does the Department get tomorrow?" | "A ranked relief list with standing acres inside 72 h, Telugu/English alerts, a photo check, SDRF sanction workflow, and an insurance decision from a written rule." | The practical value. |
| "Can it scale to all districts?" | "Yes: e-Panta, boundaries, ERA5 and Sentinel-1 are statewide. With cadastral and CCE for a district, the same gate re-runs." | Same code, more data. |

---

### D5. Attacks Murthy used in other hackathons, translated to this one
| Likely question | Answer to say | 💡 For me |
|---|---|---|
| "Flood is per mandal, but you pay per parcel. Do you check inside each parcel? Which survey numbers are only partly flooded?" | "The insurance index is deliberately area-based, like WBCIS and PMFBY's area approach, so neighbours get the same answer and no one argues over a pixel. Where cadastral exists (YSR, 2.23 lakh parcels), each parcel gets its own radar flood flag and Sentinel-2 NDVI series, compared with parcels of the same crop and sowing week; in Michaung 2023 the standing-crop check removed 60% of radar-flagged parcels. A median parcel is 0.82 ha, only about 3 cells after the 50 m speckle filter, so parcel flags are indicative. A 'partly flooded survey numbers' list for AEO priority is the next step for relief, once cadastral comes for Palnadu and Manyam." | Index = mandal on purpose; parcel checks exist for YSR. |
| "Same flood rule for paddy and cotton? Where are the crop-specific criteria, and how are they combined?" | "Crop enters in three places. One, each crop's own FAO-56 duration (paddy 150, cotton 195, chilli 120, groundnut 130 days) decides whether it was standing. Two, the gate is applied per crop against that crop's own loss rate: paddy 27%, the product passes; cotton 54%, not yet, so cotton stays with PMFBY. Three, the combination is explicit: rain AND satellite inside each cover, and total payout = Cover A + Cover B, capped at 100%. Crop-specific damage curves need more CCE; today the loss estimate is pooled (n = 30)." | Crops are treated differently already; say the three places. |
| "Has the Department or a local officer validated this?" | "Not yet in the field: that is built into the workflow. Every relief case closes as 'AEO verified 33% or more' or 'below 33%', which scores my relief list mandal by mandal. I have asked for the Arnab and Murasu enumeration for exactly this." | AEO decisions are the validation loop. |
| "What if it over- or under-estimates? Do you revise?" | "Every season: the qualification gate re-runs on new CCE, and the basis-risk log lists every disagreement. Next season's changes are already listed: a seasonal false-alarm floor, a minimum radar margin, a wind trigger. Each enters only if it passes the gate, never in the middle of a season." | Revision is a rule, not a promise. |
| "Your labels come from e-Panta / Department data, and rule-based IMD alerts already give the same thing in the same time. What is new?" | "e-Panta is used as exposure, what was planted and when, not as a model label. The only trained model is the pest classifier: Department images, 109 near-duplicates removed, tested on held-out photos; field performance is not yet measured. The insurance is rule-based by design, because a contract must be a published formula. What IMD rain alerts don't give: standing-crop acres per mandal from e-Panta, each farmer's crop stage, a second index that confirms, a CCE-tested gate, and the payout and SDRF workflow." | Rule-based on purpose; the value is in the data join and the validation. |
| "e-Panta sowing dates are self-reported. Can you trust them?" | "It is the State's official exposure record, and I use it as that. Sentinel-2 phenology per parcel can check sowing dates; the data is in hand for YSR 2023–26, and that check is post-POC work." | Admit it; say how it would be checked. |

## Part E — Morning checklist (20 minutes before)

1. **Double-click `C:\AP-ParametricInsurance\START_DEMO.bat`.** It opens a black window "AP POC backend": **keep it open for the whole demo** (closing it stops the system, and pages then show "Failed to fetch"). After 45 seconds the dashboard opens by itself.
2. Run the preflight; the last line must say **ALL CLEAR**:
   ```
   py -3.13 C:\AP-ParametricInsurance\poc\preflight.py
   ```
3. Photos are in `poc\data\demo_photos\`: `2_blurry_shaken.jpg` first, then `1_clear_paddy_brown_plant_hopper.jpg`. Form: Event *LIVE · Cyclone Arnab* · Lat 18.5999 · Lon 83.5119 · Taken 2026-10-30 10:00 · Crop Paddy.
4. After any rehearsal, delete `poc\data\compensation_log.jsonl`.
5. Have a phone hotspot as backup. Without internet the photo shows "VISION UNAVAILABLE" and the map is blank; everything else works.
6. Browser full screen at zoom 100%; click every tab once before the judges arrive.
