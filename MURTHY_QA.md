# Demo Q&A sheet (17 Nov 2026)

Each answer gives a short reply, the number behind it, and the dashboard screen to open.
Sources: `POC_REPORT.md` sections in brackets. **Rule: say the limit before he does.**

## Opening (30 seconds)
"We split the problem in two. **Insurance** pays on a pre-agreed index, by formula, with no claim and no visit. **Relief** assesses real damage in 72 hours. We tested every index against the Department's own crop-cutting yields. We published what failed. Only indices that beat chance are allowed into the contract. And this week we ran it, unchanged, on Cyclone Arnab."

---

## Cyclone Arnab (open the Live tab first)
**30-second version:**
- Arnab crossed the coast near Yanam early on 28 October. Our code was not touched.
- By T+69 hours we had opened 16 mandals for relief enumeration and issued Telugu and English alerts. On final ERA5 (published to 10 Nov) it is 15, all in Manyam.
- On ERA5 rainfall alone, 6 Manyam mandals would pay 22–80% of sum insured.
- Radar confirmed one: **Salur, 34.5%**. The other 5 are held.
- Radar timing: 5 of the 15 relief mandals were imaged at T+52 h (30 Oct); the other 10 were first imaged on 4 Nov (T+172 h).
- **Bug fix, 14 Nov, before scoring.** Each district had been scored with its first pass, so mandals outside it read "0% flood" instead of "not imaged". Each mandal now uses the earliest orbit-matched pass covering half its cropland. Salur was not imaged on 30 Oct; on 4 Nov it shows 0.60% flooded vs a 0.07% floor. The first run said 0 payouts; the corrected run says 1. Both are kept.
- The first official figures put the damage in the Godavari delta (submerged paddy), not in Manyam. That's consistent with the radar, but not yet a score.

**"So farmers in Manyam who lost crops get nothing?"**
- They get relief enumeration: 16 mandals within 72 h, 15 on final ERA5.
- Insurance pays only what two indices agree on. If enumeration finds wind-lodged paddy that a flood index can't see, it's a basis-risk case and goes into the log.
- A lodging index would have to pass the gate between seasons. We don't change the contract mid-event.

**"Salur: a 0.6% radar signal unlocks a 34.5% payout?"**
- Yes, and we state it on the screen as a design weakness: radar only confirms, rainfall sets the amount.
- A minimum-signal rule is a candidate for next season, entering only through the qualification gate. We don't change the contract mid-event.

**"Radar 172 hours later: the water had drained."**
- Possible on sloping Manyam fields. That's why radar is the *second* trigger and never the only evidence of loss; relief runs on rainfall and photos inside 72 h.
- Sentinel-1 repeats every 12 days over the pilot mandals: P(image within 72 h) is 24% (one track) to 49% (two tracks), unchanged 2021–2026 (acquisition metadata). The delta was imaged on 4 Nov, about 7 days after landfall.

**"Flooded paddy raises backscatter (double bounce). Your drop-only rule misses it."**
- We tested it with a rule declared first: a VV rise of 3 dB or more covers 5.4% of cropland after Budameru, but 3.5% on a dry February date. Ratio 1.55, below the declared 2×: no usable signal at C-band here, so the drop-only rule stays.

**"Cyclone Murasu?"**
- 3 Nov, near Ongole. 20 Palnadu mandals opened for relief (Sattenapalle and Gurazala included); 0 index payouts, all below the 1-in-5 level (Amaravathi 189.0 vs 189.1 mm).
- First radar 9 Nov (T+149 h). Chilakaluripet 22.4% flooded vs a 2.0% floor, but rainfall below the contract level: relief pays, insurance doesn't, and it is logged as basis risk. Not pre-registered; run on the frozen rules.

**"ECMWF is not ERA5."**
- Correct. ERA5 is published about 5–6 days late, so during the event the rainfall side was labelled *provisional*. Settlement waited for ERA5 (now final).
- We used ECMWF IFS because ERA5 is built from it, and we show GFS and ICON as the spread: 126–262 mm at Balijipeta. That spread is the reason we don't settle on a forecast model.

