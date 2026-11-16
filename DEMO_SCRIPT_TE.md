# Demo Script (తెలుగు) — Parametric Insurance & Disaster Loss Assessment, Case 100075

**Demo:** 17 నవంబర్ 2026, ఉదయం · **సమయం:** 10 నిమిషాలు demo + 5 నిమిషాలు Q&A
**Dashboard:** http://127.0.0.1:8010/ (ముందే Ctrl + F5 చేయండి)
**Rule:** ప్రతి number కి source చెప్పాలి. Limit ని Murthy గారు అడగకముందే మనమే చెప్పాలి.
**Numbers:** ఈ script లోని అన్ని numbers 16 Nov rebuild (corrected radar method) నుండి. Screen మీద ఉన్నవే చెప్పండి.

---

## 0. Demo ముందు (ఉదయం, 20 నిమిషాలు ముందు)

1. Backend start: Claude app లో `poc-backend` (లేదా uvicorn 127.0.0.1:8010). **1 నిమిషం ఆగండి** (photo layers background లో load అవుతాయి).
2. Preflight run చేయండి — చివర **ALL CLEAR** రావాలి:
   ```
   py -3.13 C:\AP-ParametricInsurance\poc\preflight.py
   ```
   - "vision ... not read as paddy every time" వస్తే: మళ్ళీ run చేయండి; రెండోసారి కూడా వస్తే photo demo లో "vision suggestion మాత్రమే" అని చెప్పి ముందుకు వెళ్ళండి.
   - Rehearsal తర్వాత: `poc\data\compensation_log.jsonl` delete చేయండి.
