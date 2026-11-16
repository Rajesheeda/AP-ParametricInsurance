# Demo Script (తెలుగు) — Parametric Insurance & Disaster Loss Assessment, Case 100075

**Demo:** 17 నవంబర్ 2026, ఉదయం · **సమయం:** సుమారు 15 నిమిషాలు + Q&A
**Dashboard:** http://127.0.0.1:8010/poc/ (ముందే Ctrl + F5 చేయండి)
**Rule:** ప్రతి number కి source చెప్పాలి. Limit ని Murthy గారు అడగకముందే మనమే చెప్పాలి.

---

## 0. Demo ముందు checklist (ఉదయం)

1. Live data refresh (ERA5 / కొత్త radar pass కోసం):
   ```
   cd C:\AP-ParametricInsurance\poc\pipeline
   py -3.13 p25_live_event.py --radar ap-early-warning
   py -3.13 p23_farmer_payouts.py
   py -3.13 p26_compensation.py
   py -3.13 p19_alerts.py
   py -3.13 p14_dashboard_data.py
   ```
   తర్వాత backend restart చేయండి (farmer data reload కోసం). Restart తర్వాత 1 నిమిషం ఆగండి (photo layers background లో load అవుతాయి).
   Rehearsal లో చేసిన workflow actions తీసేయాలి: `poc\data\compensation_log.jsonl` delete చేయండి; test photos `poc\data\photo_evidence.jsonl` నుండి తీసేయండి.
2. Photo demo కోసం రెండు photos ready గా ఉంచండి: ఒకటి clear గా ఉన్న వరి photo, ఒకటి blur photo.
3. Internet check (photo లో vision model కి అవసరం). Earth Engine live గా demo లో run చేయవద్దు — results అన్నీ ముందే compute అయ్యాయి.
4. Browser full screen, zoom 100%.

---

## 1. Opening (30 సెకన్లు)

> "నమస్కారం సార్. మేము ఈ problem ని **రెండు lanes** గా విడదీశాం.
> **Lane 1 — Insurance:** ముందే ఒప్పుకున్న **index** మీద formula ప్రకారం payout. Claim form లేదు, field visit లేదు.
> **Lane 2 — Relief:** నిజమైన పంట నష్టాన్ని **72 గంటల్లో** assess చేస్తాం — radar, e-Panta, photo, AEO ద్వారా.
> ప్రతి index ని Department ఇచ్చిన **CCE yields** మీద test చేశాం. ఏది fail అయిందో అది కూడా publish చేశాం. Chance కంటే బాగా పనిచేసిన index మాత్రమే contract లోకి వస్తుంది.
> ఇంకా — ఈ వారమే వచ్చిన **Cyclone Arnab** మీద మా system ని, code ఏమీ మార్చకుండా, live గా run చేశాం. అది కూడా చూపిస్తాం."

---

## 2. మా Innovation — 7 points (ఇది మా pitch యొక్క core)