**"How will you know you were right?"**
- The scoring rule is in `poc/ARNAB_PREREGISTRATION.md`: share of damaged mandals our relief list named, and share of our payouts that went to damaged mandals.
- The outcome is the Department's mandal-level SDRF enumeration. That's one ask, and they produce it anyway.

---

## Murthy's questions

**1. "NDVI / VCI is not a loss proxy."**
Agreed. We never call it loss.
- Loss comes only from the Department's CCE yields: below 70/80/90% of the mandal's normal.
- VCI is a *contract index*, the second trigger, not a loss estimate.
- *Screen:* Validation → Ground truth. [7.4]

**2. "Calling a rainfall deviation or NDVI drop 'loss' is wrong."**
Same answer. Our words are "index", "stress" and "trigger"; the only "loss" is measured CCE yield loss.
- The yield estimate attached to each decision is the median *real* CCE loss when that trigger type fired, with its sample size (acute 25%, n=30). [7.6]

**3. "This is only drought monitoring."**
No. It is multi-peril:
- Season cover: deficit, excess and dry spell by FAO-56 stage.
- Catastrophe cover: extreme 3-day rain and cyclones, confirmed by Sentinel-1 radar flood.
- Relief lane: radar-mapped flooding within 72 h.
- *Screen:* Insurance product → term sheet; Disasters & relief.

**4. "MODIS has latency; you can't do 36–72 h with it."**
Correct, and we don't.
- MODIS VCI is used only for the *season* cover, which settles at season end.
- The 72-hour relief assessment uses daily rainfall and Sentinel-1.
- Limit, said first: radar arrived within 72 h for 8 of 22 events. Every result carries its image time.
- Sentinel-1C (6-day revisit with 1A from 2025) shortens that. [7.3, 8]

**5. "ERA5 is too coarse."**
We didn't assume. We tested three products against real yields.
- CHIRPS (about 5 km), ERA5 (about 25 km) and GPM IMERG (about 10 km), each against its own record.
- The finer products were worse: CHIRPS and IMERG fired in October 2024, a season with about 2% loss.
- ERA5 was the only index that passed the qualification gate.
- Our explanation, a hypothesis: YSR losses come from synoptic systems such as cyclones, which reanalysis captures; local convective bursts that satellites flag do little damage at mandal scale.
- Limit: ERA5 is read at the mandal centroid. [7.8, 7.9]

**6. "What is the fundamental principle of parametric insurance?"**
The payout is determined solely by an objective, pre-agreed index, with no loss adjustment. The price is basis risk, which must be measured.
- That is exactly Lane 1. *Screen:* Overview → "Two lanes, never mixed".

**7. "Is field validation part of parametric insurance?"**
No. In our design a photo or field visit **never** changes an insurance payout.
- Field evidence belongs to Lane 2 (SDRF relief: input subsidy where damage is 33% or more).
- Field evidence also feeds the basis-risk log that recalibrates the index *between* seasons.
- *Screen:* Photo verification → the resolution line says "insurance unchanged".

**8. "Is there any parametric system in India?"**
Yes. WBCIS (since 2007) and Restructured WBCIS under PMFBY: weather-index cover on reference weather stations, using term sheets with phase-wise deficit, excess and dry-spell covers.
- Our Cover A uses that same term-sheet structure on purpose.

**9. "Then why build another one?"**
Because on the State's own yields, the WBCIS-style rainfall-only cover pays mostly in the wrong seasons. We fix three things:
1. **Dual trigger.** Rainfall-only paid in 24 mandal-crop-years, 20 of them with no real loss. Our product paid in 17, 14 of them real (82%, CI 59–94%; after the 14 Nov radar fix, 9 / 7 before). [7.9]
2. **Each farmer's own sowing date** instead of one calendar per reference area. 109,039 of 522,208 bookings in the 6 pilot mandals flip between paid and not paid depending on the calendar. [7.10]
3. **A qualification gate** with published failures. Our own pre-declared consensus design failed, and we report it. [7.9]