3. Photos: `poc\data\demo_photos\` — `2_blurry_shaken.jpg` (మొదట), `1_clear_paddy_brown_plant_hopper.jpg` (తర్వాత). Form: Event *LIVE · Cyclone Arnab*, Lat 18.5999, Lon 83.5119, Taken 2026-10-30 10:00, Crop Paddy.
4. Internet కి phone hotspot backup. Internet లేకపోతే photo "VISION UNAVAILABLE" అంటుంది, map ఖాళీ — మిగతా అంతా offline పని చేస్తుంది.
5. Earth Engine demo లో run చేయవద్దు. Browser full screen, zoom 100%. Tabs ముందే ఒకసారి click చేసి చూడండి.

---

## 1. Opening — 0:30

> "నమస్కారం సార్. మేము problem ని **రెండు lanes** గా విడదీశాం, ఎప్పుడూ కలపం.
> **Lane 1 — Insurance:** ముందే ఒప్పుకున్న index మీద formula payout. Claim లేదు, field visit లేదు.
> **Lane 2 — Relief (SDRF):** నిజమైన నష్టాన్ని 72 గంటల్లో — radar, e-Panta, photo, AEO తో.
> ప్రతి index ని Department **CCE yields** మీద test చేశాం; fail అయినవి కూడా చూపిస్తాం. ఈ నెల వచ్చిన **Cyclone Arnab, Murasu** మీద live గా run చేశాం."

## 2. Overview — 1:00
**Click:** Sidebar → *Overview* (hero + KPIs + two-lane diagram)

> "Rainfall-only cover (ఇప్పటి WBCIS style) YSR CCE మీద **24 సార్లు pay చేసింది, 20 తప్పు**. Dual trigger — rainfall **మరియు** satellite రెండూ — false season payouts ని **20 నుండి 0** కి తెచ్చింది.
> ప్రతి రైతు payout అతని **సొంత e-Panta sowing date** నుండి — mandal calendar వాడితే 1,09,039 bookings paid/not-paid మారిపోతాయి. అదే basis risk."

## 3. Live: Cyclone Arnab — 2:30 ⭐
**Click:** Sidebar → *Live: Cyclone Arnab*

> "Arnab 28 Oct న Yanam దగ్గర తీరం దాటింది. Back-test చేసిన **అదే code**.
> - **Relief:** T+69 గంటలకు relief list, Telugu/English alerts. ERA5 final తర్వాత **15 Manyam mandals**, 1.22 లక్షల standing acres.
> - **Insurance:** Rainfall మాత్రమే చూస్తే 6 mandals కి **22% నుండి 80%** sum insured pay చేయాల్సి వచ్చేది. Radar **ఒక్క Salur** ని మాత్రమే confirm చేసింది — 34.5%. మిగతా 5 hold.
> - **మనమే చెప్పాల్సింది:** Salur లో radar signal 0.60% మాత్రమే (floor 0.07%), కానీ payout 34.5% — ఎందుకంటే radar confirm మాత్రమే చేస్తుంది, amount rain నిర్ణయిస్తుంది. ఇది weakness. Next season కి **minimum-signal rule** ని qualification gate ద్వారా test చేస్తాం — mid-event contract మార్చం.
> - **Bug fix (14 Nov):** మా radar code ఒక district మొత్తానికి ఒకే pass వాడింది; ఆ pass కవర్ చేయని mandals ని '0% flood' అని చదివింది — 'not imaged' అనాలి. Fix చేశాం, పాత-కొత్త results రెండూ ఉంచాం. ఈ fix వల్లే Salur payout వచ్చింది.
> - **Radar timing:** 15 లో 5 mandals మాత్రమే 72 గంటల్లో imaged; మిగతావి 4 Nov (T+172 h). Sentinel-1 ఇక్కడ 12 రోజులకు ఒకసారి — 72 h లో image వచ్చే chance 24–49% (2021–2026 metadata). అందుకే relief radar కోసం ఆగదు."
> **Murasu (మాటల్లో, 15 సెకన్లు):** "3 Nov Murasu — Palnadu లో 20 mandals relief, insurance 0. Chilakaluripet లో radar 22.4% flood చూపించింది కానీ rain contract level కి చేరలేదు — relief pay చేస్తుంది, insurance చేయదు, case **basis-risk log** లోకి. ఇదే two lanes ఎందుకు అనేదానికి example."

## 4. Insurance product — 1:30
**Click:** Sidebar → *Insurance product*

> "Qualification gate: ఏ index అయినా CCE precision యొక్క Wilson 95% lower bound, base loss rate (36%) కంటే ఎక్కువ ఉంటేనే contract లోకి.
> - మా Lane 1 product (80% indemnity): **17 payouts, 14 నిజమైన నష్టాలు — 82% (CI 59–94%)**, losses లో 24% catch.
> - Honest గా: 14 లో 13 hits 2020 **Nivar** ఒక్కటే. ERA5 × SAR design data చూసిన తర్వాత ఎంచుకున్నాం. మేము ముందే declare చేసిన 3-source consensus × SAR design **fail** అయింది (17 payouts, 3 real).
> - Premium (pure burn cost, YSR): rainfall-only **24.9%** vs dual **9.4%** of sum insured."

## 5. Photo verification (Module B) — 2:00 — live
**Click:** Sidebar → *Photo verification*

**(a) `2_blurry_shaken.jpg`:**
> "Blur photo — మొదటి check లోనే **RETAKE PHOTO**. Analysis అసలు run కాదు. Limits Department యొక్క 982 field photos నుండి measure చేశాం: genuine 91% accept, degraded 100% refuse."

**(b) `1_clear_paddy_brown_plant_hopper.jpg`:**
> "ప్రతి check వేరుగా: quality ✓, location Balijipeta ✓, timing ✓, vision — Paddy, Severely damaged, confidence, photo loss % — crop match ✓, మా trained pest model — **brown plant hopper**, తర్వాత **DPPQS / ICAR / ANGRAU** నుండి interventions.
> చివరి line: insurance **మారదు**. Location type చేశాం కాబట్టి 'MANUAL GPS, OFFICER TO VERIFY'.
> Pest model Department images మీద train: held-out **60%** (Gemini 47%, McNemar p=0.02) — officer కి suggestion మాత్రమే. Damage class: Department diseased photos లో 90% ని damaged అని చెప్పింది; healthy labels లేవు కాబట్టి false alarm measure కాలేదు — **33% ని officer confirm చేస్తారు**."
> **Phone app (10 సెకన్లు):** "`/poc/capture.html` — phone camera, capture క్షణంలో phone GPS; accuracy 51 m (YSR median parcel radius) లోపు ఉంటేనే geotag."

## 6. Compensation — 1:30
**Click:** Sidebar → *Compensation*

> "Requirement A — compensation workflow.
> - **Relief:** Arnab 15 mandals = 15 cases. Photo → AEO verified hectares → sanction **MHA SDRF norms** (10 Oct 2022) నుండి ఆటోమేటిక్: ₹8,500/ha rainfed, ₹17,000/ha irrigated. Budget estimate **₹12.6–25.2 కోట్లు** — planning number, payment list కాదు.
> - MHA norms లోనే ఉంది: **PMFBY claim వస్తే input subsidy తగ్గుతుంది** — Salur లో insurance pay చేసింది కాబట్టి అక్కడ relief నుండి ఆ amount తగ్గుతుంది. ఇదే Lane 1 / Lane 2 link.
> - **Insurance:** Gurazala 2023 — 13,096 bookings ఒక settlement batch, SHA-256 తో lock. Rupees కి notified **sum insured** కావాలి — మాకు ఇవ్వలేదు, invent చేయలేదు.
> - ప్రతి action officer role తో, hash-chain audit log లో."

## 7. Limits + closing — 1:00

> "Limits, మీరు అడగకముందే:
> 1. **≥75% correlation:** CCE YSR కి మాత్రమే, 7 seasons; losses season-wise cluster అవుతాయి — ~14 independent observations. ఈ data తో 75% ని prove చేయలేం, reject కూడా చేయలేం; ~25 seasons కావాలి.
> 2. **≥80% flood accuracy vs APSDMA:** APSDMA maps ఇవ్వలేదు. Budameru 2024 positive control **PASS** (5.61% vs 1.41% dry floor). Sentinel-2 తో accuracy comparison జరుగుతోంది — **ఇంకా score కాలేదు**.
> 3. Cadastral YSR కి మాత్రమే; irrigation source 70% unknown; radar 72 h లో 24–49% chance.
> **ఒకే ఒక request:** Arnab, Murasu mandal-level crop-damage enumeration — మా predictions ని score చేయడానికి. ధన్యవాదాలు."

| Screen | సమయం |
|---|---|
| Opening | 0:30 |
| Overview | 1:00 |
| **Live: Cyclone Arnab** | 2:30 |
| Insurance product | 1:30 |
| Photo verification (live) | 2:00 |
| Compensation | 1:30 |
| Limits + closing | 1:00 |
| **మొత్తం** | **10:00** |

సమయం తక్కువ అయితే: Overview ని 0:30 కి, Compensation ని 1:00 కి తగ్గించండి. Live Arnab, Photo ని తగ్గించవద్దు.

---

## 8. Q&A — 5 నిమిషాలు (ఒక్కో answer 20–30 సెకన్లు)

| ప్రశ్న | సమాధానం |
|---|---|
| "Accuracy 75% రాలేదు కదా?" | "Data తో test చేయలేం: CCE ఒక district, 7 seasons, ~14 independent observations. r=0.75 కి 95% CI −0.01 నుండి 0.96. మేము చూపించగలిగింది: rainfall-only 24 లో 20 తప్పు; dual 17 లో 14 సరైనవి." |
| "Salur 0.6% signal తో 34.5% ఎలా?" | "అది మా design weakness — మేమే screen మీద రాశాం. Radar confirm, rain amount. Minimum-signal rule next season gate ద్వారా; mid-event contract మార్చం." |
| "Bug తర్వాత numbers మార్చారా?" | "Bug: district కి ఒకే pass; cover కాని mandals ని 0% అని చదివింది. 14 Nov fix, scoring ముందే; పాత-కొత్త రెండూ ఉన్నాయి. Fix తో precision 78% → 82%, payouts 9 → 17. Positive control మారలేదు, PASS." |
| "Radar 172 గంటల తర్వాత — నీళ్ళు పోయి ఉంటాయి" | "అవును, అందుకే radar రెండో trigger మాత్రమే, loss కి ఏకైక evidence కాదు. Relief 72 h లో rain + photo + AEO తో నడుస్తుంది. 72 h chance 24–49% — metadata నుండి measure చేశాం." |
| "Flooded paddy లో backscatter పెరుగుతుంది (double bounce)" | "Test చేశాం, rule ముందే declare: VV rise Budameru లో 5.4% vs dry date 3.5% — ratio 1.55 < 2, signal లేదు. అందుకే drop-only rule ఉంచాం." |
| "Speckle, orbit matching?" | "VH, orbit-matched pre/post, 50 m focal median; threshold ప్రతి event Otsu (JRC water + cropland sample); ≥3 dB drop (Clement 2018); JRC permanent water, HAND>15 m, <8-pixel clusters mask. Lee (1980) filter, 2/4 dB variants తో sensitivity study ముందే declare చేశాం — ఇంకా score కాలేదు." |
| "ERA5 ఎందుకు, IMD కాదా?" | "ERA5, CHIRPS, IMERG మూడూ CCE మీద gate లో test చేశాం; ERA5 మాత్రమే pass. IMD gridded మాకు reach కాలేదు; Department ఇస్తే అదే gate లో పెడతాం." |
| "Manyam రైతులు నష్టపోతే?" | "Relief 15 mandals లో open. Wind lodging flood index కి కనిపించదు — enumeration లో వస్తే relief pay, basis-risk log." |
| "Photo GPS fake చేయొచ్చు" | "EXIF కూడా fake చేయొచ్చు. Defence: crop booking, timing, crop seen, AEO sampling. Photo ఎప్పుడూ insurance payout ని మార్చదు." |
| "AI అంటున్నారు — ఎక్కడ?" | "Trained model ఒక్కటే అని claim: pest classifier, held-out 60%. Vision model general — 'suggestion' అంటాం. Fused loss model AUC 0.53 — skill లేదు, వాడలేదు." |
| "Rupees ఎంత?" | "Relief: MHA norms × verified ha — computed. Insurance: notified sum insured కావాలి; ఒక table fill చేస్తే వస్తాయి." |
| "Scale చేయగలరా?" | "Code district-agnostic: e-Panta + boundaries + ERA5 + Sentinel-1 open. Cadastral, CCE వచ్చిన district కి అదే gate re-run." |