| # | Innovation | ఎందుకు ముఖ్యం (తెలుగులో చెప్పాల్సింది) |
|---|---|---|
| 1 | **Two lanes, never mixed** | Parametric insurance అంటే payout index మీద మాత్రమే. Photo లేదా field visit insurance payout ని మార్చదు. కానీ రైతుకి నష్టం జరిగితే Relief lane (SDRF, ≥33% damage) వెంటనే పని చేస్తుంది. రెండూ కలిపితే parametric యొక్క speed, objectivity పోతాయి. |
| 2 | **Dual trigger** | Rainfall index **మరియు** satellite index (VCI / Sentinel-1 flood) రెండూ దాటితేనే payout. Rainfall-only (ఇప్పటి WBCIS style) YSR లో 24 సార్లు pay చేసింది — అందులో **20 తప్పు**. మా product 9 సార్లు pay చేసింది — **7 నిజమైన నష్టాలకు** (78%). |
| 3 | **Index qualification gate** | ఏ index అయినా contract లోకి రావాలంటే CCE మీద దాని precision (Wilson 95% lower bound) base loss rate (36%) కంటే ఎక్కువ ఉండాలి. ప్రతి season re-run. మా సొంత consensus design ఈ gate లో **fail** అయింది — అది కూడా చూపిస్తాం. |
| 4 | **ప్రతి రైతు సొంత sowing date** | FAO-56 crop stages ప్రతి e-Panta booking యొక్క sowing week నుండి మొదలవుతాయి. Mandal calendar వాడితే 6 pilot mandals లో **1,09,039 bookings** paid / not-paid మారిపోతాయి — అది basis risk. |
| 5 | **e-Panta gate on radar** | Radar కి నీళ్ళు కనిపిస్తాయి కానీ అది వరి నాట్లు (puddling) వల్లా, flood వల్లా అని తెలియదు. e-Panta sowing dates తో standing crop మాత్రమే count చేస్తాం. Michaung 2023 లో radar flags లో **60%** ఇలా తొలగించాం. |
| 6 | **Quality-gated, parcel-locked photos** | Blur / dark photo మొదటే refuse — "RETAKE PHOTO". Thresholds Department యొక్క 982 field photos నుండి measure చేశాం (hand-picked కాదు). Genuine photos 91% accept, degraded photos 100% refuse. |
| 7 | **Live test (Cyclone Arnab)** | Back-test చేసిన అదే code ని తుఫాను జరుగుతుండగానే run చేశాం — 72 గంటల లోపే relief list, alerts. కొత్త radar pass / ERA5 వచ్చినప్పుడు numbers update అవుతాయి. |

---

## 3. Screen-by-screen script

### Screen 1 — Overview (1.5 నిమిషాలు)
**Click:** Sidebar → *Overview*
**చూపించాల్సింది:** Hero heading, "Two lanes, never mixed" card, KPIs, pilot mandals map.

> "ఇది మా decision engine. పైన Lane 1 — insurance: qualified rainfall index, satellite index, రైతు సొంత calendar, formula payout.
> కింద Lane 2 — relief: radar damage map, e-Panta gate, CCE-calibrated loss estimate, photo లేదా AEO enumeration.
> రెండు lanes ఎక్కడ disagree అవుతాయో అది **basis-risk log** లోకి వెళ్తుంది. Index levels season మధ్యలో మారవు — season ల మధ్య మాత్రమే re-test చేస్తాం.
> Pilot: 7 mandals — Parvathipuram, Balijipeta (Manyam), Gurazala, Sattenapalle (Palnadu), Chapad, Khajipet (YSR), Vedurukuppam (Chittoor Rabi). Written rule ద్వారా select చేశాం."

---

### Screen 2 — Live: Cyclone Arnab (3 నిమిషాలు) ⭐ main highlight
**Click:** Sidebar → *Live: Cyclone Arnab*

**(a) Timeline card చూపించండి:**
> "Cyclone Arnab — very severe cyclonic storm — 28 అక్టోబర్ తెల్లవారుజామున Yanam దగ్గర తీరం దాటింది. మేము hours ని IMD చెప్పిన earliest time (02:00 IST) నుండి లెక్కించాం — అంటే మా hours conservative.
> - Rainfall: ERA5 (contract index) 5–6 రోజులు late గా publish అవుతుంది. అందుకే ఇప్పుడు **provisional** గా ECMWF IFS వాడాం — ERA5 దాని నుండే తయారవుతుంది. GFS, ICON spread గా చూపిస్తున్నాం.
> - **6 Manyam mandals** rainfall trigger దాటాయి — Parvathipuram, Balijipeta (మా pilots), Salur, Makkuva, Palakonda, Pachipenta.
> - **T+69 గంటలకు** relief list, alerts issue చేశాం.
> - T+69 గంటలకు **16 mandals** కి relief enumeration open చేశాం. 31 Oct update లో ECMWF rain పెరిగి Palnadu లో ఇంకో 4 mandals (Sattenapalle, Amaravathi, Pedakurapadu, Krosuru) 99th percentile ని కొద్దిగా దాటాయి — ఇప్పుడు **20 mandals** (సుమారు 1.6 లక్షల standing acres, e-Panta 2026). Relief list rain data తో పెరుగుతుంది; insurance మాత్రం ఇంకా 0. Telugu/English alerts తో — 72 గంటల లోపే."