Bonus: the premium falls from 13.2% to 2.5% of sum insured for the season cover. [7.12]
- *Screen:* Insurance product; Farmer payouts.

**10. "Farmers will upload blurry images."**
They are refused before anything else, and the app asks for a retake.
- Limits are percentiles of 982 Department field photos (blur = variance of Laplacian, exposure, clipping, resolution). None is hand-picked.
- Held-out test: 91% of genuine photos accepted; 100% of blurred, motion-blurred, dark, overexposed and low-resolution copies refused. [7.11]
- *Screen:* Validation → Photo quality gate.

**11. "How did you choose the 43% threshold?"**
There is no 43%. Every level is cited or measured:
- 1-in-5 trigger and 1-in-25 exit return periods, from each mandal's own record.
- PMFBY 70/80/90% indemnity levels.
- SDRF 33% damage.
- VCI < 35 (Kogan).
- Radar change of 3 dB or more (Clement 2018).
- The water threshold learned by Otsu each event.
- The photo limits measured on Department photos.

---

## Follow-ups he is likely to push

**"Your accuracy is below the 75% target."**
The data shared can't measure a 75% target either way:
- CCE was shared for 1 district and 7 seasons, with no PMFBY claims.
- Losses cluster by season (ICC 0.47), so 166 mandal-crop-years carry about 14 independent observations and about 5 independent loss events.
- The best weather system's detection rate has a season-bootstrap CI of **0–82%**, which contains 75%.
- A true correlation of 0.75 over 7 seasons has a CI of **−0.01 to 0.96**. About 25 seasons are needed.

What the data *can* show, it does: rainfall-only cover pays wrongly, and a second index fixes most of that. [7.13] *Screen:* Validation → Statistical power.

**"Your insurance lane catches only 24% of losses."**
By design it pays only what two independent indices agree on.
- The 2021 harvest-time floods and the 2022 losses had no rainfall signal in any product, and radar saw them only partly.
- No index can see those. They belong to relief and PMFBY area-yield, and we log them as basis risk instead of hiding them.

**"You picked ERA5 after seeing the data."**
Yes, and we say so on the screen.
- Our declared consensus design failed (17 payouts, 3 real after the radar fix; 2 before).
- After the radar fix the Lane 1 product pays 17 times, 14 real (82%, CI 59–94%), but 13 of the 14 hits are cyclone Nivar 2020. ERA5's hits are mostly Nivar, so it is on probation until the Kharif 2026 CCE tests it out of sample.

**"Radar flood: how do you know it's not paddy puddling?"**
Radar alone *can't* tell, and we measured that: Sentinel-1 alone performed at about chance (33% precision vs a 36% base rate). So we use three filters:
- **e-Panta standing-crop gate:** removed 60% of radar flags in Michaung.
- **Paddy planting-window gate:** paddy sowing within −30/+15 days of the event.
- **Per-mandal false-alarm floor**, measured on dry-season dates.

The method itself:
- VH polarisation, orbit-matched pre/post images, 50 m focal median (speckle).
- Otsu threshold on a sample of known water and cropland, plus a 3 dB change rule.
- JRC permanent water and HAND > 15 m masked.
- Positive control declared in advance: Budameru 2024 PASS (5.6% vs 1.4% floor). [3.1, 7.3]

**"MODIS 250 m on small parcels: mixed pixels."**
Yes. VCI is a mandal-level index for the season cover, not a parcel measurement.
- The parcel-level option is Sentinel-2 cohort NDVI (10 m, same crop and sowing week). It is built for YSR but not yet validated against loss, so it is not in the contract.

**"Irrigation."**
About 70% of YSR acreage has unknown irrigation source, and the data exists for Kharif 2026 only.
- It is why rainfall deficit doesn't mean loss in YSR: the soil-moisture test showed dry soil ≠ loss. [7.5]
- The satellite trigger is what protects against paying irrigated crops.

