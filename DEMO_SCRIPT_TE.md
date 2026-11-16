# Demo Guide — Parametric Insurance & Disaster Loss Assessment (Case 100075)

**Demo:** 17 Nov 2026, morning · **10 min demo + 5 min Q&A** · **Dashboard:** http://127.0.0.1:8010/
**How to use this file:**
- **Part A** explains the ideas in plain English. Read it once tonight.
- **Part B** is the story: my approach and the 7 innovations.
- **Part C** goes screen by screen: what is on screen, what I am proving, what I say word for word (simple English), and what it means for me.
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

## Part C — Screen by screen (10 minutes)

> **Format per screen:** 🖥 what is on screen · 🎯 what I am proving · 🗣 what I say (word for word) · 💡 for me (plain meaning)

### 1. Opening (0:45) — no click
🎯 Frame the problem and my core idea before any screen.

🗣 **Say:**
> "Good morning, sir. After a disaster, two things must happen: insurance must pay, and government relief must reach farmers who lost their crop. When the two are mixed, both become slow.
> So I separated them into two lanes. Lane 1 is insurance: it pays by a formula on measured indices, with no claim and no field visit. Lane 2 is relief: it checks real damage within 72 hours, using radar, e-Panta, phone photos and the AEO.
> I tested every index on the Department's own crop-cutting yields, and I will show you what failed as well. I also ran the system live on Cyclones Arnab and Murasu."

💡 You are saying: insurance = automatic formula; relief = field truth; I proved my indices on government yield data; I am honest about failures.

### 2. Overview (1:00) — Sidebar → *Overview*
🖥 Satellite hero; KPI tiles (7 pilot mandals, 22 disasters, 20 → 0, 6,25,401 bookings, 60%); the two-lane diagram; the map.
🎯 Innovations 1, 2 and 4: the architecture, and why rainfall-only insurance fails.

🗣 **Say** (point at the two-lane diagram):
> "This diagram is my solution.
> On top is Lane 1, insurance. It pays only when two independent signals agree: rainfall **and** satellite. And every farmer's crop stages start from his own sowing date in e-Panta, not one date for the whole mandal.
> Below is Lane 2, relief. Radar maps flooding, e-Panta keeps only crops that were standing that day, and photos or the AEO confirm the damage.
> Look at this tile: 20 to 0. In YSR Kadapa, rainfall-only cover paid 24 times, and 20 of those had no real loss in the crop-cutting yields. With the satellite check added, wrong season payouts went to zero.
> And if I used one mandal calendar instead of each farmer's own sowing date, 1 lakh 9 thousand bookings would flip between paid and not paid."

💡 "20 → 0": of 24 rainfall-only payouts, 20 went to farmers with no real loss; adding the satellite check removed those wrong season payouts.

### 3. Live: Cyclone Arnab (2:20) ⭐ — Sidebar → *Live: Cyclone Arnab*
🖥 LIVE badge; KPIs **15** relief mandals, **6** above the rain trigger, **1** index payout (Salur), **T+69 h**; the timeline cards; the mandal table; "Reading" and "Limits" cards.
🎯 Innovation 7: the whole system worked on a real cyclone, both lanes, with my weakness stated.

🗣 **Say:**
> "Cyclone Arnab crossed the coast near Yanam on 28 October. I ran the same code I used for the back-tests. I did not tune anything for this storm.
> **Relief lane first.** Within 69 hours of landfall, the relief list and the Telugu and English alerts were out. On the final rainfall data, 15 mandals in Manyam are open for enumeration, with 1.22 lakh acres of standing crop.
> **Now the insurance lane.** If I looked at rainfall alone, 6 mandals would be paid between 22% and 80% of the sum insured. The radar confirmed only one of them, Salur, at 34.5%. The other 5 are held.
> I want to point out a weakness myself. In Salur the radar signal was small, 0.6% of cropland, but the payout is 34.5%, because radar only confirms and rainfall sets the amount. Also, my false-alarm level comes from February and March, a different season. For next season I will test two fixes through my qualification gate: a false-alarm level from the same weeks of calm years, and a minimum radar signal.
> I also found and fixed a bug on 14 November. My code used one radar pass for a whole district, so mandals outside that pass were read as 'no flood' instead of 'not imaged'. I fixed it before scoring and kept both the old and the new results.
> On timing: only 5 of the 15 mandals had a radar image within 72 hours. Sentinel-1 passes here only once in 12 days. That is why relief never waits for radar."

🗣 **Murasu (15 sec):**
> "Cyclone Murasu, 3 November: 20 mandals in Palnadu were opened for relief, and insurance paid nothing. In Chilakaluripet the radar showed 22% of cropland flooded, but the rain stayed below the contract level. So relief pays and insurance doesn't, and the case goes into my basis-risk log. This is exactly why I keep two lanes."

💡
- **Relief opened fast** on rainfall alone, without waiting for radar.
- **Insurance waited** for the second index.
- **Salur paid**, but on a weak signal. Admitting it before Murthy finds it earns credibility.
- **"T+69 h"** = 69 hours after landfall, under the 72-hour target.
- **Basis-risk example:** Chilakaluripet shows the two lanes disagreeing, which is exactly what the log is for.

### 4. Insurance product (1:15) — Sidebar → *Insurance product*
🖥 Term sheet; qualification-gate table (each index: payouts, real, precision CI, pass/fail); premium.
🎯 Innovations 2 and 3: the index had to prove itself on government yields, and my own first design failed.