**(b) KPI "0 index payouts" చూపించండి:**
> "Sentinel-1 radar 30 అక్టోబర్ (T+52 h) pass — orbit-matched, 5 pre-storm images తో — Manyam లో ఏ mandal లోనూ standing crop మీద false-alarm floor కంటే ఎక్కువ flood చూపించలేదు. అందుకే **insurance payout లేదు**.
> Rainfall-only cover అయితే ఈ 6 mandals కి 6–15% pay చేసేది. Dual trigger hold చేసింది."

**(c) Table లో Balijipeta row చూపించండి:**
> "Balijipeta: ECMWF 167 mm, trigger 150 mm, rain side 15.4%. కానీ radar flood 0.01%, floor 0.8%. కాబట్టి Insurance: *Held*. Relief: *Photo / AEO* — relief ఆగలేదు."

**(d) "Reading" card:**
> "మొదటి official figures (Deccan Chronicle, 28 Oct, preliminary) ప్రకారం ఎక్కువ నష్టం **Godavari delta** లో — West Godavari 76,176 ha, Konaseema 44,232, Kakinada 42,222, East Godavari 29,866, Krishna 22,339 — ఎక్కువగా నీట మునిగిన వరి. Manyam ఆ list లో లేదు. మా radar result దానితో consistent. కానీ ఇది ఇంకా score కాదు — Department యొక్క mandal-level SDRF enumeration వచ్చాక, committed file లో రాసిన rule ప్రకారం score చేస్తాం."

**(e) "Limits" card — మనమే చెప్పాలి:**
> "Limits: ERA5 ఇంకా రాలేదు, rainfall provisional. Radar కి నిలిచిన నీళ్ళు కనిపిస్తాయి — గాలికి పడిపోయిన వరి (**lodging**) కనిపించదు. Delta కి తదుపరి Sentinel-1 pass 4 నవంబర్ — 12-day revisit. Manyam కి cadastral లేదు."

---

### Screen 3 — Disasters & relief (Lane 2) (2 నిమిషాలు)
**Click:** Sidebar → *Disasters & relief*
**చూపించాల్సింది:** Radar before/after slider (Budameru 2024 → తర్వాత Manyam Sep 2026), events table.

> "ఇది Sentinel-1 radar. Slider drag చేస్తే before / after — cyan రంగులో detected flood.
> **Method:** VH polarisation, orbit-matched pre/post, 50 m focal median (speckle filter), water threshold ప్రతి event కి Otsu method తో known water (JRC) మీద learn అవుతుంది, ≥3 dB drop (Clement 2018), permanent water మరియు HAND > 15 m mask.
> **Positive control** — rule ముందే declare చేసి run చేశాం: Budameru / Vijayawada floods, Sep 2024 → **PASS**: flooded cropland 5.6% vs dry floor 1.4%; Vijayawada Rural, Mangalagiri లో 18–22%.
> Limit: 22 events లో **8 events** కే radar 72 గంటల లోపు వచ్చింది. అందుకే ప్రతి result కి image date, evidence grade (A/B/C) చూపిస్తాం."

**Events table:** "C / E / I rain" columns చూపించండి:
> "CHIRPS, ERA5, GPM IMERG — మూడు rainfall products ని పక్క పక్కన చూపిస్తున్నాం. Insurance column, Relief column వేరు వేరు."

---

### Screen 4 — Insurance product (Lane 1) (2.5 నిమిషాలు)
**Click:** Sidebar → *Insurance product*

**(a) Term sheet:**
> "Cover A — season: WBCIS structure (FAO-56 stages, deficit, excess, dry spell) **మరియు** MODIS VCI < 35 (Kogan).
> Cover B — catastrophe: ERA5 3-day rainfall, mandal యొక్క సొంత 1-in-5 నుండి 1-in-25 వరకు linear payout **మరియు** Sentinel-1 flood on standing crops above floor."

**(b) Qualification gate table:**
> "ఇది ముఖ్యమైన screen. ప్రతి candidate index ని CCE మీద test చేశాం.
> - మేము ముందే declare చేసిన CHIRPS + ERA5 + IMERG consensus × SAR design — **17 payouts, 2 మాత్రమే నిజం → REJECTED**. దీనిని దాచలేదు.
> - ERA5 × SAR మాత్రమే gate pass అయింది. ఇది data చూసిన తర్వాత ఎంచుకున్నాం — అది screen మీదే రాశాం. దాని hits ఎక్కువగా Nivar 2020 — అందుకే Kharif 2026 CCE వచ్చేవరకు ఇది **probation** లో ఉంది.
> - Final Lane 1 product: **9 payouts, 7 నిజం (78%, CI 45–94%)**, base rate 36%."