**"Is the pest model AI?"**
It is a trained classifier: EfficientNet features plus logistic regression.
- Trained on 1,124 Department images; 60% held-out accuracy vs 47% for Gemini on the same images (McNemar p = 0.02).
- It is a suggestion for the officer, never a decision.

---

## Insurance section (Kalyan / Mohiuddin)

**"What is the premium?"**
- Pure burn cost 2001–2024: season cover dual **2.5%** of sum insured (rainfall-only 13.2%).
- YSR with both covers: **9.4%** (7.2–11.4%) vs 24.9% rainfall-only (after the radar fix; it was 5.9% when un-imaged mandals were read as dry, which under-counted payouts).
- The insurer adds loading. [7.12]

**"What sum insured?"**
The notified DLTC scale of finance; it is an input on the Farmer payouts screen, not something we set.

**"How does the farmer get paid?"**
- The index is computed per e-Panta booking on the farmer's own sowing week.
- Payout % × sum insured × acres goes to the account, with no claim form.
- Example: Gurazala 2023, 13,096 bookings, about 39% acre-weighted. *Screen:* Farmer payouts.

**"When does it settle?"**
- Catastrophe cover: when the radar image arrives (6–12 days).
- Season cover: at season end.
- Relief enumeration starts within 72 h.

**"What does the Department get from this tomorrow?"** (Arnab)
- A ranked list of 15 mandals for enumeration with standing acres from e-Panta, plus alerts, inside 72 hours.
- An insurance decision from a written rule, applied the same way as in the back-tests.

**"What if the farmer lost a crop and the index didn't pay?"**
- They get Lane 2 relief enumeration (SDRF, 33% damage or more) and PMFBY area-yield where applicable.
- The case enters the basis-risk log used to recalibrate the index before next season.

---

## Say these limits first
1. CCE is available for YSR only, 7 seasons; no PMFBY claims; no APSDMA maps.
2. Radar is within 72 h with probability 24–49% per pilot mandal (12-day repeat); for Arnab 5 of 15 relief mandals.
3. Parcel polygons exist for YSR only (about 56% of villages).
4. Irrigation is unknown for about 70% of YSR acreage.
5. ERA5 was chosen after seeing the data and is read at the mandal centroid.
6. Telugu alerts are machine-drafted. No pilot-mandal field photos have been collected yet.

## Compensation and the phone app (added 31 Oct)

**"Where is the compensation workflow? I see percentages, not money."**
- Compensation tab. Insurance: settlement batches per mandal-season, one line per e-Panta booking with its index evidence, then approve → send to insurer → paid. The approved file is hash-locked.
- Rupees need the notified sum insured (scale of finance). It wasn't shared and we did not invent it: the batch is in sum-insured acres until the Department fills one table.
- Relief: each Arnab mandal is a case. AEO enters verified hectares → sanction computed from the MHA SDRF norms (₹8,500 / ₹17,000 per ha, ≥33%) → paid. Every step is logged by role with a hash chain.

**"₹12.6–25.2 crore relief for Arnab: where does that come from?"**
- Standing acres from e-Panta 2026 × 30% (share of acute-trigger mandal-years with CCE loss ≥33%, YSR, CI 17–48%) × MHA rate. Irrigation is unknown in Manyam, so rainfed and irrigated ends are both shown.
- It is a planning number for the SDRF memorandum, not a payment list. With no trigger, 24% of mandal-years also reach 33%, so the trigger separates weakly; we say so on the screen.

**"Phone GPS can be faked."**
- Yes, and so can EXIF. A device fix counts only if its accuracy is within 51 m (the median YSR parcel radius, measured). Beyond that it is treated as manual and an officer verifies.
- The defences are the checks that don't depend on GPS honesty (crop booked on that parcel, timing, crop seen) plus AEO sampling. A photo never moves an insurance payout.

**"Is the Healthy / Partially / Severely classifier validated?"**
- Partly. On 218 Department photos of diseased crop it called 90% damaged (CI 85–93%). Its false alarms on healthy crop and its loss % are not measured, because no healthy or severity-labelled images exist in the Department's Label Studio.
- So it is evidence for the officer, and the officer confirms the 33% line.