🗣 **Say:**
> "This is my qualification gate. In the crop-cutting data, a loss happens in 36% of mandal-years anyway. So an index enters the contract only if, even at the low end of its confidence range, it is right more often than 36%.
> Rainfall-only cover is right 17% of the time. It fails.
> The design I declared first, three rainfall sources plus radar, paid 17 times and only 3 were real. It also fails, and I keep that on the screen.
> My final product paid 17 times and 14 were real losses: 82%, with a range of 59 to 94%. To be honest, 13 of those 14 come from one storm, Cyclone Nivar in 2020, and I chose this combination after seeing the data. So it will be tested again on the 2026 crop-cutting yields.
> The premium also drops: in YSR, rainfall-only cover costs 24.9% of the sum insured; my dual-trigger cover costs 9.4%. A lower premium means a lower farmer share and a lower State subsidy."

💡
- **Precision 82%** = about 8 in 10 payouts went to real losses. The range 59–94% is wide because the data is small.
- The Nivar point is a weakness: most hits come from one storm. Saying it first protects you.
- **Burn cost** = the average yearly payout, the "pure" premium before the insurer's margin.

### 5. Photo verification — Module B (2:00) — Sidebar → *Photo verification* (live)
🖥 Upload form; results with ✓/✗ per check; verdict; recommended interventions; the "Insurance unchanged" line.
🎯 Requirement B: a quality-checked, location-checked photo with damage class, confidence, pest ID and interventions, which never changes insurance.

🗣 **(a) Upload `2_blurry_shaken.jpg`, then say:**
> "If a farmer sends a blurred photo, it is stopped at the first check: retake photo. Nothing else runs on a bad photo. I set these limits from 982 of the Department's own field photos: 91% of genuine photos pass, and every degraded copy is refused."

🗣 **(b) Upload `1_clear_paddy_brown_plant_hopper.jpg`, then say:**
> "Now a clear photo. Each check is shown separately: photo quality, location in Balijipeta, timing inside the cyclone window. The vision model sees paddy, severely damaged, with a confidence score and a photo loss estimate, and the crop matches the booking.
> My trained pest model identifies brown plant hopper, a pest that spreads after floods, and gives the recommended actions from the DPPQS, ICAR and ANGRAU packages, with sources.
> And the last line: insurance is unchanged. A photo never changes an insurance payout. Because I typed the location, it says 'manual GPS, officer to verify'.
> The pest model was trained on Department images and scores 60% on photos it never saw, against 47% for Gemini. It is a suggestion for the officer, not a diagnosis."

🗣 **Phone (10 sec):**
> "There is also a phone page. It opens the camera and records the phone's GPS at the moment of the photo. A location counts only if it is accurate to 51 metres, which is the size of a typical parcel in YSR."

💡
- **The first photo** shows that a bad photo is rejected before anyone wastes time on it.
- **The second** shows every check, the pest, and what the farmer should do.
- **"Insurance unchanged"** is the two-lane rule in action.
- **"60% on photos it never saw"** (held-out) is the honest way to measure a model.

### 6. Compensation (1:20) — Sidebar → *Compensation*
🖥 KPIs: **15** relief cases, budget **₹12.6–25.2 cr**, **13,096** settlement lines, audit ✓. Relief-case table with states; the insurance batch with its SHA-256; the audit log.
🎯 Requirement A: the compensation workflow, from trigger to money, with official norms and an audit trail.

🗣 **Say:**
> "This is the compensation workflow.
> On the relief side, each of the 15 Arnab mandals is a case. It moves from opened, to evidence received when a photo arrives, to AEO verified with the hectares that lost 33% or more, to sanctioned, to paid. The sanction is calculated automatically from the MHA disaster-relief rates: 8,500 rupees per hectare rainfed and 17,000 irrigated. The budget estimate for Arnab is 12.6 to 25.2 crore. That is a planning number, not a payment list.
> The MHA rules also say relief is reduced when insurance has already paid for the same disaster. That is exactly the link between my two lanes, and Salur is that case.
> On the insurance side, Gurazala 2023 is one settlement batch of 13,096 bookings. The file is locked with a digital fingerprint, so the file that is approved is the file the insurer receives. To show rupees I need the notified sum insured. It wasn't shared, so I didn't invent it.
> Every action is recorded with the officer's role, in a log that shows 'broken' if anyone edits a line."

💡
- **The budget** is a planning estimate. Who actually gets paid is decided by the AEO's verified hectares.
- **SHA-256** is a digital fingerprint: if anyone edits the payout file after approval, the fingerprint changes and the system refuses it.
- (Optional live click: Balijipeta → "AEO verify ≥33%" → 120 rainfed + 30 irrigated → Sanction → ₹15,30,000. Delete `poc\data\compensation_log.jsonl` afterwards.)

### 7. Limits + close (1:20) — Sidebar → *Validation & limits* (or no click)
🎯 Say the limits before Murthy does, then make one clear ask.

🗣 **Say:**
> "Before you ask, here are my limits.
> One: the 75% target cannot be tested with this data: one district, 7 seasons, only about 14 independent data points. It needs about 25 seasons.
> Two: flood accuracy. The APSDMA maps were not shared, so I compared with the Sentinel-2 optical satellite. Overall accuracy is 96%, above the 80% target. But most land is dry, so the honest numbers are these: when my radar says flood, it is right 2 times in 3, but it finds only 1 in 10 of the water the optical satellite sees. That is why relief never depends on radar.
> Three: for Arnab, my radar did not find the delta districts where the State reported the most damage. Most of that damage was wind flattening the paddy, which radar cannot see. Next season I will test a wind trigger. For Murasu the radar did find the worst district, Prakasam.
> Four: parcel maps exist only for YSR, and irrigation is unknown for 70% of the land.
> I have one request: the mandal-level crop-damage enumeration for Arnab and Murasu, so I can score my predictions. Thank you."

💡 Saying failures first is my strategy: Murthy respects honest concessions and hammers hidden flaws.

| Screen | Time |
|---|---|
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