**(c) Premium card:**
> "Dual trigger premium కూడా తగ్గిస్తుంది. Pure burn cost 2001–2024: season cover rainfall-only **13.2%** → dual **2.5%** of sum insured. YSR రెండు covers కలిపి **24.9% → 5.9%** (4.3–8.2%). Farmer share, State subsidy రెండూ ఈ premium మీదే."

---

### Screen 5 — Farmer payouts (1.5 నిమిషాలు)
**Click:** Sidebar → *Farmer payouts*

**(a) Summary table:**
> "6 pilot mandals లో Kharif 2023–25 **5,22,208 e-Panta bookings** ప్రతి దాని సొంత sowing week మీద price చేశాం. **1,09,039 bookings** mandal calendar వాడితే paid / not-paid మారిపోతాయి.
> ఉదాహరణ: Balijipeta 2023 — 27,401 bookings సొంత calendar లో rainfall trigger అయ్యాయి, mandal calendar లో ఒక్కటీ కాదు. కానీ ఆ season VCI 100 (record లోనే అత్యంత పచ్చగా) — dual trigger వల్ల ఎవరికీ pay కాలేదు. సరైన నిర్ణయం."

**(b) Look-up — Gurazala, 2023 select చేయండి:**
> "Gurazala 2023: rainfall trigger మరియు VCI 30 రెండూ — **13,096 bookings** కి payout, acre-weighted సుమారు 39%. Sum insured box లో notified scale of finance type చేస్తే రూపాయల్లో చూపిస్తుంది. రైతు పేర్లు చూపించం, store చేయం."

**(c) Balijipeta, 2026 select చేయండి:**
> "ఇదే Cyclone Arnab live status — ప్రతి booking కి: 'ARNAB_2026: no payout (radar does not confirm)'. Season cover ఇంకా open."

---

### Screen 6 — Farmer alerts (45 సెకన్లు)
**Click:** Sidebar → *Farmer alerts*

> "Decisions నుండి Telugu + English alerts ఆటోమేటిక్ గా తయారవుతాయి. Arnab కోసం 20 mandals కి: relief enumeration open, photo ఎలా పంపాలి, నీళ్ళు తీసివేయండి, bacterial leaf blight / sheath blight / BPH గమనించండి — **మరియు** insurance status వేరుగా.
> Limit: Telugu machine-drafted — Department review తర్వాతే farmers కి పంపాలి."

---

### Screen 7 — Photo verification (Module B) (2.5 నిమిషాలు) — live demo
**Click:** Sidebar → *Photo verification*

**(a) Blur photo upload చేయండి:**
> "Farmer blur photo పంపితే — మొదటి check లోనే **RETAKE PHOTO**. App అక్కడే మళ్ళీ తీయమని అడుగుతుంది. Limits Department యొక్క 982 photos నుండి measure చేశాం."

**(b) Clear వరి photo upload చేయండి (Event: LIVE · Cyclone Arnab):**
> "ప్రతి check వేరుగా:
> 1. Photo quality ✓
> 2. Geotag — EXIF GPS (manual అయితే lower trust)
> 3. Location — ఏ mandal; YSR లో ఏ cadastral parcel, survey number
> 4. e-Panta booking — ఆ parcel లో ఆ రోజు ఏ పంట ఉంది
> 5. Timing — event window లో తీసిందా
> 6. Vision — Healthy / Partially / Severely damaged, **confidence**, **photo loss %**
> 7. Crop match — photo లో పంట = booking లో పంట
> 8. **Pest / disease** — మా trained model top-3 suggestion
> 9. **Recommended interventions** — DPPQS, ICAR, ANGRAU packages నుండి, source తో.
> చివరి line చూడండి: *'Insurance (Lane 1) is decided by the index only and is unchanged'* — photo insurance ని మార్చదు. Photo damage చూపించి index pay చేయకపోతే — **basis-risk log** లోకి."

**(c) Honest గా చెప్పాల్సింది:**
> "Pest model Department images మీద train చేశాం: held-out accuracy **60%** (53–66%), Gemini 47% — same images, McNemar p = 0.02. ఇది officer కి **suggestion** మాత్రమే, decision కాదు.
> Damage class — Department యొక్క 218 diseased-crop photos మీద 90% ని damaged అని చెప్పింది (CI 85–93%). Healthy crop మీద false alarm, loss % — measure చేయలేం, Department Label Studio లో healthy / severity labels లేవు. అందుకే **33% SDRF threshold ని officer confirm చేస్తారు**. Interventions లో chemical dose ఇవ్వం — ANGRAU current recommendation, AEO ద్వారా మాత్రమే."

---

### Screen 7b — Phone app + Compensation (2 నిమిషాలు)
**Phone app:** `http://127.0.0.1:8010/poc/capture.html` (laptop లో browser mobile view, లేదా phone).
> "Requirement B1 — mobile app. Farmer phone లో ఈ page open చేసి 'Add to Home screen' చేస్తే app లా పని చేస్తుంది. Camera నేరుగా తెరుచుకుంటుంది, తీసిన క్షణంలో **phone GPS** తీసుకుంటుంది.
> ఎందుకు: Android browsers upload లో photo EXIF location ని తీసేస్తాయి — EXIF మీద ఆధారపడితే చాలా మంది రైతుల photos fail అవుతాయి.
> GPS accuracy **51 m** లోపు ఉంటేనే geotag గా accept — అది YSR median parcel radius (cadastral నుండి measure చేశాం, 0.82 ha). అంతకంటే coarse అయితే manual గా treat చేసి officer verify చేస్తారు. పేరు, phone number collect చేయం."

**Click:** Sidebar → *Compensation*
> "Requirement A — compensation workflow.
> - **Relief (Lane 2):** Arnab లో 20 mandals = 20 cases. OPENED → photo వస్తే EVIDENCE RECEIVED → AEO ≥33% loss hectares enter చేస్తారు → **sanction MHA SDRF norms** నుండి ఆటోమేటిక్: ₹8,500/ha rainfed, ₹17,000/ha irrigated (MHA letter 10 Oct 2022) → paid.
> - Budget estimate **₹16.7–33.5 cr**: standing acres × CCE లో acute event తర్వాత ≥33% loss వచ్చిన share (30%, CI 17–48%) × rate. ఇది SDRF memorandum కి planning number — ఎవరికి pay అనేది AEO verification నిర్ణయిస్తుంది.
> - **Insurance (Lane 1):** Gurazala 2023 — 13,096 bookings ఒక settlement batch. Approve → insurer కి send → paid. File SHA-256 తో lock — approve చేసిన file నే insurer కి వెళ్తుంది.
> - Rupees కి notified **sum insured (scale of finance)** కావాలి — మాకు ఇవ్వలేదు, మేము invent చేయలేదు. ఒక table fill చేస్తే rupees వస్తాయి.
> - ప్రతి action officer role తో, hash chain log లో — ఒక line మార్చినా 'chain broken' చూపిస్తుంది.
> - MHA norms లోనే ఉంది: PMFBY claim వస్తే input subsidy నుండి తగ్గిస్తారు — అదే మా Lane 1 / Lane 2 link."

**Live గా చూపించాలంటే:** Balijipeta row → *AEO verify ≥33%* → role "AEO Balijipeta", rainfed 120, irrigated 30 → *Sanction* → ₹15,30,000 (120×8,500 + 30×17,000). Demo తర్వాత log file delete చేయండి.

---

### Screen 8 — Validation & limits (2 నిమిషాలు)
**Click:** Sidebar → *Validation & limits*

**(a) Success criteria card:**
> "PPT targets ఒక్కొక్కటి:
> - **≥75% correlation:** ఇచ్చిన data తో measure చేయడం సాధ్యం కాదు — కింద statistics.
> - **≥80% flood accuracy vs APSDMA:** APSDMA maps share కాలేదు; బదులుగా ముందే declare చేసిన positive control (Budameru PASS) మరియు measured false-alarm floor.
> - **72-hour assessment:** Relief lane లో met — Arnab లో live గా చూపించాం.
> - **5-year back-test:** ఉన్న data మీద done — CCE 2019–25 (YSR), premium 2001–2024."

**(b) Statistical power card — ఇది accuracy ప్రశ్నకు సమాధానం:**
> "CCE ఒక district కి, 7 seasons కి మాత్రమే వచ్చింది, PMFBY claims రాలేదు.
> ఒక cyclone ఒకే season లో అన్ని mandals ని కొడుతుంది — ICC 0.47, design effect 11.7 (Kish). అంటే 166 mandal-crop-years లో నిజానికి **సుమారు 14 independent observations, సుమారు 5 independent loss events** మాత్రమే.
> Best weather system detection CI **0–82%** — 75% దాని లోపలే ఉంది. 7 seasons లో true r = 0.75 అయినా CI **−0.01 నుండి 0.96** — zero నుండి వేరు చేయలేం. Test చేయాలంటే సుమారు **25 seasons** లేదా districts pool చేయాలి.
> Data ఏది చూపించగలదో అది clear గా చూపిస్తుంది: rainfall-only cover తప్పు seasons లో pay చేస్తుంది; second index వల్ల false payouts చాలా వరకు పోతాయి."

**(c) మేము try చేసి వదిలేసినవి (credibility కోసం):**
> "Fused ML loss model — CCE మీద AUC 0.53, అంటే skill లేదు — **వాడలేదు**. Soil moisture — YSR లో irrigation వల్ల dry soil ≠ loss — evidence only. Model fail అయితే దాన్ని 'AI' అని చూపించం."

---

### Closing (30 సెకన్లు)
> "సారాంశం:
> 1. **Insurance:** index మీద మాత్రమే, dual trigger, CCE gate pass అయిన index మాత్రమే, ప్రతి రైతు సొంత sowing date — false payouts 20 నుండి 0, premium 13.2% నుండి 2.5%.
> 2. **Relief:** 72 గంటల్లో radar + e-Panta + quality-gated photo — Arnab లో live గా చేశాం.
> 3. **Honesty:** ఏది fail అయిందో, ఏ data లేదో ముందే చెప్పాం. Arnab ని live గా run చేసి చూపించాం.
> Department నుండి ఒకే ఒక request: Arnab యొక్క mandal-level crop-damage enumeration — మా prediction ని score చేయడానికి. ధన్యవాదాలు."

---

## 4. Limits — Murthy గారు అడగకముందే చెప్పాలి

1. CCE YSR Kadapa కి మాత్రమే, 7 seasons; PMFBY claims లేవు; APSDMA maps లేవు.
2. Radar 22 events లో 8 కే 72 గంటల లోపు; Sentinel-1 revisit 6–12 రోజులు.
3. Cadastral parcels YSR కి మాత్రమే (సుమారు 56% villages).
4. YSR లో సుమారు 70% acreage కి irrigation source తెలియదు.
5. ERA5 data చూసిన తర్వాత ఎంచుకున్నాం; mandal centroid వద్ద read చేస్తాం.
6. Telugu alerts machine-drafted; pilot mandals నుండి real field photos ఇంకా collect కాలేదు.
7. Photo damage class / loss % — validate కాని model estimate.

---

## 5. Quick Q&A (తెలుగులో సమాధానం)

| ప్రశ్న | సమాధానం |
|---|---|
| "NDVI / VCI loss కాదు." | "అవును సార్. మేము దాన్ని loss అనం. Loss అంటే Department CCE yield మాత్రమే (normal లో 70/80/90% కంటే తక్కువ). VCI contract లో second **index** మాత్రమే." |
| "Parametric insurance fundamental principle ఏమిటి?" | "Payout పూర్తిగా ముందే ఒప్పుకున్న objective index మీద — loss adjustment లేదు. దాని ధర basis risk — దాన్ని measure చేయాలి. అదే మా Lane 1." |
| "Field validation parametric లో భాగమా?" | "కాదు. మా design లో photo / field visit insurance payout ని **ఎప్పుడూ** మార్చదు. అది Lane 2 relief కి మరియు season ల మధ్య index recalibration కి మాత్రమే." |
| "India లో parametric ఉందా?" | "ఉంది — WBCIS (2007 నుండి), PMFBY కింద RWBCIS. మా Cover A అదే term-sheet structure. మేము 3 విషయాలు fix చేశాం: dual trigger, రైతు సొంత calendar, qualification gate." |
| "ERA5 coarse కదా?" | "Assume చేయలేదు సార్ — CHIRPS (5 km), IMERG (10 km), ERA5 (25 km) మూడూ CCE మీద test చేశాం. Finer products October 2024 లో (loss 2% మాత్రమే) fire అయ్యాయి. ERA5 మాత్రమే gate pass. Hypothesis: YSR losses cyclone వంటి synoptic systems నుండి." |
| "Radar flood — puddling కాదని ఎలా తెలుసు?" | "Radar ఒక్కటే చెప్పలేదు — measure చేశాం: SAR alone precision 33% vs base 36%, chance లెవెల్. అందుకే 3 filters: e-Panta standing-crop gate, paddy planting window, per-mandal false-alarm floor." |
| "43% threshold ఎలా ఎంచుకున్నారు?" | "43% అనే threshold లేదు సార్. ప్రతి level cited లేదా measured: 1-in-5 / 1-in-25 return period, PMFBY 70/80/90%, SDRF 33%, VCI < 35 (Kogan), 3 dB (Clement 2018), Otsu, photo limits Department photos నుండి." |
| "Accuracy 75% రాలేదు." | "ఇచ్చిన data తో 75% ని confirm కానీ reject కానీ చేయలేం — 14 independent observations, detection CI 0–82%. Data చూపించగలిగింది: rainfall-only తప్పుగా pay చేస్తుంది, dual trigger దాన్ని fix చేస్తుంది." |
| "Insurance lane 12% losses మాత్రమే పట్టుకుంది." | "Design ప్రకారమే — రెండు independent indices ఒప్పుకుంటేనే pay. 2021, 2022 losses కి ఏ rainfall product లోనూ signal లేదు — అవి relief మరియు PMFBY area-yield కి; basis-risk log లో record చేస్తాం, దాచం." |
| "Arnab లో Manyam రైతులకు నష్టం జరిగితే ఏమీ రాదా?" | "Relief enumeration 20 mandals లో 72 గంటల్లో open అయింది. Lodging వంటి నష్టం flood index కి కనిపించదు — అది basis-risk case. Lodging index season ల మధ్య gate pass అయితేనే contract లోకి; event మధ్యలో contract మార్చం." |
| "ECMWF, ERA5 కాదు కదా?" | "అవును. అందుకే **provisional** అని label చేశాం. Settlement ERA5 వచ్చాకే. GFS, ICON spread (Balijipeta లో 126–262 mm) — అందుకే forecast model మీద settle చేయం." |
| "Pest model AI నా?" | "Trained classifier — EfficientNet features + logistic regression, Department 1,124 images మీద train, held-out 60% vs Gemini 47% (p = 0.02). Officer కి suggestion మాత్రమే." |
| (Insurance section) "Premium ఎంత?" | "Pure burn cost 2001–2024: season cover dual 2.5% of SI (rainfall-only 13.2%); YSR రెండు covers 5.9% (4.3–8.2%). Insurer loading వేరు." |
| (Insurance section) "రైతుకి డబ్బు ఎలా వస్తుంది?" | "e-Panta booking ప్రతి దానికి payout % × sum insured × acres — నేరుగా account కి, claim form లేదు. Catastrophe cover radar వచ్చాక (6–12 రోజులు), season cover season చివర." |

---

## 6. Timing guide

| Screen | సమయం |
|---|---|
| Opening | 0:30 |
| Innovation (మాటల్లో, Overview మీద) | 1:00 |
| Overview | 1:30 |
| **Live: Cyclone Arnab** | 3:00 |
| Disasters & relief | 2:00 |
| Insurance product | 2:30 |
| Farmer payouts | 1:30 |
| Farmer alerts | 0:45 |
| Photo verification (live) | 2:30 |
| Phone app + Compensation | 2:00 |
| Validation & limits | 2:00 |
| Closing | 0:30 |
| **మొత్తం** | **సుమారు 20 నిమిషాలు** (సమయం తక్కువ అయితే Disasters & relief, Alerts ని తగ్గించండి) |
